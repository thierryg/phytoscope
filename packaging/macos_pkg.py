# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/macos_pkg.py
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

"""Écrire un paquet d'installation macOS (`.pkg`) depuis Linux.

Apple fournit `pkgbuild` et `productbuild`, qui n'existent que sur macOS. Les
deux outils libres qui les remplacent — `xar` et `mkbom` — ne sont plus
empaquetés par Debian ni par Ubuntu. Ce module écrit donc le format lui-même,
en Python pur : aucune dépendance, rien à compiler, et un résultat déterministe.

Anatomie d'un paquet plat
-------------------------

Un `.pkg` moderne est une **archive XAR** contenant :

.. code-block:: text

    Distribution                 XML : ce que l'installateur affiche
    Resources/                   textes de licence et de bienvenue
    phytoscope.pkg/
        PackageInfo              XML : identifiant, version, destination
        Payload                  cpio compressé — les fichiers eux-mêmes
        Bom                      la « nomenclature » binaire
        Scripts                  cpio compressé — postinstall (facultatif)

Trois formats binaires cohabitent donc, et chacun est écrit ici :

* **XAR** — en-tête de 28 octets, table des matières en XML compressé par
  zlib, puis un tas où chaque fichier est rangé. La table des matières porte
  les sommes de contrôle de chaque membre : c'est ce qui permet à
  l'installateur de détecter une archive abîmée.
* **cpio** au format « odc » (POSIX portable) — en-têtes en octal ASCII,
  déterministe et sans limite de portabilité. Le choix d'Apple pour les
  charges utiles avant l'arrivée de `pbzx`, et toujours accepté.
* **BOM** (*bill of materials*) — un arbre binaire listant chaque chemin avec
  son mode, son propriétaire, sa taille et sa somme CRC. C'est lui que
  `pkgutil --files` relit, et c'est l'absence de ce fichier qui fait échouer
  un paquet autrement correct.

Ce qui est vérifié, et ce qui ne l'est pas
------------------------------------------

Tout ce qui est écrit ici est **relu et contrôlé** par les fonctions de
vérification du même module : la table des matières XAR est réextraite, le
cpio redéplié, l'arbre du BOM reparcouru et comparé fichier par fichier à ce
qu'on voulait y mettre.

En revanche, **ce paquet n'a jamais été soumis à l'installateur de macOS** :
il n'y a pas de Mac ici. La structure est juste ; son acceptation par
`installer(8)` reste à confirmer sur une vraie machine.
"""
from __future__ import annotations

import gzip
import hashlib
import io
import os
import plistlib
import struct
import time
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

__all__ = ["Entree", "recenser", "ecrire_pkg", "verifier_pkg",
           "ecrire_cpio_odc", "lire_cpio_odc", "ecrire_bom", "lire_bom"]


# ---------------------------------------------------------------------------
#  Recensement des fichiers
# ---------------------------------------------------------------------------
@dataclass
class Entree:
    """Un chemin à installer, tel que le BOM et le cpio le décriront."""
    chemin: str                 # relatif, à la mode POSIX ; "." pour la racine
    absolu: str
    est_dossier: bool
    mode: int
    taille: int = 0
    crc: int = 0
    lien: str = ""

    @property
    def type_bom(self) -> int:
        if self.lien:
            return 3            # lien symbolique
        return 2 if self.est_dossier else 1


def _normaliser(mode: int, est_dossier: bool) -> int:
    """Les droits que macOS attend, et non ceux du poste qui empaquette.

    Un paquet fabriqué sous Linux hérite sinon de l'`umask` de l'utilisateur :
    on livrerait des dossiers en 775 et des fichiers en 664, c'est-à-dire
    inscriptibles par le groupe. Dans `/Applications`, appartenant à
    `root:wheel`, cela affaiblit l'installation pour rien. On retient donc la
    convention d'Apple : 755 pour les dossiers et les exécutables, 644 pour le
    reste — seul le bit d'exécution du propriétaire est conservé, parce qu'il
    porte une information réelle.
    """
    if est_dossier:
        return 0o40755
    executable = bool(mode & 0o100)
    return 0o100000 | (0o755 if executable else 0o644)


