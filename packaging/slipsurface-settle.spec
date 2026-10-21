# PyInstaller specification; built in an isolated environment on each target OS.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
datas = collect_data_files("slipsurface.settle") + collect_data_files("qtawesome")
datas += [(str(root / "LICENSE"), "."), (str(root / "RELEASE_NOTES.md"), ".")]
datas += [(str(root / "build" / "licenses"), "licenses")]
for package in ("PySide6", "numpy", "matplotlib", "reportlab", "QtAwesome", "python-docx",
                "openpyxl"):
    datas += copy_metadata(package)

a = Analysis(
    [str(root / "packaging" / "entry.py")],
    pathex=[str(root), str(root / "packaging")],
    binaries=[],
    datas=datas,
    hiddenimports=collect_submodules("slipsurface.settle")
    + ["qtawesome", "docx", "openpyxl", "matplotlib.backends.backend_qtagg",
       "matplotlib.backends.backend_agg", "matplotlib.backends.backend_svg",
       "matplotlib.backends.backend_pdf"],
    excludes=["tkinter", "IPython", "PyQt5", "PyQt6", "PySide2", "scipy"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="slipsurface-settle",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=sys.platform != "win32",
    icon=str(root / "build" / "slipsurface-settle.ico") if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="slipsurface-settle")
