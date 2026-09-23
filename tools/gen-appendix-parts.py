#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen-appendix-parts.py
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

"""
Génère les fragments HTML de l'annexe technique dans pdf-src/parts/annexe-tech/.

Les listings de code sont extraits des archives de sources/code/ au moment de
la génération : aucun code n'est recopié à la main dans ce fichier, donc le
document ne peut pas diverger des dépôts réellement téléchargés.

Usage : python3 tools/gen-appendix-parts.py  puis  python3 tools/build-annexe.py
"""
import html
import io
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "pdf-src", "talking-tree-appendix")
CODE = os.path.join(ROOT, "sources", "code")
SOFT = os.path.join(ROOT, "sources", "software")
os.makedirs(PARTS, exist_ok=True)


def manifeste_logiciel():
    """Lit sources/software/MANIFESTE.json s'il existe (écrit par fetch-software.py)."""
    p = os.path.join(SOFT, "MANIFESTE.json")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
#  OUTILS
# =============================================================================
def lire_membre(archive, motif):
    with zipfile.ZipFile(os.path.join(CODE, archive)) as z:
        noms = [n for n in z.namelist() if re.search(motif, n) and not n.endswith("/")]
        if not noms:
            raise KeyError(f"{archive}: rien ne matche {motif!r}")
        with z.open(sorted(noms, key=len)[0]) as f:
            return io.TextIOWrapper(f, encoding="utf-8", errors="replace").read()


def bloc(archive, motif, debut=None, fin=None, degager=True):
    """Extrait les lignes entre deux regex (fin exclue)."""
    lignes = lire_membre(archive, motif).splitlines()
    i0 = 0
    if debut:
        i0 = next(i for i, l in enumerate(lignes) if re.search(debut, l))
    i1 = len(lignes)
    if fin:
        i1 = next((i for i in range(i0 + 1, len(lignes)) if re.search(fin, lignes[i])),
                  len(lignes))
    out = lignes[i0:i1]
    while out and not out[-1].strip():
        out.pop()
    if degager:                      # normalise les tabulations
        out = [l.replace("\t", "    ") for l in out]
    return "\n".join(out)


def listing(num, titre, corps, source, langue="", note=""):
    n = (f'<div class="code-h">Listing {num} — {html.escape(titre)}'
         + (f' · {html.escape(langue)}' if langue else "") + "</div>")
    s = f'<p class="small" style="margin:.3em 0 1.2em">{source}</p>'
    nt = f'<p>{note}</p>' if note else ""
    return (f'{nt}<div class="code listing">{n}<pre>{html.escape(corps)}</pre></div>{s}')


def ecrire(nom, contenu):
    p = os.path.join(PARTS, nom + ".html")
    with open(p, "w", encoding="utf-8") as f:
        f.write(contenu)
    print(f"  · {nom}.html  ({len(contenu)//1024} Ko)")


def tableau(entetes, lignes, classes="bom tight-xs", legende=None, total=None):
    th = "".join(f"<th>{h}</th>" for h in entetes)
    tr = ""
    for l in lignes:
        tr += "<tr>" + "".join(f"<td>{c}</td>" for c in l) + "</tr>\n"
    if total:
        tr += '<tr class="tot">' + "".join(f"<td>{c}</td>" for c in total) + "</tr>\n"
    cap = f"<caption>{legende}</caption>" if legende else ""
    return f'<table class="{classes}">{cap}<thead><tr>{th}</tr></thead><tbody>\n{tr}</tbody></table>'


def planche(fichier, num, titre, legende):
    """Une planche = une page paysage entière (voir @page planche dans le build)."""
    return (f'<section class="planche-page">'
            f'<figure class="planche" id="fig-{num}">'
            f'<img src="assets/svg/{fichier}" alt="{html.escape(titre)}"/>'
            f'<figcaption><span class="fig-n">PLANCHE {num}</span> — {legende}</figcaption>'
            f'</figure></section>')


# =============================================================================
#  LIMINAIRES
# =============================================================================
ecrire("00-cover", '''<section class="cover">
  <div class="kicker">Ateliers BN · Manuel d'atelier</div>
  <h1>L'Arbre<br/>qui Parle</h1>
  <div class="title-rule"></div>
  <p class="subtitle">Annexe technique — schémas électroniques,<br/>nomenclatures et programmes</p>
  <div class="cover-foot">
    <p class="small" style="color:#E0C073">Cinq planches commentées · six nomenclatures ·
    dix listings · soixante-sept dépôts téléchargés et vérifiés</p>
  </div>
</section>''')

ecrire("01-titlepage", '''<section class="titlepage frontpage">
  <h1>Annexe technique</h1>
  <p class="sub">Schémas, nomenclatures et programmes<br/>pour un arbre instrumenté</p>
  <p class="imprint">Ateliers BN — 17 septembre 2026</p>
</section>''')

ecrire("02-notice", '''<section class="frontpage">
<h2 id="notice" data-toc="chapter">Comment lire cette annexe</h2>

<p class="lettrine noindent">Cette annexe est le complément matériel du manuel
d'atelier. Elle ne raconte rien : elle donne des schémas que l'on peut câbler,
des nomenclatures que l'on peut commander et des programmes que l'on peut
téléverser. Tout ce qui s'y trouve a été vérifié à une source primaire —
datasheet du constructeur, dépôt public, ou relevé direct d'un fichier de
conception.</p>

<div class="callout sci">
  <div class="callout-title">Trois statuts, jamais confondus</div>
  <ul>
    <li><strong>Relevé</strong> — le schéma reproduit un circuit existant dont le
    fichier de conception a été téléchargé et analysé. C'est le cas de la
    planche 1, dont le netlist a été extrait du fichier Eagle
    <span class="phon">GalvShield_005.sch</span>.</li>
    <li><strong>Schéma d'application</strong> — le montage est composé à partir
    des schémas types publiés dans les datasheets des composants cités. Il est
    électriquement correct mais n'a pas été prototypé dans le cadre de cette
    annexe.</li>
    <li><strong>Non vérifié</strong> — signalé comme tel, en toutes lettres.</li>
  </ul>
</div>

<h3 id="notice-prix" data-toc="sub">Sur les prix</h3>
<p>Les prix sont des ordres de grandeur en euros TTC, relevés chez des
distributeurs généralistes (Mouser, Digi-Key, Farnell) ou chez les revendeurs
maker usuels. Ils servent à dimensionner un budget d'atelier, pas à établir un
devis. Les composants passifs sont donnés au prix unitaire, alors qu'ils
s'achètent par lots de cent : le coût réel d'un atelier est donc plus bas que la
somme des lignes, et le poste dominant est toujours le même — le boîtier, le
câble et la batterie, jamais les puces.</p>

<h3 id="notice-secu" data-toc="sub">Sécurité et déontologie arboricole</h3>
<div class="callout limite">
  <div class="callout-title">Avant toute pose sur un arbre vivant</div>
  <ul>
    <li>Ne jamais <strong>ceinturer</strong> le tronc avec un lien fermé : la
    croissance secondaire l'incruste et finit par étrangler le liber. Tout
    collier doit être ré-ouvert au moins une fois par an.</li>
    <li>Ne jamais visser profondément : on ouvre une porte aux champignons de
    carie. Une sonde de flux de sève perce déjà le bois — c'est une blessure
    assumée, à limiter en nombre et à espacer verticalement.</li>
    <li>Sangles plates de 40 mm minimum, jamais de câble ni de fil de fer, avec
    une garniture de feutre entre la sangle et l'écorce.</li>
    <li>Aucune alimentation secteur au pied de l'arbre : basse tension isolée
    uniquement, et batterie en boîtier ventilé.</li>
  </ul>
</div>
</section>''')

ecrire("03-toc", '''<section class="toc frontpage">
<h1 id="sommaire">Sommaire</h1>
<p class="toc-sub">Annexe technique</p>
<!--TOC_HERE-->
</section>''')


# =============================================================================
#  PLANCHE 1 — BIODATA LMC555
# =============================================================================
bom1 = tableau(
    ["Rep.", "Composant", "Valeur", "Référence fabricant", "Boîtier", "≈ €"],
    [["U1", "Temporisateur CMOS", "—", "Texas Instruments <b>LMC555CN</b>", "DIP-8", "1,10"],
     ["—", "Support de circuit", "8 broches", "Assmann A 08-LC-TT", "DIP-8", "0,15"],
     ["R2", "Résistance", "100 kΩ 1 %", "Stackpole RNMF14FTC100K", "axial 1/4 W", "0,10"],
     ["R1, R3–R8", "Résistances (×7)", "220 Ω", "Stackpole RNMF14FTC220R", "axial 1/4 W", "0,70"],
     ["R9", "Potentiomètre linéaire", "10 kΩ", "Bourns PTV09A-4020F-B103", "6 mm", "0,85"],
     ["R10", "Résistance", "3,9 kΩ", "Stackpole RNMF14FTC3K90", "axial", "0,10"],
     ["R11", "Résistance", "1 kΩ", "Stackpole RNMF14FTC1K00", "axial", "0,10"],
     ["C1", "Condensateur film", "4,7 nF", "KEMET C315C472K1R5TA", "pas 5 mm", "0,25"],
     ["C2", "Chimique", "47 µF / 25 V", "KEMET ESH476M025AC3AA", "radial", "0,18"],
     ["C3", "Chimique", "1 µF / 50 V", "KEMET ESH105M050AC3AA", "radial", "0,18"],
     ["C4", "Découplage", "100 nF", "KEMET C320C104K5R5TA", "pas 5 mm", "0,22"],
     ["S1", "Bouton tactile", "—", "Omron B3F-1000", "6 mm", "0,35"],
     ["LED1–6", "LED 5 mm", "R/J/V/B/W", "Lite-On LTL2H3KEK et suivantes", "5 mm", "3,40"],
     ["MIDI", "Embase DIN 5 broches", "—", "CUI SDS-50J", "traversante", "1,05"],
     ["X1, X2", "Jacks stéréo 3,5 mm (×2)", "—", "CUI SJ1-3523N", "traversante", "1,50"],
     ["—", "Électrodes adhésives", "TENS", "pastilles + cordons à pression", "—", "6,00"],
     ["—", "Carte Arduino Uno (ou compatible)", "—", "ATmega328P", "—", "12,00 – 25,00"],
     ["—", "Plaque d'essai + fils", "830 points", "—", "—", "6,00"]],
    legende="Nomenclature de la planche 1. Les références fabricant, les repères et les "
            "valeurs proviennent du fichier <i>Arduino Shield Biodata Sonification — "
            "Parts.csv</i> publié avec le dépôt ; les prix en euros sont des ordres de "
            "grandeur 2026, convertis et arrondis.",
    total=["", "<b>Total indicatif, hors carte Arduino</b>", "", "", "", "<b>≈ 22 €</b>"])

