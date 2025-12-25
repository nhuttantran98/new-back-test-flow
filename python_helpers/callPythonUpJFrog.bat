@echo off
setlocal enabledelayedexpansion

REM === Arguments ===
set "NAME=%~1"
set "JFROG_URL=%~2"
set "JFROG_REPO=%~3"
set "JFROG_ACCESS_TOKEN=%~4"

if "!NAME!"=="" (
    echo [ERROR] Missing NAME
    exit /b 1
)

echo [INFO] Upload test result for: "%NAME%"
echo [INFO] URL: %JFROG_URL%
echo [INFO] Repo: %JFROG_REPO%

REM === Paths ===
REM This .bat is inside: root\python_helpers\your_script.bat
REM The venv folder is:   root\.venv
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
set "VENV_DIR=%ROOT_DIR%\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

REM === Ensure venv exists ===
if not exist "%VENV_PY%" (
    echo [INFO] Creating virtual environment at "%VENV_DIR%"...
    py -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        exit /b 1
    )
)

REM === Install required packages inside venv ===
echo [INFO] Upgrading pip...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 (
    echo [ERROR] pip upgrade failed.
    exit /b 1
)

echo [INFO] Installing required packages: requests, python-dotenv
"%VENV_PY%" -m pip install requests python-dotenv
if errorlevel 1 (
    echo [ERROR] Package installation failed.
    exit /b 1
)

REM === Build paths for uploader arguments ===
set "ARTIFACT_RESULT=%ROOT_DIR%\project\test-results\%NAME%"
set "JSON_RESULT=%ROOT_DIR%\project\test-results\test-results.json"
set "DEST=test/testreport/ws/WS_1.21.0"

REM === Run Python uploader within venv ===
echo [INFO] Running uploader...
"%VENV_PY%" -m jfrog_uploader ^
    "--artifact_result=%ARTIFACT_RESULT%" ^
    "--json_result=%JSON_RESULT%" ^
    "--dest=%DEST%" ^
    "--base-url=%JFROG_URL%" ^
    "--repo=%JFROG_REPO%" ^
    "--access-token=%JFROG_ACCESS_TOKEN%"

if errorlevel 1 (
    echo [ERROR] Uploader failed.
    exit /b 1
)

echo [INFO] Upload completed successfully.
endlocal