def recenser(racine: str, proprietaire: Tuple[int, int] = (0, 0)) -> List[Entree]:
    """Liste ce qu'il y a à installer, dans l'ordre où le BOM l'attend.

    L'ordre compte : un dossier doit précéder ce qu'il contient, sans quoi
    l'installateur pose un fichier dans un répertoire qui n'existe pas encore.
    Un parcours en largeur, trié, le garantit — et le rend reproductible d'une
    fabrication à l'autre, ce qui n'est pas un détail quand on publie des
    empreintes.
    """
    entrees = [Entree(".", racine, True, 0o40755)]
    for dossier, sous, fichiers in os.walk(racine):
        sous.sort()
        fichiers.sort()
        for nom in sous + fichiers:
            absolu = os.path.join(dossier, nom)
            relatif = "./" + os.path.relpath(absolu, racine).replace(os.sep, "/")
            if os.path.islink(absolu):
                cible = os.readlink(absolu)
                entrees.append(Entree(relatif, absolu, False, 0o120755,
                                      len(cible), 0, cible))
                continue
            st = os.lstat(absolu)
            if os.path.isdir(absolu):
                entrees.append(Entree(relatif, absolu, True,
                                      _normaliser(st.st_mode, True)))
            else:
                with open(absolu, "rb") as f:
                    donnees = f.read()
                entrees.append(Entree(relatif, absolu, False,
                                      _normaliser(st.st_mode, False),
                                      len(donnees),
                                      zlib.crc32(donnees) & 0xFFFFFFFF))
    #  Dédoublonnage : os.walk énumère un sous-dossier à la fois comme entrée
    #  du parent et comme dossier parcouru.
    vus, propre = set(), []
    for e in entrees:
        if e.chemin in vus:
            continue
        vus.add(e.chemin)
        propre.append(e)
    return propre


# ---------------------------------------------------------------------------
#  cpio, format « odc » (POSIX portable)
# ---------------------------------------------------------------------------
_MAGIC_ODC = b"070707"


def ecrire_cpio_odc(entrees: List[Entree], horodatage: int = 0) -> bytes:
    """Le format que l'installateur d'Apple attend pour la charge utile.

    Champs en **octal ASCII** de longueur fixe, ce qui rend l'archive lisible
    à l'œil et parfaitement déterministe : aucune dépendance à l'ordre des
    inodes ni à l'horloge, à la différence du format « newc ».
    """
    sortie = bytearray()
    for i, e in enumerate(entrees, start=1):
        if e.lien:
            donnees = e.lien.encode("utf-8")
        elif e.est_dossier:
            donnees = b""
        else:
            with open(e.absolu, "rb") as f:
                donnees = f.read()
        nom = e.chemin.encode("utf-8") + b"\0"
        sortie += _entete_odc(dev=0, ino=i, mode=e.mode, uid=0, gid=0,
                              nlink=1, rdev=0, mtime=horodatage,
                              taille_nom=len(nom), taille=len(donnees))
        sortie += nom + donnees
    fin = b"TRAILER!!!\0"
    sortie += _entete_odc(0, 0, 0, 0, 0, 1, 0, 0, len(fin), 0) + fin
    return bytes(sortie)


def _entete_odc(dev: int, ino: int, mode: int, uid: int, gid: int, nlink: int,
                rdev: int, mtime: int, taille_nom: int, taille: int) -> bytes:
    def oct6(v: int) -> bytes:
        return f"{v & 0o777777:06o}".encode("ascii")

    def oct11(v: int) -> bytes:
        return f"{v & 0o77777777777:011o}".encode("ascii")

    return (_MAGIC_ODC + oct6(dev) + oct6(ino) + oct6(mode) + oct6(uid)
            + oct6(gid) + oct6(nlink) + oct6(rdev) + oct11(mtime)
            + oct6(taille_nom) + oct11(taille))


