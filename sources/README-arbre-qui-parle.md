# L'Arbre qui Parle — série en trois volumes

> **Note d'intégration.** Cette série a été fusionnée dans le dépôt PhytoScope
> le 2026-09-18. Les chemins ci-dessous sont relatifs à la racine du dépôt :
> le script de construction s'appelle désormais `build_tree.py` et sa feuille
> de style `pdf-src/arbre.css` (pour ne pas entrer en conflit avec `build.py` et
> `pdf-src/book.css`, qui produisent l’ouvrage principal).

### Enquête, traité scientifique et manuel d'atelier sur les « arbres parlants »
**Auteur : Ateliers BN** — Édition numérique, 17 septembre 2026 · Site compagnon : https://bretagne-namaste.com/

Trois ouvrages indépendants mais solidaires, partageant une charte graphique, un
glossaire et une échelle épistémique communes. Générés en PDF haute résolution avec
sommaire cliquable, signets, en-têtes, pagination, index paginé et métadonnées.

**573 pages · 24 parties · 67 chapitres · 89 figures · 41 photographies ·
5 planches de schémas · 10 programmes · 92 termes de glossaire · 236 entrées d'index.**

---

## 1. Les trois volumes

| Volume | Fichier | Pages | Question traitée |
|---|---|---|---|
| **I. L'Arbre qui Parle** | `arbre-parlant-dublin-analyse-scientifique.pdf` | 212 | Que s'est-il réellement passé, et qui parle ? |
| **II. Biocommunication végétale et IA** | `biocommunication-vegetale-et-ia.pdf` | 163 | Que sait-on vraiment de la signalisation végétale ? |
| **III. Créer un arbre parlant** | `atelier-creer-arbre-parlant.pdf` | 198 | Comment le refaire soi-même, honnêtement ? |
| *(bonus)* Annexe technique isolée | `arbre-parlant-annexe-schemas-bom-programmes.pdf` | 65 | Les planches, nomenclatures et programmes, tirés à part |

Les annexes techniques du bonus sont **également intégrées au volume III** ; le tirage
à part existe pour un usage d'atelier, à poser sur l'établi.

## 2. Contenu du dossier

```
musique-of-the-plants-2/
├── build.py                  # Assemble les fragments → HTML → PDF (WeasyPrint)
├── tools/
│   ├── gen_glossary.py      # Glossaire des 3 volumes depuis une base unique
│   ├── gen_index.py          # Index paginé, avec vérification des ancres mortes
│   ├── gen_credits.py        # Crédits iconographiques des photos réellement employées
│   ├── gen-appendix-parts.py   # Fragments de l'annexe technique (listings extraits des ZIP)
│   ├── build-annexe.py       # Tirage à part de l'annexe technique
│   └── fetch-software.py     # Téléchargement des dépôts + relevé de licence
├── recherche/                # Notes de recherche sourcées (4 fichiers)
├── sources/                  # Fonds documentaire — 1,1 Go
│   ├── INDEX.md              # Index complet du fonds
│   ├── documents/            # 40 articles scientifiques + domaine public + presse
│   ├── code/                 # 17 archives de firmware (116 Mo)
│   ├── software/             # 50 dépôts + MANIFESTE.json des licences (701 Mo)
│   └── datasheets/           # 9 fiches techniques constructeur
└── pdf-src/
    ├── book.css              # Charte graphique commune (paged media)
    ├── fonts.css
    ├── assets/
    │   ├── fonts/            # Cinzel, Cormorant Garamond ; Lato système
    │   ├── svg/              # 67 illustrations + gen.py, gen_tt.py, gen_sch.py
    │   └── img/
    │       ├── photos/       # 106 photos Wikimedia + CREDITS.md
    │       └── p/            # Versions optimisées pour l'impression (1300 px)
    └── parts/
        ├── v1-dublin/        # Fragments du volume I
        ├── v2-biocommunication/
        ├── v3-atelier/
        └── annexe-tech/      # Source du tirage à part (copiée dans v3)
```

