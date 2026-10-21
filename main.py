"""SlipSurfaceIQ Settle — start the desktop application.

Run from an IDE (open this file and press Run) or from a terminal:

    python main.py                                          # the window, default project
    python main.py slipsurface/settle/examples/strip_on_sand.settle   # open a project
    python main.py run project.settle -o report.pdf         # batch: analyse and report
    python main.py study project.settle -o samples.csv      # batch: run the study
    python main.py example -o project.settle                # write a starter project
    python main.py --check                                  # dependency check, no window

Works from any working directory: the project folder is put on sys.path, so
no installation is required (``pip install -e .`` is optional).
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REQUIRED = {
    "PySide6": "PySide6",
    "numpy": "numpy",
    "matplotlib": "matplotlib",
    "reportlab": "reportlab",
    "qtawesome": "QtAwesome",
}
OPTIONAL = {"docx": "python-docx", "openpyxl": "openpyxl"}
MIN_PYTHON = (3, 10)


def check_environment(verbose: bool = True) -> bool:
    """Verify Python version and required packages; print a readable report."""
    ok = True
    if sys.version_info < MIN_PYTHON:
        print(
            f"[ERROR] Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required "
            f"(found {sys.version.split()[0]})."
        )
        ok = False
    missing = []
    for mod, pip_name in {**REQUIRED, **OPTIONAL}.items():
        try:
            m = importlib.import_module(mod)
            if verbose:
                print(f"  {mod:10s} {getattr(m, '__version__', '?')}")
        except ImportError:
            if mod in REQUIRED:
                missing.append(pip_name)
            elif verbose:
                print(f"  {mod:10s} not installed (optional: {pip_name})")
    if missing:
        ok = False
        print("[ERROR] Missing package(s): " + ", ".join(missing))
        print(
            f"        Install:  {Path(sys.executable).name} -m pip install -r "
            f"{ROOT / 'requirements.txt'}"
        )
    if ok and verbose:
        print(f"  Python     {sys.version.split()[0]}  ({sys.executable})")
        print("Environment ready.")
    return ok


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--check"]:
        return 0 if check_environment() else 1
    if not check_environment(verbose=False):
        return 1
    # HiDPI: crisp rendering on scaled Windows displays
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    # A project path relative to this folder works from any working directory.
    if argv and argv[0].lower().endswith((".settle", ".json")):
        path = Path(argv[0])
        if not path.is_absolute() and not path.exists() and (ROOT / path).exists():
            argv[0] = str(ROOT / path)

    from slipsurface.settle.cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    sys.exit(main())
