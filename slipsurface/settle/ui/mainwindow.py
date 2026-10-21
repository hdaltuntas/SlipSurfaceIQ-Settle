"""The main window of SlipSurfaceIQ Settle.

Laid out as SlipSurfaceIQ LE: a breadcrumb workflow bar and the main toolbar
on top, the project tree and the input panel of the current step in the left
dock, the results and figures in the middle, and the soil profile and study
variables tables in a dock below them.

The analysis takes milliseconds, so it runs on every committed change while
"Recompute automatically" is on; a study runs in the background and reports
its progress in the status bar.
"""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QByteArray, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QFont, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME, __version__, forms, study_plots
from ..plotting import PLOT_KEYS, Plotter
from ..render import STUDY_VIEWS, available_study_views
from ..session import Session
from . import texts
from .icons import icon
from .preferences import (
    TECHNOLOGIES,
    apply_theme,
    fit_to_screen,
    is_dark,
    settings,
)
from .texts import core, t
from .widgets import (
    FieldForm,
    FigureView,
    ProjectTree,
    SoilTable,
    StudyTable,
    SummaryView,
    note_label,
)
from .workflow import WorkflowBar

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
EXAMPLES = [
    ("raft_soft_clay", "ex_raft"),
    ("strip_on_sand", "ex_strip"),
    ("embankment_soft_clay", "ex_embankment"),
    ("circular_tank", "ex_circle"),
]
THEORY_URL = "https://github.com/hdaltuntas/SlipSurfaceIQ-Settle/blob/main/docs/{name}"

#: Workflow steps
STEP_PROJECT, STEP_LOAD, STEP_SOIL, STEP_OPTIONS, STEP_RESULTS, STEP_STUDY = range(6)
#: The view each step opens
STEP_VIEW = ["summary", "fig:schematic", "fig:schematic", "fig:stress", "summary", "study"]
HISTORY_LIMIT = 200
RECENT_LIMIT = 8