## 3. Prérequis

- **Python 3** avec **WeasyPrint 60+** (`pip install weasyprint`)
- Police **Lato** installée sur le système. Cinzel et Cormorant Garamond sont fournies
  dans `pdf-src/assets/fonts/` et chargées par `fonts.css`.
- Facultatif : `poppler-utils` (`pdfinfo`, `pdftoppm`) et `imagemagick` pour le contrôle
  qualité et le redimensionnement des photographies.

## 4. Reconstruire

```bash
# 1. (Re)générer les illustrations vectorielles — déterministe, graines fixes
python3 pdf-src/assets/svg/gen.py        # 28 illustrations de base
python3 pdf-src/assets/svg/gen_tt.py     # 34 illustrations propres à la série
python3 pdf-src/assets/svg/gen_sch.py    #  5 planches de schémas électroniques

# 2. (Re)générer les annexes calculées
python3 tools/gen_glossary.py       # glossaire des 3 volumes
python3 tools/gen_index.py           # index paginé des 3 volumes
python3 tools/gen_credits.py         # crédits iconographiques

# 3. Produire les PDF
python3 pdf-src/build_tree.py                     # les trois volumes
python3 pdf-src/build_tree.py v1                  # un seul volume
python3 tools/build-annexe.py        # le tirage à part de l'annexe technique
```

`build.py` :
1. concatène les fragments de `pdf-src/parts/<volume>/` dans l'ordre défini par `ORDER` ;
2. construit le **sommaire cliquable** (numéros de page via `target-counter`) ;
3. **numérote automatiquement les figures** par partie — les fragments écrivent `Fig. ##.` ;
4. **vérifie** les identifiants dupliqués, les ancres mortes et les images manquantes ;
5. injecte les métadonnées et rend le PDF avec signets et pagination.

## 5. Modifier le contenu

- Le texte vit dans `pdf-src/parts/<volume>/*.html`. Éditez, relancez `python3 pdf-src/build_tree.py`.
- La mise en forme est centralisée dans `pdf-src/arbre.css`.
- Pour ajouter une illustration : écrivez une fonction dans `gen_tt.py`, régénérez,
  puis référencez `assets/svg/mon-image.svg`.
- Pour ajouter une photographie : choisissez-la dans `pdf-src/assets/img/photos/`, référencez
  la version optimisée `assets/img/p/<nom>.jpg`, puis relancez `gen_credits.py` — l'annexe
  des crédits est reconstruite à partir des images **réellement employées**.
- **Ne modifiez jamais à la main** `A1-glossaire.html`, `A3-index.html`, `A4-credits.html`
  ni les fragments `A5`-`B3` du volume III : ils sont générés.

### Titres courants

Un titre de chapitre de plus d'environ 45 caractères déborde sur deux lignes dans
l'en-tête. Les chapitres concernés portent un attribut `data-run` donnant la forme
abrégée :

```html
<h2 id="..." data-toc="chapter" data-run="Le dossier factuel">Le dossier factuel : trois arbres, trois villes</h2>
```

## 6. Palette et typographie

| Rôle | Valeur |
|---|---|
| Vert forêt | `#0E2A22` (fonds de partie, titres) |
| Vert sève | `#3F7D5A` (accents, sous-titres) |
| Or / ambre | `#B08528` / `#E0C073` (filets, ornements) |
| Bleu technique | `#2F5E86` (encadrés scientifiques) |
| Cuivre | `#A8552E` (avertissements) |
| Blanc lumineux | `#FBF9F1` (fond de lecture) |
| Titres display | **Cinzel** |
| Titres courants | **Cormorant Garamond** |
| Texte courant | **Lato** |

Format 170 × 240 mm ; planches techniques en 240 × 170 mm (paysage).

## 7. Ligne éditoriale

La série distingue systématiquement quatre registres, balisés par quatre encadrés :

