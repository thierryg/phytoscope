# Certificat de signature de PhytoScope

| Fichier | Nature | Se diffuse ? |
|---|---|---|
| `phytoscope-certificat.pem` | certificat **public**, avec son empreinte en en-tête | **oui** |
| `phytoscope.crt` | le même, brut | **oui** |
| `phytoscope.key` | **clé privée** | **JAMAIS** |

La clé de référence vit dans `~/.local/share/phytoscope-signature/` ; les
fichiers présents ici en sont une copie de travail.

## Ce que `.gitignore` protège — et ce qu'il ne protège pas

`.gitignore` empêche la clé privée d'entrer dans un dépôt Git. Il **ne
protège pas** d'une sauvegarde du dossier, d'une archive `tar`, d'une
synchronisation dans un nuage, ni d'un partage du répertoire. La clé reste un
secret à traiter comme tel :

* ne la recopiez pas dans un dossier synchronisé ;
* excluez `certificat/phytoscope.key` de vos sauvegardes automatiques, ou
  chiffrez-les ;
* sur une machine partagée, protégez-la par une phrase de passe :

```bash
openssl rsa -aes256 -in phytoscope.key -out chiffree.key && mv chiffree.key phytoscope.key
```

## Si la clé fuit

Il n'y a pas de révocation possible pour un certificat auto-signé : personne
n'interroge de liste de révocation pour lui. La seule réponse est de
**générer un nouveau certificat**, d'en publier la nouvelle empreinte, et
d'annoncer que l'ancienne ne vaut plus :

```bash
cd packaging && python3 signature.py --refaire
```

## Si la clé est perdue

Les paquets déjà publiés restent vérifiables — leur certificat est diffusé
avec eux. Mais les versions suivantes seront signées par une autre clé, et
rien ne les rattachera aux précédentes. **Sauvegardez-la**, hors ligne.

## Vérifier un paquet

```bash
openssl cms -verify -binary -inform DER \
    -in <paquet>.p7s -content <paquet> \
    -certfile phytoscope-certificat.pem -noverify -out /dev/null
```

Et pour les exécutables Windows, sous Windows :

```powershell
Get-AuthenticodeSignature .\PhytoScope-1.5.1-Windows.exe
```

---

*Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com*
