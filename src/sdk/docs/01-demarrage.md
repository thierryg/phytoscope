# 1. Démarrage pas à pas

De rien du tout à un module installé qui affiche vos valeurs. Comptez dix
minutes.

---

## Étape 0 — Ce qu'il vous faut

* **Python 3.9 ou plus récent** — celui qui fait tourner PhytoScope convient.
* **PhytoScope installé**, ou son code source. Si vous avez le code source,
  tout est déjà là.
* De quoi lancer `pytest` : `pip install pytest`.

Vous n'avez besoin **ni de matériel, ni d'une plante**. Le logiciel démarre
sur son générateur interne, et les essais d'un module n'exigent même pas qu'il
tourne.

---

## Étape 1 — Créer le squelette

```bash
python3 src/sdk/outils/nouveau_module.py mon-premier-module
```

L'outil crée un dossier de trois fichiers :

```
mon-premier-module/
    module.py                      le squelette — il fonctionne déjà
    test_mon_premier_module.py     cinq essais, qui passent
    README.md                      comment l'installer, ce qui reste à faire
```

### Choisir la capacité

Par défaut, l'outil crée un **analyseur** : le plus simple, et celui dont le
résultat se voit tout de suite. Les autres :

```bash
python3 src/sdk/outils/nouveau_module.py mon-module --capacite descripteur
python3 src/sdk/outils/nouveau_module.py mon-module --capacite sonificateur
python3 src/sdk/outils/nouveau_module.py mon-module --capacite exportateur
```

| Capacité | Ce qu'elle fait | Où ça s'affiche |
|---|---|---|
| `analyseur` | calcule des nombres | Multimètre → Grandeurs scientifiques |
| `descripteur` | produit une courbe | Descripteurs |
| `sonificateur` | fait des notes | Écoute |
| `exportateur` | écrit un format | Bibliothèque |

### Les autres options

```bash
--titre "Mon beau module"    ce que l'utilisateur lira
--auteur "Votre nom"
--dans /chemin/quelque/part  où créer le dossier
--installer                  créer directement dans le dossier des modules
```

---

## Étape 2 — Lire ce qui a été créé

Ouvrez `module.py`. Il est court, et chaque partie est commentée. Trois
choses à repérer :

### Le manifeste

```python
MANIFESTE = Manifeste(
    nom="mon-premier-module",
    titre="Mon premier module",
    version="0.1.0",
    api="1.0",
    capacites=(Capacite.ANALYSEUR,),
)
```

C'est la carte d'identité. **Elle est lue sans exécuter votre code** : le
logiciel l'extrait par analyse syntaxique du fichier. C'est ce qui lui permet
de refuser un module qui vise une interface inconnue sans avoir à l'exécuter
pour le savoir.

> **Conséquence** : écrivez des valeurs littérales. `version="1.0.0"` est lu ;
> `version=lire_ma_version()` ne l'est pas, et le défaut s'appliquera.

### Le cycle de vie

```python
def installer(self):    # une fois, au démarrage
def arreter(self):      # une fois, à la fermeture
```

`installer()` et non `__init__` : `__init__` est appelé pour tous les modules,
l'un après l'autre, au lancement du logiciel. Il doit rester instantané.

### La capacité

```python
def analyser(self, x, fs, contexte):
    ...
    return [Grandeur(...)]
```

C'est le travail. `x` est le signal **en volts**, `fs` la cadence réelle.

---

## Étape 3 — Éprouver

```bash
python3 -m pytest mon-premier-module/ -v
```

```
test_le_manifeste_est_valide PASSED
test_le_manifeste_vise_une_api_connue PASSED
test_analyser_rend_des_grandeurs_completes PASSED
test_un_signal_vide_ne_fait_pas_lever PASSED
test_arreter_ne_leve_pas PASSED
```

Remarquez ce que ces essais **n'exigent pas** : ni logiciel lancé, ni carte,
ni plante. Ils fabriquent un signal plausible et un faux contexte, puis
appellent votre code.

C'est le point le plus utile du SDK : on développe un module dans le train.

---

## Étape 4 — Écrire quelque chose à soi

Remplacez le corps de `analyser`. Un exemple qui a du sens : compter combien
de fois le signal franchit sa propre moyenne, ce qui donne une idée grossière
de son agitation.

```python
def analyser(self, x, fs, contexte):
    if x.size < 64:
        return []

    centre = x - x.mean()
    #  Un passage par zéro : deux échantillons consécutifs de signes opposés.
    passages = int(np.sum(np.diff(np.sign(centre)) != 0))
    par_minute = passages / (x.size / fs) * 60.0

    return [Grandeur(
        cle="passages-par-zero",
        libelle="Passages par la moyenne",
        valeur=par_minute,
        texte=f"{par_minute:.0f} /min",
        sens=("Nombre de fois par minute où le signal traverse sa propre "
              "moyenne. Monte avec le bruit haute fréquence et descend quand "
              "une dérive lente domine. Ne dit rien de l'activité de la "
              "plante en soi : un câble qui bouge produit le même effet."),
    )]
```

Relancez les essais. Ils passent toujours — ils vérifient la **forme** de ce
que vous rendez, pas sa valeur. Ajoutez le vôtre :

```python
def test_le_compte_monte_avec_le_bruit(instance):
    calme = np.zeros(7500) + 1e-6
    agite = np.random.default_rng(0).normal(0, 3e-6, 7500)
    a = instance.analyser(calme, 250.0, instance.contexte)[0].valeur
    b = instance.analyser(agite, 250.0, instance.contexte)[0].valeur
    assert b > a * 10
```

---

## Étape 5 — Installer

```bash
# Linux
cp -r mon-premier-module ~/.config/phytoscope/modules/

# macOS
cp -r mon-premier-module ~/Library/Application\ Support/PhytoScope/modules/

# Windows
xcopy /E mon-premier-module %APPDATA%\PhytoScope\modules\mon-premier-module\
```

Ou, dès la création : `python3 src/sdk/outils/nouveau_module.py mon-module --installer`

---

## Étape 6 — Voir le résultat

Relancez PhytoScope.

1. **Onglet Diagnostic → Modules.** Votre module doit être là, en `actif`.
2. **Onglet Multimètre → Grandeurs scientifiques.** Votre ligne s'affiche
   parmi celles des modules livrés. Survolez-la : votre `sens` apparaît.

---

## Si rien n'apparaît

Allez au **Diagnostic → Modules**. Il dit en une phrase ce qui s'est passé.
C'est la page à regarder en premier, avant de douter de soi.

| Ce qui s'affiche | Ce que ça veut dire | Quoi faire |
|---|---|---|
| absent de la liste | le dossier n'est pas au bon endroit, ou il n'y a pas de `module.py` | vérifiez le chemin |
| `incompatible` — vise l'API 2.0 | votre `api=` annonce une version inconnue | mettez celle du logiciel |
| `incompatible` — bibliothèque absente | votre `exige=` réclame quelque chose qui manque | la commande `pip` est donnée |
| `incompatible` — nom invalide | minuscules, chiffres et tirets seulement | corrigez `nom=` |
| `en_faute` | votre code a levé | la trace est dans le journal (<kbd>Ctrl+L</kbd>) |
| `desactive` | l'utilisateur n'en veut pas | Réglages |

---

**Suite :** [2. L'interface, en détail](02-api.md)