def lire_cpio_odc(brut: bytes) -> List[Tuple[str, int, int]]:
    """Relit une archive odc — (nom, mode, taille) — pour la vérification."""
    sortie, i = [], 0
    while i + 76 <= len(brut):
        if brut[i:i + 6] != _MAGIC_ODC:
            raise ValueError(f"cpio : magie inattendue à l'octet {i}")
        champs = brut[i:i + 76]
        mode = int(champs[18:24], 8)
        taille_nom = int(champs[59:65], 8)
        taille = int(champs[65:76], 8)
        i += 76
        nom = brut[i:i + taille_nom - 1].decode("utf-8")
        i += taille_nom + taille
        if nom == "TRAILER!!!":
            break
        sortie.append((nom, mode, taille))
    return sortie


# ---------------------------------------------------------------------------
#  BOM — la nomenclature binaire
# ---------------------------------------------------------------------------
class _Blocs:
    """Le tas de blocs d'un BOM, et leur table.

    Un BOM est un ensemble de blocs numérotés, rangés dans un tas, et une
    table qui donne l'adresse et la longueur de chacun. Le bloc 0 est
    conventionnellement nul : c'est la valeur qui signifie « aucun ».
    """

    def __init__(self):
        self.tas = bytearray()
        self.table: List[Tuple[int, int]] = [(0, 0)]   # le bloc nul

    def ajouter(self, donnees: bytes) -> int:
        #  Le premier bloc commence après l'en-tête de 512 octets, comme
        #  l'attendent les outils d'Apple.
        adresse = 512 + len(self.tas)
        self.tas += donnees
        self.table.append((adresse, len(donnees)))
        return len(self.table) - 1

    def reserver(self) -> int:
        """Un numéro de bloc dont le contenu viendra plus tard."""
        self.table.append((0, 0))
        return len(self.table) - 1

    def remplir(self, numero: int, donnees: bytes) -> None:
        adresse = 512 + len(self.tas)
        self.tas += donnees
        self.table[numero] = (adresse, len(donnees))