ecrire("10-planche1", f'''<section>
<h2 id="p1" data-toc="chapter">Planche 1 — Le front-end biodata à LMC555</h2>

<p class="lettrine noindent">C'est le circuit le plus copié de tout le domaine :
on le retrouve, à peu de chose près identique, dans le MIDI Sprout de Data
Garden, dans le Biotron de Playtronica et dans la quasi-totalité des projets
« plante musicale » publiés sur GitHub. Le schéma ci-dessous n'est pas une
reconstitution : il a été relevé sur le fichier de conception Eagle
<span class="phon">GalvShield_005.sch</span> du dépôt
<span class="phon">electricityforprogress/BiodataSonificationBreadboardKit</span>,
en analysant le netlist du fichier XML.</p>

{planche("sch-biodata-555.svg", 1,
         "Front-end biodata à LMC555",
         "capteur de conductance à oscillateur astable. Relevé du netlist "
         "<i>GalvShield_005.sch</i> (Eagle), dépôt electricityforprogress, licence MIT.")}

<h3 id="p1-fonc" data-toc="sub">Comment ça marche</h3>

<p>Un LMC555 monté en <strong>multivibrateur astable</strong> oscille en
chargeant puis déchargeant un condensateur à travers deux résistances. Dans le
montage classique, ces deux résistances sont des composants. Ici, la seconde
a été remplacée par <strong>le végétal lui-même</strong>.</p>

<p>Le courant part du +5 V, traverse R2 (100 kΩ), ressort par la broche 7
(décharge) vers l'électrode A, traverse le tissu de la feuille jusqu'à
l'électrode B, et vient charger C1 (4,7 nF). Quand la tension sur C1 atteint
deux tiers de l'alimentation, le comparateur interne bascule, la broche 7 est
mise à la masse et C1 se décharge à travers le même chemin. Quand la tension
retombe au tiers de l'alimentation, le cycle recommence.</p>

<div class="loupe">
  <div class="l-h">La fréquence est une mesure d'impédance</div>
  <p class="noindent">La période dépend de la résistance vue entre les deux
  électrodes :</p>
  <p class="center"><i>f</i> ≈ 1,44 / ( (R2 + 2·R<sub>plante</sub>) · C1 )</p>
  <p>Pour C1 = 4,7 nF et R2 = 100 kΩ, une feuille turgescente à 300 kΩ donne
  environ 480 Hz, tandis qu'un tissu sec à 5 MΩ tombe vers 29 Hz. La plage
  utile couvre donc plus d'une décade — c'est confortable, et c'est ce qui rend
  le montage aussi robuste pédagogiquement.</p>
</div>

<p>La sortie (broche 3) est un signal carré. Le microcontrôleur ne mesure pas
une tension : il compte le temps entre deux fronts montants, sur une entrée
d'interruption. Le reste — seuil, gamme musicale, canal MIDI — est du logiciel,
et se règle avec le potentiomètre R9 et le bouton S1.</p>

<p>Deux sorties coexistent. La sortie MIDI est une boucle de courant sur embase
DIN-5 : la broche 5 reçoit directement la ligne TX du microcontrôleur, la
broche 4 est tirée au +5 V par R1. La sortie CV/audio est le signal MLI de la
broche D11, débarrassé de sa porteuse par le réseau C3-R10-R11 avant de partir
vers un jack 3,5 mm.</p>

<div class="callout limite">
  <div class="callout-title">Ce que ce montage ne mesure pas</div>
  <p class="noindent">Il faut le dire clairement, parce que l'essentiel du
  discours commercial autour de ces appareils repose sur l'ambiguïté inverse :
  <strong>ce circuit n'écoute pas la plante, il l'interroge</strong>. Il injecte
  un courant et mesure l'impédance de surface qui en résulte. C'est l'exact
  analogue de la réponse électrodermale mesurée sur la peau humaine — et,
  comme elle, cette impédance dépend au moins autant de l'humidité de l'air, de
  la qualité du contact et de la température que de l'état physiologique du
  sujet. Ce n'est pas une raison de s'en priver : c'est une raison de ne pas lui
  faire dire ce qu'elle ne dit pas.</p>
</div>

<h3 id="p1-bom" data-toc="sub">Nomenclature</h3>
{bom1}

<div class="practice">
  <div class="p-h">Pièges de montage</div>
  <ul>
    <li><strong>Utiliser un LMC555, pas un NE555 bipolaire.</strong> La version
    CMOS a un courant d'entrée de l'ordre du picoampère ; la version bipolaire
    tire des microampères et fausse complètement la mesure sur une source de
    plusieurs mégohms.</li>
    <li><strong>Électrodes : la pression est une variable.</strong> Deux pinces
    serrées différemment donnent deux signaux différents. Les pastilles
    adhésives de type TENS sont préférables aux pinces crocodiles.</li>
    <li><strong>Laisser stabiliser dix minutes</strong> après la pose : le gel
    des électrodes met ce temps à mouiller la surface, et toute mesure faite
    avant enregistre la dérive du contact, pas la plante.</li>
  </ul>
</div>
</section>''')


# =============================================================================
#  PLANCHE 2 — ÉLECTROPHYSIOLOGIE
# =============================================================================
bom2 = tableau(
    ["Rep.", "Composant", "Caractéristique déterminante", "Référence", "≈ €"],
    [["U1", "Ampli d'instrumentation", "I<sub>bias</sub> 200 pA typ., 0,05 µV/°C",
      "TI <b>INA333AIDGKR</b>", "6,50"],
     ["—", "Variante plus bruyante mais courante", "I<sub>bias</sub> 1 nA, bruit 9 nV/√Hz",
      "ADI AD8221 / AD620", "9,00"],
     ["U2", "Convertisseur ΔΣ 16 bits", "4 voies, PGA ×1…×16, I²C, 860 SPS",
      "TI <b>ADS1115IDGSR</b>", "5,40"],
     ["—", "Variante 24 bits pour signaux lents", "PGA ×128, réf. interne",
      "TI ADS1220 / ADS1256", "8,00 – 14,00"],
     ["U3", "Isolateur I²C", "barrière 2,5 kV, alimentation isolée à part",
      "ADI <b>ADuM1251ARZ</b>", "6,80"],
     ["—", "Convertisseur DC-DC isolé", "1 W, 3,3 V → 3,3 V isolé",
      "Recom R1SE-3.33.3S", "5,90"],
     ["R1, R2", "Limitation d'entrée", "10 kΩ 0,1 %, métal", "Vishay MMA0204", "0,60"],
     ["R_G", "Gain", "1 kΩ 0,1 % → G = 101", "Vishay MMA0204", "0,30"],
     ["R4, R5", "Référence à mi-alimentation", "100 kΩ 0,1 % appairées", "Vishay", "0,60"],
     ["R3", "Anti-repliement", "16 kΩ avec C3 → f<sub>c</sub> ≈ 100 Hz", "—", "0,10"],
     ["C1, C2", "Filtrage RF d'entrée", "1 nF C0G", "KEMET", "0,40"],
     ["C3", "Anti-repliement", "100 nF C0G", "KEMET", "0,25"],
     ["E1, E2", "Pastilles Ag/AgCl (×2)", "non polarisables : interface réversible, "
      "dérive faible", "A-M Systems <b>550015</b> (Ø 2 × 4 mm), 36 $ pièce", "68,00"],
     ["—", "Variante économique", "aiguilles inox 316L Ø 1 mm", "quincaillerie", "2,00"],
     ["REF", "Électrode de référence de sol", "Pb/PbCl₂ ou Cu/CuSO₄",
      "électrode de potentiel spontané", "45,00"],
     ["—", "Câble blindé par paire", "faible triboélectricité, PTFE", "au mètre", "4,00/m"]],
    legende="Nomenclature de la planche 2. Les deux postes dominants sont les électrodes "
            "non polarisables et l'isolation galvanique — c'est-à-dire précisément les "
            "deux éléments que l'on est tenté de supprimer, et dont la suppression ruine "
            "la mesure.",
    total=["", "<b>Total voie complète, électrodes de laboratoire</b>", "", "",
           "<b>≈ 115 – 180 €</b>"])

ecrire("11-planche2", f'''<section class="pagebreak">
<h2 id="p2" data-toc="chapter">Planche 2 — La voie d'électrophysiologie</h2>

<p class="lettrine noindent">Ici, contrairement à la planche 1, on n'injecte
rien. On écoute une différence de potentiel qui existe déjà dans l'arbre, de
l'ordre de quelques millivolts, sur une source dont l'impédance se compte en
mégohms voire en gigohms. Tout le schéma découle de cette seule contrainte.</p>

{planche("sch-electrophysio-ina333.svg", 2,
         "Voie d'électrophysiologie extracellulaire",
         "électrodes → amplificateur d'instrumentation → convertisseur ΔΣ → "
         "liaison I²C isolée. Schéma d'application d'après les datasheets TI INA333, "
         "TI ADS1115 et ADI ADuM1251.")}

<h3 id="p2-imp" data-toc="sub">Pourquoi l'impédance commande tout</h3>

<p>Une électrode plantée dans l'aubier voit une source dont l'impédance
équivalente se situe couramment entre 1 et 50 MΩ. Tout étage qui prélève du
courant sur cette source crée une chute de tension parasite. C'est pourquoi le
choix de l'amplificateur ne se fait pas sur son gain — n'importe quel montage
sait amplifier — mais sur son <strong>courant de polarisation d'entrée</strong>.</p>

<p>L'INA333 tire 200 picoampères. Sur 10 MΩ, cela produit une erreur de 2 mV.
L'AD620, excellent par ailleurs, tire 1 nanoampère : 10 mV d'erreur sur la même
source, soit davantage que le signal recherché. Un amplificateur opérationnel
bipolaire ordinaire tirerait cent fois plus encore. Le critère de sélection est
donc unique, et il n'est pas négociable.</p>

<div class="callout limite">
  <div class="callout-title">L'erreur la plus fréquente</div>
  <p class="noindent">Brancher l'électrode directement sur l'entrée de
  l'ADS1115, sous prétexte qu'il possède un amplificateur à gain programmable.
  Cet étage est à capacités commutées : il présente 6 MΩ en mode commun au gain
  ×1, et seulement 710 kΩ au gain ×16. Face à un tissu de 10 MΩ, on ne mesure
  plus un potentiel mais le rapport de division entre le tissu et le
  convertisseur — c'est-à-dire la qualité du contact de l'électrode, qui dérive
  de son côté. Le montage « marche », produit des courbes, et ne mesure rien.</p>
</div>

<div class="callout key">
  <div class="callout-title">Au-delà de 10 MΩ, l'INA333 ne suffit plus</div>
  <p class="noindent">Le tableau ci-dessous donne l'erreur de tension
  <i>I</i><sub>bias</sub> × <i>R</i><sub>source</sub> pour les composants
  usuels. Le signal recherché valant 1 à 50 mV, la lecture est sans appel.</p>
  <table class="tight" style="margin:.6em 0">
  <thead><tr><th>Composant</th><th>I<sub>bias</sub> max</th><th>sur 1 MΩ</th>
  <th>sur 100 MΩ</th><th>sur 1 GΩ</th></tr></thead>
  <tbody>
  <tr><td>INA333</td><td>200 pA</td><td>0,2 mV</td><td>20 mV</td><td>200 mV</td></tr>
  <tr><td>AD8232</td><td>200 pA</td><td>0,2 mV</td><td>20 mV</td><td>200 mV</td></tr>
  <tr><td>AD8221 (grade BR)</td><td>0,4 nA</td><td>0,4 mV</td><td>40 mV</td><td>400 mV</td></tr>
  <tr><td>INA128 (pire cas)</td><td>5 nA</td><td>5 mV</td><td>500 mV</td><td>saturé</td></tr>
  <tr><td>INA826</td><td>65 nA</td><td>65 mV</td><td>saturé</td><td>saturé</td></tr>
  </tbody></table>
  <p>L'INA826 est le piège : son impédance d'entrée annoncée de 20 GΩ est
  excellente, mais son courant de polarisation est cinq cents fois pire que
  celui de l'INA333. <strong>Impédance d'entrée et courant de polarisation sont
  deux paramètres indépendants, et c'est le second qui décide.</strong></p>
  <p>Conséquence : au-delà d'une dizaine de mégohms de source — écorce sèche,
  contact vieillissant — il faut interposer un <strong>suiveur à entrée
  électromètre</strong> au plus près de l'électrode (LMP7721, ADA4530-1,
  OPA129 : courants de polarisation en femtoampères), puis attaquer l'INA333
  avec sa sortie basse impédance. C'est l'architecture obligatoire pour du
  potentiel de surface en continu, et elle est presque toujours absente des
  projets amateurs.</p>
</div>

<h3 id="p2-ref" data-toc="sub">Référence, garde et masse</h3>

<p>Le signal est unipolaire à la sortie de l'amplificateur : il faut donc le
recentrer. Le diviseur R4/R5 fixe la broche REF à la moitié de l'alimentation,
ce qui place le zéro du signal au milieu de la plage du convertisseur et permet
de voir les excursions dans les deux sens.</p>

<p>Cette même tension sert de <strong>garde active</strong> : le blindage des
câbles d'entrée n'est pas relié à la masse mais à REF. Le blindage suit alors le
potentiel du signal, la capacité parasite du câble ne se charge plus, et la
bande passante ne s'effondre pas malgré la résistance de source élevée. C'est le
même principe que la « driven right leg » des électrocardiographes.</p>

<p>L'électrode de référence a deux fonctions, souvent confondues. La première
est d'<strong>offrir un chemin de retour au courant de polarisation</strong> :
un amplificateur d'instrumentation dont les deux entrées flottent ne mesure
rien, ses entrées dérivant hors de la plage de mode commun. Sans électrode de
référence, le montage ne fonctionne pas, quelle que soit la qualité de
l'amplificateur. La seconde est de fixer un potentiel de comparaison.</p>

<p>Ces deux fonctions n'appellent pas le même emplacement. Une référence
<strong>dans le sol</strong> offre une impédance faible et une grande surface,
mais son potentiel de jonction sol/racine dérive avec la pluie et la
température : bonne pour le retour de courant, médiocre comme référence de
potentiel. Une référence <strong>dans le tronc</strong>, à cinquante centimètres
au moins des électrodes de mesure, baigne dans la même chimie : son potentiel de
jonction est comparable à celui des électrodes de mesure et se soustrait donc au
premier ordre. C'est le meilleur compromis, au prix d'une blessure
supplémentaire. Le dispositif employé par Gibert et ses collègues sur un
peuplier en 2006 utilisait, lui, une électrode plomb / chlorure de plomb
enterrée à 80 cm.</p>

<p>Dans tous les cas l'électrode doit être <strong>non polarisable</strong>. Un
piquet d'acier est une électrode polarisable : il se comporte en condensateur de
double couche, développe des potentiels galvaniques avec le milieu et dérive de
plusieurs millivolts par jour par corrosion et variation de sa couche d'oxyde.
L'acier reste acceptable pour un signal rapide en couplage alternatif ; il est
inutilisable pour un potentiel lent suivi sur plusieurs jours.</p>

<div class="callout key">
  <div class="callout-title">Le compromis qui résout presque tout</div>
  <p class="noindent">Le problème dominant en mesure longue durée n'est pas le
  bruit : c'est la <strong>dérive du potentiel de demi-pile</strong> des
  électrodes, qui apparaît en différentiel et se confond avec un signal
  biologique lent. Si le projet ne cherche que des <i>événements</i> — réponse à
  une blessure, à un choc thermique, à l'arrosage — un couplage alternatif à
  0,05 Hz élimine le problème d'un seul coup. C'est précisément ce que fait
  l'AD8232 avec son passe-haut intégré à deux pôles, explicitement conçu pour
  supprimer les artefacts de mouvement et le potentiel de demi-pile. Pour un
  arbre parlant, c'est très probablement le bon choix — à condition d'assumer
  qu'on renonce alors aux dérives lentes, c'est-à-dire à la saisonnalité.</p>
  <p>Deux précautions gratuites : prendre les deux électrodes de mesure dans le
  <strong>même lot et le même modèle</strong>, pour que leurs dérives se
  soustraient ; et interposer un pont de gel <strong>KCl</strong> — les mobilités
  du potassium et du chlorure étant quasi identiques, le potentiel de jonction
  y est minimal. C'est exactement ce que fait le gel d'une électrode ECG
  jetable.</p>
</div>

<h3 id="p2-50hz" data-toc="sub">Le 50 Hz et l'isolation</h3>

<p>Un arbre instrumenté est une antenne de plusieurs mètres au milieu d'un champ
électrique à 50 Hz. Trois lignes de défense se cumulent, dans cet ordre :</p>
<ol>
  <li><strong>Le mode commun.</strong> Les deux électrodes captent le secteur
  presque à l'identique ; l'amplificateur d'instrumentation, qui ne répond qu'à
  la différence, en élimine l'essentiel — d'où l'importance de câbles de même
  longueur et de même cheminement.</li>
  <li><strong>L'intégration.</strong> En échantillonnant sur une durée multiple
  entière de 20 ms, la moyenne du secteur est rigoureusement nulle. À 8
  échantillons par seconde, l'ADS1115 intègre sur 125 ms, soit très exactement
  six périodes et quart — on préférera un réglage à 8 SPS ou 16 SPS.</li>
  <li><strong>Le filtre réjecteur numérique</strong>, en dernier recours, sur ce
  qui reste.</li>
</ol>

<p>L'isolateur ADuM1251 ne sert pas à protéger l'humain : sous 3,3 V il n'y a
rien à protéger. Il coupe la <strong>boucle de masse</strong>. Sans lui, la masse
du montage rejoint la terre du réseau par l'alimentation de la passerelle, et le
secteur revient dans la mesure par ce chemin, en contournant toutes les
précautions prises en amont.</p>

<h3 id="p2-bom" data-toc="sub">Nomenclature</h3>
{bom2}
</section>''')


