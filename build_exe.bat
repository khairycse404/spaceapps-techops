@echo off
echo ========================================================
echo  Building Tech Ops Room Inspector Standalone .EXE
echo ========================================================
cd /d "%~dp0"
python -m pip install pyinstaller requests
python -m PyInstaller --noconfirm --onedir --windowed --name "TechOps_RoomInspector" check_room.py
echo.
if exist "dist\TechOps_RoomInspector\TechOps_RoomInspector.exe" (
    copy config.json "dist\TechOps_RoomInspector\" >nul 2>&1
    echo [SUCCESS] Standalone EXE created in: dist\TechOps_RoomInspector\TechOps_RoomInspector.exe
    echo You can zip that folder and send it to your team!
) else (
    echo [ERROR] Build failed. Check the errors above.
)
pause
