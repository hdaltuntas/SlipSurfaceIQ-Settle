"""Appearance and persistent preferences — the same look as the other
SlipSurfaceIQ desktop programs (Fusion style, Source Sans 3, light / dark)."""

from __future__ import annotations

from functools import cache
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

from .. import __version__

DESIGN_SIZE = (1920, 1080)  # logical resolution the window sizes were designed for


def settings() -> QSettings:
    return QSettings("SlipSurface", "SlipSurfaceIQ Settle")


def is_dark() -> bool:
    return settings().value("dark", False, type=bool)


@cache
def interface_font() -> QFont:
    folder = Path(__file__).resolve().parents[1] / "fonts"
    family = "Segoe UI"
    for name in ("Regular", "SemiBold", "Bold", "Italic"):
        font_id = QFontDatabase.addApplicationFont(str(folder / f"SourceSans3-{name}.ttf"))
        if font_id >= 0:
            family = QFontDatabase.applicationFontFamilies(font_id)[0]
    return QFont(family, 10)


def available_geometry(widget=None):
    """Usable area (without taskbar / dock) of the widget's screen or the primary one."""
    app = QApplication.instance()
    screen = (widget.screen() if widget is not None else None) or app.primaryScreen()
    return screen.availableGeometry()


def fit_to_screen(widget, width: int, height: int, center: bool = True) -> None:
    """Size a window for the screen: designed sizes scale with the screen
    (relative to 1920 x 1080) and never exceed 95 % of the available area."""
    avail = available_geometry(widget)
    scale = min(avail.width() / DESIGN_SIZE[0], avail.height() / DESIGN_SIZE[1])
    scale = min(max(scale, 0.6), 1.6)
    w = min(int(width * scale), int(avail.width() * 0.95))
    h = min(int(height * scale), int(avail.height() * 0.95))
    widget.resize(max(w, 200), max(h, 150))
    if center:
        frame = widget.frameGeometry()
        frame.moveCenter(avail.center())
        widget.move(frame.topLeft())


def show_screen_sized(window) -> None:
    """Open a main window covering the whole usable screen (maximized)."""
    window.setGeometry(available_geometry(window))
    window.showMaximized()


#: Colours of the two themes: background, input base, text, border
COLOURS = {
    False: dict(
        bg="#f1f5f9",
        base="#ffffff",
        text="#243348",
        border="#d9e2ed",
        dim="#5b6b80",
        header_a="#e9f2fd",
        header_b="#cfe2fa",
        header_edge="#8fb4e3",
        header_text="#1b3a63",
        shade="#eef2f7",
    ),
    True: dict(
        bg="#161e2c",
        base="#202c3e",
        text="#e6edf7",
        border="#36465d",
        dim="#9aa8bc",
        header_a="#2a3a52",
        header_b="#223047",
        header_edge="#3f5677",
        header_text="#cfe0f7",
        shade="#1a2434",
    ),
}

#: Status colours used in the summary and the project tree
OK, BAD, NA = "#2e9d4f", "#d23b2f", "#8a95a3"


def colours() -> dict:
    return COLOURS[is_dark()]