# =============================================================================
#  PLANCHE 3 — NŒUD ENVIRONNEMENTAL
# =============================================================================
bom3 = tableau(
    ["Rep.", "Capteur / composant", "Grandeur · plage", "Précision annoncée",
     "Interface", "≈ €"],
    [["U1", "ESP32-S3 (carte DevKit)", "—", "veille ≈ 13 µA au niveau carte",
      "Wi-Fi / BLE", "9,00 – 15,00"],
     ["—", "Variante ESP32-C6", "—", "veille ≈ 7 µA au niveau puce",
      "Wi-Fi 6 / Thread", "8,00"],
     ["—", "Variante Raspberry Pi Pico 2 W", "—", "RP2350, 520 Ko SRAM",
      "Wi-Fi / BLE 5.2", "7,00"],
     ["A1", "BME280", "T −40…+85 °C · HR 0–100 % · P 300–1100 hPa",
      "±1,0 °C · ±3 % HR · ±1 hPa", "I²C / SPI", "4,00"],
     ["—", "BME680 (ajoute un capteur de gaz)", "idem + COV (indice)",
      "indice non étalonné, dérive", "I²C / SPI", "12,00"],
     ["—", "SHT31 (référence T/HR)", "T −40…+125 °C · HR 0–100 %",
      "±0,2 °C · ±2 % HR", "I²C", "9,00"],
     ["—", "SHT85 (métrologie)", "T −40…+105 °C · HR 0–100 %",
      "±0,1 °C · ±1,5 % HR", "I²C", "45,00"],
     ["A2", "BH1750FVI", "éclairement 1 – 65 535 lx", "±20 % typ.", "I²C", "3,00"],
     ["—", "TSL2591 (forte dynamique)", "188 µlx – 88 000 lx", "—", "I²C", "7,00"],
     ["—", "Apogée SQ-500 (PAR de référence)", "PPFD 0 – 4 000 µmol m⁻² s⁻¹",
      "erreur directionnelle ≤ ±5 % à 75°", "analogique 0,01 mV/µmol", "≈ 300,00"],
     ["A3", "SCD41", "CO₂ 400 – 5 000 ppm", "±(40 ppm + 5 %)",
      "I²C", "38,00"],
     ["—", "SCD30 (meilleure justesse absolue)", "CO₂ 400 – 10 000 ppm",
      "±(30 ppm + 3 %)", "I²C", "45,00"],
     ["A4–A6", "DS18B20 étanches (×3)", "T −55…+125 °C",
      "±0,5 °C entre −10 et +85 °C", "1-Wire", "9,00"],
     ["A7", "Sonde capacitive d'humidité du sol v2.0", "sortie 0 – 3 V, non étalonnée",
      "relatif seulement", "analogique", "4,00"],
     ["—", "Watermark 200SS (potentiel matriciel)", "0 – 200 kPa",
      "étalonnage Shock 1998, 10–100 kPa", "résistif (excitation alternative)", "40,00"],
     ["—", "TEROS 12 (teneur en eau volumique)", "VWC · T · CE",
      "±0,03 m³/m³ étalonnage générique", "SDI-12", "≈ 250,00"],
     ["R1–R4", "Résistances de tirage et anti-rebond", "4,7 kΩ ×3, 10 kΩ", "1 %",
      "—", "0,40"],
     ["C1, C2", "Anti-rebond et découplage", "100 nF ×2", "X7R", "—", "0,30"],
     ["—", "Anémomètre à coupelles à contact ILS", "vent", "selon modèle", "impulsions",
      "25,00"],
     ["—", "Pluviomètre à augets", "0,2 mm par bascule", "±2 % typ.", "impulsions",
      "30,00"]],
    legende="Nomenclature de la planche 3, avec les alternatives de montée en gamme. "
            "Plages et précisions issues des datasheets constructeur ; les écarts de prix "
            "d'un facteur dix entre un BH1750 et un SQ-500 correspondent à un écart de "
            "nature, pas de qualité — voir la discussion lux / PPFD.")

ecrire("12-planche3", f'''<section class="pagebreak">
<h2 id="p3" data-toc="chapter">Planche 3 — Le nœud environnemental</h2>

<p class="lettrine noindent">Sans contexte, le signal d'un arbre ne veut rien
dire. Une variation d'impédance à midi en juillet et la même variation à
quatre heures du matin en novembre n'ont pas le même sens. Le nœud
environnemental n'est donc pas un accessoire : c'est ce qui rend le signal
principal interprétable.</p>

{planche("sch-bus-capteurs-esp32.svg", 3,
         "Nœud environnemental ESP32",
         "bus I²C partagé, bus 1-Wire, entrée analogique et comptage d'impulsions "
         "avec anti-rebond matériel.")}

<h3 id="p3-bus" data-toc="sub">Quatre familles de liaison, quatre logiques</h3>

<p>Le <strong>bus I²C</strong> porte les capteurs intelligents : température,
humidité, pression, lumière, CO₂. Chacun répond à une adresse propre, deux fils
suffisent pour tous. La contrainte est la longueur : au-delà d'un mètre environ,
la capacité du câble arrondit les fronts et le bus devient instable. On descend
alors les résistances de tirage à 2,2 kΩ, ou l'on renonce à l'I²C.</p>

<p>Le <strong>1-Wire</strong> accepte au contraire plusieurs dizaines de mètres.
C'est lui qui va chercher les températures loin du boîtier : l'air sous abri, le
sol à dix centimètres, le tronc lui-même. Chaque DS18B20 porte une adresse
gravée sur 64 bits, ce qui permet d'en mettre plusieurs sur le même fil sans
ambiguïté — à condition de noter quelle adresse correspond à quel emplacement,
faute de quoi l'ordre change au premier remplacement.</p>

<p>L'<strong>entrée analogique</strong> reçoit la sonde capacitive d'humidité du
sol. Le <strong>comptage d'impulsions</strong> reçoit l'anémomètre et le
pluviomètre.</p>

<div class="callout limite">
  <div class="callout-title">L'anti-rebond doit être matériel</div>
  <p class="noindent">Un contact à lame souple rebondit pendant une à cinq
  millisecondes. Une bascule de pluviomètre produit alors trois ou quatre
  interruptions au lieu d'une, et la pluie est surestimée d'autant. Le réseau
  R4-C2 (10 kΩ × 100 nF, soit 1 ms de constante de temps) résout le problème
  avant qu'il n'atteigne le logiciel. Un anti-rebond purement logiciel oblige à
  rester éveillé, ce qui ruine le budget d'énergie.</p>
</div>

<h3 id="p3-lux" data-toc="sub">Lux et µmol : une confusion coûteuse</h3>

<p>Un BH1750 mesure des <strong>lux</strong>, c'est-à-dire un flux lumineux
pondéré par la sensibilité de l'œil humain, qui culmine dans le vert vers
555 nm. Or la photosynthèse ne voit pas comme nous : elle compte des
<strong>photons</strong> entre 400 et 700 nm, et travaille surtout dans le bleu
et le rouge — précisément là où l'œil est peu sensible. Les deux grandeurs ne
mesurent pas la même chose.</p>

<p>Sous lumière solaire, et sous elle seulement, un facteur empirique d'environ
0,0185 permet de passer des lux aux µmol·m⁻²·s⁻¹ : 108 000 lx de plein soleil
correspondent à environ 2 000 µmol·m⁻²·s⁻¹. Ce facteur est <strong>faux pour
toute autre source</strong> : sous un éclairage horticole à LED rouge et bleu,
l'erreur dépasse couramment un facteur trois. Si le rayonnement utile à la
plante est une variable du projet, il faut un capteur quantique — un Apogee
SQ-500 ou équivalent, dix fois plus cher, mais qui mesure la bonne grandeur.</p>

<h3 id="p3-bom" data-toc="sub">Nomenclature et alternatives</h3>
{bom3}

<h3 id="p3-sol" data-toc="sub">Pourquoi les sondes d'humidité résistives sont à proscrire</h3>

<p>Les sondes vendues quelques centimes, à deux broches nues et dorées, mesurent
la conductivité du sol entre deux électrodes traversées par un courant continu.
Cette configuration provoque une <strong>électrolyse</strong> : le métal d'une
électrode se dissout et se dépose sur l'autre. En sol humide et sous tension
permanente, la destruction est visible en quelques semaines, et la dérive bien
avant. S'y ajoute une sensibilité majeure à la salinité : un apport d'engrais
fait chuter la résistance sans qu'une goutte d'eau ait bougé.</p>

<p>Les sondes <strong>capacitives</strong> déplacent le problème : leurs
électrodes sont noyées dans l'époxy, le courant continu ne circule plus, la
corrosion disparaît. Elles restent toutefois non étalonnées et sensibles à la
texture du sol — elles donnent un indice relatif, pas une teneur en eau. Les
versions v1.2, très répandues, sont dépourvues de régulateur embarqué et leur
lecture varie avec la tension d'alimentation : on privilégiera les v2.0, et l'on
alimentera la sonde sous une tension stable.</p>

<p>Au-dessus, deux familles de mesures véritablement quantitatives coexistent :
le <strong>potentiel matriciel</strong>, qui exprime l'effort que la plante doit
fournir pour extraire l'eau, mesuré par un Watermark 200SS ou un tensiomètre ; et
la <strong>teneur en eau volumique</strong>, mesurée par réflectométrie
temporelle. Pour un arbre, c'est le potentiel matriciel qui est
physiologiquement pertinent : c'est lui que l'arbre « ressent ».</p>
</section>''')


