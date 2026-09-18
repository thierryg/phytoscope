# Bonjour, monde — module d'exemple

Le plus petit module de PhytoScope qui fasse quelque chose. Lisez
[`module.py`](module.py) : il est écrit pour être lu en entier, puis copié.

## L'essayer

```bash
# Linux
cp -r sdk/bonjour-monde ~/.config/phytoscope/modules/
# macOS
cp -r sdk/bonjour-monde ~/Library/Application\ Support/PhytoScope/modules/
# Windows
xcopy /E sdk\bonjour-monde %APPDATA%\PhytoScope\modules\bonjour-monde\
```

Relancez PhytoScope. Onglet **Multimètre → Grandeurs scientifiques** : trois
lignes de plus. Onglet **Diagnostic → Modules** : votre module dans la liste.

Si rien n'apparaît, le Diagnostic dit pourquoi en une phrase — manifeste
invalide, API visée inconnue, bibliothèque absente, ou faute au chargement.

## Les essais

```bash
python3 -m pytest sdk/bonjour-monde/test_bonjour_monde.py -v
```

Les essais n'ont besoin **ni du logiciel lancé, ni de matériel** : ils
appellent le module avec un signal fabriqué et un contexte de fausse monnaie.
C'est ce qui permet de développer un module sans plante sur le bureau.

## En créer un nouveau

```bash
python3 src/sdk/outils/nouveau_module.py mon-module --capacite analyseur
```

L'outil crée le dossier, le manifeste, le squelette et les essais.

## Ce qu'il faut retenir

| | |
|---|---|
| Importer | seulement depuis `phytoscope.api` |
| Écrire | seulement dans `contexte.dossier()` |
| Lever | jamais pour dire « rien à signaler » — rendre une liste vide |
| `sens` | toujours renseigné : ce que le nombre dit, et ce qu'il ne dit pas |
| Rappels | courts : ils s'exécutent dans le fil de l'interface |
| Libellés | des gabarits (`« à {tau} s »`), jamais des phrases déjà composées |

---

*Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com — licence MIT*
