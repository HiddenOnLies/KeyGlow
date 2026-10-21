"""Entrada de KeyGlow.exe (PyInstaller necesita un script, no un módulo)."""

import sys

from keyglow.app.main import main

if __name__ == "__main__":
    sys.exit(main())
