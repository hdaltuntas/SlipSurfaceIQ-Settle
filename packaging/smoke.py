"""Exercise real packaged resources and native libraries after installation."""

import json
import tempfile
from pathlib import Path


def smoke_test(output: Path) -> None:
    import qtawesome
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from slipsurface.settle import __version__, forms
    from slipsurface.settle.session import Session
    from slipsurface.settle.ui import texts
    from slipsurface.settle.ui.mainwindow import EXAMPLES_DIR, SettleWindow
    from slipsurface.settle.ui.preferences import apply_theme

    app = QApplication.instance() or QApplication([])
    session = Session(lang="tr")
    examples = sorted(EXAMPLES_DIR.glob("*.settle"))
    if len(examples) < 4:
        raise RuntimeError("Bundled example projects are missing")
    data = json.loads((EXAMPLES_DIR / "raft_soft_clay.settle").read_text(encoding="utf-8"))
    values = session.load_project(data)["values"]
    result = session.analyse(values)
    if not 130.0 < result["total"] < 155.0:
        raise RuntimeError(f"Packaged calculation failed: {result['total']}")
    if qtawesome.icon("mdi6.layers-outline").pixmap(32, 32).isNull():
        raise RuntimeError("Bundled QtAwesome fonts are missing")
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        project = folder / "model.settle"
        project.write_text(json.dumps(forms.project_file(values)), encoding="utf-8")
        session.load_project(json.loads(project.read_text(encoding="utf-8")))
        session.report("pdf", str(folder / "report.pdf"))
        if not (folder / "report.pdf").read_bytes().startswith(b"%PDF"):
            raise RuntimeError("PDF generation failed")
        session.report("docx", str(folder / "report.docx"))
        if (folder / "report.docx").stat().st_size < 10000:
            raise RuntimeError("Word report generation failed")
    texts.set_language("tr")
    apply_theme(False)
    window = SettleWindow()
    window.show()
    window.show_view("fig:schematic")
    QTimer.singleShot(1000, app.quit)
    app.exec()
    if not window.fig_views["schematic"].drawn:
        raise RuntimeError("The section figure was not drawn")
    window.dirty = False
    window.close()
    output.write_text(
        json.dumps(
            {
                "version": __version__,
                "settlement_mm": result["total"],
                "qt_platform": app.platformName(),
                "checks": ["engine", "project", "pdf", "docx", "fonts", "icons", "gui"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
