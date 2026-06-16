import sys
from pathlib import Path


def setup_import_path() -> Path:
    """Añade la raíz del proyecto al sys.path para imports desde agents/."""
    root = Path(__file__).resolve().parents[2]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root
