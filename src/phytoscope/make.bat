rem  ==========================================================================
rem  PhytoScope  attribution  src/phytoscope/make.bat
rem
rem  Version   : 1.6.0
rem  Date      : 2026-09-23
rem  Publisher : Bretagne Namaste
rem  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
rem  Website   : https://bretagne-namaste.com
rem  Contact   : contact@bretagne-namaste.com
rem  License   : MIT  see LICENSE.txt
rem
rem  SPDX-License-Identifier: MIT
rem  end of attribution
rem  ==========================================================================

@echo off
REM ==========================================================================
REM  PhytoScope — equivalent du Makefile pour l'invite de commandes Windows
REM  Usage :  make install  ^|  make run  ^|  make demo  ^|  make doctor
REM ==========================================================================
setlocal
set VENV=.venv
set PY=%VENV%\Scripts\python.exe

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="install" goto install
if "%1"=="run" goto run
if "%1"=="demo" goto demo
if "%1"=="test" goto test
if "%1"=="doctor" goto doctor
if "%1"=="check" goto check
if "%1"=="clean" goto clean
goto help

:help
echo.
echo   PhytoScope - ecoute et mesure des signaux vegetaux
echo   -------------------------------------------------
echo.
echo   make install    environnement virtuel + dependances
echo   make run        lance le logiciel
echo   make demo       lance le logiciel sans materiel
echo   make test       execute les tests
echo   make doctor     diagnostic d'installation
echo   make clean      nettoie les fichiers temporaires
echo.
goto end

:install
if not exist %VENV% python -m venv %VENV%
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto :erreur_deps
echo   dependances facultatives ^(leur echec est sans gravite^)
%PY% -m pip install -r requirements-optionnel.txt
echo.
echo Installation terminee. Lancez : make run
goto end

:erreur_deps
echo.
echo ECHEC : les dependances indispensables n'ont pas pu etre installees.
echo Verifiez votre connexion, puis relancez : make install
goto end

:run
%PY% run.py
goto end

:demo
%PY% run.py --simulation
goto end

:test
%PY% -m pytest tests -q
goto end

:doctor
python tools\doctor.py
goto end

:check
python tools\check_syntax.py
goto end

:clean
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
if exist .pytest_cache rd /s /q .pytest_cache
goto end

:end
endlocal
