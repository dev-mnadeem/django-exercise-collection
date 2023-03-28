@echo off
REM Create a virtualenv, install dependencies, migrate and load the demo data.
REM Safe to re-run: the seed command is idempotent.

setlocal
if "%VENV_DIR%"=="" set VENV_DIR=.venv

echo Setting up venv in %VENV_DIR%...
python -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt

echo Migrating...
python manage.py migrate --noinput
if errorlevel 1 exit /b 1

echo Loading demo data...
python manage.py seed_demo_data
if errorlevel 1 exit /b 1

echo.
echo Done. Activate the venv with: %VENV_DIR%\Scripts\Activate.ps1
echo Then run the API with:        python manage.py runserver
