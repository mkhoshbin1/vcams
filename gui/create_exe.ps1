# Windows batch file used for creating an executable using PyInstaller.
# Note that:
#   1. All dependencies and PyInstaller must be installed using pip.
#   1. UPX must be installed.
#      It's available in chocolatey or at https://github.com/upx/upx/tree/v3.96.

# Use --console and run the executable in cmd when debugging.

..\venv312\Scripts\Activate.ps1
pyrcc5 .\resources\main_gui_resources.qrc -o main_gui_resources.py

$exe_name = python create_versionfile.py

pyi-makespec --onefile --noupx --windowed `
    --add-data 'main_window.ui;.' `
    --add-data 'resources\main_gui_resources.qrc;.\resources\' `
    --hidden-import=pyi_splash `
    --icon='.\resources\icon.ico' `
    --splash='.\resources\splash.png' `
    --version='versionfile.txt' `
    --paths .. `
    --name "$exe_name" `
    main_gui.py

(Get-Content "$exe_name.spec") -Replace 'text_pos=None', 'text_pos=(25, 440)' |
Set-Content "$exe_name.spec"

pyinstaller --clean --noconfirm "$exe_name.spec"

Remove-Item 'versionfile.txt', "$exe_name.spec"

pause