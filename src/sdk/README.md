# SDK PhytoScope

De quoi écrire un module : la documentation, un exemple complet, et un outil
qui crée un squelette qui fonctionne déjà.

```
sdk/
  README.md              ce fichier
  docs/                  la documentation, pas à pas
  bonjour-monde/         l'exemple complet, avec ses essais
  outils/
    new_module.py    crée un module prêt à l'essai
```

## En trois commandes

```bash
python3 src/sdk/outils/new_module.py mon-module     # créer
python3 -m pytest mon-module/ -v                    # éprouver
cp -r mon-module ~/.config/phytoscope/modules/      # installer
```

Relancez PhytoScope : vos valeurs s'affichent dans l'onglet **Multimètre →
Grandeurs scientifiques**, et le module apparaît dans **Diagnostic → Modules**.

## La documentation

| | |
|---|---|
| [1. Démarrage pas à pas](docs/01-demarrage.md) | de zéro à un module installé |
| [2. L'interface, en détail](docs/02-api.md) | chaque classe, chaque champ, chaque méthode |
| [3. Les cinq capacités](docs/03-capacites.md) | analyser, décrire, sonifier, exporter, mesurer |
| [4. Les événements](docs/04-evenements.md) | s'abonner à ce qui se passe |
| [5. Éprouver son module](docs/05-essais.md) | sans logiciel, sans matériel |
| [6. Publier](docs/06-publier.md) | diffuser, versionner, empaqueter |
| [7. Les pièges](docs/07-pieges.md) | ce qui coûte une soirée quand on l'ignore |

Le même contenu, mis en page pour l'impression, est dans
`build/Ecrire-un-module-PhytoScope.pdf` (`python3 build_sdk.py`).

## Ce qu'il faut retenir

| | |
|---|---|
| Importer | seulement depuis `phytoscope.api` |
| Écrire | seulement dans `contexte.dossier()` |
| Lever | jamais pour dire « rien à signaler » — rendre une liste vide |
| `sens` | toujours renseigné : ce que le nombre dit, et ce qu'il ne dit pas |
| Rappels | courts : ils s'exécutent dans le fil de l'interface |
| Libellés | des gabarits (`« à {tau} s »`), jamais des phrases composées |
| Manifeste | des valeurs littérales : il est lu sans exécuter votre code |

---

*Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com — licence MIT*
