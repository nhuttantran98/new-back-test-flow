@echo off
setlocal enabledelayedexpansion


set "NAME=%~1"
set "JFROG_URL=%~2"
set "JFROG_REPO=%~3"
set "JFROG_ACCESS_TOKEN=%~4"

if "!NAME!"=="" (
    echo Missing NAME
    exit /b 1
)

echo Upload test result for: "%NAME%"
echo URL: %JFROG_URL%
echo Repo: %JFROG_REPO%

REM --- Virtual env unchanged ---
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate"
) else (
    echo Creating virtual environment...
    py -m venv .venv
    call ".venv\Scripts\activate"
    py -m pip install --upgrade pip
    py -m pip install requests dotenv
)

REM ✅ RUN Python uploader with ARGS:
py -m jfrog_uploader ^
    "--artifact_result=.\..\project\test-results\%NAME%" ^
    "--json_result=.\..\project\test-results\test-results.json" ^
    "--dest=test/testreport/ws/WS_1.21.0" ^
    "--base-url=%JFROG_URL%" ^
    "--repo=%JFROG_REPO%" ^
    "--access-token=%JFROG_ACCESS_TOKEN%"

endlocal