def apply_theme(dark=None) -> None:
    app = QApplication.instance()
    if dark is None:
        dark = is_dark()
    settings().setValue("dark", bool(dark))
    c = COLOURS[bool(dark)]
    bg, base, text, border = c["bg"], c["base"], c["text"], c["border"]
    pal = QPalette()
    for role in (QPalette.Window, QPalette.Button):
        pal.setColor(role, QColor(bg))
    for role in (QPalette.Base, QPalette.AlternateBase, QPalette.ToolTipBase):
        pal.setColor(role, QColor(base))
    pal.setColor(QPalette.AlternateBase, QColor(c["shade"]))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText, QPalette.ToolTipText):
        pal.setColor(role, QColor(text))
        pal.setColor(QPalette.Disabled, role, QColor("#8491a4"))
    pal.setColor(QPalette.Highlight, QColor("#287ae6"))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.PlaceholderText, QColor(c["dim"]))
    app.setPalette(pal)
    app.setFont(interface_font())
    app.setStyleSheet(f"""
        QWidget {{ font-family: "Source Sans 3"; font-size: 14px; }}
        QMainWindow, QDialog {{ background: {bg}; }}
        QToolBar {{ spacing: 5px; padding: 7px; border: none;
                    border-bottom: 1px solid {border}; }}
        QToolButton {{ padding: 6px; border-radius: 6px; }}
        QToolButton:hover, QPushButton:hover {{ background: {border}; }}
        QToolButton:checked {{ background: #315b88; color: white; }}
        QPushButton {{ padding: 7px 16px; border: 1px solid {border}; border-radius: 6px; }}
        QLineEdit, QComboBox, QPlainTextEdit, QTextBrowser {{
            padding: 5px; border: 1px solid {border}; border-radius: 5px;
            background: {base}; color: {text}; }}
        QSpinBox, QDoubleSpinBox {{ background: {base}; color: {text}; min-height: 28px; }}
        QSpinBox QLineEdit, QDoubleSpinBox QLineEdit {{ padding: 0; border: none; }}
        QTreeWidget, QListWidget, QTableWidget {{ border: 1px solid {border}; }}
        QTableWidget QComboBox {{ border: none; border-radius: 0; padding: 2px 4px; }}
        QHeaderView::section {{ background: {bg}; color: {text}; padding: 4px 6px;
                                border: none; border-right: 1px solid {border};
                                border-bottom: 1px solid {border}; font-weight: 600; }}
        QTabWidget::pane {{ border: 1px solid {border}; top: -1px; }}
        QTabBar::tab {{ padding: 6px 14px; border: 1px solid {border}; border-bottom: none;
                        border-top-left-radius: 5px; border-top-right-radius: 5px;
                        background: {bg}; margin-right: 2px; }}
        QTabBar::tab:selected {{ background: {base}; font-weight: 600; }}
        QMenu {{ padding: 5px; }}
        QMenu::item {{ padding: 7px 26px; }}
        QMenu::item:selected {{ background: #287ae6; color: white; }}
        QStatusBar {{ border-top: 1px solid {border}; }}
        QProgressBar {{ border: 1px solid {border}; border-radius: 4px; text-align: center;
                        background: {base}; max-height: 16px; }}
        QProgressBar::chunk {{ background: #287ae6; border-radius: 3px; }}
    """)
    for widget in app.topLevelWidgets():
        widget.update()


def header_css() -> str:
    c = colours()
    return (
        f"QLabel{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 {c['header_a']},"
        f"stop:1 {c['header_b']});border:1px solid {c['header_edge']};"
        f"color:{c['header_text']};font-weight:bold;padding:2px;}}"
    )


TECHNOLOGIES = f"""
<h3>SlipSurfaceIQ Settle {__version__}</h3>
<p>{{subtitle}}</p>
<p>© 2026 Hasan Deniz Altuntaş — GNU AGPL v3 or later. No warranty.<br>
<a href="https://slipsurface.dev">slipsurface.dev</a> · slipsurface@proton.me</p>
<table cellpadding="5">
<tr><th>Technology</th><th>License</th></tr>
<tr><td>Python</td><td>PSF License</td></tr>
<tr><td>PySide6 / Qt / Shiboken6</td><td>LGPL-3.0 / GPL-3.0 / commercial</td></tr>
<tr><td>NumPy</td><td>BSD-3-Clause</td></tr>
<tr><td>Matplotlib</td><td>PSF-based (Matplotlib License)</td></tr>
<tr><td>ReportLab</td><td>BSD</td></tr>
<tr><td>python-docx · openpyxl (optional)</td><td>MIT</td></tr>
<tr><td>QtAwesome · QtPy</td><td>MIT</td></tr>
<tr><td>Material Design Icons (Pictogrammers)</td><td>Apache-2.0</td></tr>
<tr><td>Source Sans 3</td><td>SIL Open Font License 1.1</td></tr>
</table>
<p><a href="https://doc.qt.io/qtforpython-6/licenses.html">Qt licenses</a> ·
<a href="https://github.com/spyder-ide/qtawesome/blob/master/LICENSE.txt">QtAwesome licenses</a> ·
<a href="https://github.com/Templarian/MaterialDesign/blob/master/LICENSE">Icon license</a></p>
"""
