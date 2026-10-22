"""Dialogs of the main window: Define Materials and Study Variables.

The materials dialog follows SlipSurfaceIQ LE's: the materials in a list on
the left, the properties of the selected one on the right. Only the
properties its behaviour and its consolidation description use are shown.
"""

from __future__ import annotations

import copy
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import forms
from ..config import MATERIAL_DEFAULT
from .icons import color_icon, icon
from .preferences import colours, fit_to_screen
from .texts import language, t
from .widgets import QuietCombo, QuietSpin, StudyTable, header, material_colour, note_label

TITLE_CSS = "color:#2a7ad0;font-size:16px;font-weight:600;"


def ok_cancel() -> QDialogButtonBox:
    """OK / Cancel in the interface's language."""
    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText(t("btn_ok"))
    buttons.button(QDialogButtonBox.Cancel).setText(t("btn_cancel"))
    return buttons


class MaterialsDialog(QDialog):
    """Define the project's materials.

    `materials` is edited on a copy; after `exec()` returns Accepted, read
    `result()` for the new list and `renames` for {old name: new name}.
    `used` maps a material name to the number of layers that use it.
    """

    def __init__(
        self,
        materials: list[dict],
        used: dict[str, int] | None = None,
        parent=None,
        select: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dlg_materials"))
        fit_to_screen(self, 940, 720)
        self.used = dict(used or {})
        lang = language()
        self.mats = [{**MATERIAL_DEFAULT, **m} for m in materials]
        if not self.mats:
            self.mats = [forms.new_material([], lang)]
        self._orig = [str(m["name"]) for m in self.mats]
        self._loading = False
        self.cur = -1
        self.renames: dict[str, str] = {}

        # ---------------------------------------------------------- left
        self.list = QListWidget()
        self.list.setIconSize(self.list.iconSize() * 1.2)
        self.list.currentRowChanged.connect(self._select)
        bar = QHBoxLayout()
        bar.setSpacing(2)
        for name, tip, slot in (
            ("add", t("a_add_mat"), self._add),
            ("copy", t("a_copy_mat"), self._copy),
            ("delete", t("a_del_mat"), self._delete),
            ("up", t("a_up"), lambda: self._move(-1)),
            ("down", t("a_down"), lambda: self._move(1)),
        ):
            b = QToolButton()
            b.setIcon(icon(name))
            b.setToolTip(tip)
            b.clicked.connect(lambda _=False, s=slot: s())
            bar.addWidget(b)
        bar.addStretch(1)
        left = QVBoxLayout()
        left.addWidget(self.list, 1)
        left.addLayout(bar)

        # --------------------------------------------------------- right
        self.title = QLabel()
        self.title.setStyleSheet(TITLE_CSS)
        self.name = QLineEdit()
        self.name.textEdited.connect(self._name_edited)
        self.color_btn = QToolButton()
        self.color_btn.setFixedWidth(110)
        self.color_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.color_btn.clicked.connect(self._pick_color)
        self.behaviour = QuietCombo()
        choices = forms.material_choices(lang)
        for value, label in choices["behaviour"]:
            self.behaviour.addItem(label, value)
        self.behaviour.currentIndexChanged.connect(lambda _i: self._choice_changed())
        self.compression = QuietCombo()
        for value, label in choices["compression"]:
            self.compression.addItem(label, value)
        self.compression.currentIndexChanged.connect(lambda _i: self._choice_changed())
        self.compression_label = QLabel(t("mat_compression"))

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.addWidget(QLabel(t("mat_name")), 0, 0)
        grid.addWidget(self.name, 0, 1)
        grid.addWidget(QLabel(t("mat_color")), 0, 2)
        grid.addWidget(self.color_btn, 0, 3)
        grid.addWidget(QLabel(t("mat_behaviour")), 1, 0)
        grid.addWidget(self.behaviour, 1, 1, 1, 3)
        grid.addWidget(self.compression_label, 2, 0)
        grid.addWidget(self.compression, 2, 1, 1, 3)
        grid.setColumnStretch(1, 1)

        # property groups, built from the schema
        self.spins: dict[str, QuietSpin] = {}
        self.rows: dict[str, tuple[QLabel, QuietSpin, list[str]]] = {}
        self.groups: dict[str, tuple[QLabel, QWidget]] = {}
        body = QWidget()
        props = QVBoxLayout(body)
        props.setContentsMargins(0, 0, 0, 0)
        props.setSpacing(6)
        forms_by_group: dict[str, QFormLayout] = {}
        for f in forms.material_fields(lang):
            if f["group"] not in forms_by_group:
                head = header(f["group_label"])
                box = QWidget()
                fl = QFormLayout(box)
                fl.setContentsMargins(8, 2, 8, 2)
                fl.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
                fl.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
                props.addWidget(head)
                props.addWidget(box)
                forms_by_group[f["group"]] = fl
                self.groups[f["group"]] = (head, box)
            spin = QuietSpin()
            spin.setDecimals(f["decimals"])
            spin.setRange(f["min"], f["max"])
            spin.setSingleStep(f["step"])
            if f["unit"]:
                spin.setSuffix(f" {f['unit']}")
            spin.valueChanged.connect(lambda v, k=f["key"]: self._value_changed(k, v))
            label = QLabel(f["label"])
            forms_by_group[f["group"]].addRow(label, spin)
            self.spins[f["key"]] = spin
            self.rows[f["key"]] = (label, spin, f["applies"])
        self.note = note_label("")
        self.note.setStyleSheet(
            f"color:{colours()['dim']};font-size:12px;padding:6px 8px;"
            f"border:1px solid {colours()['border']};border-radius:5px;"
        )
        props.addWidget(self.note)
        props.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setWidget(body)

        right = QVBoxLayout()
        right.addWidget(self.title)
        right.addLayout(grid)
        right.addSpacing(4)
        right.addWidget(scroll, 1)

        columns = QHBoxLayout()
        left_box = QWidget()
        left_box.setLayout(left)
        left_box.setFixedWidth(250)
        columns.addWidget(left_box)
        columns.addLayout(right, 1)

        buttons = ok_cancel()
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(columns, 1)
        lay.addWidget(buttons)

        self._fill_list()
        start = 0
        if select is not None:
            start = next((i for i, m in enumerate(self.mats) if m["name"] == select), 0)
        self.list.setCurrentRow(start)

    # ---------------------------------------------------------------- list
    def _fill_list(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        for m in self.mats:
            item = QListWidgetItem(color_icon(material_colour(m), 16), m["name"])
            self.list.addItem(item)
        self.list.blockSignals(False)

    def _refresh_item(self, i: int) -> None:
        item = self.list.item(i)
        if item is not None:
            m = self.mats[i]
            item.setText(m["name"])
            item.setIcon(color_icon(material_colour(m), 16))

    def _select(self, i: int) -> None:
        if not 0 <= i < len(self.mats):
            return
        self.cur = i
        m = self.mats[i]
        self._loading = True
        try:
            self.name.setText(m["name"])
            self.behaviour.setCurrentIndex(max(self.behaviour.findData(m["behaviour"]), 0))
            self.compression.setCurrentIndex(
                max(self.compression.findData(m.get("compression", "index")), 0)
            )
            for key, spin in self.spins.items():
                spin.setValue(float(m.get(key, MATERIAL_DEFAULT[key]) or 0.0))
        finally:
            self._loading = False
        self._show_color()
        self._update_visibility()

    def _show_color(self) -> None:
        m = self.mats[self.cur]
        self.color_btn.setIcon(color_icon(material_colour(m), 16))
        self.color_btn.setText(material_colour(m).upper())

    def _update_visibility(self) -> None:
        m = self.mats[self.cur]
        kind = forms.material_kind(m)
        cohesive = m["behaviour"] == "cohesive"
        self.compression.setVisible(cohesive)
        self.compression_label.setVisible(cohesive)
        shown_groups = set()
        for label, spin, applies in self.rows.values():
            on = kind in applies
            label.setVisible(on)
            spin.setVisible(on)
            if on:
                shown_groups.add(
                    next(g for g, (h, b) in self.groups.items() if b.isAncestorOf(spin))
                )
        for group, (head, box) in self.groups.items():
            head.setVisible(group in shown_groups)
            box.setVisible(group in shown_groups)
        note = {
            forms.GRANULAR: "mat_note_granular",
            forms.INDEX: "mat_note_index",
            forms.MV: "mat_note_mv",
            forms.ROCK: "mat_note_incompressible",
        }[kind]
        self.note.setText(t(note))
        self.title.setText(f"{m['name']}  ·  {self.behaviour.currentText()}")

    # ---------------------------------------------------------------- edits
    def _name_edited(self, text: str) -> None:
        if self.cur < 0:
            return
        self.mats[self.cur]["name"] = text
        self._refresh_item(self.cur)
        self.title.setText(f"{text}  ·  {self.behaviour.currentText()}")

    def _choice_changed(self) -> None:
        if self._loading or self.cur < 0:
            return
        m = self.mats[self.cur]
        m["behaviour"] = self.behaviour.currentData()
        m["compression"] = self.compression.currentData()
        self._refresh_item(self.cur)
        self._show_color()
        self._update_visibility()

    def _value_changed(self, key: str, value: float) -> None:
        if not self._loading and self.cur >= 0:
            self.mats[self.cur][key] = float(value)

    def _pick_color(self) -> None:
        m = self.mats[self.cur]
        chosen = QColorDialog.getColor(QColor(material_colour(m)), self, t("mat_color"))
        if chosen.isValid():
            m["color"] = chosen.name()
            self._refresh_item(self.cur)
            self._show_color()

    def _add(self) -> None:
        self.mats.append(forms.new_material(self.mats, language()))
        self._orig.append("")
        self._fill_list()
        self.list.setCurrentRow(len(self.mats) - 1)
        self.name.setFocus()
        self.name.selectAll()

    def _copy(self) -> None:
        if self.cur < 0:
            return
        fresh = forms.new_material(self.mats, language())
        clone = {**copy.deepcopy(self.mats[self.cur]), "color": fresh["color"]}
        names = {m["name"] for m in self.mats}
        base, n = clone["name"], 2
        clone["name"] = f"{base} ({n})"
        while clone["name"] in names:
            n += 1
            clone["name"] = f"{base} ({n})"
        self.mats.insert(self.cur + 1, clone)
        self._orig.insert(self.cur + 1, "")
        self._fill_list()
        self.list.setCurrentRow(self.cur + 1)

    def _delete(self) -> None:
        if self.cur < 0:
            return
        in_use = self.used.get(self._orig[self.cur], 0)
        if in_use:
            QMessageBox.information(
                self, t("a_del_mat"), t("mat_in_use", name=self.mats[self.cur]["name"], n=in_use)
            )
            return
        if len(self.mats) == 1:
            return
        del self.mats[self.cur]
        del self._orig[self.cur]
        row = min(self.cur, len(self.mats) - 1)
        self._fill_list()
        self.cur = -1
        self.list.setCurrentRow(row)

    def _move(self, step: int) -> None:
        i, j = self.cur, self.cur + step
        if i < 0 or not 0 <= j < len(self.mats):
            return
        self.mats[i], self.mats[j] = self.mats[j], self.mats[i]
        self._orig[i], self._orig[j] = self._orig[j], self._orig[i]
        self._fill_list()
        self.list.setCurrentRow(j)

    # ---------------------------------------------------------------- result
    def _accept(self) -> None:
        names = [str(m["name"]).strip() for m in self.mats]
        for i, name in enumerate(names):
            if not name:
                self.list.setCurrentRow(i)
                QMessageBox.warning(self, t("dlg_materials"), t("mat_name_empty"))
                return
            if names.count(name) > 1:
                self.list.setCurrentRow(i)
                QMessageBox.warning(self, t("dlg_materials"), t("mat_name_dup", name=name))
                return
        for m, name in zip(self.mats, names, strict=True):
            m["name"] = name
        self.renames = {
            old: m["name"]
            for old, m in zip(self._orig, self.mats, strict=True)
            if old and old != m["name"]
        }
        self.accept()

    def result_materials(self) -> list[dict[str, Any]]:
        return [dict(m) for m in self.mats]


class StudyVariablesDialog(QDialog):
    """The variables of a parametric / reliability study, in a table."""

    def __init__(self, choices: list[dict], rows: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(t("dlg_study_vars"))
        fit_to_screen(self, 1080, 520)
        self.table = StudyTable()
        self.table.set_choices(choices)
        self.table.set_rows(rows)
        if not rows and choices:
            self.table.add_row()
        buttons = ok_cancel()
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addWidget(self.table, 1)
        lay.addWidget(note_label(t("study_note")))
        lay.addWidget(buttons)

    def result_rows(self) -> list[dict[str, Any]]:
        return self.table.rows()
