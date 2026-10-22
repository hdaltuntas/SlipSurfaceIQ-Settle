"""Building blocks of the main window.

FieldForm     input groups built from `forms` (the schema the core declares)
LayerTable    the soil profile: material, thickness, drainage
StudyTable    the variables of a parametric / reliability study
FigureView    a Matplotlib figure with its navigation toolbar
SummaryView   the headline numbers and checks as cards
ProjectTree   the project navigator in the left dock
"""

from __future__ import annotations

import html
import math
from typing import Any
from collections.abc import Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTreeWidgetItemIterator,
    QVBoxLayout,
    QWidget,
)

from .. import forms
from ..config import SOIL_FILL
from .icons import color_icon, icon
from .preferences import BAD, NA, OK, colours, header_css, is_dark
from .texts import language, t


def header(text: str) -> QLabel:
    """Section header in the style of SlipSurfaceIQ LE's dock panels."""
    lab = QLabel(f"▾  {text}")
    lab.setAlignment(Qt.AlignCenter)
    lab.setStyleSheet(header_css())
    return lab


def note_label(text: str) -> QLabel:
    lab = QLabel(text)
    lab.setWordWrap(True)
    lab.setStyleSheet(f"color:{colours()['dim']};font-size:12px;padding:2px 4px 6px 4px;")
    return lab


