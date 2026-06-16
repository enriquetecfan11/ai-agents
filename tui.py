"""Atajo visual. Equivalente a: python main.py tui"""

import sys

from agents.paths import setup_import_path

setup_import_path()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv = ["main.py", "tui"]
    from main import main

    main()
