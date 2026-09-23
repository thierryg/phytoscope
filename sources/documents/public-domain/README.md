# Domaine public — fac-similés

Ce dossier réunit les œuvres fondatrices de l'électrophysiologie végétale.
Elles sont **dans le domaine public** : Jagadis Chandra Bose (1902-1907) et
Charles Darwin (1880).

## Ce qui est dans le dépôt, et ce qui n'y est pas

| | Dans le dépôt | Poids |
|---|---|---|
| **Transcriptions** — `.txt`, `.html`, `.epub` | **oui** | ~2 Mo |
| **Fac-similés numérisés** — `.pdf` | **non** | 260 Mo |

Ce n'est pas une question de droits : rien n'interdirait de rediffuser ces
livres. C'est une question de poids. Le dépôt pèse 155 Mo sans eux ; un clone
de 415 Mo pour des numérisations que l'on retélécharge en une commande n'a
pas de sens. Les transcriptions, elles, restent versionnées — ce sont elles
que l'on cite et que l'on recherche en plein texte.

## Les récupérer

Chaque fac-similé vient d'Internet Archive, sous l'identifiant indiqué :

```bash
cd sources/documents/domaine-public

# Bose J. C. (1902) — Response in the Living and Non-Living
curl -L -o 1902-Bose-response-in-the-living-and-non-living.pdf \
  https://archive.org/download/responseinliving00boseuoft/responseinliving00boseuoft.pdf

# Bose J. C. (1906) — Plant Response as a Means of Physiological Investigation
curl -L -o 1906-Bose-plant-response-as-a-means-of-physiological-investigation.pdf \
  https://archive.org/download/plantresponseasm00boseuoft/plantresponseasm00boseuoft.pdf

# Bose J. C. (1907) — Comparative Electro-Physiology
curl -L -o 1907-Bose-comparative-electro-physiology.pdf \
  https://archive.org/download/comparativeelect00boseuoft/comparativeelect00boseuoft.pdf

# Bose J. C. (1906) — Plant Autographs and their Revelations
curl -L -o plantautographst00bose.pdf \
  https://archive.org/download/plantautographst00bose/plantautographst00bose.pdf

# Bose J. C. — Researches on Irritability of Plants
curl -L -o researchesonirri00boseuoft.pdf \
  https://archive.org/download/researchesonirri00boseuoft/researchesonirri00boseuoft.pdf

# Darwin C. & F. (1880) — The Power of Movement in Plants
curl -L -o 1880-Darwin-the-power-of-movement-in-plants.pdf \
  https://archive.org/download/powerofmovementi00darwiala/powerofmovementi00darwiala.pdf
```

Le texte intégral recherchable de Darwin vient, lui, de Project Gutenberg :
[gutenberg.org/ebooks/5605](https://www.gutenberg.org/ebooks/5605) — il **est**
versionné (`1880-Darwin-power-of-movement-in-plants-gutenberg.txt`).

## Où les références sont consignées

`sources/INDEX.md`, § 2 — titre complet, éditeur, année, lien archive.org et
ce que l'ouvrage apporte au projet.

## Attention

`plantresponseasm00bose.pdf` et
`1906-Bose-plant-response-as-a-means-of-physiological-investigation.pdf` sont
**deux numérisations différentes du même livre** (40 et 50 Mo). La seconde est
celle que cite `sources/INDEX.md`.
