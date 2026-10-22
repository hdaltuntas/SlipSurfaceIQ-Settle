"""Toolbar and tree icons — Material Design Icons through QtAwesome, in the
same colour as the other SlipSurfaceIQ desktop programs."""

from __future__ import annotations

from functools import cache

from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

COLOR = "#568cce"
DISABLED = "#8794a6"

NAMES = {
    "new": "file-plus-outline",
    "open": "folder-open-outline",
    "save": "content-save-outline",
    "undo": "undo",
    "redo": "redo",
    "compute": "play-circle-outline",
    "auto": "autorenew",
    "study": "chart-bell-curve-cumulative",
    "cancel": "stop-circle-outline",
    "report": "file-pdf-box",
    "export": "export-variant",
    "image": "image-outline",
    "table": "table-arrow-right",
    "add": "plus",
    "delete": "delete-outline",
    "up": "chevron-up",
    "down": "chevron-down",
    "project": "clipboard-text-outline",
    "foundation": "office-building-outline",
    "embankment": "slope-uphill",
    "water": "waves",
    "soil": "layers-outline",
    "materials": "palette-swatch-outline",
    "copy": "content-copy",
    "rock": "terrain",
    "layer": "square-rounded-outline",
    "options": "tune-variant",
    "criteria": "check-decagram-outline",
    "results": "chart-line",
    "figure": "chart-areaspline",
    "time": "timer-sand",
    "study_vars": "dice-multiple-outline",
    "theme": "theme-light-dark",
    "info": "information-outline",
    "book": "book-open-page-variant-outline",
    "ok": "check-circle-outline",
    "bad": "alert-circle-outline",
}


@cache
def icon(name: str, color: str = COLOR) -> QIcon:
    import qtawesome as qta

    return qta.icon(
        "mdi6." + NAMES.get(name, "help-circle-outline"), color=color, color_disabled=DISABLED
    )


def color_icon(color: str, size: int = 14) -> QIcon:
    """A small filled square, used for the soil layers in the project tree."""
    pm = QPixmap(size, size)
    pm.fill(QColor(color))
    p = QPainter(pm)
    p.setPen(QPen(QColor("#333"), 1))
    p.drawRect(0, 0, size - 1, size - 1)
    p.end()
    return QIcon(pm)