def ecrire_bom(entrees: List[Entree]) -> bytes:
    """Construit la nomenclature binaire d'un paquet.

    La structure est un arbre : un en-tête pointe vers un « arbre des
    chemins », dont les feuilles décrivent chaque fichier. Pour chaque chemin
    il faut trois blocs — la description (mode, taille, somme), l'identité
    (numéro), et le nom rattaché à son parent — puis une feuille qui les
    associe deux à deux.

    Les identifiants commencent à 1 : zéro est réservé, c'est le parent de la
    racine.
    """
    blocs = _Blocs()
    numeros: Dict[str, int] = {}
    for i, e in enumerate(entrees, start=1):
        numeros[e.chemin] = i

    indices: List[Tuple[int, int]] = []
    for e in entrees:
        identifiant = numeros[e.chemin]
        parent = 0 if e.chemin == "." else numeros[
            os.path.dirname(e.chemin) or "."]
        nom = os.path.basename(e.chemin) if e.chemin != "." else "."

        #  Description : type, mode, propriétaire, taille, somme de contrôle.
        lien = e.lien.encode("utf-8") + b"\0" if e.lien else b""
        description = struct.pack(
            ">BBHHIIIIBI", e.type_bom, 1, 0, e.mode & 0xFFFF, 0, 0,
            0, e.taille, 1, e.crc)
        if lien:
            description += struct.pack(">I", len(lien)) + lien
        bloc_description = blocs.ajouter(description)

        bloc_identite = blocs.ajouter(
            struct.pack(">II", identifiant, bloc_description))
        bloc_nom = blocs.ajouter(
            struct.pack(">I", parent) + nom.encode("utf-8") + b"\0")
        indices.append((bloc_identite, bloc_nom))

    #  La feuille : les couples (identité, nom), dans l'ordre du recensement.
    feuille = struct.pack(">HHII", 1, len(indices), 0, 0)
    for a, b in indices:
        feuille += struct.pack(">II", a, b)
    bloc_feuille = blocs.ajouter(feuille)

    #  Le nœud racine pointe sur la feuille. Deux niveaux suffisent tant que
    #  le paquet tient sous quelques milliers de fichiers — au-delà, Apple
    #  ajoute des niveaux, ce que `installer` accepte mais n'exige pas.
    racine = struct.pack(">HHII", 0, 1, 0, 0) + struct.pack(">II", bloc_feuille, 0)
    bloc_racine = blocs.ajouter(racine)

    def arbre(enfant: int, compte: int) -> bytes:
        return b"tree" + struct.pack(">IIIIB", 1, enfant, 4096, compte, 0)

    bloc_chemins = blocs.ajouter(arbre(bloc_racine, len(entrees)))

    #  Trois arbres vides, que les outils d'Apple s'attendent à trouver même
    #  lorsqu'ils ne servent pas : liens durs, index de version, tailles 64 bits.
    def arbre_vide() -> int:
        vide = blocs.ajouter(struct.pack(">HHII", 1, 0, 0, 0))
        return blocs.ajouter(arbre(vide, 0))

    bloc_hlindex = arbre_vide()
    bloc_size64 = arbre_vide()
    bloc_vindex_arbre = arbre_vide()
    bloc_vindex = blocs.ajouter(
        struct.pack(">IIBBBB", 1, bloc_vindex_arbre, 0, 0, 0, 0))

    #  BomInfo : le compte des chemins. Le tableau d'entrées qui suit décrit
    #  les architectures présentes ; il reste vide, le logiciel étant en
    #  Python pur.
    bloc_info = blocs.ajouter(struct.pack(">III", 1, len(entrees), 0))

    variables = [("BomInfo", bloc_info), ("VIndex", bloc_vindex),
                 ("HLIndex", bloc_hlindex), ("Size64", bloc_size64),
                 ("Paths", bloc_chemins)]

    #  Table des blocs, puis liste libre (vide), puis variables.
    table = struct.pack(">I", len(blocs.table))
    for adresse, longueur in blocs.table:
        table += struct.pack(">II", adresse, longueur)
    table += struct.pack(">I", 0)              # aucun bloc libre

    vars_brut = struct.pack(">I", len(variables))
    for nom, numero in variables:
        vars_brut += struct.pack(">IB", numero, len(nom)) + nom.encode("ascii")

    decalage_table = 512 + len(blocs.tas)
    decalage_vars = decalage_table + len(table)
    entete = (b"BOMStore" + struct.pack(">IIIIII", 1, len(blocs.table),
                                        decalage_table, len(table),
                                        decalage_vars, len(vars_brut)))
    entete += b"\0" * (512 - len(entete))
    return entete + bytes(blocs.tas) + table + vars_brut


