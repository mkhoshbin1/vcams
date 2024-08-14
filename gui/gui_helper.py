"""Various helper classes and functions for use in the GUI."""

# The pyi_splash module is only included when using PyInstaller.
try:
    # noinspection PyUnresolvedReferences
    import pyi_splash
except ImportError:
    is_pyi_splash_available = False
else:
    is_pyi_splash_available = True


def splash_update_text(msg):
    if is_pyi_splash_available and pyi_splash.is_alive:
        pyi_splash.update_text(msg)


def splash_close():
    if is_pyi_splash_available and pyi_splash.is_alive:
        pyi_splash.close()
