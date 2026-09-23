#  ==========================================================================
#  PhytoScope — attribution — packaging/templates/fedora/phytoscope.spec
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

# ===========================================================================
#  PhytoScope — gabarit RPM (Fedora, Red Hat, Rocky, AlmaLinux, CentOS)
#
#  Construit depuis Debian/Ubuntu/Mint par « packaging/build.py --rpm ».
#  Les jetons @…@ sont remplacés par le script ; ce fichier n'est jamais
#  utilisé tel quel.
# ===========================================================================
Name:           phytoscope
Version:        @VERSION@
Release:        @RELEASE@%{?dist}
Summary:        Listen to, measure and record plant signals
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
PhytoScope measures the variations in a plant's electrical potential and
makes them audible. It brings together an oscilloscope, a multimeter, a
spectrum analyzer, a plotter, musical sonification and a speech mode.

The software starts with no hardware attached: an internal generator takes
over, so you can explore the whole thing before buying anything. With a
PhytoSense One board, a sound card or a plain serial rig, it measures for
real.

Every representation states what it assumes and what it does not let you
conclude. The software claims neither to translate a plant nor to identify
one.

Published by @EDITEUR@ (@SITE@), written by @AUTEUR@.

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
install -m 0755 usr/bin/phytoscope-desktop-icon %{buildroot}%{_bindir}/phytoscope-desktop-icon
install -m 0755 usr/bin/phytoscope-uninstall %{buildroot}%{_bindir}/phytoscope-uninstall
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
%license usr/share/phytoscope/LICENSE.txt
%doc usr/share/phytoscope/README.txt usr/share/phytoscope/CHANGELOG.txt
%{_datadir}/phytoscope
%{_bindir}/phytoscope
%{_bindir}/phytoscope-desktop-icon
%{_bindir}/phytoscope-uninstall
%{_datadir}/applications/phytoscope.desktop
%{_datadir}/icons/hicolor/scalable/apps/phytoscope.svg

%changelog
* @DATE_RPM@ @RESPONSABLE@ - @VERSION@-@RELEASE@
- Voir CHANGELOG.txt pour le détail des versions.
