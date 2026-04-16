@echo off
chcp 65001 >nul
echo.
echo  ═══════════════════════════════════════════
echo   SexytexBDO Launcher — Build Script
echo  ═══════════════════════════════════════════
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause & exit /b 1
)

:: Install/upgrade PyInstaller
echo [1/4] Installing PyInstaller...
pip install pyinstaller --quiet --upgrade
if errorlevel 1 (
    echo [ERROR] pip failed.
    pause & exit /b 1
)

:: Clean previous build
echo [2/4] Cleaning previous build...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

:: Build (onedir mode — exe + _internal\ in one folder)
echo [3/4] Building...
if not exist "assets\icon.ico" (
    echo [ERROR] File not found - assets\icon.ico
    pause & exit /b 1
)

python -m PyInstaller SexytexBdoLauncher.spec --noconfirm --clean
if errorlevel 1 (
    echo.
    echo [ERROR] Build failed. Check output above.
    pause & exit /b 1
)

:: Copy assets into the dist folder alongside the exe
echo [4/4] Copying assets...
if not exist "dist\SexytexBdoLauncher\" (
    echo [ERROR] Output folder not found: dist\SexytexBdoLauncher\
    pause & exit /b 1
)

if not exist "assets\nvidiaProfileInspector\" (
    echo [ERROR] File not found - assets\nvidiaProfileInspector
    pause & exit /b 1
)
if not exist "assets\profiles\" (
    echo [ERROR] File not found - assets\profiles
    pause & exit /b 1
)

xcopy /E /I /Y "assets\nvidiaProfileInspector" "dist\SexytexBdoLauncher\nvidiaProfileInspector\" >nul
xcopy /E /I /Y "assets\profiles"               "dist\SexytexBdoLauncher\profiles\"               >nul

echo.
echo  ✓ Build complete!
echo.
echo  Output folder: dist\SexytexBdoLauncher\
echo    SexytexBdoLauncher.exe   (the launcher)
echo    _internal\               (Python runtime; must travel with exe)
echo    nvidiaProfileInspector\
echo    profiles\
echo.
echo  To distribute: zip the entire dist\SexytexBdoLauncher\ folder.
echo  The exe works from any location as long as the folder contents stay together.
echo.
pause
