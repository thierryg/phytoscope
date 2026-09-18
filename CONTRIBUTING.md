# Contribuer à PhytoScope

Merci de vous y intéresser. Ce fichier dit comment travailler ici sans perdre
de temps — le vôtre ni celui des autres.

## Avant d'écrire une ligne : lire, dans cet ordre

| Ordre | Fichier | Ce qu'on y trouve |
|---|---|---|
| 1 | [`AGENTS.md`](AGENTS.md) | Le point d'entrée : l'ordre de lecture, ce qu'on ne fait pas ici, comment laisser une trace. |
| 2 | [`constraints.md`](constraints.md) | **Le cahier des charges**, contraintes numérotées `C-1`…`C-64`. Il fait autorité : une contribution qui contredit une contrainte est refusée, ou la contrainte change d'abord. |
| 3 | [`.ai/etat.md`](.ai/etat.md) | Où en est le travail. |
| 4 | [`.ai/decisions.md`](.ai/decisions.md) | Les décisions de conception **et leurs raisons**. Beaucoup de « pourquoi pas comme ça ? » y ont déjà leur réponse. |

## Les cinq règles qui coûtent cher quand on les oublie

1. **Le français partout** — code, commentaires, docstrings, interface,
   documents, messages de commit. Typographie française : « guillemets »,
   espace insécable avant `: ; ! ?`.

2. **Expliquer le pourquoi.** Un commentaire qui paraphrase le code est à
   supprimer ; un commentaire qui dit *pourquoi* le code est ainsi est à
   garder. C'est la règle qui fait la différence entre ce dépôt et un autre.

3. **Vérifier, ne pas supposer.** Toute affirmation chiffrée — nombre de
   pages, de tests, de références, un débit, un prix — se **mesure par une
   commande** avant d'être écrite.

4. **Ne jamais modifier un fichier généré** (`C-45`). On modifie la source et
   on relance le générateur. Les fichiers générés sont repérables : nom
   commençant par `_`, ou dossier `build/`, ou `pdf-src/assets/svg/*.svg`.

5. **Tester avant de conclure.** `cd src/phytoscope && make test` — sans
   matériel ni réseau.

## Ce qu'on ne fait pas ici

