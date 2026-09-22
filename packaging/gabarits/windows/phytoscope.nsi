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
;  Windows. Les jetons @…@ sont remplacés par packaging/build.py.
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
!include "LogicLib.nsh"
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

;  Le choix de la langue, AVANT TOUT LE RESTE - licence comprise, qui sera
;  donc lue dans la langue retenue. NSIS sait le faire lui-meme :
;  MUI_LANGDLL_DISPLAY affiche la boite avant la premiere page.
;
;  On DEMANDE, on ne devine pas : la contrainte C-31 interdit la detection
;  automatique de la locale. NSIS propose par defaut celle du systeme, mais
;  la boite reste affichee et le choix appartient a qui installe.
;
;  Le choix est memorise sous HKCU, ce qui evite de reposer la question a la
;  mise a jour suivante, et ecrit dans reglages.json pour que PhytoScope le
;  reprenne.
!define MUI_LANGDLL_DISPLAY
!define MUI_LANGDLL_REGISTRY_ROOT "HKCU"
!define MUI_LANGDLL_REGISTRY_KEY "Software\${NOM}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "Langue"

!insertmacro MUI_PAGE_LICENSE "@FICHIER_LICENCE@"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;  Les onze langues du logiciel. L'ordre compte : NSIS retient la PREMIERE
;  comme langue de repli quand celle du systeme n'est pas dans la liste.
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "Portuguese"
!insertmacro MUI_LANGUAGE "Italian"
!insertmacro MUI_LANGUAGE "Indonesian"
!insertmacro MUI_LANGUAGE "Russian"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "Korean"
!insertmacro MUI_LANGUAGE "Arabic"

;  La boite de choix doit etre reservee APRES la declaration des langues :
;  elle enumere celles qui sont compilees dans l'executable.
Function .onInit
    !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

Function un.onInit
    !insertmacro MUI_UNGETLANGUAGE
FunctionEnd

;  Le code a deux lettres qui correspond a la langue retenue, pour l'ecrire
;  dans reglages.json. NSIS ne travaille qu'avec des identifiants numeriques
;  (« $LANGUAGE ») : cette table est la traduction vers ce que PhytoScope lit.
!macro CodeLangue sortie
    StrCpy ${sortie} "fr"
    ${If} $LANGUAGE == ${LANG_ENGLISH}
        StrCpy ${sortie} "en"
    ${ElseIf} $LANGUAGE == ${LANG_SPANISH}
        StrCpy ${sortie} "es"
    ${ElseIf} $LANGUAGE == ${LANG_PORTUGUESE}
        StrCpy ${sortie} "pt"
    ${ElseIf} $LANGUAGE == ${LANG_ITALIAN}
        StrCpy ${sortie} "it"
    ${ElseIf} $LANGUAGE == ${LANG_INDONESIAN}
        StrCpy ${sortie} "id"
    ${ElseIf} $LANGUAGE == ${LANG_RUSSIAN}
        StrCpy ${sortie} "ru"
    ${ElseIf} $LANGUAGE == ${LANG_SIMPCHINESE}
        StrCpy ${sortie} "zh"
    ${ElseIf} $LANGUAGE == ${LANG_JAPANESE}
        StrCpy ${sortie} "ja"
    ${ElseIf} $LANGUAGE == ${LANG_KOREAN}
        StrCpy ${sortie} "ko"
    ${ElseIf} $LANGUAGE == ${LANG_ARABIC}
        StrCpy ${sortie} "ar"
    ${EndIf}
!macroend

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

    ;  Cache de bytecode. Le paquet Windows embarque l'interpreteur et les
    ;  bibliotheques deja depliees, sans le moindre .pyc : Python les
    ;  recompilerait au premier demarrage, et l'attente se voit — quelques
    ;  secondes pour Qt et NumPy. On le fait ici, une fois.
    ;
    ;  DetailPrint pour que l'utilisateur sache pourquoi cela prend un moment.
    ;  Aucune verification de code de retour : un module illisible ne doit pas
    ;  faire echouer une installation reussie.
    DetailPrint "Preparation du cache de bytecode (demarrages plus rapides)..."
    nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m compileall -q "$INSTDIR\phytoscope"'
    nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m compileall -q "$INSTDIR\run.py"'
    nsExec::ExecToLog '"$INSTDIR\python\python.exe" -m compileall -q "$INSTDIR\python\Lib\site-packages"'

    ;  La langue choisie devient celle de PhytoScope. Le logiciel lit
    ;  « ui.language » dans reglages.json a chaque demarrage : on l'y ecrit
    ;  une fois, plutot que de faire refaire dans le logiciel le choix qu'on
    ;  vient de faire ici.
    ;
    ;  On passe par Python plutot que par des ecritures NSIS : un JSON se
    ;  relit et se fusionne - une reinstallation ne doit pas effacer les
    ;  reglages de qui s'en sert.
    !insertmacro CodeLangue $R0
    DetailPrint "Langue de PhytoScope : $R0"
    nsExec::ExecToLog '"$INSTDIR\python\python.exe" "$INSTDIR\app\write_language.py" "$R0"'
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
