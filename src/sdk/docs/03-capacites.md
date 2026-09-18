# 3. Les cinq capacités

Une capacité est ce que votre module sait faire. Vous en déclarez une,
plusieurs, ou aucune — un module qui n'agit qu'à l'installation et à l'arrêt
est parfaitement légitime.

| Capacité | Appelée | Contrainte de temps | S'affiche dans |
|---|---|---|---|
| [Analyseur](#analyseur) | toutes les 2 s, page visible | quelques dizaines de ms | Multimètre |
| [Descripteur](#descripteur) | à la demande | une seconde passe | Descripteurs |
| [Sonificateur](#sonificateur) | à chaque événement | **très court** | Écoute |
| [Exportateur](#exportateur) | à la demande | aucune | Bibliothèque |
| [Source](#source) | en continu | **critique** | Réglages |

---

## Analyseur

Calcule des grandeurs sur une fenêtre de signal.

```python
from phytoscope.api import Analyseur, Capacite, Grandeur, Manifeste, Module

class MonAnalyse(Module, Analyseur):
    MANIFESTE = Manifeste(nom="mon-analyse", api="1.0",
                          capacites=(Capacite.ANALYSEUR,))

    FENETRE_S = 60.0        # combien de secondes vous voulez
    SIGNAL_BRUT = True      # avant réjecteur et passe-bas

    def analyser(self, x, fs, contexte):
        if x.size < 64:
            return []       # « rien à dire » — jamais une exception
        return [Grandeur(
            cle="ecart-type",
            libelle="Écart-type",
            valeur=float(np.std(x)),
            texte=f"{np.std(x) * 1e6:.2f} µV",
            sens=("La dispersion du signal autour de sa moyenne. Croît avec "
                  "le bruit ET avec l'activité : ne permet pas de distinguer "
                  "l'un de l'autre."),
        )]
```

### `FENETRE_S` et `SIGNAL_BRUT`

```python
FENETRE_S = 60.0        # l'hôte donne ce qu'il a, jamais plus
SIGNAL_BRUT = True
```

**Brut** = avant réjecteur de réseau et passe-bas. C'est ce qu'il faut pour
toute mesure de bruit : *filtrer avant de mesurer le bruit revient à mesurer
son propre filtre*. Le réjecteur effacerait le résidu de secteur qu'on cherche
justement à voir ; le passe-bas à 40 Hz effacerait la bande où se lit le bruit
thermique.

**Traité** = ce qu'on voit à l'écran. Pour analyser l'*activité* plutôt que la
chaîne de mesure.

### Un exemple qui a du sens

Estimer la résistance de la source à partir du bruit thermique :

```python
BOLTZMANN = 1.380649e-23
TEMPERATURE_K = 293.15          # 20 °C

def analyser(self, x, fs, contexte):
    if x.size < int(10 * fs):
        return []

    #  La densité de bruit se lit AU-DESSUS de la bande biologique, là où la
    #  plante ne produit plus rien. Sinon on compterait son activité comme du
    #  bruit, et le résultat n'aurait aucun sens.
    spectre = np.abs(np.fft.rfft(x - x.mean())) ** 2
    freqs = np.fft.rfftfreq(x.size, 1 / fs)
    bande = (freqs > 10.0) & (freqs < min(40.0, fs / 2.5))
    densite = np.sqrt(np.mean(spectre[bande]) * 2 / (fs * x.size))

    resistance = densite ** 2 / (4 * BOLTZMANN * TEMPERATURE_K)

    return [Grandeur(
        cle="resistance-equivalente",
        libelle="Résistance équivalente",
        valeur=resistance,
        texte=f"{resistance / 1e6:.2f} MΩ",
        sens=("Déduite du bruit thermique de Johnson-Nyquist, R = Sᵥ / 4kT. "
              "C'est un MAJORANT, non une mesure à l'ohmmètre : le bruit de "
              "l'amplificateur s'y ajoute. C'est sa VARIATION qui informe — "
              "un contact qui sèche la fait grimper d'une décade."),
        alerte=resistance > 5e6,
    )]
```

Remarquez le `sens` : il dit ce que le nombre vaut **et** ce qu'il ne vaut
pas. C'est ce qui sépare une mesure d'une impression.

---

## Descripteur

Produit une représentation — une courbe, un spectre, une carte d'énergie.

```python
def decrire(self, x, fs, contexte):
    if x.size < 64:
        return []
    spectre = np.abs(np.fft.rfft(x - x.mean()))
    freqs = np.fft.rfftfreq(x.size, 1 / fs)
    return [Trace(
        x=freqs[1:], y=20 * np.log10(np.maximum(spectre[1:], 1e-15)),
        titre=contexte.traduire("Mon spectre"),
        x_libelle=contexte.traduire("fréquence (Hz)"),
        y_libelle="dB",
        x_log=True,
        avertissement=contexte.traduire(
            "Suppose le signal stationnaire sur la fenêtre analysée, ce qui "
            "est rarement vrai longtemps sur un signal végétal."),
    )]
```

Ce n'est pas un chemin critique : l'utilisateur a demandé la représentation et
attend. Une seconde de calcul passe.

`Trace` vérifie que `x` et `y` ont la même taille, et lève sinon — ce qui vaut
mieux qu'une courbe silencieusement fausse.

---

## Sonificateur

Transforme une valeur mesurée en notes.

```python
def sonifier(self, valeur_v, contexte):
    gamme = (0, 2, 4, 5, 7, 9, 11)          # diatonique majeure
    rang = int(abs(valeur_v) * 1e6) % len(gamme)
    octave = min(int(abs(valeur_v) * 1e5), 3)
    return [NoteProposee(
        hauteur_midi=48 + 12 * octave + gamme[rang],
        velocite=min(40 + int(abs(valeur_v) * 5e5), 110),
        duree_s=0.4,
        origine_v=valeur_v,     # d'où vient cette note
    )]
```

> **Soyez rapide.** Vous êtes dans la boucle de rendu musical. Pas de calcul
> spectral ici, pas d'accès disque, pas de requête réseau.

Rendre une liste vide signifie « pas de note pour cette valeur ». C'est une
réponse légitime, et souvent la bonne : toutes les variations ne méritent pas
d'être entendues.

---

## Exportateur

Écrit une séance dans un autre format.

```python
FORMAT = "Mon format (.xyz)"    # ce qui s'affiche dans la liste
EXTENSION = ".xyz"

def exporter(self, seance, cible, contexte):
    """`seance` : le dossier à LIRE. `cible` : le fichier à ÉCRIRE."""
    source = os.path.join(seance, "mesures.csv")
    if not os.path.exists(source):
        contexte.journal(f"« {source} » introuvable", "warning")
        return False        # faux, pas une exception

    with open(source, encoding="utf-8", newline="") as entree, \
         open(cible, "w", encoding="utf-8", newline="") as sortie:
        ...
    return True
```

### Ce qu'une séance contient

```
2026-09-18_143000_basilic/
    signal.wav          le signal brut, 24 bits, à la cadence réelle
    mesures.csv         t, tension, ligne de base, bruit, dérive, événements
    evenements.csv      instant, amplitude, durée
    notes.csv           instant, hauteur MIDI, vélocité, valeur d'origine
    enonces.csv         le mode Parole, avec les valeurs qui l'ont déclenché
    seance.json         plante, lieu, cadence, PLEINE ÉCHELLE, réglages
    musique.wav         le rendu sonore
```

> **`seance.json` contient la pleine échelle.** Si votre format perd cette
> information, il produit un fichier joli et inexploitable. Recopiez-la.

### N'écrivez que dans `cible`

Le dossier de la séance appartient à l'utilisateur. Si vous avez besoin
d'écrire plusieurs fichiers, dérivez-les de `cible` :

```python
os.path.splitext(cible)[0] + "-metadonnees.json"
```

---

## Source

Fournit un flux de mesure. **La plus délicate.**

```python
LIBELLE = "Ma carte"        # dans la liste des sources d'acquisition

def ouvrir(self, contexte):
    self._port = ...
    return True             # faux si l'ouverture a échoué

def lire(self):
    """Un bloc d'échantillons EN VOLTS, ou None s'il n'y a rien."""
    brut = self._port.read(...)
    return np.frombuffer(brut, dtype=np.int32) * self._volts_par_unite

def fermer(self):
    self._port.close()
```

> **Vous êtes sur le chemin des données.** Le logiciel vous isole des fautes,
> mais il ne peut pas vous isoler du temps que vous prenez. Une source lente
> fait tomber des échantillons, et cela ne se rattrape pas.
>
> Concrètement : pas d'allocation dans `lire()`, pas de journalisation à
> chaque bloc, pas de calcul. Vous lisez et vous rendez.

### La conversion en volts

`lire()` rend des **volts**, pas des unités arbitraires. C'est vous qui
connaissez l'étalonnage de votre matériel ; le logiciel ne peut pas le
deviner, et un signal sans échelle n'est pas une mesure.

---

## Fournir plusieurs capacités

```python
class MonModule(Module, Analyseur, Descripteur):
    MANIFESTE = Manifeste(
        nom="mon-module", api="1.0",
        capacites=(Capacite.ANALYSEUR, Capacite.DESCRIPTEUR),
    )

    def analyser(self, x, fs, contexte): ...
    def decrire(self, x, fs, contexte): ...
```

Attention : `FENETRE_S` et `SIGNAL_BRUT` sont **communs** aux deux. Si vos
deux capacités ont des besoins différents, écrivez deux modules — ils peuvent
partager du code par un fichier voisin.

---

**Suite :** [4. Les événements](04-evenements.md)
