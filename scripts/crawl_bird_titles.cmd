@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT_DIR=%%~fI"

set "CRAWLER=%ROOT_DIR%\scripts\crawl_from_wikipedia.py"
set "INPUT_FILE=%ROOT_DIR%\data\bird_titles.csv"

if not exist "%CRAWLER%" (
  echo [error] crawler script not found: "%CRAWLER%"
  exit /b 1
)

if not exist "%INPUT_FILE%" (
  echo [error] input file not found: "%INPUT_FILE%"
  exit /b 1
)

set "PYTHON_CMD="
python --version >nul 2>nul
if not errorlevel 1 (
  set "PYTHON_CMD=python"
)

if not defined PYTHON_CMD (
  py -3 --version >nul 2>nul
  if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
  )
)

if not defined PYTHON_CMD (
  echo [error] python not found in PATH
  exit /b 1
)

echo [run] input file: "%INPUT_FILE%"
echo [run] crawler: "%CRAWLER%"
echo [run] extra args: %*

call %PYTHON_CMD% "%CRAWLER%" --input-file "%INPUT_FILE%" --build-json %*
exit /b %errorlevel%