# =============================================================================
#  PLANCHE 4 — ALIMENTATION
# =============================================================================
bom4 = tableau(
    ["Rep.", "Composant", "Caractéristique", "Référence indicative", "≈ €"],
    [["PV", "Panneau solaire", "6 V / 5 W, verre trempé", "générique cadre alu", "18,00"],
     ["D1", "Diode Schottky anti-retour", "40 V / 3 A, V<sub>f</sub> 0,5 V",
      "SS34", "0,20"],
     ["U1", "Chargeur MPPT 1 cellule", "point de puissance par pont résistif",
      "CN3791 (module)", "6,00"],
     ["BT1", "Accumulateur LiFePO₄", "3,2 V · 6 000 mA·h · −20…+60 °C",
      "cellule 32700 + support", "14,00"],
     ["U2", "Convertisseur abaisseur-élévateur", "3,3 V, η > 90 %, arrêt commandé",
      "TI TPS63020", "7,50"],
     ["—", "Sonde de température de batterie", "verrouillage de charge < 0 °C",
      "DS18B20", "3,00"],
     ["F1", "Fusible réarmable", "PTC 1 A", "MF-R110", "0,40"],
     ["—", "Boîtier étanche", "IP65/IP67, ABS, presse-étoupes",
      "160 × 110 × 90 mm", "16,00"],
     ["—", "Évent à membrane ePTFE", "équilibrage de pression, anti-condensation",
      "Gore Protective Vent (vissant)", "7,00"],
     ["—", "Presse-étoupes M12 à joint", "×4", "nylon IP68", "4,00"],
     ["—", "Abri météorologique à persiennes", "erreur radiative réduite",
      "type Stevenson, 7 coupelles", "35,00"]],
    legende="Nomenclature de la planche 4. L'évent à membrane et l'abri météorologique "
            "sont les deux lignes que l'on supprime le plus volontiers, et les deux dont "
            "l'absence se paie en données inutilisables.",
    total=["", "<b>Total chaîne d'énergie et protection</b>", "", "", "<b>≈ 111 €</b>"])

ecrire("13-planche4", f'''<section class="pagebreak">
<h2 id="p4" data-toc="chapter">Planche 4 — Énergie et survie en extérieur</h2>

<p class="lettrine noindent">Une station qui s'arrête en novembre n'a pas
mesuré une année : elle a mesuré un été. L'autonomie n'est pas un raffinement,
c'est la condition de l'existence même d'une série temporelle.</p>

{planche("sch-alim-solaire.svg", 4,
         "Alimentation solaire LiFePO₄",
         "chaîne panneau → MPPT → accumulateur → régulateur, avec budget d'énergie.")}

<h3 id="p4-budget" data-toc="sub">Le budget d'énergie, ligne à ligne</h3>

<p>Le calcul se fait toujours sur un cycle complet, pas sur une consommation
moyenne. Pour un relevé toutes les quinze minutes avec émission LoRa :</p>

<table class="tight">
<thead><tr><th>Phase</th><th>Courant</th><th>Durée</th><th>Charge</th></tr></thead>
<tbody>
<tr><td>Veille profonde</td><td>15 µA</td><td>899 s</td><td>13,5 mA·s</td></tr>
<tr><td>Réveil, stabilisation et mesures</td><td>40 mA</td><td>0,9 s</td><td>36,0 mA·s</td></tr>
<tr><td>Émission LoRa</td><td>120 mA</td><td>0,1 s</td><td>12,0 mA·s</td></tr>
<tr class="tot"><td><b>Par cycle</b></td><td></td><td>900 s</td><td><b>61,5 mA·s</b></td></tr>
</tbody>
</table>

<p>Soit 0,0171 mA·h par cycle, 1,64 mA·h par jour, environ 600 mA·h par an. Une
cellule de 6 000 mA·h tiendrait donc près de dix ans sans le moindre apport
solaire. Ce résultat, contre-intuitif, a une conséquence pratique nette :
<strong>dans une station bien conçue, la capacité n'est jamais la contrainte.</strong>
Ce qui tue les stations, c'est la consommation résiduelle des cartes de
développement — un régulateur à faible rendement ou une puce USB-série qui
continue de tirer dix milliampères pendant la veille suffit à multiplier le
budget par mille.</p>

<div class="callout limite">
  <div class="callout-title">La charge sous zéro degré</div>
  <p class="noindent">Toutes les chimies au lithium, LiFePO₄ comprise,
  interdisent la charge sous 0 °C : le lithium se dépose alors sous forme
  métallique sur l'anode, de façon irréversible, et la capacité s'effondre en
  quelques cycles. C'est l'avarie numéro un des stations hivernales, et elle est
  silencieuse. La parade tient en trois euros : un DS18B20 collé contre la
  cellule et un verrouillage logiciel de la charge.</p>
</div>

<h3 id="p4-liaison" data-toc="sub">Choisir la liaison</h3>

<table class="tight">
<thead><tr><th>Liaison</th><th>Portée réaliste</th><th>Débit utile</th>
<th>Contrainte</th><th>Abonnement</th></tr></thead>
<tbody>
<tr><td>Wi-Fi</td><td>30 – 80 m</td><td>élevé</td>
<td>consommation d'association élevée</td><td>—</td></tr>
<tr><td>LoRaWAN (TTN)</td><td>2 – 15 km</td><td>quelques octets</td>
<td>1 % de rapport cyclique en EU868 ; sur le réseau communautaire TTN,
politique d'usage équitable de 30 s d'émission par jour et 10 messages
descendants</td><td>gratuit</td></tr>
<tr><td>NB-IoT / LTE-M</td><td>couverture opérateur</td><td>quelques ko</td>
<td>dépend d'un opérateur, carte SIM</td><td>≈ 10 – 30 €/an</td></tr>
<tr><td>Maillage LoRa (Meshtastic)</td><td>quelques km, relayé</td><td>faible</td>
<td>pas d'infrastructure, mais pas de garantie</td><td>—</td></tr>
</tbody>
</table>

<p>La politique d'usage équitable de TTN est plus contraignante qu'il n'y
paraît : trente secondes d'émission par jour, à un facteur d'étalement moyen,
autorisent environ une centaine de messages courts — soit très exactement le
rythme d'un relevé au quart d'heure. Il n'y a pas de marge pour transmettre une
forme d'onde. <strong>Le traitement doit donc avoir lieu dans le nœud</strong>,
et c'est le résumé statistique, non le signal brut, qui voyage.</p>

<h3 id="p4-boitier" data-toc="sub">Le boîtier : condensation et presse-étoupes</h3>

<p>Un boîtier IP67 parfaitement étanche est une machine à fabriquer de l'eau. Le
jour, l'air intérieur se dilate ; la nuit, il se contracte et aspire de l'air
humide par le moindre défaut ; au matin, la vapeur condense sur l'électronique
froide. Le cycle se répète et l'eau s'accumule.</p>

<p>La solution n'est pas de mieux étancher mais de <strong>ventiler
sélectivement</strong> : un évent à membrane ePTFE laisse passer les molécules
de gaz et de vapeur, bloque l'eau liquide et les poussières, et supprime la
différence de pression qui aspirait l'air humide. Les câbles, eux, entrent par
des presse-étoupes à joint, toujours <strong>par le dessous</strong>, avec une
boucle d'égouttement en amont pour que l'eau ruisselant le long du câble tombe
avant d'atteindre l'entrée.</p>

<h3 id="p4-bom" data-toc="sub">Nomenclature</h3>
{bom4}
</section>''')


# =============================================================================
#  PLANCHE 5 — FLUX DE SÈVE
# =============================================================================
bom5 = tableau(
    ["Rep.", "Élément", "Détail", "≈ €"],
    [["—", "Tube inox 316L", "Ø ext. 2 mm, paroi 0,2 mm, longueur 20 mm ×2", "6,00"],
     ["R_ch", "Fil résistif constantan", "≈ 25 Ω bobinés sur l'aiguille amont", "3,00"],
     ["—", "Couple thermoélectrique cuivre / constantan", "type T, fil 0,08 mm", "9,00"],
     ["—", "Résine époxy thermiquement conductrice", "remplissage des aiguilles", "8,00"],
     ["U1", "Convertisseur ΔΣ 24 bits", "TI ADS1220, PGA ×128, réf. interne", "8,00"],
     ["—", "Référence de tension de précision", "LM4040 2,048 V", "1,50"],
     ["—", "Isolation thermique du site de mesure", "mousse réfléchissante + écran", "6,00"],
     ["—", "Mèche et guide de perçage", "Ø 2 mm, butée de profondeur", "12,00"],
     ["", "<b>Total sonde bricolée, les deux aiguilles</b>", "", "<b>≈ 54 €</b>"]],
    legende="Nomenclature indicative d'une sonde de dissipation thermique auto-construite. "
            "À comparer aux instruments du commerce : un TreeTalker®Water est annoncé à "
            "210 € en version LoRa par le tarif public 2026 de Nature 4.0, et les "
            "SFM1x d'ICT International ou les Dynagage de Dynamax ne sont vendus que sur "
            "devis. La littérature (Davis et al., 2012) documente des capteurs "
            "auto-construits donnant des estimations acceptables pour une fraction du "
            "coût des instruments commerciaux — le procédé Granier étant tombé dans le "
            "domaine public.")

