#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_code_annex.py
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

"""
Génère l'annexe « Codes source » du livre à partir des fichiers réels,
afin qu'aucune transcription manuelle ne puisse introduire d'erreur.

Usage : python3 tools/gen_code_annex.py
Sortie : pdf-src/parts/A0b-codes.html
"""
import os, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "sources")
OUT = os.path.join(ROOT, "pdf-src", "la-musique-des-plantes", "A0b-codes.html")

LARGEUR_MAX = 96   # au-delà, le listing déborde de la colonne


def lire(rel):
    """Lit un listing, qu'il soit tiers ou de notre main.

    Les programmes tiers vivent sous ``sources/`` ; les nôtres non — depuis le
    rangement du 2026-09-18, DamanhurBridge est sous ``reverse/``. On essaie
    donc les deux racines plutôt que de disperser les chemins dans l'appelant.
    """
    for base in (SRC, ROOT):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return f.read().rstrip("\n")
    raise FileNotFoundError(rel)


def bloc(titre, chemin, contenu, ident):
    lignes = contenu.split("\n")
    trop_long = [i + 1 for i, l in enumerate(lignes) if len(l) > LARGEUR_MAX]
    if trop_long:
        print(f"  ! {chemin} : {len(trop_long)} ligne(s) > {LARGEUR_MAX} car. "
              f"(n° {trop_long[:6]}…)")
    return (f'<h3 id="{ident}" data-toc="sub">{titre}</h3>\n'
            f'<p class="small"><code>{html.escape(chemin)}</code> — '
            f'{len(lignes)} lignes</p>\n'
            f'<div class="code listing"><pre>{html.escape(contenu)}</pre></div>\n')


SECTIONS = [
    # (titre affiché, chemin relatif à sources/, identifiant d'ancre)
    ("Fichier principal", "schemas/midisprout/MIDI_Psychogalv_328p_v021/"
     "MIDI_Psychogalv_328p_v021.ino", "code-ms-main"),
    ("Analyse d'échantillons", "schemas/midisprout/MIDI_Psychogalv_328p_v021/"
     "SampleAnalysis.ino", "code-ms-sample"),
    ("Quantification sur gamme", "schemas/midisprout/MIDI_Psychogalv_328p_v021/"
     "Scale.ino", "code-ms-scale"),
    ("Couche MIDI et polyphonie", "schemas/midisprout/MIDI_Psychogalv_328p_v021/"
     "MIDIserial.ino", "code-ms-midi"),
    ("Périphériques et contrôle de pile", "schemas/midisprout/"
     "MIDI_Psychogalv_328p_v021/Peripherals.ino", "code-ms-periph"),
]


