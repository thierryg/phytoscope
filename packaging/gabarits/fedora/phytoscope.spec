#  ==========================================================================
#  PhytoScope — attribution — packaging/gabarits/fedora/phytoscope.spec
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

# ===========================================================================
#  PhytoScope — gabarit RPM (Fedora, Red Hat, Rocky, AlmaLinux, CentOS)
#
#  Construit depuis Debian/Ubuntu/Mint par « packaging/construire.py --rpm ».
#  Les jetons @…@ sont remplacés par le script ; ce fichier n'est jamais
#  utilisé tel quel.
# ===========================================================================
Name:           phytoscope
Version:        @VERSION@
Release:        @RELEASE@%{?dist}
Summary:        Écoute, mesure et enregistrement des signaux végétaux
License:        MIT
URL:            @SITE@
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3 >= 3.9
Requires:       python3-pip
#  Sans ces bibliothèques, Qt se charge puis échoue au premier affichage, et
#  le message du chargeur dynamique nomme rarement la bonne. Le paquet Debian
#  les déclarait déjà ; le .rpm ne les déclarait pas, et l'installation
#  paraissait réussie jusqu'au premier lancement.
Requires:       mesa-libGL
Requires:       mesa-libEGL
Requires:       libxkbcommon-x11
Requires:       xcb-util-cursor
Requires:       xcb-util-wm
Requires:       xcb-util-keysyms
Requires:       xcb-util-image
Requires:       xcb-util-renderutil
Requires:       fontconfig
Requires:       freetype
Requires:       dbus-libs
#  Audio : facultatif au sens du logiciel, mais son absence désactive
#  silencieusement l'entrée et la sortie son.
Recommends:     portaudio
Recommends:     espeak-ng
Recommends:     python3-numpy
Suggests:       python3-pyserial

#  Le contenu est déjà construit : rpmbuild n'a rien à compiler, et surtout
#  rien à réécrire. Sans ces deux lignes, il tenterait d'extraire des symboles
#  de débogage de fichiers Python et de réécrire les lignes « #! ».
%global debug_package %{nil}
%global __brp_mangle_shebangs %{nil}

%description
PhytoScope mesure les variations de potentiel électrique d'une plante et les
rend audibles. Il réunit un oscilloscope, un multimètre, un analyseur de
spectre, un traceur, une sonification musicale et un mode vocal.

Le logiciel démarre sans matériel : un générateur interne prend le relais, ce
qui permet de découvrir l'ensemble avant d'acheter quoi que ce soit. Avec une
carte PhytoSense One, une carte son ou un simple montage série, il mesure pour
de bon.

Chaque représentation affiche ce qu'elle suppose et ce qu'elle ne permet pas de
conclure. Le logiciel ne prétend ni traduire une plante, ni l'identifier.

Publié par @EDITEUR@ (@SITE@), écrit par @AUTEUR@.

%prep
%setup -q

%build
# Rien à compiler : le logiciel est en Python pur.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_datadir}/phytoscope
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp -a usr/share/phytoscope/. %{buildroot}%{_datadir}/phytoscope/
install -m 0755 usr/bin/phytoscope %{buildroot}%{_bindir}/phytoscope
install -m 0755 usr/bin/phytoscope-icone-bureau %{buildroot}%{_bindir}/phytoscope-icone-bureau
install -m 0755 usr/bin/phytoscope-desinstaller %{buildroot}%{_bindir}/phytoscope-desinstaller
install -m 0644 usr/share/applications/phytoscope.desktop \
        %{buildroot}%{_datadir}/applications/phytoscope.desktop
install -m 0644 usr/share/icons/hicolor/scalable/apps/phytoscope.svg \
        %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/phytoscope.svg

%post
#  Même raisonnement que pour le paquet Debian : un environnement Python privé,
#  parce que PySide6 n'est pas dans les dépôts de toutes les versions de
#  Fedora ni de Red Hat, et qu'on ne touche pas au Python du système.
CIBLE=%{_datadir}/phytoscope
if [ ! -d "$CIBLE/venv" ]; then
    python3 -m venv "$CIBLE/venv" 2>/dev/null || exit 0
fi
if [ -d "$CIBLE/roues" ] && [ -n "$(ls -A "$CIBLE/roues" 2>/dev/null)" ]; then
    "$CIBLE/venv/bin/pip" install --quiet --no-index --find-links "$CIBLE/roues" \
        -r "$CIBLE/requirements.txt" 2>/dev/null \
    || "$CIBLE/venv/bin/pip" install --quiet -r "$CIBLE/requirements.txt" || :
else
    "$CIBLE/venv/bin/pip" install --quiet -r "$CIBLE/requirements.txt" || :
fi
"$CIBLE/venv/bin/pip" install --quiet -r "$CIBLE/requirements-optionnel.txt" \
    >/dev/null 2>&1 || :

#  Cache de bytecode : sans lui, Python recompile à chaque démarrage tous les
#  modules dont le dossier n'est pas inscriptible — et l'attente se voit au
#  premier lancement. On le construit ici, une fois, tant qu'on a les droits.
"$CIBLE/venv/bin/python" -m compileall -q "$CIBLE/phytoscope" >/dev/null 2>&1 || :
"$CIBLE/venv/bin/python" -m compileall -q "$CIBLE/run.py" >/dev/null 2>&1 || :
"$CIBLE/venv/bin/python" -m compileall -q "$CIBLE/venv/lib" >/dev/null 2>&1 || :
exit 0

%postun
#  L'environnement virtuel n'appartient à aucun paquet : rpm l'ignore, donc
#  c'est à nous de l'effacer, sans quoi il survivrait à la désinstallation.
if [ $1 -eq 0 ]; then
    rm -rf %{_datadir}/phytoscope/venv
    #  Le bytecode produit après coup n'est pas listé dans %files : rpm ne le
    #  connaît pas, et sans cela il survivrait à la désinstallation.
    find %{_datadir}/phytoscope -name '__pycache__' -type d \
        -exec rm -rf {} + 2>/dev/null || :
fi
exit 0

%files
%license usr/share/phytoscope/LICENCE.txt
%doc usr/share/phytoscope/README.txt usr/share/phytoscope/CHANGELOG.txt
%{_datadir}/phytoscope
%{_bindir}/phytoscope
%{_bindir}/phytoscope-icone-bureau
%{_bindir}/phytoscope-desinstaller
%{_datadir}/applications/phytoscope.desktop
%{_datadir}/icons/hicolor/scalable/apps/phytoscope.svg

%changelog
* @DATE_RPM@ @RESPONSABLE@ - @VERSION@-@RELEASE@
- Voir CHANGELOG.txt pour le détail des versions.
