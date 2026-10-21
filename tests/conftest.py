"""Run the tests from a clone without installing, and without a display."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")


def pytest_sessionfinish(session, exitstatus):
    """Tear Qt down in order before the interpreter does.

    Cached icons and fonts, and windows not yet deleted, would otherwise be
    destroyed during interpreter finalization after the QApplication, which
    crashes some PySide6 / Python 3.10 combinations ("deallocating None").
    """
    import gc

    if "PySide6" not in sys.modules:
        return
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        return
    for widget in QApplication.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    app.processEvents()
    try:
        from slipsurface.settle.ui import icons, preferences

        icons.icon.cache_clear()
        preferences.interface_font.cache_clear()
    except ImportError:
        pass
    gc.collect()
    app.processEvents()
