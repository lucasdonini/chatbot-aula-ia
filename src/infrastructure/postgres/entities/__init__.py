from importlib import import_module
from pathlib import Path

from .base import Base as Base

package_dir = Path(__file__).parent

for file in package_dir.glob("*.py"):
    if file.stem in {"__init__", "base"}:
        continue

    import_module(f"{__name__}.{file.stem}")