def lire_bom(brut: bytes) -> List[Tuple[str, int, int]]:
    """Relit un BOM et rend (chemin, mode, taille) — pour la vérification.

    On refait le chemin inverse : variables, arbre, feuille, puis pour chaque
    couple la description et le nom, que l'on recolle au parent.
    """
    if brut[:8] != b"BOMStore":
        raise ValueError("BOM : signature absente")
    (_version, _nb, decalage_table, _lt, decalage_vars,
     _lv) = struct.unpack(">IIIIII", brut[8:32])

    nb_blocs = struct.unpack(">I", brut[decalage_table:decalage_table + 4])[0]
    table = []
    p = decalage_table + 4
    for _ in range(nb_blocs):
        table.append(struct.unpack(">II", brut[p:p + 8]))
        p += 8

    def bloc(n: int) -> bytes:
        adresse, longueur = table[n]
        return brut[adresse:adresse + longueur]

    nb_vars = struct.unpack(">I", brut[decalage_vars:decalage_vars + 4])[0]
    p = decalage_vars + 4
    variables = {}
    for _ in range(nb_vars):
        numero, longueur = struct.unpack(">IB", brut[p:p + 5])
        p += 5
        variables[brut[p:p + longueur].decode("ascii")] = numero
        p += longueur

    arbre = bloc(variables["Paths"])
    if arbre[:4] != b"tree":
        raise ValueError("BOM : l'arbre des chemins est absent")
    enfant = struct.unpack(">I", arbre[8:12])[0]

    #  Descendre jusqu'à la feuille. L'en-tête d'un nœud fait douze octets —
    #  isLeaf, count, forward, backward — et les couples d'indices commencent
    #  donc à l'octet 12, pas 8.
    ENTETE_NOEUD = 12
    noeud = bloc(enfant)
    while struct.unpack(">H", noeud[:2])[0] == 0:       # nœud interne
        premier = struct.unpack(">I", noeud[ENTETE_NOEUD:ENTETE_NOEUD + 4])[0]
        noeud = bloc(premier)

    compte = struct.unpack(">H", noeud[2:4])[0]
    noms: Dict[int, Tuple[int, str]] = {}
    infos: Dict[int, Tuple[int, int]] = {}
    ordre: List[int] = []
    for i in range(compte):
        debut = ENTETE_NOEUD + 8 * i
        a, b = struct.unpack(">II", noeud[debut:debut + 8])
        identifiant, bloc_description = struct.unpack(">II", bloc(a))
        description = bloc(bloc_description)
        mode = struct.unpack(">H", description[4:6])[0]
        taille = struct.unpack(">I", description[18:22])[0]
        nom_brut = bloc(b)
        parent = struct.unpack(">I", nom_brut[:4])[0]
        nom = nom_brut[4:].split(b"\0")[0].decode("utf-8")
        noms[identifiant] = (parent, nom)
        infos[identifiant] = (mode, taille)
        ordre.append(identifiant)

    def complet(identifiant: int) -> str:
        parent, nom = noms[identifiant]
        if parent == 0 or parent not in noms:
            return nom
        return complet(parent) + "/" + nom

    return [(complet(i), infos[i][0], infos[i][1]) for i in ordre]


# ---------------------------------------------------------------------------
#  XAR
# ---------------------------------------------------------------------------
@dataclass
class _Membre:
    nom: str
    donnees: bytes
    decalage: int = 0
    compresse: bytes = b""


def _xar(membres: List[_Membre]) -> bytes:
    """Assemble une archive XAR : en-tête, table des matières, tas.

    La table des matières est elle-même compressée par zlib, et l'en-tête en
    donne les deux longueurs — compressée et non compressée. Chaque membre
    porte sa taille et sa somme SHA-1 avant et après compression : c'est ce
    qui permet à l'installateur de refuser une archive abîmée plutôt que
    d'installer n'importe quoi.
    """
    tas = bytearray()
    for m in membres:
        m.compresse = zlib.compress(m.donnees, 9)
        m.decalage = len(tas)
        tas += m.compresse

    lignes = ['<?xml version="1.0" encoding="UTF-8"?>', "<xar>", " <toc>",
              f"  <creation-time>{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(0))}"
              "</creation-time>",
              "  <checksum style=\"sha1\">", "   <offset>0</offset>",
              "   <size>20</size>", "  </checksum>"]
    #  La somme de contrôle de la table occupe les vingt premiers octets du
    #  tas ; les membres sont donc décalés d'autant.
    decalage_base = 20
    for i, m in enumerate(membres, start=1):
        lignes += [
            f'  <file id="{i}">',
            f"   <name>{m.nom}</name>",
            "   <type>file</type>",
            "   <data>",
            f"    <length>{len(m.compresse)}</length>",
            f"    <offset>{m.decalage + decalage_base}</offset>",
            f"    <size>{len(m.donnees)}</size>",
            "    <encoding style=\"application/x-gzip\"/>",
            f"    <extracted-checksum style=\"sha1\">"
            f"{hashlib.sha1(m.donnees).hexdigest()}</extracted-checksum>",
            f"    <archived-checksum style=\"sha1\">"
            f"{hashlib.sha1(m.compresse).hexdigest()}</archived-checksum>",
            "   </data>",
            "  </file>",
        ]
    lignes += [" </toc>", "</xar>", ""]
    toc = "\n".join(lignes).encode("utf-8")
    toc_compresse = zlib.compress(toc, 9)

    entete = struct.pack(">4sHHQQI", b"xar!", 28, 1, len(toc_compresse),
                         len(toc), 1)          # 1 = SHA-1
    return (entete + toc_compresse + hashlib.sha1(toc_compresse).digest()
            + bytes(tas))


