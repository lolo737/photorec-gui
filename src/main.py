"""
main.py: entry point.  Run with:  python3 src/main.py
"""

import sys

if sys.version_info < (3, 8):
    sys.exit("PhotoRec Recovery GUI needs Python 3.8 or newer.")

try:
    import tkinter  # noqa: F401
except ImportError:
    sys.exit(
        "Tkinter isn't available in this Python.\n"
        "macOS: install Python from python.org (bundles Tk 8.6), or  brew install python-tk\n"
        "Linux: sudo apt install python3-tk"
    )

from gui import App


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