def _number(value, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _fmt(value) -> str:
    """A table cell: numbers short and exact enough, missing values empty."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float)):
        return f"{float(value):.6g}"
    return str(value)


class QuietSpin(QDoubleSpinBox):
    """A spin box that ignores the mouse wheel unless it has the focus, so
    scrolling the input panel never changes a value by accident."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setKeyboardTracking(False)

    def wheelEvent(self, ev):  # noqa: N802 (Qt API)
        if self.hasFocus():
            super().wheelEvent(ev)
        else:
            ev.ignore()


class SciSpin(QuietSpin):
    """A spin box for small coefficients (cv in cm²/s, mv in m²/kN): shows four
    significant figures, as 4.75e-04 when small, and takes 4.75e-4, 0,000475
    or 0.000475 alike."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDecimals(12)

    def textFromValue(self, value: float) -> str:  # noqa: N802 (Qt API)
        if value == 0:
            return "0"
        if abs(value) >= 0.01:
            return f"{value:.4g}"
        mantissa, exponent = f"{value:.3e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa}e{int(exponent)}"

    def valueFromText(self, text: str) -> float:  # noqa: N802 (Qt API)
        try:
            return float(self._plain(text))
        except ValueError:
            return self.value()

    def validate(self, text: str, pos: int):  # noqa: N802 (Qt API)
        from PySide6.QtGui import QValidator

        plain = self._plain(text)
        if plain in ("", "-", ".", "e", "E") or plain.lower().endswith(("e", "e-", "e+")):
            return QValidator.Intermediate, text, pos
        try:
            value = float(plain)
        except ValueError:
            return QValidator.Invalid, text, pos
        ok = self.minimum() <= value <= self.maximum()
        return (QValidator.Acceptable if ok else QValidator.Intermediate), text, pos

    def _plain(self, text: str) -> str:
        text = text.strip()
        suffix = self.suffix().strip()
        if suffix and text.endswith(suffix):
            text = text[: -len(suffix)].strip()
        return text.replace(",", ".")


class QuietCombo(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)

    def wheelEvent(self, ev):  # noqa: N802 (Qt API)
        if self.hasFocus():
            super().wheelEvent(ev)
        else:
            ev.ignore()


# ============================================================ input form
class FieldForm(QScrollArea):
    """A scrollable property panel built from `forms.Group` objects.

    Emits `changed(key, value)` when the user commits a value (Enter, focus
    out, an arrow step, a pick from a list); setting values from code is silent.
    """

    changed = Signal(str, object)

    def __init__(self, groups: list[forms.Group], note: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.editors: dict[str, QWidget] = {}
        self.fields: dict[str, forms.Field] = {}
        self._rows: list[tuple] = []  # (shapes, label widget, editor) per field
        self._groups: list[tuple] = []  # (shapes, [widgets]) per group
        self._quiet = False

        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)
        for group in groups:
            widgets: list[QWidget] = [header(group.title)]
            lay.addWidget(widgets[0])
            box = QWidget()
            fl = QFormLayout(box)
            fl.setContentsMargins(6, 2, 6, 2)
            fl.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
            fl.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
            fl.setVerticalSpacing(5)
            for f in group.fields:
                editor = self._editor(f)
                label = QLabel(f.label)
                label.setWordWrap(True)
                label.setMinimumWidth(120)
                fl.addRow(label, editor)
                self.editors[f.key] = editor
                self.fields[f.key] = f
                self._rows.append((f.shapes, label, editor))
            lay.addWidget(box)
            widgets.append(box)
            if group.note:
                n = note_label(group.note)
                lay.addWidget(n)
                widgets.append(n)
            self._groups.append((group.shapes, widgets))
        if note:
            lay.addWidget(note_label(note))
        lay.addStretch(1)
        self.setWidget(body)

    def _editor(self, f: forms.Field) -> QWidget:
        if f.kind == "number":
            w = QuietSpin()
            w.setDecimals(max(int(f.decimals), 0))
            w.setRange(
                -1e9 if f.min is None else float(f.min), 1e9 if f.max is None else float(f.max)
            )
            if f.step:
                w.setSingleStep(float(f.step))
            if f.unit:
                w.setSuffix(f" {f.unit}")
            w.setValue(_number(f.default))
            w.valueChanged.connect(lambda v, k=f.key: self._emit(k, float(v)))
            return w
        if f.kind == "check":
            w = QCheckBox()
            w.setChecked(bool(f.default))
            w.toggled.connect(lambda v, k=f.key: self._emit(k, bool(v)))
            return w
        if f.kind == "select":
            w = QuietCombo()
            for opt in f.options:
                w.addItem(opt["label"], opt["value"])
            w.setCurrentIndex(max(w.findData(f.default), 0))
            w.currentIndexChanged.connect(
                lambda _i, k=f.key, box=w: self._emit(k, box.currentData())
            )
            return w
        w = QLineEdit(str(f.default or ""))
        w.editingFinished.connect(lambda k=f.key, box=w: self._emit(k, box.text()))
        return w

    def _emit(self, key: str, value: Any) -> None:
        if not self._quiet:
            self.changed.emit(key, value)

    def set_values(self, values: dict[str, Any]) -> None:
        self._quiet = True
        try:
            for key, w in self.editors.items():
                if key not in values:
                    continue
                v = values[key]
                if isinstance(w, QDoubleSpinBox):
                    w.setValue(_number(v, w.value()))
                elif isinstance(w, QCheckBox):
                    w.setChecked(bool(v))
                elif isinstance(w, QComboBox):
                    i = w.findData(v)
                    if i >= 0:
                        w.setCurrentIndex(i)
                elif isinstance(w, QLineEdit):
                    w.setText("" if v is None else str(v))
        finally:
            self._quiet = False

    def set_shape(self, shape: str) -> None:
        """Shows only what applies to a foundation of this shape (or an embankment)."""
        for shapes, widgets in self._groups:
            for w in widgets:
                w.setVisible(not shapes or shape in shapes)
        for shapes, label, editor in self._rows:
            visible = not shapes or shape in shapes
            label.setVisible(visible)
            editor.setVisible(visible)


# ============================================================ tables
class _EditableTable(QWidget):
    """A table with a small toolbar (add, remove, up, down) above it.

    Text and number cells are table items; choice cells are combo boxes.
    Emits `changed()` whenever the user edits the table.
    """

    changed = Signal()

    def __init__(
        self, columns: list[dict], add_text: str, del_text: str, note: str = "", parent=None
    ) -> None:
        super().__init__(parent)
        self.columns = columns
        self.keys = [c["key"] for c in columns]
        self._quiet = False

        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(2)
        self.buttons = {}
        for name, text, slot in (
            ("add", add_text, self.add_row),
            ("delete", del_text, self.remove_row),
            ("up", t("a_up"), lambda: self.move_row(-1)),
            ("down", t("a_down"), lambda: self.move_row(1)),
        ):
            b = QToolButton()
            b.setIcon(icon(name))
            b.setIconSize(QSize(18, 18))
            b.setToolTip(text)
            if name in ("add", "delete"):
                b.setText(text)
                b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.clicked.connect(lambda _=False, s=slot: s())
            bar.addWidget(b)
            self.buttons[name] = b
        bar.addSpacing(12)
        self.note = note_label(note) if note else QLabel("")
        self.note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bar.addWidget(self.note, 1)

        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels([c["label"] for c in columns])
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.verticalHeader().setMinimumWidth(28)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.itemChanged.connect(self._item_changed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        lay.addLayout(bar)
        lay.addWidget(self.table, 1)

    # -------------------------------------------------- cells
    def _set_cell(self, row: int, col: int, value: Any) -> None:
        column = self.columns[col]
        if column["kind"] == "select":
            combo = self.table.cellWidget(row, col)
            if combo is None:
                combo = QuietCombo()
                for opt in column["options"]:
                    combo.addItem(opt["label"], opt["value"])
                combo.currentIndexChanged.connect(
                    lambda _i, c=combo, k=column["key"]: self._combo_changed(c, k)
                )
                self.table.setCellWidget(row, col, combo)
            i = combo.findData(value)
            combo.blockSignals(True)
            combo.setCurrentIndex(i if i >= 0 else 0)
            combo.blockSignals(False)
            return
        item = self.table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            self.table.setItem(row, col, item)
        text = _fmt(value)
        item.setText(text)
        item.setData(Qt.UserRole, text)  # last good value
        if column["kind"] == "number":
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

    def _cell(self, row: int, col: int) -> Any:
        column = self.columns[col]
        if column["kind"] == "select":
            combo = self.table.cellWidget(row, col)
            return combo.currentData() if combo is not None else ""
        item = self.table.item(row, col)
        text = item.text().strip() if item is not None else ""
        if column["kind"] == "number":
            return _number(text.replace(",", "."), 0.0) if text else ""
        return text

    def _row_of(self, widget: QWidget) -> int:
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                if self.table.cellWidget(r, c) is widget:
                    return r
        return -1

    def _item_changed(self, item: QTableWidgetItem) -> None:
        if self._quiet:
            return
        column = self.columns[item.column()]
        if column["kind"] == "number":
            text = item.text().strip().replace(",", ".")
            try:
                ok = text == "" or math.isfinite(float(text))
            except ValueError:
                ok = False
            self._quiet = True
            if not ok:
                item.setText(item.data(Qt.UserRole) or "")
            else:
                item.setText(text)
                item.setData(Qt.UserRole, text)
            self._quiet = False
            if not ok:
                return
        self.on_cell_edited(item.row(), column["key"])
        self.changed.emit()

    def _combo_changed(self, combo: QComboBox, key: str) -> None:
        if self._quiet:
            return
        row = self._row_of(combo)
        if row >= 0:
            self.on_cell_edited(row, key)
        self.changed.emit()

    def on_cell_edited(self, row: int, key: str) -> None:
        """Hook: a cell of this row was edited by the user."""
        self.restyle_row(row)

    def restyle_row(self, row: int) -> None:
        """Hook: shade the cells that do not apply to the row."""

    def shade(self, row: int, keys: list[str], shaded: bool) -> None:
        c = colours()
        brush = QBrush(QColor(c["shade"])) if shaded else QBrush()
        dim = QBrush(QColor(c["dim"])) if shaded else QBrush()
        for key in keys:
            item = self.table.item(row, self.keys.index(key))
            if item is not None:
                item.setBackground(brush)
                item.setForeground(dim)

    # -------------------------------------------------- rows
    def rows(self) -> list[dict[str, Any]]:
        return [
            {key: self._cell(r, c) for c, key in enumerate(self.keys)}
            for r in range(self.table.rowCount())
        ]

    def set_rows(self, rows: list[dict[str, Any]]) -> None:
        self._quiet = True
        try:
            self.table.setRowCount(0)
            for row in rows:
                self._append(row)
        finally:
            self._quiet = False
        self.table.resizeColumnsToContents()
        for c in range(self.table.columnCount()):
            self.table.setColumnWidth(c, max(self.table.columnWidth(c), 64))

    def _append(self, row: dict[str, Any]) -> int:
        r = self.table.rowCount()
        self.table.insertRow(r)
        for c, key in enumerate(self.keys):
            self._set_cell(r, c, row.get(key, ""))
        self.restyle_row(r)
        return r

    def new_row(self) -> dict[str, Any]:
        return {}

    def add_row(self) -> None:
        self._quiet = True
        r = self._append(self.new_row())
        self._quiet = False
        self.table.selectRow(r)
        self.changed.emit()

    def remove_row(self) -> None:
        r = self.table.currentRow()
        if r < 0:
            r = self.table.rowCount() - 1
        if r < 0:
            return
        self.table.removeRow(r)
        self.changed.emit()

    def move_row(self, step: int) -> None:
        r = self.table.currentRow()
        dst = r + step
        if r < 0 or not 0 <= dst < self.table.rowCount():
            return
        rows = self.rows()
        rows[r], rows[dst] = rows[dst], rows[r]
        self.set_rows(rows)
        self.table.selectRow(dst)
        self.changed.emit()


def material_colour(material: dict) -> str:
    """The fill of a material: its own colour, or that of its behaviour."""
    fills = SOIL_FILL["dark" if is_dark() else "light"]
    return str(material.get("color") or "") or fills.get(
        str(material.get("behaviour", "granular")), "#cccccc"
    )


class LayerTable(_EditableTable):
    """The soil profile from the ground surface down: a material, a thickness
    and, for a cohesive layer, the drainage."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            forms.layer_columns(language()), t("a_add_row"), t("a_del_row"), "", parent
        )
        self.materials: list[dict] = []
        for name in ("add", "delete"):  # the dock is narrow: icons only
            self.buttons[name].setToolButtonStyle(Qt.ToolButtonIconOnly)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(28)

    def _material(self, name: str) -> dict:
        return next((m for m in self.materials if m.get("name") == name), {})

    def set_materials(self, materials: list[dict]) -> None:
        """The materials a layer may name; the layers keep the one they had."""
        self.materials = [dict(m) for m in materials]
        self.buttons["add"].setEnabled(bool(materials))
        self.buttons["add"].setToolTip(t("a_add_row") if materials else t("need_materials"))
        col = self.keys.index("material")
        self.columns[col]["options"] = [{"value": m["name"], "label": m["name"]} for m in materials]
        self._quiet = True
        try:
            for r in range(self.table.rowCount()):
                combo = self.table.cellWidget(r, col)
                if combo is None:
                    continue
                current = combo.currentData()
                combo.blockSignals(True)
                combo.clear()
                self._fill(combo)
                i = combo.findData(current)
                combo.setCurrentIndex(max(i, 0))
                combo.blockSignals(False)
                self.restyle_row(r)
        finally:
            self._quiet = False

    def _fill(self, combo: QComboBox) -> None:
        for m in self.materials:
            combo.addItem(color_icon(material_colour(m)), m["name"], m["name"])

    def _set_cell(self, row: int, col: int, value: Any) -> None:
        if self.keys[col] == "material" and self.table.cellWidget(row, col) is None:
            combo = QuietCombo()
            self._fill(combo)
            combo.currentIndexChanged.connect(
                lambda _i, c=combo: self._combo_changed(c, "material")
            )
            self.table.setCellWidget(row, col, combo)
        super()._set_cell(row, col, value)

    def new_row(self) -> dict[str, Any]:
        rows = self.rows()
        if rows:
            return dict(rows[-1])
        name = self.materials[0]["name"] if self.materials else ""
        return {"material": name, "thickness": 1.0, "drainage": "double"}

    def restyle_row(self, row: int) -> None:
        name = self._cell(row, self.keys.index("material"))
        cohesive = self._material(name).get("behaviour") == "cohesive"
        combo = self.table.cellWidget(row, self.keys.index("drainage"))
        if combo is not None:
            combo.setEnabled(cohesive)


