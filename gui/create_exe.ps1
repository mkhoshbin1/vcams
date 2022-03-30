# Windows batch file used for creating an executable using PyInstaller.
# Note that:
#   1. All dependencies and PyInstaller must be installed using pip.
#   1. UPX must be installed.
#      It's available in chocolatey or at https://github.com/upx/upx/tree/v3.96.

# Use --console and run the executable in cmd when debugging.

..\venv\Scripts\Activate.ps1

pyinstaller --onefile --clean --noupx `
    --add-data 'main_window.ui;.' `
    --add-data 'resources\main_gui_resources.qrc;.\resources\' `
    --icon=".\resources\icon.ico" `
    --splash=".\resources\splash.png" `
    --paths .. `
    --name VCAMS `
    main_gui.py

#    VCAMS.spec
# 
#    --hidden-import scipy `
#    --hidden-import skimage `
#    --hidden-import uarray `
#    --collect-submodules numpy `
#    --collect-submodules scipy `
#    --collect-submodules skimage `
#    --collect-submodules uarray `
pause