"""QApplication bootstrap (used by main.py, `python -m slipsurface.settle` and the
`slipsurface-settle` command)."""

from __future__ import annotations

import sys
import traceback

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from .. import APP_NAME, ORG, __version__


def _install_excepthook() -> None:
    """Show unexpected errors in a dialog (and the console) instead of a silent
    crash; the application keeps running."""

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        if sys.__stderr__ is not None:  # None under pythonw.exe
            sys.__stderr__.write(text)
        app = QApplication.instance()
        if app is not None and not app.closingDown():
            from .texts import t

            box = QMessageBox(QMessageBox.Critical, t("error"), f"{exc_type.__name__}: {exc}")
            box.setDetailedText(text)
            box.exec()

    sys.excepthook = hook


def run(
    argv: list[str] | None = None, project_path: str | None = None, smoke: float | None = None
) -> int:
    argv = list(argv if argv is not None else sys.argv[:1])
    app = QApplication.instance() or QApplication(argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(ORG)
    app.setStyle("Fusion")

    from . import texts
    from .icons import icon
    from .preferences import apply_theme, settings, show_screen_sized

    texts.set_language(settings().value("language", "tr"))
    apply_theme()
    app.setWindowIcon(icon("foundation"))
    _install_excepthook()

    from .mainwindow import SettleWindow

    win = SettleWindow()
    if project_path:
        from pathlib import Path

        win.load_file(Path(project_path))
    show_screen_sized(win)
    if smoke:

        def _quit():
            win.dirty = False
            win.close()
            app.quit()

        QTimer.singleShot(int(smoke * 1000), _quit)
    return app.exec()