class StudyTable(_EditableTable):
    """The study variables: an input, and a range or a distribution for it."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            forms.study_columns(language()), t("a_add_var"), t("a_del_var"), "", parent
        )
        self.choices: list[dict] = []

    def set_choices(self, choices: list[dict]) -> None:
        """The inputs a study may vary, with their project values."""
        self.choices = choices
        col = self.keys.index("path")
        self.columns[col]["options"] = [{"value": c["value"], "label": c["label"]} for c in choices]
        self._quiet = True
        try:
            for r in range(self.table.rowCount()):
                combo = self.table.cellWidget(r, col)
                if combo is None:
                    continue
                current = combo.currentData()
                combo.blockSignals(True)
                combo.clear()
                for c in choices:
                    combo.addItem(c["label"], c["value"])
                i = combo.findData(current)
                if i < 0 and current:
                    combo.addItem(str(current), current)  # an input no longer offered
                    i = combo.count() - 1
                combo.setCurrentIndex(max(i, 0))
                combo.blockSignals(False)
        finally:
            self._quiet = False

    def _choice(self, path: str) -> dict | None:
        return next((c for c in self.choices if c["value"] == path), None)

    def new_row(self) -> dict[str, Any]:
        used = {row.get("path") for row in self.rows()}
        choice = next(
            (c for c in self.choices if c["value"] not in used),
            self.choices[0] if self.choices else None,
        )
        if choice is None:
            return {}
        return self._defaults_for(choice, "dist")

    @staticmethod
    def _defaults_for(choice: dict, mode: str) -> dict[str, Any]:
        base = float(choice["base"])
        span = abs(base) * 0.2 or 1.0
        return {
            "path": choice["value"],
            "label": choice["label"],
            "mode": mode,
            "min": base - span,
            "max": base + span,
            "dist": "normal",
            "mean": base,
            "cov": 0.10,
            "n_points": 5,
        }

    def on_cell_edited(self, row: int, key: str) -> None:
        if key == "path":
            path = self._cell(row, self.keys.index("path"))
            choice = self._choice(path)
            if choice is not None:
                mode = self._cell(row, self.keys.index("mode")) or "dist"
                fresh = self._defaults_for(choice, mode)
                self._quiet = True
                for k in ("min", "max", "mean"):
                    self._set_cell(row, self.keys.index(k), fresh[k])
                self._quiet = False
        self.restyle_row(row)

    def restyle_row(self, row: int) -> None:
        mode = self._cell(row, self.keys.index("mode")) or "range"
        self.shade(row, ["min", "max", "n_points"], mode != "range")
        self.shade(row, ["mean", "cov"], mode != "dist")
        combo = self.table.cellWidget(row, self.keys.index("dist"))
        if combo is not None:
            combo.setEnabled(mode == "dist")

    def rows(self) -> list[dict[str, Any]]:
        out = []
        for row in super().rows():
            choice = self._choice(row.get("path"))
            row["label"] = choice["label"] if choice else row.get("path", "")
            out.append(row)
        return out


# ============================================================ figure
class FigureView(QWidget):
    """A Matplotlib figure that fills its space, with zoom / pan / save."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 7), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setIconSize(QSize(18, 18))
        self.toolbar.setStyleSheet("QToolBar{border:none;padding:2px;}")
        self.message = QLabel("")
        self.message.setAlignment(Qt.AlignCenter)
        self.message.setWordWrap(True)
        self.message.hide()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.message, 1)
        lay.addWidget(self.canvas, 1)
        self.drawn = False

    def draw(self, painter: Callable[[Figure], None]) -> None:
        self.figure.clear()
        painter(self.figure)
        self.message.hide()
        self.canvas.show()
        self.canvas.draw_idle()
        self.drawn = True

    def show_message(self, text: str) -> None:
        self.figure.clear()
        self.canvas.hide()
        self.message.setText(text)
        self.message.setStyleSheet(f"color:{colours()['dim']};font-size:15px;")
        self.message.show()
        self.drawn = False


