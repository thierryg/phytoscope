#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_index.py
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
Génère l'annexe « Index détaillé » d'un volume.

L'index renvoie vers des ancres réelles ; les numéros de page sont résolus à
l'impression par `target-counter`. Le script VÉRIFIE que chaque ancre existe
dans les fragments du volume et refuse d'écrire un index qui contiendrait des
renvois morts — un index faux est pire que pas d'index.

Usage : python3 tools/gen_index.py v1 [v2 v3]
"""
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "pdf-src", "the-music-of-plants")
DIRS = {"v1": "v1-dublin", "v2": "v2-biocommunication", "v3": "v3-atelier"}

# Entrées : terme -> [ancres]  |  ou terme -> {"": [ancres], "sous-entrée": [ancres]}
INDEX = {
"v1": {
 "Ablation (test d')": ["c15-tests", "c7-couche-ia"],
 "Agency for Nature": ["c2-dossier"],
 "Amplificateur d'instrumentation": ["c10-signal-donnee", "c22-limites"],
 "Animisme": ["c16-personne"],
 "Anémomètre": ["c5-capteurs", "c11-catalogue"],
 "Artefacts": {"": ["c11-artefacts"],
               "catalogue des sept": ["c11-catalogue"],
               "dérive d'électrode": ["c11-catalogue", "c22-limites"],
               "couplage électromagnétique": ["c11-catalogue", "c22-limites"],
               "humidité de surface": ["c11-catalogue"],
               "mouvement": ["c11-catalogue"]},
 "Attribution": ["c1-ce-qu-on-voit", "c12-budget", "c13-eliza"],
 "Audification": ["c14-defendable"],
 "Austin (SXSW)": ["c2-trois-installations"],
 "Backster (effet)": ["c25-replication"],
 "Biais de citation": ["c25-www"],
 "Bioacoustique": ["c9-acoustique"],
 "Biofeedback": ["c14-ce-qui-change"],
 "Bose, Jagadish Chandra": ["c4-continuite", "bib-electro"],
 "Bruxelles (Talking Tree, 2010)": ["c4-precedent", "c4-dispositif-2010", "bib-2010"],
 "Burdon-Sanderson, John": ["c4-continuite", "bib-electro"],
 "Cambium": ["c23-deontologie"],
 "CASA (paradigme)": ["c1-ce-qu-on-voit", "c13-eliza"],
 "Cavitation": ["c9-acoustique"],
 "Chamanisme": ["c18-chamanique", "c18-validation"],
 "Communication facilitée": ["c13-facilitee", "c13-parallele"],
 "Contraintes (bloc d'invite)": ["c23-invite", "c26-compter"],
 "Convertisseur analogique-numérique": ["c10-signal-donnee"],
 "Darwin, Charles": ["c4-continuite", "bib-electro"],
 "Dendromètre": ["c5-capteurs"],
 "Descripteurs": ["c23-structure", "c10-signal-donnee"],
 "Droga5": ["c2-dossier", "c8-non-publie"],
 "Druidisme": ["c16-europe"],
 "Dublin (Trinity College)": ["c2-trois-installations", "c8-scientificite"],
 "Échelle épistémique": ["note-lecteur", "introduction"],
 "Électrode": {"": ["c10-signal-donnee"],
               "impolarisable": ["c5-bioelectrique", "c22-limites"],
               "pose sur un tronc": ["c23-deontologie"]},
 "Électrophysiologie végétale": ["c9-trois-signaux", "c5-bioelectrique"],
 "ELIZA (effet)": ["c13-eliza"],
 "Émerveillement": ["c26-compter"],
 "Épreuve du vide (test)": ["c15-tests"],
 "Étalonnage": ["c21-materiel", "c26-compter", "c24-protocole"],
 "Ferran, Alexandre": ["c14-clavier", "c14-dispositif", "bib-mapping"],
 "Flux de sève": ["c9-rythmes", "c5-capteurs"],
 "Géobiologie": ["c19-energetique", "c19-mesurable", "c19-non-mesurable"],
 "Glutamate (signalisation)": ["c9-glutamate"],
 "Graves, Robert": ["c17-reconstruit"],
 "Greally, Evan": ["note-lecteur", "c2-greally", "c1-honnetete"],
 "Hallucination (modèle)": ["c7-couche-ia", "c12-budget"],
 "Happiness Brussels": ["c4-precedent"],
 "Humidité du sol": ["c5-capteurs", "c5-plausible"],
 "Impédance": ["c10-signal-donnee", "c22-limites"],
 "Index épistémique, voir Échelle épistémique": [],
 "Invite système": ["c7-invite", "c23-invite", "c26-compter"],
 "Khait et al. (2023)": ["c9-acoustique"],
 "Karst, Jones & Hoeksema (2023)": ["c25-www"],
 "Klein et al. (2016)": ["c25-www"],
 "Londres (Morden Hall Park)": ["c2-trois-installations", "c3-quatre-erreurs"],
 "LoRaWAN": ["c21-niveau2"],
 "Mac Mini": ["c6-architecture"],
 "Mapping": {"": ["c14-ce-qui-change"],
             "paramétrique": ["c14-dispositif"],
             "sémantique": ["c14-clavier", "c14-ce-qui-change"],
             "isomorphe": ["c14-defendable"]},
 "Markel, Kasey": ["c25-replication"],
 "Menthe (prototype « Eight »)": ["c2-greally"],
 "MIDI": ["c14-dispositif"],
 "Modèle de langage": ["c7-couche-ia", "c12-budget", "c6-architecture"],
 "Mycorhiziens (réseaux)": ["c25-www"],
 "Neurobiologie végétale (débat)": ["c25-neurobiologie"],
 "Ogham": ["c17-ogham", "c17-atteste", "c17-reconstruit"],
 "Pré-enregistrement": ["c15-tests", "c24-protocole"],
 "Potentiel d'action": ["c9-trois-signaux"],
 "Potentiel d'écoulement": ["c11-catalogue", "c5-bioelectrique"],
 "Potentiel de variation": ["c9-trois-signaux"],
 "Propagation (chaîne de)": ["c3-rumeur", "c3-quatre-erreurs", "c3-miroir"],
 "Protocole en sept séances": ["c24-protocole"],
 "Purpose Disruptors": ["c2-dossier"],
 "Reconnaissance vocale": ["c7-couche-ia", "c6-boucle"],
 "Reproductibilité": ["c20-refaire", "c20-etat"],
 "Repliement de spectre": ["c10-signal-donnee", "c22-limites"],
 "Rythmes circadiens": ["c9-rythmes"],
 "RTÉ": ["c2-trois-installations", "c3-rumeur", "bib-projet"],
 "Sélection rétrospective": ["c15-tests"],
 "Signalétique (panneau)": ["c21-niveau3", "c26-compter"],
 "Simard, Suzanne": ["c25-www"],
 "Sonification": ["c14-defendable", "c4-lecon"],
 "Synthèse vocale": ["c7-voix", "c7-couche-ia"],
 "Taiz, Lincoln": ["c25-neurobiologie"],
 "Tan et al. (2024)": ["c7-couche-ia", "c15-tests"],
 "Tests de contrôle": ["c15-tests", "c26-compter"],
 "Toyota & Gilroy (2018)": ["c9-glutamate"],
 "Tran et al. (2019)": ["c11-regle"],
 "Trois lectures (instrumentale, physiologique, sensible)": ["c19-trois-lectures"],
 "Ultrasons": ["c9-acoustique"],
 "Voies parallèles (règle des)": ["c11-regle", "c26-compter"],
 "Voix (choix du timbre)": ["c7-voix"],
 "Wegner, Daniel": ["c13-facilitee"],
 "Weizenbaum, Joseph": ["c13-eliza"],
 "Wood Wide Web": ["c25-www"],
 "Xylème": ["c9-acoustique", "c9-physiologie"],
},
"v2": {
 "Ablation (test d')": ["c15-llm", "c19-replication"],
 "Acoustique (canal)": ["c6-cavitation", "c7-khait", "c8-perception"],
 "Alpi et al. (2007)": ["c18-debat"],
 "Amorçage du voisinage": ["c9-cov"],
 "Apprentissage automatique": ["c14-classification", "c14-resultats"],
 "Arbre-mère (hypothèse)": ["c10-critique"],
 "Audification": ["c11-familles"],
 "Backster (effet)": ["c2-backster"],
 "Biais de citation": ["c10-biais"],
 "Bose, Jagadish Chandra": ["c2-fondateurs"],
 "Bruit blanc (test du)": ["c12-test"],
 "Burdon-Sanderson, John": ["c2-fondateurs"],
 "Canaux (inventaire des)": ["c1-inventaire", "c1-criteres", "introduction"],
 "Cavitation": ["c6-cavitation", "c6-valeur"],
 "Cellule compagne": ["c4-raffinement"],
 "Classification automatique": ["c14-classification"],
 "Complexité et conscience": ["c17-trois"],
 "Composés organiques volatils": ["c9-cov", "c9-trois-effets"],
 "Conscience végétale (débat)": ["c18-debat", "c18-neurotransmetteurs"],
 "Contrôle négatif": ["c7-protocole", "c12-controles"],
 "Damanhur": ["c12-controles"],
 "Darwin, Charles": ["c2-fondateurs"],
 "Dionée": ["c2-fondateurs", "c3-mecanisme"],
 "Écoute indiscrète": ["c9-trois-effets", "c17-quatre"],
 "Échantillonnage (fréquence d')": ["c1-couts"],
 "Échelles de temps": ["c1-couts"],
 "Électrode": ["c5-arbres", "c12-domine"],
 "Électrome": ["c5-electrome", "c5-portee", "c14-resultats"],
 "Émission et communication": ["c17-quatre", "c7-critiques"],
 "Embolie": ["c6-cavitation"],
 "Glutamate (voie du)": ["c4-glutamate", "c4-raffinement"],
 "GLR (récepteurs)": ["c4-glutamate", "c4-raffinement"],
 "Granier (méthode de)": ["c20-atelier"],
 "Hermann, Thomas": ["c11-definition"],
 "Horowitz et al. (1975)": ["c2-backster"],
 "Hydraulique (canal)": ["c20-atelier", "c1-inventaire"],
 "Impédance": ["c12-grandeur", "c12-domine"],
 "Isomorphe (mapping)": ["c13-isomorphe"],
 "Karst, Jones & Hoeksema (2023)": ["c10-critique", "c10-biais"],
 "Khait et al. (2023)": ["c7-khait", "c7-protocole", "c7-resultats"],
 "Kiers et al. (2011)": ["c10-etabli"],
 "Klein et al. (2016)": ["c10-etabli"],
 "Mapping paramétrique": ["c11-familles"],
 "Markel, Kasey": ["c19-cas"],
 "Milburn & Johnson (1966)": ["c6-histoire"],
 "Modèle de langage": ["c15-llm", "c15-technique"],
 "Mycorhiziens (réseaux)": ["c10-mycorhizes", "c10-etabli", "c10-critique"],
 "Nardini et al. (2024)": ["c7-critiques"],
 "Neurobiologie végétale": ["c18-debat"],
 "Neurotransmetteurs": ["c18-neurotransmetteurs"],
 "Nolf et al. (2015)": ["c6-valeur"],
 "Oenothera": ["c8-perception"],
 "Phloème": ["c3-taxonomie", "c4-raffinement"],
 "Potentiel d'action": ["c3-trois-signaux", "c3-mecanisme", "c3-chiffres"],
 "Potentiel d'écoulement": ["c5-terrain", "c5-arbres"],
 "Potentiel de variation": ["c3-trois-signaux", "c3-chiffres"],
 "Potentiel systémique": ["c3-taxonomie"],
 "Prosodie (mapping vers la)": ["c16-prosodie", "c16-proposition"],
 "Protéines (sonification des)": ["c13-isomorphe"],
 "Réplication": ["c19-cas", "c19-lecons"],
 "Reproductibilité": ["c19-replication", "c19-grille"],
 "Seuil de détection": ["c12-domine"],
 "Simard, Suzanne": ["c10-etabli", "c10-reponse"],
 "Son et al. (2024)": ["c7-critiques"],
 "Sonification": ["c11-familles", "c11-definition", "c13-honnete"],
 "Souza, Gustavo": ["c5-electrome"],
 "Style prosodique (jetons de)": ["c16-gst"],
 "Taiz, Lincoln": ["c18-debat"],
 "Tan et al. (2024)": ["c15-technique", "c19-replication"],
 "Tang et al. (2023)": ["c15-decoder"],
 "Temple, Mark": ["c13-adn"],
 "Toyota & Gilroy (2018)": ["c4-glutamate"],
 "Tran et al. (2019)": ["c5-terrain", "c14-resultats"],
 "Ultrasons": ["c6-protocoles", "c7-resultats"],
 "Veits et al. (2019)": ["c8-perception"],
 "Vibration de substrat": ["c7-critiques"],
 "Volatils, voir Composés organiques volatils": [],
 "Wood Wide Web": ["c10-mycorhizes", "c10-critique"],
 "Xylème": ["c6-cavitation"],
},
"v3": {
 "Ablation (test d')": ["c15-controles"],
 "ADS1115": ["c6-ads", "p2-imp"],
 "Abri météorologique": ["c2-regles", "c3-ambiance"],
 "Amplificateur d'instrumentation": ["c6-courant", "c6-tableau", "p2"],
 "Anti-repliement (filtre)": ["c6-chaine"],
 "Arboricole (règle)": ["c1-deontologie", "c1-interdits"],
 "Autorisations": ["c1-autorisations"],
 "Batterie": ["c9-budget", "c14-miseenservice"],
 "Bioélectrique (chaîne)": ["c6-courant", "c7-electrodes", "c11-bio"],
 "Cahier de bord": ["c2-cahier", "c16-publier"],
 "Cambium": ["c1-deontologie"],
 "Capacitif (capteur)": ["c4-capacitif"],
 "Charge sous 0 °C": ["c9-budget", "c14-miseenservice"],
 "Condensation": ["c14-miseenservice"],
 "Contraintes (invite)": ["c13-invite"],
 "Contrôle (tests de)": ["c15-controles", "c16-publier"],
 "Corps de l'opérateur": ["c8-corps"],
 "Couplage capacitif": ["c8-corps"],
 "Courant de polarisation": ["c6-courant", "c6-tableau"],
 "Dendromètre": ["c5-dendro"],
 "Dérive de demi-pile": ["c7-metal"],
 "Donnée brute (règle de la)": ["c10-analyse", "c16-publier"],
 "Échantillonnage synchrone": ["c8-50hz"],
 "Électrode": {"": ["c7-electrodes"],
               "impolarisable": ["c7-metal"],
               "de référence": ["c7-reference"],
               "pose sur tronc": ["c1-interdits"]},
 "Épreuve du vide": ["c15-controles"],
 "ESPHome": ["c10-firmware", "prog-2"],
 "ESP32": ["c9-plateformes", "p3"],
 "Étalonnage": ["c11-etalonnage", "c11-sol", "c11-thermique"],
 "Étanchéité": ["c14-miseenservice"],
 "Flux de sève": ["c5-sapflow", "c5-biais", "p5"],
 "Grafana": ["c10-collecte"],
 "Granier (coefficient de)": ["c5-sapflow", "c5-biais", "p5-metro"],
 "Gravimétrique (étalonnage)": ["c11-sol"],
 "Humidité du sol": ["c4-sol", "c4-capacitif", "c11-sol"],
 "Hygroscopie du rhytidome": ["c8-humidite"],
 "Impédance de source": ["c6-courant", "c16-grille"],
 "InfluxDB": ["c10-collecte"],
 "Invite (système)": ["c13-invite"],
 "Licences": ["c10-collecte", "c13-tts", "c16-licences", "inv"],
 "Lux et PPFD": ["c3-lumiere"],
 "LoRaWAN": ["c9-lora", "p4-liaison"],
 "Mapping (déclaration du)": ["c12-declarer", "prog-5"],
 "Mise en service": ["c14-miseenservice"],
 "Modèle de langage local": ["c13-llm", "prog-6"],
 "MQTT": ["c10-collecte"],
 "Nomenclature": ["bomg", "p1-bom", "p2-bom", "p3-bom", "p4-bom", "p5-bom"],
 "Planches (statut des)": ["c16-grille", "note-lecteur"],
 "Pré-enregistrement": ["c15-controles"],
 "Programmes": ["prog", "prog-1", "prog-5", "prog-6"],
 "Publier (ce qu'il faut)": ["c16-publier"],
 "Quantification sur gamme": ["c12-sonifier"],
 "Référence (voie de)": ["c11-reference"],
 "Rongeurs": ["c14-miseenservice"],
 "Résistif (capteur, à proscrire)": ["c4-resistif"],
 "Secteur (50 Hz)": ["c8-50hz", "p2-50hz"],
 "Signalétique": ["c1-autorisations"],
 "Solaire (alimentation)": ["c9-budget", "p4"],
 "Sonification": ["c12-sonifier", "c12-declarer", "c10-restitution"],
 "strauss": ["c10-restitution", "bib-sonif"],
 "Suiveur électromètre": ["c6-courant", "c6-ads"],
 "Synthèse vocale": ["c13-tts", "prog-6"],
 "Température (capteurs de)": ["c3-air", "c11-thermique"],
 "Thermique (gradient du tronc)": ["c5-biais", "p5-metro"],
 "Veille profonde": ["c9-plateformes", "c9-budget"],
 "Vent (artefact du)": ["c8-vent"],
 "Voies parallèles (règle des)": ["c6-chaine"],
 "Wheatstone (pont de)": ["p1-fonc"],
},
}


def fold(s):
    """Replie les accents : « Épreuve » doit se classer sous E, pas sous É."""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def existing_ids(vol):
    d = os.path.join(PARTS, DIRS[vol])
    ids = set()
    for fn in os.listdir(d):
        if fn.endswith(".html"):
            with open(os.path.join(d, fn), encoding="utf-8") as f:
                ids |= set(re.findall(r'\bid="([^"]+)"', f.read()))
    return ids


def links(anchors, ids, term, dead):
    out = []
    for a in anchors:
        if a not in ids:
            dead.append(f"{term} → #{a}")
            continue
        out.append(f'<a class="pg" href="#{a}"></a>')
    return ", ".join(out)


def render(vol):
    ids = existing_ids(vol)
    dead = []
    rows, cur = [], ""
    entries = INDEX.get(vol, {})
    for term in sorted(entries, key=lambda s: fold(s).lower()
                       .replace("«", "").strip()):
        val = entries[term]
        letter = fold(term)[0].upper()
        if letter != cur:
            cur = letter
            rows.append(f'  <div class="idx-alpha">{letter}</div>')
        if isinstance(val, list):
            if not val:                      # simple renvoi « voir … »
                rows.append(f'  <div class="idx-e"><span class="idx-t">{term}</span></div>')
                continue
            lk = links(val, ids, term, dead)
            rows.append(f'  <div class="idx-e"><span class="idx-t">{term}</span>&nbsp;&nbsp;{lk}</div>')
        else:
            main = links(val.get("", []), ids, term, dead)
            head = f'  <div class="idx-e"><span class="idx-t">{term}</span>'
            head += f'&nbsp;&nbsp;{main}' if main else ""
            for sub, anch in val.items():
                if sub == "":
                    continue
                head += (f'<span class="idx-sub">{sub}&nbsp;&nbsp;'
                         f'{links(anch, ids, term + " / " + sub, dead)}</span>')
            rows.append(head + "</div>")

    if dead:
        print(f"  ! {len(dead)} renvoi(s) mort(s) — index NON écrit :")
        for d in dead[:20]:
            print(f"      {d}")
        return None, 0

    n = sum(1 for t, v in entries.items() if v)
    html = f'''<section class="chapter">
  <h2 id="index" data-toc="chapter">Index détaillé</h2>
  <p class="chapo">{n} entrées, renvoyant aux pages où la notion est traitée — et non à chaque occurrence du mot. Les numéros de page sont calculés à l'impression.</p>

  <div class="index">
{chr(10).join(rows)}
  </div>
</section>
'''
    return html, n


def main():
    vols = [a for a in sys.argv[1:] if a in DIRS] or [v for v in DIRS if v in INDEX]
    print("• Index…")
    for vol in vols:
        html, n = render(vol)
        if html is None:
            continue
        out = os.path.join(PARTS, DIRS[vol], "A3-index.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  · {vol} : {n} entrées → {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