def main():
    print("• Génération de l'annexe des codes source…")
    parts = []

    parts.append("""<section class="chapter first">
  <h2 id="annexe-codes" data-toc="chapter">Annexe A — Codes source complets</h2>
  <p class="chapo">Les programmes reproduits ici sont livrés tels quels, générés
  automatiquement à partir des fichiers de référence afin d'exclure toute erreur
  de transcription. Ils sont tous librement réutilisables.</p>

  <table>
    <thead><tr><th>Programme</th><th>Cible</th><th>Origine</th><th>Licence</th></tr></thead>
    <tbody>
      <tr><td><strong>MIDI Sprout v021</strong></td><td>ATmega328P, 16 MHz</td>
        <td>Electricity for Progress / Data Garden, 2016</td><td><strong>MIT</strong></td></tr>
      <tr><td><strong>LEDFader</strong></td><td>Bibliothèque AVR</td>
        <td>Jeremy Gillick, 2013 — <code>github.com/jgillick/arduino-LEDFader</code></td><td><strong>MIT</strong></td></tr>
      <tr><td><strong>DamanhurBridge</strong></td><td>ATmega328P + ADS1115 + MCP4725</td>
        <td><em>Implémentation originale</em> écrite pour cet ouvrage, d'après le brevet US 6 487 817 expiré</td><td><strong>MIT</strong></td></tr>
      <tr><td>Biotron</td><td>RP2040 (Raspberry Pi Pico)</td>
        <td>Playtronica — <code>github.com/Playtronica/biotron-firmware</code></td><td><strong>GPL-3.0</strong></td></tr>
    </tbody>
    <caption>Les quatre micrologiciels publics du domaine. Le programme du
    <em>Device U1</em> de Damanhur, lui, n'a jamais été publié : le brevet le
    désigne comme « le code objet de l'ANNEXE I », déposée sur microfiche et
    absente du document numérisé.</caption>
  </table>

  <div class="callout limite">
    <div class="callout-title">⚠️ Avant de téléverser quoi que ce soit</div>
    <p>Débranchez les électrodes avant de relier la carte à un ordinateur pour
    la programmer. Une carte alimentée par le port USB d'une machine branchée
    au secteur ne doit jamais être connectée à une plante, et encore moins à
    une personne. Reportez-vous aux règles de sécurité du chapitre 36.</p>
  </div>
</section>

<section class="chapter">
  <h2 id="annexe-codes-ms" data-toc="chapter">A.1 — MIDI Sprout : micrologiciel complet</h2>
  <p class="chapo">Quatre cent vingt-six lignes réparties en cinq fichiers, pour
  ATmega328P. C'est le code dont le brevet US 10 909 956 dit lui-même qu'il est
  <em>open-source firmware</em>. Commentaires d'origine conservés en anglais.</p>
""")

    for titre, chemin, ident in SECTIONS:
        try:
            contenu = lire(chemin)
        except FileNotFoundError:
            print(f"  ! introuvable : {chemin}")
            continue
        parts.append(bloc(titre, chemin, contenu, ident))
        print(f"  · {chemin.split('/')[-1]}")

    parts.append("""</section>

<section class="chapter">
  <h2 id="annexe-codes-dam" data-toc="chapter">A.2 — DamanhurBridge</h2>
  <p class="chapo">Le programme du <em>Device U1</em> n'étant pas public, voici une
  implémentation originale des fonctions que le brevet décrit en clair :
  pont de Wheatstone, boucle de nullification, commutation automatique de calibre,
  les sept réglages de la face avant, et sortie MIDI.</p>

  <div class="callout key">
    <div class="callout-title">✦ Ce que ce programme démontre</div>
    <p>Que l'architecture Damanhur est entièrement reproductible aujourd'hui avec
    trois circuits intégrés courants et une centaine d'euros. La boucle de
    nullification — l'invention centrale du brevet de 1999, alors réalisée par un
    convertisseur fréquence/tension et un intégrateur analogique de 220 ms — tient
    ici en une quinzaine de lignes de C.</p>
    <p>Différence notable avec le MIDI Sprout : la grandeur analysée est la
    <strong>consigne d'annulation</strong>, proportionnelle au déséquilibre du pont
    donc à la variation de résistance de la plante. La correspondance mesure →
    hauteur reste <em>monotone</em>, sans repliement modulo : elle est
    physiquement interprétable, et donc étalonnable en ohms.</p>
  </div>
""")

    try:
        dam = lire("reverse/damanhur-bridge/DamanhurBridge.ino")
        parts.append(bloc("Programme complet",
                          "sources/reverse/damanhur-bridge/DamanhurBridge.ino",
                          dam, "code-dam-main"))
        print("  · DamanhurBridge.ino")
    except FileNotFoundError:
        print("  ! DamanhurBridge.ino introuvable")

    parts.append("""  <div class="recap">
    <h4>À retenir</h4>
    <ul>
      <li>Les trois micrologiciels reproduits ici sont sous licence MIT : usage, modification et revente libres.</li>
      <li>Le code du Device U1 n'existe pas publiquement ; DamanhurBridge en propose une reconstruction fonctionnelle.</li>
      <li>La boucle de nullification de 1999 tient aujourd'hui en quinze lignes de C.</li>
      <li>Débrancher les électrodes avant toute programmation par USB.</li>
    </ul>
  </div>

  <div class="ornament"></div>
</section>
""")

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    taille = os.path.getsize(OUT) // 1024
    print(f"✓ Annexe écrite : {OUT} ({taille} Ko)")


if __name__ == "__main__":
    main()