# ============================================================ summary
class SummaryView(QTextBrowser):
    """The headline numbers as cards, the checks, and any warnings."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(False)
        self.setFrameShape(QTextBrowser.NoFrame)

    def _wrap(self, body: str) -> str:
        c = colours()
        return f"""<html><head><style>
            body {{ color:{c["text"]}; font-family:'Source Sans 3'; font-size:14px; }}
            h2 {{ font-size:20px; margin:4px 0 2px 0; }}
            .head {{ color:{c["dim"]}; font-size:14px; margin-bottom:10px; }}
            td.card {{ border:1px solid {c["border"]}; background:{c["base"]};
                       padding:10px 12px; }}
            .t {{ color:{c["dim"]}; font-size:12px; }}
            .v {{ font-size:22px; font-weight:600; }}
            .s {{ color:{c["dim"]}; font-size:12px; }}
            .warn {{ background:{"#3a2f14" if is_dark() else "#fff7e0"};
                     border:1px solid #d9a55b; padding:8px 10px; }}
            .err {{ background:{"#3a1c1c" if is_dark() else "#fdecea"};
                    border:1px solid {BAD}; padding:10px 12px; }}
        </style></head><body>{body}</body></html>"""

    def show_cards(
        self, title: str, headline: str, cards: list[dict], warnings: list[str], stale: str = ""
    ) -> None:
        colour = {"ok": OK, "bad": BAD, "na": NA}
        cells = []
        for card in cards:
            v_colour = colour.get(card.get("state"), "")
            style = f' style="color:{v_colour}"' if v_colour else ""
            cells.append(
                f'<td class="card" width="25%"><div class="t">{html.escape(card["title"])}'
                f'</div><div class="v"{style}>{html.escape(str(card["value"]))}</div>'
                f'<div class="s">{html.escape(card.get("sub") or "") or "&nbsp;"}</div></td>'
            )
        rows = "".join(
            "<tr>" + "".join(cells[i : i + 4]) + "</tr>" for i in range(0, len(cells), 4)
        )
        body = [
            f"<h2>{html.escape(title)}</h2>",
            f'<div class="head">{html.escape(headline)}</div>',
        ]
        if stale:
            body.append(f'<p class="warn">{html.escape(stale)}</p>')
        body.append(f'<table width="100%" cellspacing="6" cellpadding="0">{rows}</table>')
        if warnings:
            items = "".join(f"<li>{html.escape(w)}</li>" for w in warnings)
            body.append(
                f"<p><b>{html.escape(t('warnings_title'))}</b></p>"
                f'<div class="warn"><ul style="margin:0">{items}</ul></div>'
            )
        self.setHtml(self._wrap("".join(body)))

    def show_error(self, title: str, message: str) -> None:
        self.setHtml(
            self._wrap(
                f'<h2>{html.escape(title)}</h2><div class="err">{html.escape(message)}</div>'
            )
        )

    def show_text(self, text: str) -> None:
        self.setHtml(self._wrap(f'<p class="head">{html.escape(text)}</p>'))


# ============================================================ project tree
class ProjectTree(QTreeWidget):
    """The project at a glance; picking an item opens its step and view.

    Each item carries (step, target) in its data; `activated` passes them on.
    """

    activated = Signal(int, str)
    #: a double click on an item that has an editor: "materials", "study_vars"
    edit_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(14)
        self.setColumnCount(2)
        self.header().setStretchLastSection(True)
        self.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.itemClicked.connect(self._clicked)
        self.itemDoubleClicked.connect(self._double)
        self._expanded: dict[str, bool] = {}

    def _double(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.UserRole)
        if data and str(data[1]) in ("materials", "study_vars"):
            self.edit_requested.emit(str(data[1]))

    def _clicked(self, item: QTreeWidgetItem, _col: int) -> None:
        data = item.data(0, Qt.UserRole)
        if data:
            self.activated.emit(int(data[0]), str(data[1]))

    def _item(
        self,
        parent,
        text: str,
        value: str = "",
        ic: str = "",
        step: int = 0,
        target: str = "",
        colour: str = "",
        bold: bool = False,
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem(parent if parent is not None else self, [text, value])
        if ic:
            item.setIcon(0, icon(ic))
        item.setData(0, Qt.UserRole, (step, target))
        item.setToolTip(0, f"{text}: {value}" if value else text)
        item.setToolTip(1, value)
        if colour:
            item.setForeground(1, QBrush(QColor(colour)))
        if bold:
            f = QFont(item.font(0))
            f.setBold(True)
            item.setFont(0, f)
            item.setFont(1, f)
        return item

    def refresh(
        self,
        values: dict[str, Any],
        results: dict | None,
        study: dict | None,
        figure_keys: list[str],
    ) -> None:
        """Rebuilds the tree; branches keep the expanded state the user left them in."""
        it = QTreeWidgetItemIterator(self)
        while it.value():
            key = it.value().data(1, Qt.UserRole)
            if key:
                self._expanded[key] = it.value().isExpanded()
            it += 1
        self.clear()
        L = {
            k: t(k)
            for k in (
                "step_project",
                "step_load",
                "step_soil",
                "step_options",
                "step_results",
                "step_study",
            )
        }

        title = str(values.get("title") or t("untitled"))
        top = self._item(None, L["step_project"], title, "project", 0, "summary", bold=True)
        top.setData(1, Qt.UserRole, "project")

        shape = values.get("shape", "rectangle")
        shape_text = t(f"shape_{shape}")
        if shape == "embankment":
            dims = (
                f"H = {_number(values.get('emb_height')):g} m, "
                f"{t('emb_crest_label').split('(')[0].strip()} = "
                f"{_number(values.get('emb_crest')):g} m"
            )
            self._item(top, shape_text, dims, "embankment", 1, "fig:schematic")
        else:
            dims = f"B = {_number(values.get('B')):g} m"
            if shape == "rectangle":
                dims += f", L = {_number(values.get('L')):g} m"
            dims += f", q = {_number(values.get('q')):g} kPa"
            self._item(top, shape_text, dims, "foundation", 1, "fig:schematic")
        self._item(
            top,
            t("tr_water"),
            f"{_number(values.get('water_depth')):g} m",
            "water",
            1,
            "fig:schematic",
        )

        materials = values.get("materials") or []
        by_name = {str(m.get("name")): m for m in materials}
        mats = self._item(top, t("tr_materials"), str(len(materials)), "materials", 2, "materials")
        mats.setData(1, Qt.UserRole, "materials")
        mats.setToolTip(0, t("tr_edit_hint"))
        for m in materials:
            kind = t("behaviour_" + str(m.get("behaviour", "granular")))
            if m.get("behaviour") == "cohesive":
                kind += " · mv" if m.get("compression") == "mv" else " · Cc"
            item = self._item(mats, str(m.get("name") or "—"), kind, "", 2, "materials")
            item.setIcon(0, color_icon(material_colour(m)))
            item.setToolTip(0, t("tr_edit_hint"))
        self._expanded.setdefault("materials", False)

        layers = values.get("soil_profile") or []
        soil = self._item(top, t("tr_layers"), str(len(layers)), "soil", 2, "fig:schematic")
        soil.setData(1, Qt.UserRole, "soil")
        depth = 0.0
        for layer in layers:
            thickness = _number(layer.get("thickness"))
            name = str(layer.get("material") or "—")
            item = self._item(
                soil,
                name,
                f"{depth:g} – {depth + thickness:g} m",
                "",
                2,
                "fig:schematic",
            )
            depth += thickness
            item.setIcon(0, color_icon(material_colour(by_name.get(name, {}))))

        method = t(f"stress_{values.get('stress_method', 'boussinesq')}")
        immediate = t(f"immediate_{values.get('immediate_method', 'elastic')}")
        self._item(top, t("group_options"), f"{method} · {immediate}", "options", 3, "fig:stress")
        allow = _number(values.get("s_allow"))
        self._item(
            top,
            t("group_criteria"),
            f"s ≤ {allow:g} mm" if allow > 0 else "—",
            "criteria",
            3,
            "summary",
        )

        res = self._item(
            None,
            L["step_results"],
            "" if results else t("tr_no_results"),
            "results",
            4,
            "summary",
            bold=True,
        )
        res.setData(1, Qt.UserRole, "results")
        if results:
            colour = {"ok": OK, "bad": BAD, "na": NA}
            for card in results["cards"]:
                self._item(
                    res,
                    card["title"],
                    str(card["value"]),
                    "",
                    4,
                    "summary",
                    colour.get(card.get("state"), ""),
                )
            figs = self._item(
                res, t("tr_figures"), str(len(figure_keys)), "figure", 4, "fig:" + figure_keys[0]
            )
            figs.setData(1, Qt.UserRole, "figures")
            for key in figure_keys:
                self._item(figs, t(f"fig_{key}"), "", "", 4, f"fig:{key}")
            self._expanded.setdefault("figures", False)

        st = self._item(
            None,
            L["step_study"],
            t("tr_vars", n=len(values.get("study_variables") or [])),
            "study",
            5,
            "study",
            bold=True,
        )
        st.setData(1, Qt.UserRole, "study")
        variables = self._item(
            st,
            t("tab_vars"),
            str(len(values.get("study_variables") or [])),
            "study_vars",
            5,
            "study_vars",
        )
        variables.setToolTip(0, t("tr_edit_hint"))
        if study:
            self._item(
                st,
                t(f"method_{study['method']}"),
                t("tr_samples", n=study["n"]),
                "study_vars",
                5,
                "study",
            )

        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            item.setExpanded(self._expanded.get(item.data(1, Qt.UserRole), True))
            for j in range(item.childCount()):
                child = item.child(j)
                key = child.data(1, Qt.UserRole)
                if key:
                    child.setExpanded(self._expanded.get(key, True))