ecrire("14-planche5", f'''<section class="pagebreak">
<h2 id="p5" data-toc="chapter">Planche 5 — Le flux de sève</h2>

<p class="lettrine noindent">De toutes les grandeurs mesurables sur un arbre,
le flux de sève est la plus proche de ce qu'un profane appellerait « ce que
l'arbre est en train de faire ». C'est aussi la plus invasive : elle exige de
percer l'aubier.</p>

{planche("sch-granier-tdp.svg", 5,
         "Sonde de flux de sève par dissipation thermique",
         "méthode Granier : aiguille chauffée à puissance constante et aiguille de "
         "référence, couple thermoélectrique différentiel, numérisation 24 bits.")}

<h3 id="p5-principe" data-toc="sub">Le principe</h3>

<p>Deux aiguilles sont implantées dans l'aubier sur la même verticale, à quarante
millimètres d'écart. Celle du haut contient une résistance chauffée à puissance
constante — environ 0,2 W. Celle du bas ne chauffe pas et sert de référence. Un
couple thermoélectrique différentiel mesure l'écart de température entre les
deux.</p>

<p>Quand la sève ne monte pas, la chaleur ne s'évacue que par conduction et
l'écart est maximal. Quand la sève monte, elle emporte la chaleur et l'écart
diminue. Granier a établi en 1985 une relation empirique entre cet écart et la
densité de flux :</p>

<p class="center"><i>K</i> = (ΔT<sub>max</sub> − ΔT) / ΔT<br/>
<i>u</i> = 118,99·10⁻⁶ · <i>K</i><sup>1,231</sup>&nbsp;&nbsp;[m³ m⁻² s⁻¹]</p>

<div class="callout limite">
  <div class="callout-title">Le facteur 100 qui fausse une implémentation sur deux</div>
  <p class="noindent">Le coefficient dépend entièrement du système d'unités
  retenu, et les quatre écritures suivantes, toutes présentes dans la
  littérature, sont strictement équivalentes :</p>
  <table class="tight" style="margin:.6em 0">
  <thead><tr><th>Écriture</th><th>Unité de u</th></tr></thead>
  <tbody>
  <tr><td>u = 4,284 · K<sup>1,231</sup></td><td>L·dm⁻²·h⁻¹, soit dm/h</td></tr>
  <tr><td>u = 0,0119 · K<sup>1,231</sup></td><td>cm³·cm⁻²·s⁻¹, soit <b>cm/s</b></td></tr>
  <tr><td>u = 119·10⁻⁶ · K<sup>1,231</sup></td><td>m³·m⁻²·s⁻¹, soit <b>m/s</b></td></tr>
  <tr><td>u = 0,119 · K<sup>1,231</sup></td><td>kg·m⁻²·s⁻¹ (× masse volumique)</td></tr>
  </tbody></table>
  <p>Confondre les deux écritures du milieu introduit un <strong>facteur
  100</strong>. C'est l'erreur d'implémentation la plus fréquente de toute la
  méthode. L'exposant exact est 1,231 ; la valeur 1,23 est un arrondi. Enfin,
  u est une <strong>vitesse de filtration</strong> — un volume par unité de
  surface d'aubier conducteur — et non la vitesse réelle de la sève dans les
  vaisseaux, qui est plus élevée.</p>
</div>

<p>où ΔT<sub>max</sub> est l'écart relevé en fin de nuit, lorsque le flux est
supposé nul. Cette hypothèse est elle-même une source d'erreur : par nuit chaude
et sèche, la transpiration nocturne ne s'annule pas, et l'on sous-estime alors
ΔT<sub>max</sub>, donc tout le reste de la journée.</p>

<div class="callout limite">
  <div class="callout-title">Un indice, pas un débit</div>
  <p class="noindent">L'étalonnage d'origine de Granier a été établi sur un
  petit nombre d'espèces. La littérature ultérieure documente des
  sous-estimations massives : −60 % sur noisetier contre potomètre de précision
  (<i>Sensors</i> 19:2419, 2019) ; −69 % sur <i>Pinus tabuliformis</i> faute de
  calibration d'espèce ; −37 % sur l'usage d'eau d'un peuplement de conifères
  (Peters et al., <i>New Phytologist</i>, 2018) ; jusqu'à −50 % lorsque la sonde
  déborde de l'aubier conducteur (Clearwater et al., 1999). Une méta-analyse de
  290 expériences de calibration (Flo et al., <i>Agric. For. Meteorol.</i>, 2019)
  conclut que les méthodes à dissipation ont la plus faible exactitude et le plus
  fort biais proportionnel, mais une bonne linéarité et une bonne précision :
  elles conviennent au flux <i>relatif</i>, pas au flux absolu. Sans
  recalibration sur l'espèce étudiée, <strong>ce montage ne donne pas un débit
  absolu</strong>. Il donne un indice relatif, parfaitement utilisable pour
  suivre une dynamique jour/nuit ou un stress hydrique sur un même arbre, mais
  qu'il serait malhonnête de convertir en litres par jour.</p>
</div>

<div class="callout limite">
  <div class="callout-title">L'artefact qu'on ne voit jamais venir</div>
  <p class="noindent">Un tronc n'est pas isotherme. Do et Rocheteau ont mesuré
  en 2002 des <strong>gradients thermiques naturels de 0,3 à 3,5 °C</strong>
  entre deux points distants de huit à dix centimètres — positifs la nuit,
  négatifs le jour — capables d'induire des erreurs de flux dépassant 100 %.
  L'écart utile de la mesure étant du même ordre, l'artefact est indiscernable
  du signal. Le remède validé est le <strong>chauffage cyclique</strong> :
  45 minutes allumé, 15 minutes éteint. La phase froide donne le gradient
  naturel seul, qu'on soustrait ensuite. Elle divise en outre la consommation
  par quatre — dans une station solaire, c'est un double bénéfice.</p>
</div>

<h3 id="p5-metro" data-toc="sub">La contrainte métrologique</h3>

<p>L'écart utile va de zéro à une dizaine de kelvins, et il faut le résoudre au
centième de kelvin. Un couple cuivre-constantan produit environ 40 µV par
kelvin : il faut donc distinguer 0,4 µV. Aucun convertisseur intégré à un
microcontrôleur ne sait faire cela. D'où le choix d'un convertisseur 24 bits
muni d'un amplificateur à gain programmable ×128, et d'une référence de tension
stable en température — car une dérive de la référence se lit exactement comme
une variation de flux.</p>

<p>Les autres méthodes thermiques répondent à d'autres besoins. La
<strong>méthode du rapport de chaleur</strong> (heat ratio method) envoie une
impulsion brève au lieu d'un chauffage continu et mesure la dissymétrie de
propagation de part et d'autre de la source : elle sait mesurer les flux très
lents et surtout les <strong>flux inverses</strong>, invisibles à la méthode
Granier, et elle consomme beaucoup moins. C'est celle qu'emploient les
instruments d'ICT International, et c'est aussi celle retenue par le TreeTalker,
qui envoie une impulsion de six secondes une fois par heure.</p>

<h3 id="p5-bom" data-toc="sub">Nomenclature</h3>
{bom5}

<div class="callout limite">
  <div class="callout-title">Percer un arbre</div>
  <p class="noindent">Deux trous de deux millimètres dans l'aubier d'un arbre
  adulte sain se compartimentent normalement. Mais chaque perforation est une
  porte d'entrée pour les champignons de carie, et le bois ne cicatrise pas : il
  cloisonne. On limitera donc le nombre de sondes, on les espacera
  verticalement, on désinfectera le matériel entre deux arbres, et l'on
  s'abstiendra sur un sujet déjà affaibli, sur un arbre remarquable ou sur un
  jeune sujet. Sur un arbre de moins de quinze centimètres de diamètre, la
  méthode est de toute façon inapplicable.</p>
</div>
</section>''')


# =============================================================================
#  BOM GLOBALE
# =============================================================================
bomg = tableau(
    ["Configuration", "Ce qu'elle mesure", "Ce qu'elle ne mesure pas", "Budget"],
    [["<b>A — Atelier découverte</b><br/><span class='small'>planche 1 seule</span>",
      "Impédance de surface d'une feuille, convertie en MIDI. Un micro-contrôleur, "
      "une plante, un synthétiseur.",
      "Rien de physiologique au sens strict. Aucune donnée conservable.",
      "<b>≈ 45 €</b><br/><span class='small'>avec la carte Arduino</span>"],
     ["<b>B — Station environnementale</b><br/><span class='small'>planches 3 et 4</span>",
      "Température de l'air, du sol et du tronc, humidité, pression, lumière, CO₂, "
      "pluie, vent. Séries horodatées sur plusieurs années.",
      "L'état interne de l'arbre. On mesure son environnement, pas lui.",
      "<b>≈ 230 €</b>"],
     ["<b>C — Station physiologique</b><br/><span class='small'>B + planche 5</span>",
      "Tout ce qui précède, plus la dynamique du flux de sève et donc la "
      "transpiration relative.",
      "Un débit absolu, sans recalibration par espèce.",
      "<b>≈ 290 €</b>"],
     ["<b>D — Chaîne complète</b><br/><span class='small'>B + C + planche 2</span>",
      "Tout ce qui précède, plus le potentiel électrique extracellulaire, "
      "correctement amplifié et isolé.",
      "Une interprétation. Le signal existe ; sa signification reste à construire.",
      "<b>≈ 420 €</b><br/><span class='small'>électrodes de laboratoire : +120 €</span>"]],
    classes="compare tight",
    legende="Quatre configurations d'atelier, du plus démonstratif au plus "
            "métrologique. La colonne du milieu est la plus importante du document.")

ecrire("20-bom-globale", f'''<section class="pagebreak">
<h2 id="bomg" data-toc="chapter">Nomenclature d'ensemble et budgets</h2>

<p class="lettrine noindent">Les nomenclatures précédentes se lisent planche par
planche. Celle-ci se lit projet par projet : elle répond à la seule question que
pose réellement un porteur d'atelier, qui est de savoir ce qu'il obtient pour ce
qu'il dépense.</p>

{bomg}

<h3 id="bomg-outils" data-toc="sub">Outillage minimal de l'atelier</h3>
<table class="tight">
<thead><tr><th>Outil</th><th>Usage</th><th>≈ €</th></tr></thead>
<tbody>
<tr><td>Fer à souder à température régulée, panne fine</td><td>tout</td><td>45,00</td></tr>
<tr><td>Multimètre avec mesure de capacité</td><td>vérification des valeurs, continuité</td><td>35,00</td></tr>
<tr><td>Oscilloscope d'entrée de gamme ou analyseur logique USB</td>
<td>indispensable pour voir le signal du LMC555 et déboguer l'I²C</td><td>25,00 – 120,00</td></tr>
<tr><td>Pince à dénuder, pince coupante, troisième main</td><td>montage</td><td>25,00</td></tr>
<tr><td>Alimentation de laboratoire réglable</td><td>caractérisation, mise au point</td><td>60,00</td></tr>
<tr><td>Sonde de température de référence étalonnée</td>
<td>vérifier les capteurs les uns contre les autres avant la pose</td><td>30,00</td></tr>
</tbody>
</table>

<div class="callout key">
  <div class="callout-title">La dépense qu'on oublie toujours</div>
  <p class="noindent">Ce n'est ni un capteur ni une carte : c'est le
  <strong>temps de maintenance</strong>. Une station extérieure demande une
  visite par trimestre — nettoyage de l'abri, vérification des presse-étoupes,
  contrôle de la dérive, ré-ouverture des sangles, relevé de la batterie. Une
  station qu'on ne visite pas produit des données qu'on ne pourra pas défendre,
  parce que personne ne saura dire à partir de quelle date le capteur s'était
  rempli d'eau.</p>
</div>
</section>''')

print("  (fragments de contenu écrits ; les listings suivent)")


# =============================================================================
#  PROGRAMMES
# =============================================================================
L1 = bloc("electricityforprogress_BiodataSonificationBreadboardKit.zip",
          r"BiodataSonification_026_kit\.ino$",
          debut=r"^//interrupt timing sample array", fin=r"^int scaleSearch")
L2 = bloc("electricityforprogress_BiodataSonificationBreadboardKit.zip",
          r"BiodataSonification_026_kit\.ino$",
          debut=r"^int scaleSearch")
L3 = bloc("electricityforprogress_BiodataFeather.zip",
          r"Biodata_v007_ESP32S3/MIDI\.ino$",
          debut=r"void setNote", fin=r"^void midiSerial")

SRC_MIT = ('dépôt <span class="phon">electricityforprogress/'
           'BiodataSonificationBreadboardKit</span>, licence MIT — archive '
           '<span class="phon">sources/code/</span>, extrait à la construction du PDF.')
SRC_FEA = ('dépôt <span class="phon">electricityforprogress/BiodataFeather</span>, '
           'licence MIT — archive <span class="phon">sources/code/</span>.')