- **🔬 Point scientifique** — ce qui est mesuré, publié, vérifiable ;
- **🌿 Regard énergétique** — la lecture traditionnelle et sensible, présentée comme telle ;
- **⚠️ Limites et interprétation** — ce que les données ne permettent pas de conclure ;
- **✨ Expérience intérieure** — l'invitation à pratiquer.

Chaque affirmation est rattachée à l'un des quatre barreaux d'une **échelle épistémique**
explicitée dès le volume I : *mesure*, *fait établi*, *hypothèse*, *interprétation*.

**Ce qui n'a pas pu être vérifié est signalé comme non vérifié.** Plusieurs chiffres
largement diffusés sont nommés et écartés plutôt que repris par commodité — notamment la
vitesse de l'onde calcique de Toyota et al. (2018), les « clics racinaires à 220 Hz », et
une chercheuse en bioacoustique végétale dont aucune trace n'existe dans les bases
interrogées.

### Deux corrections de fait au récit qui circule

1. Le concepteur du projet de 2025 se nomme **Evan Greally** (et non « Grealy ») ;
   son titre est *Head of Creative Tech and Innovation* chez Droga5 Dublin.
2. **Ce n'est pas un projet dublinois** : c'est une campagne britannique lancée à
   **Londres** en février 2025 ; Dublin est la troisième escale, en avril. Le chapitre 3
   du volume I retrace la chaîne de propagation qui a produit cette erreur.

## 8. Avertissements

**Sécurité (volume III).** Les montages fonctionnent sur pile ou batterie basse tension,
exclusivement. Jamais de raccordement au secteur, jamais d'application sur une personne
sans isolation galvanique conforme, jamais d'oscilloscope relié à la terre sur un montage
connecté à un être vivant.

**Arboriculture (volume III).** L'arbre passe avant la mesure. Ni vis, ni clou, ni sangle
serrée, ni décapage d'écorce, ni compactage du sol. Autorisation écrite obligatoire dès
que l'arbre n'est pas chez vous.

**Statut des schémas.** La planche 1 est un **relevé fidèle** d'un fichier de conception
publié sous licence libre. Les planches 2 à 5 sont des **schémas d'application composés
d'après les fiches techniques constructeur** : cohérents et conformes, mais **non
prototypés**. Les prix sont des ordres de grandeur.

## 9. Sources et licences

- **Photographies** : 106 images, toutes issues de **Wikimedia Commons** sous licence
  libre (domaine public, CC0, CC BY, CC BY-SA). Crédits complets dans
  `pdf-src/assets/img/photos/CREDITS.md` et en annexe de chaque volume.
- **Illustrations vectorielles** : créations originales, générées de façon déterministe —
  donc reproductibles à l'identique.
- **Articles scientifiques** : accès ouvert uniquement (PubMed Central, bioRxiv, arXiv,
  MDPI, Frontiers, PLOS, Nature Portfolio, Science Advances). Aucun site pirate n'a été
  utilisé ; les articles sous accès restreint figurent à l'index par leur seul identifiant.
- **Domaine public** : œuvres de J. C. Bose (1902-1913) et de Darwin (1880).
- **Code** : chaque dépôt est accompagné de sa licence relevée dans l'archive elle-même
  (`sources/software/MANIFESTE.json`). Les programmes écrits pour l'ouvrage sont en CC0.

⚠️ **Rappel juridique** : un dépôt sans fichier `LICENSE` est « tous droits réservés »
par défaut, quelle que soit sa visibilité publique. Plusieurs dépôts populaires de ce
domaine sont dans ce cas ; l'annexe du volume III les signale.

Les marques citées appartiennent à leurs détenteurs respectifs. Cet ouvrage n'est ni
sponsorisé, ni affilié, ni rémunéré par aucune organisation, et ne comporte aucun lien
commissionné.

## 10. Licence de l'ouvrage

**Ebook librement diffusable sans aucune condition.** Auteur : Ateliers BN.