class SettleWindow(QMainWindow):
    def __init__(
        self,
        values: dict[str, Any] | None = None,
        path: Path | None = None,
        dirty: bool = False,
        session: Session | None = None,
    ) -> None:
        super().__init__()
        fit_to_screen(self, 1560, 940)
        self.setIconSize(QSize(24, 24))
        lang = texts.language()
        self.session = session or Session(lang=lang)
        self.session.set_language(lang)
        self.values: dict[str, Any] = copy.deepcopy(values) if values else forms.defaults(lang)
        self.path: Path | None = Path(path) if path else None
        self.dirty = dirty
        self.result: dict | None = None
        self.error: str = ""
        self.stale = False
        self._figures_dirty = set(PLOT_KEYS)
        self._study_dirty = True
        self._history: list[dict] = [copy.deepcopy(self.values)]
        self._history_index = 0
        self._replaced = False  # closed by a rebuild (language / theme)

        self._compute_timer = QTimer(self, singleShot=True, interval=220)
        self._compute_timer.timeout.connect(self.compute)
        self._poll_timer = QTimer(self, interval=150)
        self._poll_timer.timeout.connect(self._poll_study)

        self._build_actions()
        self._build_central()
        self._build_docks()
        self._build_menus()
        self._build_toolbars()
        self._build_statusbar()

        self._apply_values(self.values, record=False)
        self._restore_layout()
        self._step_changed(STEP_PROJECT)
        self._update_title()
        self._update_actions()
        if self.session.study is not None and self.session.study.rows:
            self._refresh_study()
        if self.session.state()["job"] == "running":  # a study carried over
            self.progress.setRange(0, 0)
            self.progress.show()
            self.cancel_button.show()
            self._poll_timer.start()

    # ================================================================ actions
    def _act(self, key, slot, ic=None, shortcut=None, checkable=False, tip=None) -> QAction:
        text = t(key)
        a = QAction(text, self)
        if ic:
            a.setIcon(icon(ic))
        if shortcut:
            a.setShortcut(QKeySequence(shortcut))
        plain = text.replace("&", "").replace("…", "")
        a.setToolTip(tip or (f"{plain} ({a.shortcut().toString()})" if shortcut else plain))
        a.setStatusTip(tip or plain)
        a.setCheckable(checkable)
        if checkable:
            a.toggled.connect(slot)
        else:
            a.triggered.connect(lambda _=False: slot())
        return a

    def _build_actions(self) -> None:
        A = self._act
        self.a_new = A("a_new", self.new_project, "new", QKeySequence.New)
        self.a_open = A("a_open", self.open_project, "open", QKeySequence.Open)
        self.a_save = A("a_save", self.save_project, "save", QKeySequence.Save)
        self.a_save_as = A("a_save_as", self.save_project_as, None, QKeySequence.SaveAs)
        self.a_undo = A("a_undo", self.undo, "undo", QKeySequence.Undo)
        self.a_redo = A("a_redo", self.redo, "redo", QKeySequence.Redo)
        self.a_compute = A("a_compute", self.compute, "compute", "F5")
        self.a_auto = A("a_auto", self._auto_toggled, "auto", checkable=True)
        self.a_auto.setChecked(settings().value("auto", True, type=bool))
        self.a_study = A("a_study", self.start_study, "study", "F6")
        self.a_cancel = A("a_cancel", self.cancel_study, "cancel", "Esc")
        self.a_report_pdf = A("a_report_pdf", lambda: self.write_report("pdf"), "report", "Ctrl+P")
        self.a_report_html = A("a_report_html", lambda: self.write_report("html"))
        self.a_report_docx = A("a_report_docx", lambda: self.write_report("docx"))
        self.a_export_fig = A("a_export_fig", self.export_figure, "image", "Ctrl+E")
        self.a_export_csv = A("a_export_csv", lambda: self.export_study("csv"), "table")
        self.a_export_xlsx = A("a_export_xlsx", lambda: self.export_study("xlsx"))
        self.a_dark = A("a_dark", self._dark_toggled, "theme", checkable=True)
        self.a_dark.blockSignals(True)
        self.a_dark.setChecked(is_dark())
        self.a_dark.blockSignals(False)
        self.a_theory = A("a_theory", self._theory, "book", "F1")
        self.a_about = A("a_about", self._about, "info")
        self.a_quit = A("a_quit", self.close, None, QKeySequence.Quit)

    def _build_menus(self) -> None:
        mb = self.menuBar()
        m = mb.addMenu(t("m_file"))
        for a in (self.a_new, self.a_open):
            m.addAction(a)
        self.recent_menu = m.addMenu(t("m_recent"))
        self._fill_recent()
        ex = m.addMenu(t("m_examples"))
        for name, key in EXAMPLES:
            act = ex.addAction(t(key))
            act.triggered.connect(lambda _=False, n=name: self.open_example(n))
        m.addSeparator()
        m.addAction(self.a_save)
        m.addAction(self.a_save_as)
        m.addSeparator()
        rm = m.addMenu(icon("report"), t("m_report"))
        for a in (self.a_report_pdf, self.a_report_html, self.a_report_docx):
            rm.addAction(a)
        m.addAction(self.a_export_fig)
        m.addSeparator()
        m.addAction(self.a_quit)

        m = mb.addMenu(t("m_analysis"))
        for a in (
            self.a_compute,
            self.a_auto,
            None,
            self.a_study,
            self.a_cancel,
            None,
            self.a_export_csv,
            self.a_export_xlsx,
        ):
            m.addSeparator() if a is None else m.addAction(a)

        m = mb.addMenu(t("m_view"))
        m.addAction(self.a_dark)
        lm = m.addMenu(t("m_language"))
        for code, name in (("tr", "Türkçe"), ("en", "English")):
            act = lm.addAction(name)
            act.setCheckable(True)
            act.setChecked(texts.language() == code)
            act.triggered.connect(lambda _=False, c=code: self.change_language(c))
        m.addSeparator()
        for dock in (self.left_dock, self.bottom_dock):
            m.addAction(dock.toggleViewAction())

        m = mb.addMenu(t("m_help"))
        m.addAction(self.a_theory)
        m.addAction(self.a_about)

    def _build_toolbars(self) -> None:
        wf = QToolBar(t("dock_project"))
        wf.setObjectName("workflow_toolbar")
        wf.setMovable(False)
        self.workflow = WorkflowBar(
            [
                t(k)
                for k in (
                    "step_project",
                    "step_load",
                    "step_soil",
                    "step_options",
                    "step_results",
                    "step_study",
                )
            ]
        )
        self.workflow.step_changed.connect(self._step_changed)
        wf.addWidget(self.workflow)
        self.addToolBar(Qt.TopToolBarArea, wf)
        self.addToolBarBreak()

        tb = QToolBar("main")
        tb.setObjectName("main_toolbar")
        tb.setIconSize(QSize(24, 24))
        report = QToolButton()
        report.setIcon(icon("report"))
        report.setToolTip(t("a_report"))
        report.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(report)
        for a in (self.a_report_pdf, self.a_report_html, self.a_report_docx):
            menu.addAction(a)
        report.setMenu(menu)
        for a in (
            self.a_new,
            self.a_open,
            self.a_save,
            None,
            self.a_undo,
            self.a_redo,
            None,
            self.a_compute,
            self.a_auto,
            None,
            self.a_study,
            self.a_cancel,
            None,
        ):
            tb.addSeparator() if a is None else tb.addAction(a)
        tb.addWidget(report)
        for a in (self.a_export_fig, self.a_export_csv, None, self.a_dark):
            tb.addSeparator() if a is None else tb.addAction(a)
        self.addToolBar(Qt.TopToolBarArea, tb)

    def _build_statusbar(self) -> None:
        sb = self.statusBar()
        self.progress = QProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.hide()
        self.cancel_button = QToolButton()
        self.cancel_button.setDefaultAction(self.a_cancel)
        self.cancel_button.hide()
        self.version_label = QLabel(f"{APP_NAME} {__version__}")
        self.version_label.setStyleSheet("color:#8491a4;padding:0 6px;")
        sb.addPermanentWidget(self.progress)
        sb.addPermanentWidget(self.cancel_button)
        sb.addPermanentWidget(self.version_label)
        sb.showMessage(t("ready"))

    # ================================================================ widgets
    def _build_central(self) -> None:
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.summary = SummaryView()
        self.text_view = QPlainTextEdit()
        self.text_view.setReadOnly(True)
        mono = QFont("DejaVu Sans Mono")
        mono.setStyleHint(QFont.Monospace)
        mono.setPointSize(10)
        self.text_view.setFont(mono)
        self.text_view.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_view.setFrameShape(QPlainTextEdit.NoFrame)

        self.fig_tabs = QTabWidget()
        self.fig_tabs.setDocumentMode(True)
        self.fig_views: dict[str, FigureView] = {}
        for key in PLOT_KEYS:
            view = FigureView()
            self.fig_views[key] = view
            self.fig_tabs.addTab(view, t(f"fig_{key}"))
        self.fig_tabs.currentChanged.connect(lambda _i: self._draw_current_figure())

        self.tabs.addTab(self.summary, icon("results"), t("tab_summary"))
        self.tabs.addTab(self.fig_tabs, icon("figure"), t("tab_figures"))
        self.tabs.addTab(self.text_view, icon("project"), t("tab_text"))
        self.tabs.addTab(self._build_study_panel(), icon("study"), t("tab_study"))
        self.tabs.currentChanged.connect(lambda _i: self._view_changed())
        self.setCentralWidget(self.tabs)

    def _build_study_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(4, 4, 4, 4)
        row = QHBoxLayout()
        self.study_view_combo = QComboBox()
        self.study_output_combo = QComboBox()
        self.study_view_combo.currentIndexChanged.connect(lambda _i: self._draw_study())
        self.study_output_combo.currentIndexChanged.connect(lambda _i: self._draw_study())
        row.addWidget(QLabel(t("view")))
        row.addWidget(self.study_view_combo)
        row.addSpacing(12)
        row.addWidget(QLabel(t("output")))
        row.addWidget(self.study_output_combo, 1)
        self.run_study_button = QPushButton(icon("study"), t("study_run"))
        self.run_study_button.clicked.connect(self.start_study)
        row.addWidget(self.run_study_button)
        self.study_export_buttons = []
        for a, key in (
            (self.a_export_csv, "study_export_csv"),
            (self.a_export_xlsx, "study_export_xlsx"),
        ):
            b = QPushButton(icon("table"), t(key))
            b.clicked.connect(a.trigger)
            row.addWidget(b)
            self.study_export_buttons.append((a, b))
        lay.addLayout(row)

        split = QSplitter(Qt.Vertical)
        self.study_figure = FigureView()
        split.addWidget(self.study_figure)
        lower = QTabWidget()
        lower.setDocumentMode(True)
        self.study_text = QPlainTextEdit()
        self.study_text.setReadOnly(True)
        self.study_text.setFont(self.text_view.font())
        self.study_table = QTableWidget(0, 0)
        self.study_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.study_table.verticalHeader().setDefaultSectionSize(24)
        self.study_note = note_label(t("study_table_note"))
        table_box = QWidget()
        tl = QVBoxLayout(table_box)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(self.study_table, 1)
        tl.addWidget(self.study_note)
        lower.addTab(self.study_text, t("tab_study_text"))
        lower.addTab(table_box, t("tab_study_table"))
        split.addWidget(lower)
        split.setSizes([620, 260])
        lay.addWidget(split, 1)
        return panel

    def _build_docks(self) -> None:
        lang = texts.language()
        # ---------------------------------------------------------- left: tree + inputs
        self.tree = ProjectTree()
        self.tree.activated.connect(self._tree_activated)
        self.pages = QStackedWidget()
        self.form_project = FieldForm(forms.project_groups(lang))
        self.form_load = FieldForm(forms.foundation_groups(lang))
        self.form_options = FieldForm(forms.option_groups(lang))
        self.form_study = FieldForm(forms.study_groups(lang), note=t("study_vars_page"))
        self.forms = [self.form_project, self.form_load, self.form_options, self.form_study]
        for form in self.forms:
            form.changed.connect(self._field_changed)
        self.pages.addWidget(self.form_project)
        self.pages.addWidget(self.form_load)
        self.pages.addWidget(self._note_page(t("step_soil"), t("soil_page")))
        self.pages.addWidget(self.form_options)
        self.pages.addWidget(self._note_page(t("step_results"), t("results_page")))
        self.pages.addWidget(self.form_study)

        split = QSplitter(Qt.Vertical)
        split.addWidget(self.tree)
        split.addWidget(self.pages)
        split.setSizes([360, 480])
        dock = QDockWidget(t("dock_project"), self)
        dock.setObjectName("project_dock")
        dock.setWidget(split)
        dock.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        self.resizeDocks([dock], [380], Qt.Horizontal)
        self.left_dock = dock

        # ---------------------------------------------------------- bottom: tables
        self.soil_table = SoilTable()
        self.soil_table.changed.connect(self._soil_changed)
        self.vars_table = StudyTable()
        self.vars_table.changed.connect(self._vars_changed)
        self.table_tabs = QTabWidget()
        self.table_tabs.setDocumentMode(True)
        self.table_tabs.addTab(self.soil_table, icon("soil"), t("tab_soil"))
        self.table_tabs.addTab(self.vars_table, icon("study_vars"), t("tab_vars"))
        bottom = QDockWidget(t("dock_tables"), self)
        bottom.setObjectName("tables_dock")
        bottom.setWidget(self.table_tabs)
        bottom.setFeatures(
            QDockWidget.DockWidgetMovable
            | QDockWidget.DockWidgetFloatable
            | QDockWidget.DockWidgetClosable
        )
        self.addDockWidget(Qt.BottomDockWidgetArea, bottom)
        self.resizeDocks([bottom], [250], Qt.Vertical)
        self.bottom_dock = bottom

    @staticmethod
    def _note_page(title: str, text: str) -> QWidget:
        from .widgets import header

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.addWidget(header(title))
        lay.addWidget(note_label(text))
        lay.addStretch(1)
        return page

    # ================================================================ values
    def _apply_values(self, values: dict[str, Any], record: bool = True) -> None:
        """Puts a whole set of values into every editor and recomputes."""
        self.values = copy.deepcopy(values)
        for form in self.forms:
            form.set_values(self.values)
        self._update_shape()
        self.soil_table.set_rows(self.values.get("soil_profile") or [])
        self._refresh_choices()
        self.vars_table.set_rows(self.values.get("study_variables") or [])
        if record:
            self._record()
        self.compute()

    def _field_changed(self, key: str, value: Any) -> None:
        self.values[key] = value
        if key == "shape":
            self._update_shape()
        self._changed(recompute=not key.startswith("study_"))

    def _soil_changed(self) -> None:
        self.values["soil_profile"] = self.soil_table.rows()
        self._changed()

    def _vars_changed(self) -> None:
        self.values["study_variables"] = self.vars_table.rows()
        self._changed(recompute=False)

    def _changed(self, recompute: bool = True) -> None:
        self.dirty = True
        self._record()
        self._update_title()
        if recompute:
            if self.a_auto.isChecked():
                self._compute_timer.start()
            else:
                self.stale = True
                self._show_summary()
                self.statusBar().showMessage(t("stale"))
        self._refresh_tree()

    def _update_shape(self) -> None:
        shape = self.values.get("shape", "rectangle")
        for form in self.forms:
            form.set_shape(shape)

    def _refresh_choices(self) -> None:
        try:
            self.vars_table.set_choices(forms.variable_choices(self.values, texts.language()))
        except (ValueError, KeyError, TypeError, IndexError):
            pass

    # ---------------------------------------------------------------- history
    def _record(self) -> None:
        snapshot = copy.deepcopy(self.values)
        if snapshot == self._history[self._history_index]:
            return
        del self._history[self._history_index + 1 :]
        self._history.append(snapshot)
        if len(self._history) > HISTORY_LIMIT:
            self._history.pop(0)
        self._history_index = len(self._history) - 1
        self._update_actions()

    def undo(self) -> None:
        if self._history_index > 0:
            self._history_index -= 1
            self._restore_history()

    def redo(self) -> None:
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            self._restore_history()

    def _restore_history(self) -> None:
        self.dirty = True
        self._apply_values(self._history[self._history_index], record=False)
        self._update_title()
        self._update_actions()

    # ================================================================ analysis
    def compute(self) -> None:
        self._compute_timer.stop()
        start = time.perf_counter()
        try:
            self.result = self.session.analyse(self.values)
            self.error = ""
            ms = (time.perf_counter() - start) * 1000.0
            self.statusBar().showMessage(t("computed", ms=ms), 6000)
        except ValueError as exc:
            self.result = None
            self.error = str(exc)
            self.statusBar().showMessage(f"{t('input_error')}: {exc}")
        self.stale = False
        self._refresh_choices()
        self._figures_dirty = set(PLOT_KEYS)
        self._show_summary()
        self.text_view.setPlainText(self.result["text"] if self.result else self.error)
        if self.session.study is None:
            self._study_dirty = True  # the study belonged to other inputs
        self._view_changed()
        self._refresh_tree()
        self._update_actions()

    def _show_summary(self) -> None:
        title = str(self.values.get("title") or t("untitled"))
        if self.result is None:
            self.summary.show_error(t("input_error"), self.error or t("no_results"))
            return
        self.summary.show_cards(
            title,
            self.result["headline"],
            self.result["cards"],
            self.result["warnings"],
            t("stale") if self.stale else "",
        )

    def _auto_toggled(self, on: bool) -> None:
        settings().setValue("auto", bool(on))
        if on and self.stale:
            self.compute()

    # ---------------------------------------------------------------- figures
    def _theme(self) -> str:
        return "dark" if is_dark() else "light"

    def _current_view(self) -> str:
        w = self.tabs.currentWidget()
        if w is self.fig_tabs:
            return "fig:" + PLOT_KEYS[self.fig_tabs.currentIndex()]
        if w is self.summary:
            return "summary"
        if w is self.text_view:
            return "text"
        return "study"

    def _view_changed(self) -> None:
        view = self._current_view()
        if view.startswith("fig:"):
            self._draw_current_figure()
        elif view == "study" and self._study_dirty:
            self._refresh_study()

    def _draw_current_figure(self) -> None:
        if self.tabs.currentWidget() is not self.fig_tabs:
            return
        key = PLOT_KEYS[self.fig_tabs.currentIndex()]
        if key not in self._figures_dirty:
            return
        view = self.fig_views[key]
        analysis = self.session.analysis if self.result is not None else None
        if analysis is None:
            view.show_message(self.error or t("no_results"))
        else:
            plotter = Plotter(analysis, texts.language(), self._theme())
            try:
                view.draw(lambda fig: plotter.draw(key, fig))
            except Exception as exc:  # a figure must never take the window down
                view.show_message(f"{type(exc).__name__}: {exc}")
        self._figures_dirty.discard(key)

    def show_view(self, view: str) -> None:
        if view == "summary":
            self.tabs.setCurrentWidget(self.summary)
        elif view == "text":
            self.tabs.setCurrentWidget(self.text_view)
        elif view == "study":
            self.tabs.setCurrentIndex(3)
        elif view.startswith("fig:"):
            key = view[4:]
            self.tabs.setCurrentWidget(self.fig_tabs)
            if key in PLOT_KEYS:
                self.fig_tabs.setCurrentIndex(PLOT_KEYS.index(key))
            self._draw_current_figure()

    # ================================================================ workflow
    def _step_changed(self, step: int) -> None:
        self.workflow.set_current(step, emit=False)
        self.pages.setCurrentIndex(step)
        if step == STEP_SOIL:
            self.table_tabs.setCurrentWidget(self.soil_table)
            self.bottom_dock.show()
        elif step == STEP_STUDY:
            self.table_tabs.setCurrentWidget(self.vars_table)
            self.bottom_dock.show()
        self.show_view(STEP_VIEW[step])

    def _tree_activated(self, step: int, target: str) -> None:
        self._step_changed(step)
        if target:
            self.show_view(target)

    def _refresh_tree(self) -> None:
        study = None
        if self.session.study is not None and self.session.study.rows:
            study = {"method": self.session.study.method, "n": len(self.session.study.rows)}
        self.tree.refresh(self.values, self.result, study, PLOT_KEYS)

    # ================================================================ study
    def start_study(self) -> None:
        if self.session.state()["job"] == "running":
            return
        self.compute()
        started = self.session.start_study(self.values)
        if not started.get("ok"):
            QMessageBox.warning(self, t("tab_study"), started.get("error", ""))
            return
        self.progress.setRange(0, 0)
        self.progress.show()
        self.cancel_button.show()
        self.statusBar().showMessage(t("study_running"))
        self._poll_timer.start()
        self._update_actions()

    def cancel_study(self) -> None:
        if self.session.state()["job"] == "running":
            self.session.cancel()

    def _poll_study(self) -> None:
        state = self.session.state()
        if state["total"]:
            self.progress.setRange(0, state["total"])
            self.progress.setValue(state["done"])
            self.progress.setFormat(t("study_progress", done=state["done"], total=state["total"]))
        if state["job"] == "running":
            return
        self._poll_timer.stop()
        self.progress.hide()
        self.cancel_button.hide()
        if state["job"] == "error":
            box = QMessageBox(QMessageBox.Critical, t("tab_study"), state["error"], parent=self)
            box.setDetailedText(state.get("detail", ""))
            box.exec()
        else:
            self.statusBar().showMessage(state.get("note", ""), 10000)
        self._refresh_study()
        self._refresh_tree()
        self._step_changed(STEP_STUDY)
        self._update_actions()

    def _refresh_study(self) -> None:
        self._study_dirty = False
        payload = self.session.study_payload()
        for combo in (self.study_view_combo, self.study_output_combo):
            combo.blockSignals(True)
            combo.clear()
        if not payload.get("ok"):
            for combo in (self.study_view_combo, self.study_output_combo):
                combo.blockSignals(False)
            self.study_figure.show_message(t("no_study"))
            self.study_text.setPlainText(payload.get("error", ""))
            self.study_table.setRowCount(0)
            self.study_table.setColumnCount(0)
            self.study_note.hide()
            return
        for view in payload["views"]:
            self.study_view_combo.addItem(t(f"study_fig_{view}"), view)
        for out in payload["outputs"]:
            self.study_output_combo.addItem(out["label"], out["value"])
        for combo in (self.study_view_combo, self.study_output_combo):
            combo.blockSignals(False)
        self.study_text.setPlainText(payload["text"])
        table = payload["table"]
        self.study_table.setColumnCount(len(table["columns"]))
        self.study_table.setHorizontalHeaderLabels(table["columns"])
        self.study_table.setRowCount(len(table["rows"]))
        for r, row in enumerate(table["rows"]):
            for c, cell in enumerate(row):
                item = QTableWidgetItem(cell)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.study_table.setItem(r, c, item)
        self.study_table.resizeColumnsToContents()
        self.study_note.setVisible(bool(table["truncated"]))
        self._draw_study()

    def _draw_study(self) -> None:
        study = self.session.study
        view = self.study_view_combo.currentData()
        output = self.study_output_combo.currentData()
        if study is None or not study.rows or view not in STUDY_VIEWS:
            self.study_figure.show_message(t("no_study"))
            return
        if view not in available_study_views(study):
            view = available_study_views(study)[0]
        draw = {
            "oat": study_plots.plot_oat,
            "hist": study_plots.plot_hist,
            "scatter": study_plots.plot_scatter,
            "tornado": study_plots.plot_tornado,
        }[view]
        try:
            self.study_figure.draw(
                lambda fig: draw(fig, study, core(), output or "s_total", theme=self._theme())
            )
        except Exception as exc:
            self.study_figure.show_message(f"{type(exc).__name__}: {exc}")

    # ================================================================ output
    def _ask_save(self, title: str, suffix: str, filt: str) -> str | None:
        folder = settings().value("last_dir", str(Path.home()))
        stem = (
            self.path.stem
            if self.path
            else str(self.values.get("title") or "settle").split(":")[-1].strip() or "settle"
        )
        stem = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in stem).strip()
        path, _ = QFileDialog.getSaveFileName(
            self, title, str(Path(folder) / f"{stem}{suffix}"), filt
        )
        if not path:
            return None
        if not path.lower().endswith(suffix):
            path += suffix
        settings().setValue("last_dir", str(Path(path).parent))
        return path

    def write_report(self, fmt: str) -> None:
        if self.result is None:
            QMessageBox.information(self, t("a_report"), t("need_results"))
            return
        suffix = {"pdf": ".pdf", "html": ".html", "docx": ".docx"}[fmt]
        filt = {"pdf": "PDF (*.pdf)", "html": "HTML (*.html)", "docx": "Word (*.docx)"}[fmt]
        path = self._ask_save(t(f"a_report_{fmt}"), suffix, filt)
        if not path:
            return
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.statusBar().showMessage(t("report_running"))
        try:
            self.session.report(fmt, path)
        except ImportError:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, t("report_failed"), t("docx_missing"))
            return
        except Exception as exc:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, t("report_failed"), f"{type(exc).__name__}: {exc}")
            return
        QApplication.restoreOverrideCursor()
        self.statusBar().showMessage(t("written", path=path), 10000)
        QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def export_figure(self) -> None:
        view = self._current_view()
        if view == "study":
            target = self.study_figure
        elif view.startswith("fig:"):
            target = self.fig_views[view[4:]]
        else:
            self.show_view("fig:schematic")
            target = self.fig_views["schematic"]
        if not target.drawn:
            QMessageBox.information(self, t("a_export_fig"), t("no_figure"))
            return
        path = self._ask_save(t("a_export_fig"), ".png", "PNG (*.png);;SVG (*.svg);;PDF (*.pdf)")
        if path:
            target.figure.savefig(
                path, dpi=200, bbox_inches="tight", facecolor=target.figure.get_facecolor()
            )
            self.statusBar().showMessage(t("written", path=path), 10000)

    def export_study(self, kind: str) -> None:
        if self.session.study is None or not self.session.study.rows:
            QMessageBox.information(self, t("tab_study"), t("study_no_data"))
            return
        path = self._ask_save(
            t(f"a_export_{kind}"), f".{kind}", "CSV (*.csv)" if kind == "csv" else "Excel (*.xlsx)"
        )
        if not path:
            return
        try:
            self.session.export_study(kind, path)
        except ImportError:
            QMessageBox.warning(self, t("save_failed"), t("xlsx_missing"))
            return
        except Exception as exc:
            QMessageBox.critical(self, t("save_failed"), f"{type(exc).__name__}: {exc}")
            return
        self.statusBar().showMessage(t("written", path=path), 10000)

    # ================================================================ files
    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        answer = QMessageBox.question(
            self,
            t("unsaved_title"),
            t("unsaved_text"),
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            QMessageBox.Save,
        )
        if answer == QMessageBox.Save:
            return self.save_project()
        return answer == QMessageBox.Discard

    def _reset_history(self) -> None:
        self._history = [copy.deepcopy(self.values)]
        self._history_index = 0
        self._update_actions()

    def new_project(self) -> None:
        if not self._confirm_discard():
            return
        self.path = None
        self.dirty = False
        self._apply_values(forms.defaults(texts.language()), record=False)
        self._reset_history()
        self._update_title()
        self._step_changed(STEP_PROJECT)

    def open_example(self, name: str) -> None:
        if not self._confirm_discard():
            return
        self.load_file(EXAMPLES_DIR / f"{name}.settle", as_example=True)

    def open_project(self, path: str | None = None) -> None:
        if not self._confirm_discard():
            return
        if path is None:
            folder = settings().value("last_dir", str(Path.home()))
            path, _ = QFileDialog.getOpenFileName(
                self, t("a_open").replace("&", ""), folder, t("file_filter")
            )
            if not path:
                return
        self.load_file(Path(path))

    def load_file(self, path: Path, as_example: bool = False) -> bool:
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
            values = self.session.load_project(data)["values"]
        except (OSError, ValueError) as exc:
            QMessageBox.critical(self, t("open_failed"), f"{path}\n\n{exc}")
            return False
        self.path = None if as_example else Path(path)
        self.dirty = False
        self._apply_values(values, record=False)
        self._reset_history()
        self._update_title()
        if not as_example:
            settings().setValue("last_dir", str(Path(path).parent))
            self._add_recent(str(path))
            self.statusBar().showMessage(t("opened", path=path), 8000)
        self._step_changed(STEP_RESULTS if self.result else STEP_PROJECT)
        return True

    def save_project(self) -> bool:
        if self.path is None:
            return self.save_project_as()
        return self._write(self.path)

    def save_project_as(self) -> bool:
        path = self._ask_save(t("a_save_as").replace("&", ""), ".settle", t("file_filter"))
        if not path:
            return False
        return self._write(Path(path))

    def _write(self, path: Path) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(forms.project_file(self.values), fh, indent=2, ensure_ascii=False)
        except OSError as exc:
            QMessageBox.critical(self, t("save_failed"), f"{path}\n\n{exc}")
            return False
        self.path = path
        self.dirty = False
        self._add_recent(str(path))
        self._update_title()
        self.statusBar().showMessage(t("saved_to", path=path), 8000)
        return True

    def _recent(self) -> list[str]:
        value = settings().value("recent", [])
        if isinstance(value, str):
            value = [value]
        return [p for p in (value or []) if p]

    def _add_recent(self, path: str) -> None:
        recent = [p for p in self._recent() if p != path]
        settings().setValue("recent", [path, *recent][:RECENT_LIMIT])
        self._fill_recent()

    def _fill_recent(self) -> None:
        self.recent_menu.clear()
        recent = [p for p in self._recent() if Path(p).exists()]
        for p in recent:
            act = self.recent_menu.addAction(Path(p).name)
            act.setToolTip(p)
            act.triggered.connect(lambda _=False, path=p: self.open_project(path))
        self.recent_menu.setEnabled(bool(recent))

    # ================================================================ window
    def _update_title(self) -> None:
        name = self.path.name if self.path else t("untitled")
        self.setWindowTitle(f"{name}{' *' if self.dirty else ''} — {APP_NAME}")
        self.setWindowModified(self.dirty)

    def _update_actions(self) -> None:
        running = self.session.state()["job"] == "running"
        has_study = self.session.study is not None and bool(self.session.study.rows)
        self.a_undo.setEnabled(self._history_index > 0)
        self.a_redo.setEnabled(self._history_index < len(self._history) - 1)
        self.a_study.setEnabled(not running)
        self.run_study_button.setEnabled(not running)
        self.a_cancel.setEnabled(running)
        for a in (self.a_report_pdf, self.a_report_html, self.a_report_docx):
            a.setEnabled(self.result is not None and not running)
        for a in (self.a_export_csv, self.a_export_xlsx):
            a.setEnabled(has_study and not running)
        for a, b in self.study_export_buttons:
            b.setEnabled(a.isEnabled())

    def _restore_layout(self) -> None:
        state = settings().value("window_state")
        if isinstance(state, QByteArray) and not state.isEmpty():
            self.restoreState(state)

    def _rebuild(self) -> None:
        """Opens an identical window in the new language / theme and closes this one.

        The values, the file, the history and the session (with any finished
        study) carry over; nothing the user entered is lost.
        """
        win = SettleWindow(self.values, self.path, self.dirty, self.session)
        win._history, win._history_index = self._history, self._history_index
        win._update_actions()
        win.restoreState(self.saveState())
        win.setGeometry(self.geometry())
        step = self.workflow.current
        view = self._current_view()
        if self.isMaximized():
            win.showMaximized()
        else:
            win.show()
        win._step_changed(step)
        win.show_view(view)
        self._replaced = True
        self.close()

    def change_language(self, lang: str) -> None:
        if lang == texts.language():
            return
        texts.set_language(lang)
        settings().setValue("language", lang)
        self._rebuild()

    def _dark_toggled(self, on: bool) -> None:
        apply_theme(bool(on))
        self._rebuild()

    def _theory(self) -> None:
        name = "theory.tr.md" if texts.language() == "tr" else "theory.md"
        QDesktopServices.openUrl(QUrl(THEORY_URL.format(name=name)))

    def _about(self) -> None:
        QMessageBox.about(self, t("a_about"), TECHNOLOGIES.replace("{subtitle}", t("about_sub")))

    def closeEvent(self, ev) -> None:  # noqa: N802 (Qt API)
        if not self._replaced:
            if not self._confirm_discard():
                ev.ignore()
                return
            if self.session.state()["job"] == "running":
                self.session.cancel()
            settings().setValue("window_state", self.saveState())
        self._poll_timer.stop()
        self._compute_timer.stop()
        super().closeEvent(ev)