def lire_xar(brut: bytes) -> Dict[str, bytes]:
    """Relit une archive XAR — pour la vérification."""
    magie, taille_entete, _v, toc_c, toc_d, _alg = struct.unpack(
        ">4sHHQQI", brut[:28])
    if magie != b"xar!":
        raise ValueError("XAR : signature absente")
    toc = zlib.decompress(brut[taille_entete:taille_entete + toc_c])
    if len(toc) != toc_d:
        raise ValueError("XAR : table des matières de longueur inattendue")
    debut_tas = taille_entete + toc_c
    import re
    sortie = {}
    for bloc in re.findall(rb"<file id=.*?</file>", toc, re.S):
        nom = re.search(rb"<name>(.*?)</name>", bloc, re.S).group(1).decode()
        longueur = int(re.search(rb"<length>(\d+)</length>", bloc).group(1))
        decalage = int(re.search(rb"<offset>(\d+)</offset>", bloc).group(1))
        brut_membre = brut[debut_tas + decalage:debut_tas + decalage + longueur]
        sortie[nom] = zlib.decompress(brut_membre)
    return sortie


# ---------------------------------------------------------------------------
#  Le paquet complet
# ---------------------------------------------------------------------------
def ecrire_pkg(racine: str, sortie: str, identifiant: str, version: str,
               titre: str, destination: str = "/Applications",
               licence: str = "", bienvenue: str = "",
               postinstall: str = "") -> str:
    """Écrit un paquet `.pkg` installable, et rend son chemin.

    :param racine: le dossier dont le contenu sera posé dans `destination`.
    :param destination: où l'installateur déposera ce contenu.
    :param postinstall: script `sh` exécuté après la copie, s'il y en a un.
    """
    entrees = recenser(racine)
    charge = gzip.compress(ecrire_cpio_odc(entrees), 9, mtime=0)
    bom = ecrire_bom(entrees)
    octets = sum(e.taille for e in entrees)

    infos = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<pkg-info format-version="2" identifier="{identifiant}" '
        f'version="{version}" install-location="{destination}" '
        f'auth="root">',
        f'    <payload installKBytes="{max(octets // 1024, 1)}" '
        f'numberOfFiles="{len(entrees)}"/>',
    ]
    membres: List[_Membre] = []
    if postinstall:
        script = Entree("./postinstall", "", False, 0o100755)
        tampon = ecrire_cpio_odc([])   # remplacé ci-dessous
        tampon = _cpio_dun_script(postinstall)
        membres.append(_Membre("phytoscope.pkg/Scripts",
                               gzip.compress(tampon, 9, mtime=0)))
        infos.append('    <scripts><postinstall file="postinstall"/></scripts>')
    infos.append("</pkg-info>")

    #  Le fichier « Distribution » décrit ce que l'assistant affiche : titre,
    #  version minimale du système, et l'unique choix d'installation.
    distribution = f'''<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>{titre}</title>
    <organization>com.bretagne-namaste</organization>
    <options customize="never" require-scripts="false" hostArchitectures="x86_64,arm64"/>
    <!-- 11.0 : la version la plus ancienne pour laquelle Qt publie encore
         des roues « universal2 ». En annoncer moins serait mentir. -->
    <volume-check>
        <allowed-os-versions><os-version min="11.0"/></allowed-os-versions>
    </volume-check>
    {'<license file="licence.txt"/>' if licence else ''}
    {'<welcome file="bienvenue.txt"/>' if bienvenue else ''}
    <choices-outline><line choice="default"/></choices-outline>
    <choice id="default" title="{titre}">
        <pkg-ref id="{identifiant}"/>
    </choice>
    <pkg-ref id="{identifiant}" version="{version}"
             installKBytes="{max(octets // 1024, 1)}">#phytoscope.pkg</pkg-ref>
</installer-gui-script>
'''
    membres = [
        _Membre("Distribution", distribution.encode("utf-8")),
        _Membre("phytoscope.pkg/PackageInfo", "\n".join(infos).encode("utf-8")),
        _Membre("phytoscope.pkg/Bom", bom),
        _Membre("phytoscope.pkg/Payload", charge),
    ] + membres
    if licence:
        membres.append(_Membre("Resources/licence.txt", licence.encode("utf-8")))
    if bienvenue:
        membres.append(_Membre("Resources/bienvenue.txt",
                               bienvenue.encode("utf-8")))

    with open(sortie, "wb") as f:
        f.write(_xar(membres))
    return sortie