ESPHOME = '''# noeud-arbre.yaml — ESPHome (licence du projet : MIT/GPLv3 composite)
# Relevé toutes les 15 min puis veille profonde. Adapter substitutions/secrets.
substitutions:
  nom: arbre-01
  intervalle: 15min

esphome:
  name: ${nom}
  on_boot:
    priority: -100
    then:
      - delay: 20s            # laisse le temps aux capteurs et à la publication
      - deep_sleep.enter: veille

esp32:
  board: esp32-s3-devkitc-1
  framework: { type: esp-idf }

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_pass
  fast_connect: true          # évite le balayage complet : ~1 s gagnée par cycle

mqtt:
  broker: !secret mqtt_host
  topic_prefix: arbres/${nom}

deep_sleep:
  id: veille
  run_duration: 25s
  sleep_duration: ${intervalle}

i2c:
  sda: GPIO8
  scl: GPIO9
  frequency: 100kHz           # 400 kHz devient instable au-delà d'un metre de cable

one_wire:
  - platform: gpio
    pin: GPIO4

sensor:
  - platform: bme280_i2c
    address: 0x76
    temperature:  { name: "T air",      accuracy_decimals: 2 }
    humidity:     { name: "HR air",     accuracy_decimals: 1 }
    pressure:     { name: "Pression",   accuracy_decimals: 1 }
    update_interval: 10s

  - platform: bh1750
    name: "Eclairement"
    address: 0x23
    update_interval: 10s

  - platform: scd4x
    address: 0x62
    co2: { name: "CO2" }
    update_interval: 10s

  - platform: dallas_temp          # adresses relevees au premier demarrage
    address: 0x1c0000031edd2a28
    name: "T sol -10 cm"
  - platform: dallas_temp
    address: 0x3b00000320ab5c28
    name: "T tronc nord"

  - platform: adc                  # sonde capacitive d'humidite du sol
    pin: GPIO5
    name: "Humidite sol (brut)"
    attenuation: 12db
    update_interval: 10s
    filters:
      - median: { window_size: 9, send_every: 9 }
      - calibrate_linear:          # A ETALONNER : sec puis immerge, voir listing 5
          - 2.90 -> 0.0
          - 1.20 -> 100.0
      - clamp: { min_value: 0, max_value: 100 }
    unit_of_measurement: "%"

  - platform: pulse_counter        # pluviometre a augets, 0,2 mm par bascule
    pin:
      number: GPIO6
      mode: { input: true, pullup: true }
    name: "Pluie"
    internal_filter: 10ms          # en complement de l'anti-rebond materiel
    update_interval: ${intervalle}
    unit_of_measurement: "mm"
    filters:
      - multiply: 0.2
'''

ADS = '''#!/usr/bin/env python3
"""Acquisition electrophysiologique : ADS1115 -> rejet du 50 Hz -> MQTT.

Le point cle n'est pas le filtrage mais la CADENCE : en integrant sur une duree
multiple entiere de 20 ms, la composante a 50 Hz s'annule par construction.
L'ADS1115 a 8 SPS integre sur 125 ms = 6,25 periodes ; a 16 SPS, 3,125.
On prend donc 8 SPS et on moyenne un nombre entier de fenetres.

Dependances : adafruit-circuitpython-ads1x15, paho-mqtt, numpy
Licence : CC0 - code d'exemple, a reprendre sans condition.
"""
import json
import time

import board
import busio
import numpy as np
import paho.mqtt.client as mqtt
from adafruit_ads1x15.ads1115 import ADS1115, Mode
from adafruit_ads1x15.analog_in import AnalogIn

PERIODE_SECTEUR = 1 / 50          # 20 ms
N_FENETRES = 16                   # 16 x 125 ms = 2 s par point publie
SEUIL_SATURATION = 0.95           # fraction de pleine echelle

i2c = busio.I2C(board.SCL, board.SDA)
adc = ADS1115(i2c, address=0x48)
adc.mode = Mode.CONTINUOUS
adc.data_rate = 8                 # 8 SPS -> integration sur 125 ms
adc.gain = 4                      # +/- 1.024 V pleine echelle

voie = AnalogIn(adc, 0)           # AIN0 par rapport a la masse du montage


def mesure_bloc(n=N_FENETRES):
    """Renvoie (moyenne_V, ecart_type_V, n_satures)."""
    ech, satures = [], 0
    for _ in range(n):
        v = voie.voltage
        if abs(voie.value) > SEUIL_SATURATION * 32767:
            satures += 1
        ech.append(v)
        time.sleep(1 / adc.data_rate)
    a = np.asarray(ech)
    return float(a.mean()), float(a.std()), satures


def qualite(ecart_type, satures):
    """Un point sans indicateur de qualite est un point indefendable."""
    if satures:
        return "sature"
    if ecart_type > 5e-4:         # 0,5 mV d'agitation : contact ou vent
        return "bruite"
    return "ok"


def main():
    cli = mqtt.Client()
    cli.connect("localhost", 1883, 60)
    cli.loop_start()
    while True:
        moy, sd, sat = mesure_bloc()
        charge = {
            "t": time.time(),
            "v_uV": round(moy * 1e6, 1),      # microvolts : l'unite du domaine
            "sd_uV": round(sd * 1e6, 1),
            "qualite": qualite(sd, sat),
        }
        cli.publish("arbres/arbre-01/electro", json.dumps(charge), qos=1)
        time.sleep(1.0)


if __name__ == "__main__":
    main()
'''

GRANIER = '''#!/usr/bin/env python3
"""Reduction Granier : de l'ecart de temperature a la densite de flux de seve.

u = 118,99e-6 * K^1,231   avec  K = (dT_max - dT) / dT      [m3 m-2 s-1]
Granier A. (1985), Ann. For. Sci. 42(2), DOI 10.1051/forest:19850204

dT_max est estime sur une fenetre glissante de plusieurs jours, en prenant le
maximum nocturne. C'est l'hypothese faible de la methode : par nuit chaude et
seche la transpiration nocturne n'est pas nulle et dT_max est sous-estime.

Licence : CC0.
"""
import numpy as np
import pandas as pd

A, B = 118.99e-6, 1.231           # coefficients de Granier, unites SI


def dt_max_glissant(dt, index, jours=7, debut_nuit=0, fin_nuit=5):
    """Maximum nocturne sur une fenetre glissante, reindexe sur toute la serie."""
    s = pd.Series(dt, index=index)
    nuit = s.between_time(f"{debut_nuit:02d}:00", f"{fin_nuit:02d}:00")
    quotidien = nuit.resample("1D").max()
    lisse = quotidien.rolling(jours, center=True, min_periods=1).max()
    return lisse.reindex(s.index, method="nearest")


def densite_de_flux(dt, index, **kw):
    """Renvoie u en m3 m-2 s-1, et NaN la ou la mesure n'a pas de sens."""
    dtm = dt_max_glissant(dt, index, **kw)
    dt = np.asarray(dt, dtype=float)
    dtm = np.asarray(dtm, dtype=float)

    with np.errstate(divide="ignore", invalid="ignore"):
        k = (dtm - dt) / dt
    k = np.where(dt <= 0.05, np.nan, k)      # chauffage coupe ou sonde arrachee
    k = np.where(k < 0, 0.0, k)              # dT > dT_max : bruit, pas flux inverse
    return A * np.power(k, B)


def flux_sur_section(u, aire_aubier_m2):
    """Debit en litres par heure, une fois l'aire d'aubier connue.

    ATTENTION : cette conversion suppose le profil radial uniforme, ce qui est
    faux. Sans recalibration par espece, ne publier que u, jamais des litres.
    """
    return u * aire_aubier_m2 * 3600 * 1000
'''

OSC = '''#!/usr/bin/env python3
"""Pont sonification : MQTT -> OSC -> SuperCollider.

La regle de conception tient en une phrase : le mapping doit etre DECLARE,
REPRODUCTIBLE et INVERSIBLE. Si l'on ne peut pas retrouver la donnee a partir
du son, ce n'est pas de la sonification, c'est de l'illustration sonore.
Cf. Hermann T. (2008), Taxonomy and definitions for sonification and auditory
display, ICAD 2008.

Dependances : paho-mqtt, python-osc (The Unlicense)
Licence : CC0.
"""
import json

import paho.mqtt.client as mqtt
from pythonosc.udp_client import SimpleUDPClient

osc = SimpleUDPClient("127.0.0.1", 57120)      # port d'ecoute de sclang

# --- Le mapping, en un seul endroit, explicite et documente ------------------
# Chaque entree : (topic, champ, domaine_donnee, domaine_sonore, adresse OSC)
MAPPING = [
    ("arbres/+/electro", "v_uV",    (-2000.0, 2000.0), (48, 84),   "/arbre/hauteur"),
    ("arbres/+/seve",    "u",       (0.0, 2.5e-4),     (0.0, 1.0), "/arbre/densite"),
    ("arbres/+/env",     "hr_sol",  (0.0, 100.0),      (0.2, 1.0), "/arbre/timbre"),
    ("arbres/+/env",     "lux",     (0.0, 100000.0),   (0.0, 1.0), "/arbre/brillance"),
]


def echelle(x, source, cible, borner=True):
    (a, b), (c, d) = source, cible
    if b == a:
        return c
    y = c + (x - a) * (d - c) / (b - a)
    return min(max(y, min(c, d)), max(c, d)) if borner else y


def sur_message(_client, _userdata, msg):
    charge = json.loads(msg.payload)
    if charge.get("qualite") == "sature":
        return                       # on ne sonifie pas un artefact connu
    for motif, champ, dom, son, adresse in MAPPING:
        if champ not in charge or not mqtt.topic_matches_sub(motif, msg.topic):
            continue
        osc.send_message(adresse, float(echelle(charge[champ], dom, son)))


cli = mqtt.Client()
cli.on_message = sur_message
cli.connect("localhost", 1883, 60)
for motif, *_ in MAPPING:
    cli.subscribe(motif)
cli.loop_forever()
'''

SC = '''// arbre.scd — SuperCollider (GPLv3). Recoit l'OSC du listing 5.
// Une voix continue dont la hauteur suit le potentiel et le timbre l'humidite.
// Le silence est signifiant : pas de donnee valide -> pas de son.

s.waitForBoot({
    SynthDef(\\arbre, { |freq = 110, densite = 0.3, timbre = 0.5,
                        brillance = 0.4, amp = 0.15, porte = 1|
        var exc, corps, env;
        // Excitation : bruit filtre, densite pilotee par le flux de seve
        exc = Dust.ar(densite.linexp(0, 1, 1, 400)) * 0.6
              + PinkNoise.ar(0.08 * densite);
        // Corps resonant : le tronc comme filtre en peigne
        corps = Klank.ar(
            `[ Array.geom(6, freq, 1.51),
               Array.fill(6, { |i| 1 / (i + 1) }),
               Array.fill(6, { |i| timbre.linlin(0, 1, 0.6, 4.0) / (i + 1) }) ],
            exc);
        corps = LPF.ar(corps, brillance.linexp(0, 1, 400, 9000));
        env = EnvGen.kr(Env.asr(4, 1, 6), porte, doneAction: 2);
        Out.ar(0, Pan2.ar(corps * env * amp, 0));
    }).add;

    s.sync;
    ~voix = Synth(\\arbre);

    // Lissage : les donnees arrivent toutes les 2 s, l'oreille veut du continu.
    OSCdef(\\hauteur, { |m|
        ~voix.set(\\freq, m[1].midicps);
    }, "/arbre/hauteur");

    OSCdef(\\densite,   { |m| ~voix.set(\\densite,   m[1]) }, "/arbre/densite");
    OSCdef(\\timbre,    { |m| ~voix.set(\\timbre,    m[1]) }, "/arbre/timbre");
    OSCdef(\\brillance, { |m| ~voix.set(\\brillance, m[1]) }, "/arbre/brillance");
});
'''

PAROLE = '''#!/usr/bin/env bash
# parole.sh — de la mesure au son : LLM local (Ollama) puis synthese (Piper).
# Piper 1 : depot OHF-Voice/piper1-gpl, code GPLv3, poids MIT, voix francaises
# issues du corpus SIWIS (CC-BY 4.0). Ollama : MIT. Qwen3 : Apache-2.0.
set -euo pipefail

VOIX="${VOIX:-$HOME/voix/fr_FR-siwis-medium.onnx}"   # + le .onnx.json a cote
MODELE="${MODELE:-qwen3:1.7b}"                       # 1,28 Go en Q4_K_M

# 1. Les mesures des dernieres 24 h, deja reduites, en JSON compact.
mesures=$(curl -sS --get 'http://localhost:8086/api/v2/query' \
  --data-urlencode "org=arbres" \
  --data-urlencode 'q=from(bucket:"arbre") |> range(start:-24h)
                     |> aggregateWindow(every:1h, fn:mean)' )

# 2. On CONTRAINT le modele : il commente des chiffres, il ne les invente pas.
#    Le prompt est aussi un garde-fou deontologique : pas de premiere personne
#    attribuee a l'arbre sans que le dispositif soit explicite.
lu=$(ollama run "$MODELE" <<EOF
Tu commentes des mesures faites sur un arbre instrumente.
Regles absolues :
- n'ecris QUE ce que les chiffres montrent ; aucune emotion, aucune intention ;
- si une valeur manque ou est marquee "bruite", dis-le explicitement ;
- trois phrases maximum, en francais, sans metaphore ;
- termine par l'heure du dernier releve.
Donnees : $mesures
EOF
)

echo "$lu"

# 3. Synthese locale. Sur Raspberry Pi 5, mesurer soi-meme le facteur temps
#    reel : aucun chiffre officiel n'est publie par le projet Piper.
printf '%s' "$lu" | piper --model "$VOIX" --output_file /tmp/arbre.wav
aplay -q /tmp/arbre.wav
'''

