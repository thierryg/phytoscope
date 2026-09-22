# 5. Éprouver son module

Sans logiciel lancé, sans matériel, sans plante. C'est le point le plus utile
du SDK.

```bash
python3 -m pytest mon-module/ -v
```

---

## Le principe

Un module ne dépend que de `phytoscope.api`. On peut donc l'instancier avec un
**faux contexte** — un objet qui offre la même surface, sans rien derrière —
et un **signal fabriqué**.

```python
instance = MonModule(ContexteDEssai())
instance.installer()
grandeurs = instance.analyser(signal_dessai(30.0), 250.0, instance.contexte)
```

---

## Le faux contexte

Fourni avec les essais générés. Recopiez-le.

```python
class ContexteDEssai:
    """La même surface que `Contexte`, sans rien derrière."""

    def __init__(self, reglages=None):
        self.reglages = dict(reglages or {})
        self.abonnements = {}
        self.journal_ecrit = []
        self.frequence_hz = 250.0
        self.pleine_echelle_v = 2.5
        self.reseau_hz = 50.0

    def abonner(self, evenement, rappel):
        self.abonnements.setdefault(evenement, []).append(rappel)

    def journal(self, message, niveau="info"):
        self.journal_ecrit.append(f"{niveau}: {message}")

    def message(self, texte):
        self.journal_ecrit.append(f"message: {texte}")

    def traduire(self, texte):
        return texte                  # la langue source suffit en essai

    def dossier(self):
        import tempfile
        return tempfile.mkdtemp(prefix="essai-")

    def signal(self, secondes=60.0, brut=False):
        return signal_dessai(secondes)

    def instants_evenements(self):
        return []

    def etat(self):
        from types import SimpleNamespace
        return SimpleNamespace(duree_s=120.0, source="essai",
                               en_marche=True, relecture=False)
```

> **Si un essai échoue parce qu'une méthode manque ici**, c'est le signe que
> vous employez une partie de l'interface qu'il faudra aussi éprouver. C'est
> une bonne nouvelle, pas un ennui.

---

## Le signal d'essai

```python
def signal_dessai(secondes=30.0, fs=250.0):
    """Du bruit, une dérive lente, quelques bouffées d'activité."""
    n = int(secondes * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)          # graine fixe : essais reproductibles
    x = r.normal(0.0, 3e-6, n)             # bruit de fond, 3 µV
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)      # dérive lente
    for t0 in np.arange(5.0, secondes, 7.0):       # bouffées
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x
```

**Graine fixe.** Un essai qui échoue une fois sur dix est pire qu'un essai
absent : on finit par le désactiver, et l'on perd aussi les neuf fois où il
aurait servi.

### Des signaux pour les cas limites

```python
np.zeros(0)                              # rien encore reçu
np.zeros(1000)                           # signal nul
np.full(1000, 2.5)                       # saturé
np.random.default_rng(0).normal(0, 1, n) # amplitude absurde
```

Votre module doit traverser les quatre **sans lever**.

---

## Ce qu'il faut éprouver

### Le manifeste

```python
def test_le_manifeste_est_valide(instance):
    assert instance.MANIFESTE.defauts() == [], instance.MANIFESTE.defauts()

def test_le_manifeste_vise_une_api_connue(instance):
    from phytoscope.api import compatible
    assert compatible(instance.MANIFESTE.api)
```

Un manifeste refusé, et votre module n'est jamais chargé. C'est le premier
essai à écrire, et celui qui vous évitera de chercher pendant une heure.

### La forme de ce que vous rendez

```python
def test_chaque_grandeur_explique_ce_quelle_signifie(instance):
    for g in instance.analyser(signal_dessai(), 250.0, instance.contexte):
        assert g.cle and g.libelle
        assert g.texte
        assert len(g.sens) > 20, f"« {g.cle} » n'explique rien"
        assert np.isfinite(g.valeur)
```

### Les cas limites

```python
def test_un_signal_vide_ne_fait_pas_lever(instance):
    assert instance.analyser(np.zeros(0), 250.0, instance.contexte) == []

def test_un_signal_sature_ne_fait_pas_lever(instance):
    instance.analyser(np.full(2000, 2.5), 250.0, instance.contexte)
```

### Les réglages

```python
def test_un_reglage_a_faux_se_voit(module_classe):
    contexte = ContexteDEssai(reglages={"montrer_le_detail": False})
    obj = module_classe(contexte); obj.installer()
    cles = {g.cle for g in obj.analyser(signal_dessai(), 250.0, contexte)}
    assert "detail" not in cles
```

### Les abonnements

```python
def test_le_rappel_compte_bien(instance):
    from phytoscope.api import EVENEMENT_DETECTE
    for rappel in instance.contexte.abonnements[EVENEMENT_DETECTE]:
        rappel(1.0, 1e-4)
        rappel(2.0, 2e-4)
    ...
```

### La physique, quand il y en a

C'est le plus important, et le plus souvent oublié. Si votre module calcule
quelque chose, **confrontez-le au calcul au crayon** :

```python
def test_la_densite_de_bruit_est_juste(instance):
    """2 µV eff. sur 125 Hz de bande donnent 179 nV/√Hz."""
    fs = 250.0
    x = np.random.default_rng(0).normal(0, 2e-6, int(120 * fs))
    attendu = 2e-6 / np.sqrt(fs / 2)
    obtenu = next(g for g in instance.analyser(x, fs, instance.contexte)
                  if g.cle == "densite").valeur
    assert obtenu == pytest.approx(attendu, rel=0.10)
```

Un essai qui vérifie qu'une fonction « rend un nombre » ne vérifie rien. Un
essai qui vérifie que ce nombre est le bon vérifie tout.

---

## Éprouver plusieurs modules ensemble

Nommez votre fichier d'essais **`test_<votre-module>.py`**, et non
`test_module.py`. Deux fichiers de même nom, dans deux dossiers sans
`__init__.py`, ne peuvent pas être collectés dans la même session pytest.

L'outil `new_module.py` le fait pour vous.

---

## Le module dans le vrai logiciel

Une fois les essais passés, il reste à vérifier qu'il se charge pour de bon :

```bash
cp -r mon-module ~/.config/phytoscope/modules/
phytoscope --check          # les contrôles avant vol
phytoscope                  # onglet Diagnostic → Modules
```

Et pour voir vos lignes de journal :

```bash
tail -f ~/.config/phytoscope/phytoscope.log | grep mon-module
```

---

**Suite :** [6. Publier](06-publier.md)