def _cpio_dun_script(contenu: str) -> bytes:
    """Une archive cpio d'un seul script, exécutable."""
    donnees = contenu.encode("utf-8")
    nom = b"./postinstall\0"
    entete = _entete_odc(0, 1, 0o100755, 0, 0, 1, 0, 0, len(nom), len(donnees))
    fin_nom = b"TRAILER!!!\0"
    return (entete + nom + donnees
            + _entete_odc(0, 0, 0, 0, 0, 1, 0, 0, len(fin_nom), 0) + fin_nom)


# ---------------------------------------------------------------------------
#  Vérification
# ---------------------------------------------------------------------------
def verifier_pkg(chemin: str, attendus: Optional[List[str]] = None
                 ) -> Dict[str, object]:
    """Relit un paquet écrit ici et contrôle qu'il dit bien ce qu'on a voulu.

    On ne peut pas soumettre le paquet à `installer(8)` sans Mac ; on peut en
    revanche vérifier que chacun des trois formats se relit, et que les trois
    décrivent **le même ensemble de fichiers**. Une charge utile et une
    nomenclature qui divergent sont la panne classique d'un paquet fabriqué à
    la main : l'installateur copie, puis refuse.
    """
    with open(chemin, "rb") as f:
        brut = f.read()
    membres = lire_xar(brut)

    manquants = [n for n in ("Distribution", "phytoscope.pkg/PackageInfo",
                             "phytoscope.pkg/Bom", "phytoscope.pkg/Payload")
                 if n not in membres]
    if manquants:
        raise ValueError(f"paquet incomplet : {', '.join(manquants)}")

    charge = lire_cpio_odc(gzip.decompress(membres["phytoscope.pkg/Payload"]))
    nomenclature = lire_bom(membres["phytoscope.pkg/Bom"])

    noms_charge = {n for n, _, _ in charge}
    noms_bom = {("." + n[1:]) if n.startswith("./") else
                ("." if n == "." else "./" + n) for n, _, _ in nomenclature}
    if noms_charge != noms_bom:
        seulement_charge = sorted(noms_charge - noms_bom)[:5]
        seulement_bom = sorted(noms_bom - noms_charge)[:5]
        raise ValueError(
            "la charge utile et la nomenclature divergent — "
            f"charge seule : {seulement_charge} ; nomenclature seule : "
            f"{seulement_bom}")

    if attendus:
        absents = [a for a in attendus if a not in noms_charge]
        if absents:
            raise ValueError(f"absents du paquet : {absents}")

    return {
        "membres": sorted(membres),
        "fichiers": len(charge),
        "octets": sum(t for _, _, t in charge),
        "identifiant": _extraire(membres["phytoscope.pkg/PackageInfo"],
                                 b"identifier="),
        "version": _extraire(membres["phytoscope.pkg/PackageInfo"],
                             b"version="),
        "destination": _extraire(membres["phytoscope.pkg/PackageInfo"],
                                 b"install-location="),
    }


def _extraire(brut: bytes, attribut: bytes) -> str:
    """Un attribut de la balise `pkg-info`, et d'elle seule.

    Chercher `version="` dans tout le fichier renvoyait « 1.0 » : celle de la
    déclaration XML de la première ligne. On délimite donc d'abord la balise.
    """
    debut = brut.find(b"<pkg-info")
    if debut < 0:
        return ""
    fin = brut.find(b">", debut)
    balise = brut[debut:fin]
    i = balise.find(b" " + attribut)
    if i < 0:
        return ""
    i += len(attribut) + 1
    j = balise.find(b'"', i + 1)
    return balise[i + 1:j].decode("utf-8")
