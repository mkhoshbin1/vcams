# Windows batch file used for creating an executable using PyInstaller.
# Note that:
#   1. All dependencies and PyInstaller must be installed using pip.
#   1. UPX must be installed.
#      It's available in chocolatey or at https://github.com/upx/upx/tree/v3.96.

..\venv\Scripts\Activate.ps1

pyinstaller --onefile --clean --windowed `
    --add-data 'main_window.ui;.' `
    --icon=".\resources\icon.ico" `
    --splash=".\resources\splash.png" `
    --paths .. `
    --name VCAMS `
    main_gui.py
#    VCAMS.spec
# --noupx

pause