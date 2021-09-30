:: Windows batch file used for creating an executable using PyInstaller.
:: Note that:
::   1. All dependencies and PyInstaller must be installed using pip.
::   1. UPX must be installed.
::      It's available in chocolatey or at https://github.com/upx/upx/tree/v3.96.
:: --noupx

pyinstaller --onefile --clean --windowed ^
    --icon="NONE" ^
    --splash=".\resources\splash.png" ^
    --paths .. ^
    --name simple ^
    main_gui.py

pause