ETAL = '''#!/usr/bin/env python3
"""Etalonnage en deux points d'une sonde capacitive d'humidite du sol.

Ce n'est pas un etalonnage metrologique : la sonde capacitive repond a la
permittivite du milieu, qui depend de la texture du sol autant que de l'eau.
Deux points donnent un INDICE 0-100 reproductible sur UN sol donne, rien de
plus. Toute comparaison entre deux sols est illegitime.

Licence : CC0.
"""
import json
import statistics
import time

import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
voie = AnalogIn(ADS1115(i2c), 0)


def point(libelle, n=60):
    input(f"\\n>>> {libelle}, puis Entree…")
    print("    acquisition 60 s", end="", flush=True)
    ech = []
    for i in range(n):
        ech.append(voie.voltage)
        time.sleep(1)
        if i % 10 == 0:
            print(".", end="", flush=True)
    moy, sd = statistics.mean(ech), statistics.pstdev(ech)
    print(f"\\n    {moy:.4f} V  (ecart-type {sd:.4f} V)")
    if sd > 0.01:
        print("    ! dispersion elevee : contact instable ou sonde mal enfouie")
    return moy, sd


sec, sd_sec = point("Sonde a l'air libre, SECHE et propre")
eau, sd_eau = point("Sonde immergee dans l'eau jusqu'au trait de garde")

if sec <= eau:
    raise SystemExit("Incoherent : la tension doit BAISSER quand l'humidite monte.")

etalon = {
    "date": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "v_sec": round(sec, 4), "v_eau": round(eau, 4),
    "sd_sec": round(sd_sec, 4), "sd_eau": round(sd_eau, 4),
    "formule": "indice = 100 * (v_sec - v) / (v_sec - v_eau)",
    "portee": "valable pour CE sol et CETTE sonde uniquement",
}
print(json.dumps(etalon, indent=2, ensure_ascii=False))
open("etalonnage-sol.json", "w").write(json.dumps(etalon, indent=2, ensure_ascii=False))
'''

ecrire("30-programmes", f'''<section class="pagebreak">
<h2 id="prog" data-toc="chapter">Les programmes</h2>

<p class="lettrine noindent">Les trois premiers listings sont extraits des
dépôts téléchargés dans <span class="phon">sources/code/</span> : ils ne sont
pas recopiés à la main dans ce document mais lus dans les archives au moment où
le PDF est fabriqué. Ils ne peuvent donc pas diverger du code réel. Les listings
suivants sont écrits pour cette annexe et placés sous CC0 : reprenez-les sans
condition.</p>

<h3 id="prog-1" data-toc="sub">Firmware biodata — l'échantillonnage et la détection</h3>

<p>Voici le cœur du MIDI Sprout et de tous ses dérivés. Le premier bloc est la
routine d'interruption : elle ne fait rien d'autre que noter la durée écoulée
depuis le front précédent. C'est tout ce que le montage de la planche 1 produit
comme donnée brute — une suite de périodes.</p>

{listing(1, "routine d'interruption et détection de changement", L1, SRC_MIT,
         "Arduino / C++")}

<p>Le second bloc mérite d'être lu attentivement, parce qu'il contient le
véritable acte d'interprétation. Il calcule l'écart-type des dix dernières
périodes et déclare un « événement » lorsque l'étendue dépasse cet écart-type
multiplié par un seuil réglable. La note produite dérive de la <i>moyenne</i>
des périodes, sa durée de l'<i>étendue</i>.</p>

<div class="callout sci">
  <div class="callout-title">Où se cache la décision</div>
  <p class="noindent">Le seuil, réglé par un potentiomètre entre 1,61 et 3,71,
  détermine à lui seul la densité de notes. Tourné à gauche, la plante « joue »
  sans arrêt ; tourné à droite, elle se tait. Aucune de ces deux positions n'est
  plus vraie que l'autre : <strong>l'expressivité perçue est un réglage
  humain</strong>, pas une propriété du végétal. C'est la ligne la plus
  importante de tout ce firmware, et c'est celle dont on ne parle jamais dans les
  démonstrations.</p>
</div>

{listing(2, "quantification sur une gamme musicale", L2, SRC_MIT, "Arduino / C++")}

<p>La quantification achève le travail : la valeur mesurée est ramenée de force
sur les degrés d'une gamme — chromatique, majeure, mineure, « indienne ». Une
plante ne joue pas juste ; on la fait jouer juste. Le résultat est agréable
précisément dans la mesure où l'information a été écrasée.</p>

{listing(3, "génération des messages MIDI (portage ESP32-S3)", L3, SRC_FEA,
         "Arduino / C++")}

<h3 id="prog-2" data-toc="sub">Le nœud environnemental sous ESPHome</h3>

<p>ESPHome décrit le nœud en YAML et fabrique le firmware. L'intérêt, pour un
atelier, est qu'il n'y a pas de code à déboguer : tout ce qui suit est de la
configuration, et la veille profonde est gérée par la plateforme.</p>

{listing(4, "configuration complète d'un nœud", ESPHOME,
         'écrit pour cette annexe · CC0. ESPHome : dépôt '
         '<span class="phon">esphome/esphome</span>, licence composite MIT (Python) '
         'et GPLv3 (C++).', "YAML")}

<h3 id="prog-3" data-toc="sub">La voie électrophysiologique</h3>

{listing(5, "acquisition ADS1115 avec réjection du secteur", ADS,
         'écrit pour cette annexe · CC0.', "Python",
         note="Ce listing met en œuvre le point développé à la planche 2 : "
              "le rejet du 50 Hz se joue d'abord dans le choix de la cadence "
              "d'intégration, pas dans un filtre. Noter aussi que chaque point "
              "publié porte un indicateur de qualité — une série sans indicateur "
              "de qualité n'est pas défendable.")}

{listing(6, "étalonnage en deux points d'une sonde de sol", ETAL,
         'écrit pour cette annexe · CC0.', "Python")}

<h3 id="prog-4" data-toc="sub">La réduction du flux de sève</h3>

{listing(7, "équation de Granier appliquée à une série", GRANIER,
         'écrit pour cette annexe · CC0. Coefficients d’après Granier (1985), '
         '<i>Ann. For. Sci.</i> 42(2), DOI 10.1051/forest:19850204.', "Python")}

<h3 id="prog-5" data-toc="sub">Sonification : le mapping doit être déclaré</h3>

{listing(8, "pont MQTT vers OSC, table de correspondance explicite", OSC,
         'écrit pour cette annexe · CC0. python-osc : dépôt '
         '<span class="phon">attwad/python-osc</span>, The Unlicense.', "Python")}

{listing(9, "synthétiseur SuperCollider recevant l'OSC", SC,
         'écrit pour cette annexe · CC0. SuperCollider : dépôt '
         '<span class="phon">supercollider/supercollider</span>, GPLv3.',
         "SuperCollider")}

<h3 id="prog-6" data-toc="sub">Parole : modèle de langue local et synthèse vocale</h3>

{listing(10, "de la base de données à la voix", PAROLE,
         'écrit pour cette annexe · CC0.', "Bash",
         note="Le prompt fait ici office de garde-fou : il interdit au modèle "
              "d'attribuer une intention à l'arbre et l'oblige à signaler les "
              "données manquantes. C'est le seul endroit de toute la chaîne où "
              "l'on peut empêcher le dispositif de mentir avec aplomb.")}

<div class="callout limite">
  <div class="callout-title">Deux chiffres à mesurer soi-même</div>
  <p class="noindent">Le projet Piper ne publie <strong>aucun</strong> facteur
  temps réel officiel pour Raspberry Pi : les valeurs qui circulent viennent de
  blogs non reproductibles et sont à écarter. Mesurez sur votre cible, avec
  trois longueurs de phrase. Côté modèle de langue, les mesures publiées par
  Jeff Geerling donnent sur Raspberry Pi 5 environ 4,6 jetons par seconde pour
  un modèle 3 milliards de paramètres en Q4_K_M, et 2,0 pour un 8 milliards —
  ce dernier étant à la limite de l'utilisable. La zone confortable se situe
  entre 0,6 et 4 milliards de paramètres.</p>
</div>
</section>''')


# =============================================================================
#  INVENTAIRE DES ARCHIVES
# =============================================================================
DEPOTS = [
    ("electricityforprogress_MIDIsprout.zip", "electricityforprogress/MIDIsprout",
     "MIT", "Firmware, schémas Eagle, gerbers et BOM du MIDI Sprout d'origine. "
     "Figé depuis 2021."),
    ("electricityforprogress_BiodataSonificationBreadboardKit.zip",
     "electricityforprogress/BiodataSonificationBreadboardKit",
     "aucune licence déclarée", "Version pédagogique sur plaque d'essai : c'est "
     "d'elle que provient le netlist de la planche 1 et la nomenclature. "
     "<b>Statut juridique à clarifier avant tout usage public.</b>"),
    ("electricityforprogress_BiodataFeather.zip",
     "electricityforprogress/BiodataFeather", "MIT",
     "Portage ESP32 / ESP32-S3 avec MIDI BLE et RTP-MIDI. La version à reprendre "
     "aujourd'hui."),
    ("electricityforprogress_Organon.zip", "electricityforprogress/Organon",
     "non spécifiée", "Déclinaison Eurorack : sorties CV et gate."),
    ("leetronics_midi-biodata.zip", "leetronics/midi-biodata",
     "MIT (matériel et firmware) · CC0 (boîtier)",
     "Réimplémentation industrialisée sous KiCad, USB-C et sortie CV."),
    ("Playtronica_biotron-firmware.zip", "Playtronica/biotron-firmware", "GPL-3.0",
     "Firmware RP2040 du Biotron commercial. Un rare cas de produit vendu dont le "
     "firmware est réellement ouvert."),
    ("Lessnullvoid_Pulsum-Plantae.zip", "Lessnullvoid/Pulsum-Plantae", "à vérifier",
     "Installation de Leslie García : amplificateur galvanique à LM324, cartes "
     "Fritzing, gerbers et application openFrameworks."),
    ("OPEnSLab-OSU_SapFlowMeterOld.zip", "OPEnSLab-OSU/SapFlowMeterOld", "à vérifier",
     "Capteur de flux de sève par dissipation thermique, open source, OPEnS Lab, "
     "Oregon State University."),
    ("james-trayford_strauss.zip", "james-trayford/strauss",
     "Apache-2.0 (dépôt) / MIT (PyPI) — <b>divergence non résolue</b>",
     "Bibliothèque de sonification scientifique la plus complète et la seule "
     "réellement maintenue. Publiée dans JOSS, DOI 10.21105/joss.07875."),
    ("spacetelescope_astronify.zip", "spacetelescope/astronify", "BSD 3-Clause",
     "Sonification de séries temporelles, Space Telescope Science Institute. "
     "Maintenance lente."),
    ("lockepatton_sonipy.zip", "lockepatton/sonipy", "MIT",
     "Nuages de points vers blips perceptuellement uniformes. <b>Aucune release "
     "depuis 2020 : à considérer comme abandonné.</b>"),
    ("klaemsch_plant-sonification.zip", "klaemsch/plant-sonification", "à vérifier",
     "Projet de sonification végétale (archive présente dans le dossier)."),
    ("RominaSR_SonicPlants.zip", "RominaSR/SonicPlants", "à vérifier",
     "Projet de sonification végétale (archive présente dans le dossier)."),
    ("ettorhake_BioDataToMidiToDigitakt.zip", "ettorhake/BioDataToMidiToDigitakt",
     "à vérifier", "Adaptation du biodata vers un séquenceur Elektron Digitakt."),
    ("electricityforprogress_BiodataWifi.zip", "electricityforprogress/BiodataWifi",
     "à vérifier", "Variante ESP8266 + Circuit Playground : le seul portage Wi-Fi "
     "de la première génération."),
    ("electricityforprogress_ListeningStation.zip",
     "electricityforprogress/ListeningStation", "à vérifier",
     "Station d'écoute audio sur Adafruit Feather."),
    ("ChubbyLobsters_Electrophysiology-and-Biorobotics.zip",
     "ChubbyLobsters/Electrophysiology-and-Biorobotics", "à vérifier",
     "Électrophysiologie et biorobotique."),
]

