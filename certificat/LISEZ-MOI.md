# Le certificat de signature

Ce dossier porte la **copie de travail** du certificat qui signe les paquets
de PhytoScope. La copie de référence, elle, vit dans
`~/.local/share/phytoscope-signature/` et n'entre jamais dans le dépôt.

> **FICHIER GÉNÉRÉ** par `packaging/certificate.py`. Le modifier à la main
> serait perdu à la prochaine exécution (`C-45`).

## Ce qu'il y a ici

| Fichier | Nature | Dans le dépôt ? |
|---|---|---|
| `phytoscope-certificat.pem` | certificat **public**, commenté | **oui** — c'est lui qu'on diffuse |
| `phytoscope.crt` | le même, brut | **oui** |
| `phytoscope.key` | **la clé privée** | **non, jamais** |
| `LISEZ-MOI.md` | ce fichier | oui |

Le certificat public **doit** se diffuser : c'est lui qui permet de vérifier
une signature. Le taire rendrait les signatures invérifiables.

## Empreinte SHA-256

```
57:3D:90:32:5C:16:14:B2:F3:B2:D9:81:68:82:7E:CE:E3:F6:D5:22:F7:B8:6D:0D:24:70:C6:80:7C:22:31:F0
```

C'est ce qu'on publie sur https://bretagne-namaste.com et ce que compare qui veut s'assurer
qu'un paquet vient bien de nous.

## Trois filets contre la publication de la clé

1. `.gitignore` écarte `certificat/phytoscope.key` nommément, puis `*.key`
   et `*.pem` partout, avec deux exceptions nommées pour les fichiers
   publics ;
2. le crochet `pre-commit` « detection-cle-privee » la refuse **sur son seul
   nom** — même vide, même renommée ;
3. le job « secrets » de l'intégration continue échoue si un fichier de ce
   genre est suivi.

Trois filets parce qu'une clé publiée ne se dépublie pas.

> `.gitignore` protège de `git`, **pas d'une sauvegarde ni d'une archive du
> dossier**. Si vous archivez ce dépôt, excluez `certificat/phytoscope.key`.

## Recréer, déposer, vérifier

```bash
python3 packaging/certificate.py              # l'état, sans rien changer
python3 packaging/certificate.py --creer      # créer s'il n'existe pas
python3 packaging/certificate.py --deposer    # re-remplir ce dossier
python3 packaging/certificate.py --verifier   # les deux copies concordent ?
```

**Ne refaites pas le certificat sans raison.** `--refaire` remplace la clé, et
rompt le lien avec tout ce qui a déjà été signé : les paquets publiés
deviennent invérifiables avec le nouveau certificat, et qui avait noté
l'empreinte en voit soudain une autre.

## Ce que ce certificat prouve, et ce qu'il ne prouve pas

Il est **auto-signé**. Il prouve l'**intégrité** d'un paquet et la
**continuité d'origine** : deux paquets signés par la même clé viennent bien
du même endroit.

Il ne fait **pas** taire SmartScreen sous Windows ni Gatekeeper sous macOS,
et n'a jamais prétendu le faire (`C-2Q`). Cela demanderait un certificat
d'une autorité reconnue, payant et nominatif.

---

Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com
