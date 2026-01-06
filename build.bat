@echo off
chcp 65001 > nul
title HanaKiosk Build Tool

:menu
echo.
echo ============================================================
echo   HanaKiosk / SuperKioskBuilder Build Tool
echo ============================================================
echo.
echo   1. Build All (HanaKiosk + SuperKioskBuilder)
echo   2. Build HanaKiosk only
echo   3. Build SuperKioskBuilder only
echo   4. Build All + GitHub Release
echo   5. Exit
echo.

set /p choice="Select (1-5): "

if "%choice%"=="1" goto build_all
if "%choice%"=="2" goto build_kiosk
if "%choice%"=="3" goto build_builder
if "%choice%"=="4" goto build_all_deploy
if "%choice%"=="5" goto end

echo Invalid selection.
goto menu

:build_kiosk
echo.
echo ============================================================
echo   [Building HanaKiosk]
echo ============================================================

if not exist "super-kiosk-online.spec" (
    echo [ERROR] super-kiosk-online.spec not found.
    goto end
)

echo Cleaning previous build...
if exist "build\HanaKiosk" rmdir /s /q "build\HanaKiosk"

echo Running PyInstaller...
pyinstaller "super-kiosk-online.spec" --noconfirm

if %errorlevel% neq 0 (
    echo [ERROR] HanaKiosk build failed!
    goto end
)

if exist "dist\HanaKiosk.exe" (
    for %%A in ("dist\HanaKiosk.exe") do echo [OK] HanaKiosk.exe - %%~zA bytes
) else (
    echo [ERROR] HanaKiosk.exe was not created.
)

if "%choice%"=="1" goto build_builder
if "%choice%"=="4" goto build_builder
goto end

:build_builder
echo.
echo ============================================================
echo   [Building SuperKioskBuilder]
echo ============================================================

if not exist "kiosk-builder-app\run_gui.spec" (
    echo [ERROR] kiosk-builder-app\run_gui.spec not found.
    goto end
)

echo Cleaning previous build...
if exist "kiosk-builder-app\build\run_gui" rmdir /s /q "kiosk-builder-app\build\run_gui"

echo Running PyInstaller...
pushd kiosk-builder-app
pyinstaller "run_gui.spec" --noconfirm
popd

if %errorlevel% neq 0 (
    echo [ERROR] SuperKioskBuilder build failed!
    goto end
)

if exist "kiosk-builder-app\dist\SuperKioskBuilder.exe" (
    for %%A in ("kiosk-builder-app\dist\SuperKioskBuilder.exe") do echo [OK] SuperKioskBuilder.exe - %%~zA bytes

    if not exist "release" mkdir release
    copy /y "kiosk-builder-app\dist\SuperKioskBuilder.exe" "release\" > nul
    echo [COPY] release\SuperKioskBuilder.exe
) else (
    echo [ERROR] SuperKioskBuilder.exe was not created.
)

if exist "dist\HanaKiosk.exe" (
    if not exist "release" mkdir release
    copy /y "dist\HanaKiosk.exe" "release\" > nul
    echo [COPY] release\HanaKiosk.exe
)

if "%choice%"=="4" goto deploy
goto end

:build_all
goto build_kiosk

:build_all_deploy
goto build_kiosk

:deploy
echo.
echo ============================================================
echo   [GitHub Release]
echo ============================================================

where gh >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] GitHub CLI not installed.
    echo         Install: winget install GitHub.cli
    goto end
)

gh auth status >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] GitHub auth required.
    echo         Run: gh auth login
    goto end
)

set "version="
set /p version="Version tag (e.g. v1.0.3, Enter=auto): "

if "%version%"=="" (
    for /f "delims=" %%i in ('powershell -NoProfile -Command "Get-Date -Format 'vyyyy.MM.dd'"') do set "version=%%i"
)

echo.
echo Version: %version%
echo.

set REPO=Hana-EventTech-Labs/kiosk_builder

if not exist "release\HanaKiosk.exe" (
    echo [ERROR] release\HanaKiosk.exe not found.
    goto end
)
if not exist "release\SuperKioskBuilder.exe" (
    echo [ERROR] release\SuperKioskBuilder.exe not found.
    goto end
)

echo Checking existing release...
gh release view %version% --repo %REPO% >nul 2>nul
if %errorlevel% equ 0 (
    echo Deleting existing release %version%...
    gh release delete %version% --repo %REPO% --yes
    git push origin --delete %version% 2>nul
)

echo Creating release...

gh release create %version% "release\HanaKiosk.exe" "release\SuperKioskBuilder.exe" --repo %REPO% --title "Release %version%" --notes "HanaKiosk Release - Kiosk App and Config Tool"

if %errorlevel% equ 0 (
    echo.
    echo ============================================================
    echo   [OK] GitHub Release Success!
    echo ============================================================
    echo.
    echo   URL: https://github.com/%REPO%/releases/tag/%version%
    echo.
) else (
    echo [ERROR] GitHub Release failed.
)

goto end

:end
echo.
pause