- ❌ **Écrire dans les réglages de qui exécute le logiciel**
  (`~/.config/phytoscope/reglages.json`) pendant un essai. Détourner
  `XDG_CONFIG_HOME` vers un dossier temporaire.
  *(Cette règle vient d'un incident réel : voir le journal du 2026-09-18.)*
- ❌ Ajouter une détection automatique de la locale (`C-31`).
- ❌ Ajouter une dépendance obligatoire (`C-40`), ou SciPy sous quelque
  prétexte.
- ❌ Employer le vocabulaire de la parole sans son avertissement (`C-5`).
  Une plante n'exprime rien ; un signal est transposé. La nuance est le cœur
  de l'honnêteté du projet.
- ❌ `sudo` : tout s'installe dans le dossier personnel (`C-55`).
- ❌ **Copier la clé privée de signature** ailleurs que dans
  `~/.local/share/phytoscope-signature/` et `certificat/` (`C-2R`).
- ❌ Poser notre en-tête d'attribution sur du code tiers. `sources/` est
  exclu de `tools/entetes.py` pour cette raison : y écrire
  « SPDX-License-Identifier: MIT » sur du GPL est une fausse déclaration.

## Mettre en place son poste

```bash
git clone https://github.com/thierryg/phytoscope.git
cd phytoscope

# Le logiciel
cd src/phytoscope
make install-dev            # environnement virtuel + outils de développement
make test                   # la suite complète, sans matériel ni réseau
make doctor                 # dit ce qui est installé et ce qui manque
cd ../..

# Les garde-fous avant commit (fortement conseillé)
python3 -m pip install --user pre-commit
pre-commit install
pre-commit run --all-files  # pour voir l'état du dépôt entier
```

Les archives de dépôts tiers (`sources/code/`, `sources/software/`) ne sont
pas versionnées — elles pèsent 817 Mo. Pour les récupérer :

```bash
python3 tools/fetch-software.py
```

## Les commandes utiles

```bash
# Logiciel
cd src/phytoscope
make test                                        # la suite de tests
make lint                                        # ruff
make demo                                        # sans matériel
.venv/bin/python tools/i18n.py --couverture      # état des 10 traductions
.venv/bin/python tools/sbom.py --json            # nomenclature logicielle

# Publications (depuis la racine)
python3 pdf-src/assets/svg/gen.py       && python3 pdf-src/build.py         # l'ouvrage
python3 pdf-src/assets/svg/gen_carte.py && python3 pdf-src/build_carte.py   # le hors-série
python3 pdf-src/assets/svg/gen_tt.py    && python3 pdf-src/build_arbre.py   # la série
python3 pdf-src/assets/svg/gen_sdk.py   && python3 pdf-src/build_sdk.py     # le guide du SDK
python3 tools/verifier_svg.py                                   # XML bien formé
python3 tools/entetes.py --verifier                             # en-têtes à jour

# Paquets (depuis Debian, Ubuntu ou Mint)
cd packaging
make outils        # ce qui manque pour empaqueter
make deps          # NSIS, msitools, osslsigncode — sans sudo
make tout          # .deb .rpm .run .exe .msi .pkg .zip .tar.gz, signés
make verifier      # rouvre et contrôle tout ce qui a été produit

# Micrologiciel
cd src/firmware
./build.sh --deps  # SDK + chaîne ARM dans $HOME, sans sudo
./build.sh         # → phytosense.uf2
```

## Proposer une modification

1. **Ouvrez un ticket d'abord** si le changement touche une contrainte, une
   interface, ou plus de quelques fichiers. Cela évite d'écrire du code qui
   sera refusé pour une raison déjà consignée dans `.ai/decisions.md`.
2. Créez une branche : `git checkout -b sujet-court`.
3. Faites une chose à la fois. Une branche = un sujet.
4. **Messages de commit en français**, à l'impératif, avec le pourquoi :

   ```
   corrige l'échappement des & dans les illustrations générées

   Le générateur écrivait le texte tel quel dans le SVG. Un « & » nu rend
   le fichier mal formé ; WeasyPrint le laisse alors tomber et compose un
   cadre vide, sans rien signaler. timeline.svg en était victime.
   ```

5. Avant de pousser :

   ```bash
   pre-commit run --all-files
   cd src/phytoscope && make test && make lint
   python3 tools/entetes.py --verifier
   ```

6. **Consignez** : ajoutez une entrée datée dans [`.ai/journal.md`](.ai/journal.md)
   et mettez [`.ai/etat.md`](.ai/etat.md) à jour. C'est ce qui permet à la
   personne suivante — ou à vous, trois semaines plus tard — de reprendre.
7. Ouvrez la demande de fusion. L'intégration continue passera l'analyse
   statique, les tests sur Linux, Windows et macOS, la fabrication des
   paquets et les contrôles de sécurité.

## Signaler une anomalie

Ouvrez un ticket avec ce qu'il faut pour la reproduire : la version
(`phytoscope --version`), le système, la version de Python, et la suite
d'actions minimale. Un gabarit vous y aidera.

**Sauf s'il s'agit d'une faille de sécurité** : dans ce cas, n'ouvrez pas de
ticket public. Lisez [`SECURITY.md`](SECURITY.md).

## Les licences, et ce que votre contribution devient

Le dépôt porte deux licences (`C-53`) :

- **MIT** pour le logiciel, le micrologiciel, la trousse et les outils ;
- **CERN-OHL-P v2** pour le matériel (`hardware/`).

Voir [`LICENSES/README.md`](LICENSES/README.md). En proposant une
contribution, vous acceptez qu'elle soit diffusée sous la licence du fichier
concerné. Les personnes qui contribuent sont ajoutées à [`AUTHORS`](AUTHORS).

## Le ton

Le projet parle de plantes et de signaux électriques, sujet où l'enthousiasme
déborde vite sur des affirmations qu'on ne peut pas tenir. La règle
rédactionnelle du dépôt est donc simple : **dire ce qui est mesuré, dire ce
qui est supposé, et ne jamais confondre les deux.** Une contribution qui
améliore cette honnêteté est toujours bienvenue, même si elle ne change pas
une ligne de code.
