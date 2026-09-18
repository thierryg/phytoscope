;  ==========================================================================
;  PhytoScope — attribution — packaging/gabarits/windows/phytoscope.nsi
;
;  Version  : 1.5.1
;  Date     : 2026-09-18
;  Éditeur  : Bretagne Namasté
;  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
;  Site     : https://bretagne-namaste.com
;  Contact  : contact@bretagne-namaste.com
;  Licence  : MIT — voir LICENCE.txt
;
;  SPDX-License-Identifier: MIT
;  fin de l'attribution
;  ==========================================================================

; ===========================================================================
;  PhytoScope — script d'installation NSIS (Windows 10 et 11)
;
;  Compilé depuis Debian/Ubuntu/Mint par « makensis », que NSIS fournit aussi
;  sous Linux : l'exécutable d'installation se fabrique donc sans machine
;  Windows. Les jetons @…@ sont remplacés par packaging/construire.py.
; ===========================================================================
Unicode true
SetCompressor /SOLID lzma

!define NOM       "PhytoScope"
!define VERSION   "@VERSION@"
!define EDITEUR   "@ATTRIBUTION@"
!define SITE      "@SITE@"

Name "${NOM} ${VERSION}"
OutFile "@SORTIE@"
InstallDir "$LOCALAPPDATA\${NOM}"
InstallDirRegKey HKCU "Software\${NOM}" "InstallDir"
;  Installation dans le profil de l'utilisateur : aucun privilège
;  administrateur n'est demandé. C'est délibéré — un logiciel de mesure n'a
;  rien à faire dans « Program Files », et beaucoup d'ateliers et de salles de
;  classe ne donnent pas les droits d'administration.
RequestExecutionLevel user
ShowInstDetails show
ShowUnInstDetails show

!include "MUI2.nsh"
!define MUI_ABORTWARNING
!define MUI_ICON "@ICONE@"
!define MUI_UNICON "@ICONE@"
!define MUI_FINISHPAGE_RUN "$INSTDIR\PhytoScope.cmd"
!define MUI_FINISHPAGE_RUN_TEXT "Lancer PhytoScope maintenant"
;  Cochee par defaut : on vient d'installer, on veut voir. La case reste
;  decochable pour qui installe sur une machine qu'il prepare pour autrui.
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\LISEZ-MOI.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Lire le manuel"
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED

!insertmacro MUI_PAGE_LICENSE "@FICHIER_LICENCE@"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"

Section "PhytoScope" SecPrincipale
    SectionIn RO
    SetOutPath "$INSTDIR"
    File /r "@CHARGE@\*.*"

    WriteRegStr HKCU "Software\${NOM}" "InstallDir" "$INSTDIR"
    WriteUninstaller "$INSTDIR\Desinstaller.exe"

    ;  Panneau « Applications et fonctionnalités ».
    !define DESINST "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NOM}"
    WriteRegStr   HKCU "${DESINST}" "DisplayName"     "${NOM} ${VERSION}"
    WriteRegStr   HKCU "${DESINST}" "DisplayVersion"  "${VERSION}"
    WriteRegStr   HKCU "${DESINST}" "Publisher"       "${EDITEUR}"
    WriteRegStr   HKCU "${DESINST}" "URLInfoAbout"    "${SITE}"
    WriteRegStr   HKCU "${DESINST}" "DisplayIcon"     "$INSTDIR\phytoscope.ico"
    WriteRegStr   HKCU "${DESINST}" "UninstallString" "$INSTDIR\Desinstaller.exe"
    WriteRegDWORD HKCU "${DESINST}" "NoModify" 1
    WriteRegDWORD HKCU "${DESINST}" "NoRepair" 1

    CreateDirectory "$SMPROGRAMS\${NOM}"
    CreateShortCut "$SMPROGRAMS\${NOM}\${NOM}.lnk" \
        "$INSTDIR\PhytoScope.cmd" "" "$INSTDIR\phytoscope.ico"
    CreateShortCut "$SMPROGRAMS\${NOM}\Diagnostic.lnk" \
        "$INSTDIR\Diagnostic.cmd" "" "$INSTDIR\phytoscope.ico"
    CreateShortCut "$SMPROGRAMS\${NOM}\Desinstaller.lnk" \
        "$INSTDIR\Desinstaller.exe"
SectionEnd

;  L'icone du Bureau est une section A PART, donc une case a cocher sur la
;  page des composants : certains la veulent, d'autres trouvent qu'un bureau
;  encombre est une nuisance. Poser la question coute trois lignes et evite
;  les deux reproches. Cochee par defaut, car c'est ce qu'attend la plupart.
Section "Icone sur le Bureau" SecBureau
    CreateShortCut "$DESKTOP\${NOM}.lnk" \
        "$INSTDIR\PhytoScope.cmd" "" "$INSTDIR\phytoscope.ico"
SectionEnd

;  Ce que chaque case explique quand on la survole.
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecPrincipale} \
    "Le logiciel, son interpreteur Python et ses bibliotheques. Indispensable."
!insertmacro MUI_DESCRIPTION_TEXT ${SecBureau} \
    "Ajoute un raccourci sur le Bureau. Le raccourci du menu Demarrer est \
pose dans tous les cas."
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
    ;  Les réglages de l'utilisateur vivent dans %APPDATA%\PhytoScope et ne
    ;  sont PAS effacés : une désinstallation n'est pas une demande d'oubli.
    ;  Le message ci-dessous dit où ils sont, pour qui veut les retirer.
    RMDir /r "$INSTDIR"
    Delete "$DESKTOP\${NOM}.lnk"
    RMDir /r "$SMPROGRAMS\${NOM}"
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${NOM}"
    DeleteRegKey HKCU "Software\${NOM}"
    MessageBox MB_OK|MB_ICONINFORMATION \
        "PhytoScope est désinstallé.$\r$\n$\r$\nVos réglages et vos séances \
sont conservés dans :$\r$\n    %APPDATA%\${NOM}$\r$\n    %USERPROFILE%\Documents\${NOM}"
SectionEnd