lignes_dep = [[f'<span class="phon">{d[1]}</span>', d[2], d[3]] for d in DEPOTS]

# --- Chaîne logicielle : tableau engendré depuis le manifeste réel ------------
MAN = manifeste_logiciel()
CAT_LBL = {
    "libs-mcu": "Bibliothèques microcontrôleur",
    "firmware": "Firmware",
    "ingest": "Ingestion et stockage",
    "viz": "Visualisation",
    "sonification": "Sonification et audio",
    "tts": "Synthèse vocale",
    "llm": "Modèles de langue locaux",
}
ORDRE_CAT = ["libs-mcu", "firmware", "ingest", "viz", "sonification", "tts", "llm"]


def tableaux_logiciels():
    if not MAN:
        return ('<p class="small">Manifeste absent : exécuter '
                '<span class="phon">python3 tools/fetch-software.py</span>.</p>')
    out = []
    for cat in ORDRE_CAT:
        rows = [m for m in MAN if m["categorie"] == cat]
        if not rows:
            continue
        lignes = []
        for m in rows:
            if m["statut"] != "présent":
                lignes.append([f'<span class="phon">{m["depot"]}</span>',
                               "<b>ABSENT au téléchargement</b>", "—", m["role"]])
                continue
            lic = m["licence"]
            if lic and ("AGPL" in lic or "TSL" in lic):
                lic = f"<b>{lic}</b>"
            lignes.append([f'<span class="phon">{m["depot"]}</span>', lic or "—",
                           f'{m["taille_Mo"]:.0f}' if m["taille_Mo"] else "—",
                           m["role"]])
        tot = sum(m["taille_Mo"] or 0 for m in rows)
        out.append(f'<h4>{CAT_LBL[cat]}</h4>' + tableau(
            ["Dépôt", "Licence lue dans l\u2019archive", "Mo", "Rôle"], lignes,
            classes="tight-xs",
            legende=f"{len(rows)} dépôts, {tot:.0f} Mo."))
    return "\n".join(out)


TOTAL_MO = sum(m.get("taille_Mo") or 0 for m in MAN)
N_PRESENTS = len([m for m in MAN if m["statut"] == "présent"])
N_ABSENTS = len([m for m in MAN if m["statut"] != "présent"])

ecrire("40-inventaire", f'''<section class="pagebreak">
<h2 id="inv" data-toc="chapter">Ce qui a été téléchargé, et sous quelle licence</h2>

<p class="lettrine noindent">Toutes les archives listées ci-dessous se trouvent
dans <span class="phon">sources/code/</span>. Elles ont été récupérées depuis
les dépôts publics correspondants ; les licences indiquées « à vérifier » n'ont
pas pu être confirmées par lecture d'un fichier LICENSE et doivent l'être avant
tout usage autre que privé.</p>

{tableau(["Dépôt", "Licence", "Contenu"], lignes_dep, classes="tight",
         legende="Archives présentes dans sources/code/. L'absence de fichier de "
                 "licence ne vaut pas permission : en droit d'auteur, un dépôt sans "
                 "licence est « tous droits réservés » par défaut, même publié "
                 "publiquement.")}

<h3 id="inv-mcu" data-toc="sub">Les firmwares de microcontrôleur, cible par cible</h3>

<p>La question se pose en atelier : que peut-on téléverser, et sur quoi ?
Voici l\u2019état exact de ce qui est présent dans
<span class="phon">sources/code/</span>.</p>

{tableau(["Firmware", "Cible", "Sorties", "Licence", "État"],
 [["<span class='phon'>MIDI_Psychogalv_328p_v021</span>", "<b>ATmega328P</b>",
   "MIDI DIN-5 · CV par MLI", "MIT", "l\u2019original, figé 2021"],
  ["<span class='phon'>BiodataSonification_026_kit</span>", "<b>ATmega328P</b>",
   "MIDI · CV · 6 LED · menu EEPROM", "<b>aucune</b>",
   "version d\u2019atelier, la mieux commentée"],
  ["<span class='phon'>MIDI_Psychogalv_328p_13-37.org</span>", "<b>ATmega328P</b>",
   "MIDI · CV sur jack TRS", "MIT", "portage leetronics, USB-C"],
  ["<span class='phon'>BiodataSonification_Digitakt_v027</span>", "<b>ATmega328P</b>",
   "MIDI vers séquenceur Elektron", "à vérifier", "adaptation tierce"],
  ["<span class='phon'>BiodataModular_002</span>", "ATmega32u4 (Pro Micro)",
   "3 paires CV/Gate · MIDI · MCP4728", "non spécifiée", "déclinaison Eurorack"],
  ["<span class='phon'>Biodata_Feather_ESP32Wifi_04</span>", "<b>ESP32</b>",
   "RTP-MIDI sur Wi-Fi (AppleMIDI)", "MIT", "première version réseau"],
  ["<span class='phon'>Biodata_Feather_ESP32_05</span>", "<b>ESP32</b>",
   "BLE MIDI · MIDI série", "MIT", "version BLE"],
  ["<span class='phon'>Biodata_Feather_ESP32_07</span>", "<b>ESP32-S3</b>",
   "BLE MIDI · RTP-MIDI · MIDI série", "MIT",
   "<b>la plus récente — à reprendre</b>"],
  ["<span class='phon'>BiodataWifi_006</span>", "ESP8266 + CircuitPlayground",
   "Wi-Fi · sortie sonore", "à vérifier", "variante historique"],
  ["<span class='phon'>pulsumSensorRead</span>", "Arduino (LM324 externe)",
   "série vers Pure Data / openFrameworks", "à vérifier",
   "Pulsu(m) Plantae, Leslie García"],
  ["<span class='phon'>main.c</span> (PLSDK)", "<b>RP2040</b> (Pico SDK)",
   "USB-MIDI · capteur de lumière", "GPL-3.0", "Biotron, Playtronica"],
  ["<span class='phon'>SapFlowMeter</span>", "SAMD21 (Feather M0)",
   "carte SD · dissipation thermique", "à vérifier",
   "OPEnS Lab, Oregon State University"],
 ], classes="tight",
 legende="Douze firmwares réellement présents. Les deux familles qui comptent pour "
         "un atelier sont l\u2019ATmega328P — le plus simple à comprendre et à déboguer, "
         "sans pile réseau — et l\u2019ESP32-S3, qui apporte le MIDI sans fil et la veille "
         "profonde. Le nœud environnemental des planches 3 et 4 ne demande, lui, "
         "aucun firmware écrit à la main : ESPHome le fabrique depuis le YAML du "
         "listing 4.")}

<h3 id="inv-stack" data-toc="sub">La chaîne logicielle complète</h3>

<p>Les {N_PRESENTS} dépôts ci-dessous ont été téléchargés en archives source —
sans historique git — par <span class="phon">tools/fetch-software.py</span>,
qui relève la licence <strong>en lisant le fichier de licence réellement
présent dans chaque archive</strong> plutôt qu\u2019en se fiant à une page web.
Total : {TOTAL_MO:.0f} Mo dans <span class="phon">sources/software/</span>.
{"Aucun dépôt manquant." if N_ABSENTS == 0 else
 f"<b>{N_ABSENTS} dépôt(s) n\u2019ont pas pu être récupérés</b> et sont signalés comme tels."}</p>

{tableaux_logiciels()}

<div class="callout limite">
  <div class="callout-title">Trois pièges de licence, par ordre de gravité</div>
  <ol>
    <li><strong>XTTS v2</strong> est publié sous <i>Coqui Public Model
    License</i>, qui n'autorise que l'usage non commercial et couvre
    explicitement <strong>les fichiers audio produits</strong>. Une billetterie
    ou une subvention fléchée suffit à sortir du périmètre. À écarter pour toute
    installation publique financée.</li>
    <li><strong>Grafana</strong> est passé d'Apache-2.0 à AGPLv3 en avril 2021 :
    si vous exposez un tableau de bord modifié sur le réseau, l'AGPL vous oblige
    à en publier les sources.</li>
    <li><strong>Les dépôts biodata sans licence</strong> — notamment le kit sur
    plaque d'essai, pourtant le plus étoilé — ne sont pas réutilisables tels
    quels dans un atelier payant ou une publication.</li>
    <li><strong>Arduino-AppleMIDI-Library est sous CC BY-SA 4.0</strong>, une
    licence à partage à l'identique conçue pour des œuvres, pas pour du code, et
    dont la clause de réciprocité est mal définie sur un logiciel. Or c'est une
    dépendance directe du firmware BiodataFeather en mode RTP-MIDI. À signaler
    si le firmware est redistribué.</li>
  </ol>
</div>

<h3 id="inv-nonverif" data-toc="sub">Ce qui n'a pas pu être vérifié</h3>
<ul>
  <li>Le facteur temps réel de Piper sur Raspberry Pi : <strong>aucune source
  primaire n'existe</strong>. Toutes les valeurs qui circulent proviennent de
  blogs non reproductibles.</li>
  <li>La divergence de licence de <span class="phon">strauss</span> entre le
  dépôt (Apache-2.0) et PyPI (MIT) n'est pas résolue.</li>
  <li>Les prix des instruments de flux de sève d'ICT International et de Dynamax
  ne sont pas publics : vente sur devis uniquement.</li>
  <li>Les schémas des planches 2 à 5 sont des schémas d'application composés
  d'après les datasheets ; ils n'ont pas été prototypés dans le cadre de cette
  annexe.</li>
  <li>Les licences marquées « à vérifier » dans le tableau des archives.</li>
  <li>Quatre licences de bibliothèques n'étaient pas lisibles par automate et
  ont été relevées à la main : TSL2591 (BSD, en-tête de source), OneWire (MIT,
  en-tête de source), AppleMIDI (CC BY-SA 4.0, LICENSE.md), AD8232 SparkFun
  (matériel CC BY-SA 3.0, code Beerware). Le détecteur automatique s'est par
  ailleurs trompé deux fois avant correction — le préambule de la GPL v2 cite
  la LGPL, et le texte de la MPL 2.0 cite la GPL : toute lecture de licence par
  mot-clé doit se limiter à l'en-tête.</li>
  <li><span class="phon">electricityforprogress/Biodata_Manuel</span> :
  <strong>n'a pas pu être téléchargé</strong> (ni branche <i>main</i> ni
  <i>master</i>).</li>
</ul>
</section>''')

ecrire("99-colophon", '''<section class="frontpage pagebreak">
<h2 id="colophon" data-toc="chapter">Colophon</h2>
<p class="noindent">Annexe technique de la série <i>L'Arbre qui Parle</i>,
Ateliers BN, 17 septembre 2026.</p>
<p>Les cinq planches ont été produites par le générateur
<span class="phon">pdf-src/assets/svg/gen_sch.py</span>, de façon déterministe.
Les listings 1 à 3 sont extraits des archives de
<span class="phon">sources/code/</span> à la construction du document, par
<span class="phon">tools/gen-appendix-parts.py</span> : ils sont donc
nécessairement conformes au code téléchargé. Les listings 4 à 10 sont placés
sous CC0.</p>
<p>Composition : WeasyPrint, charte <span class="phon">pdf-src/book.css</span>.
Reconstruction complète du document :</p>
<div class="code"><pre>python3 pdf-src/assets/svg/gen_sch.py
python3 tools/gen-appendix-parts.py
python3 tools/build-annexe.py</pre></div>
<p class="small">Les marques et références de composants citées appartiennent à
leurs détenteurs respectifs et ne sont mentionnées qu'à titre d'identification
technique.</p>
</section>''')

print("Fragments de l'annexe générés.")
