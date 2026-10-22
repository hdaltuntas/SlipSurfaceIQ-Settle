"""The desktop interface, driven offscreen: the window builds, follows the inputs,
draws every figure, runs a study, saves and reopens a project, and keeps the
user's work across a change of language or theme."""

import json
import re
import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QSettings  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from slipsurface.settle import forms  # noqa: E402
from slipsurface.settle.plotting import PLOT_KEYS  # noqa: E402

UI = Path(__file__).resolve().parents[1] / "slipsurface" / "settle" / "ui"


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    application.setStyle("Fusion")
    return application


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    from slipsurface.settle.ui import preferences, texts

    store = QSettings(str(tmp_path / "settings.ini"), QSettings.IniFormat)
    monkeypatch.setattr(preferences, "settings", lambda: store)
    import slipsurface.settle.ui.mainwindow as mw

    monkeypatch.setattr(mw, "settings", lambda: store)
    texts.set_language("tr")
    preferences.apply_theme(False)
    win = mw.SettleWindow()
    win.show()
    app.processEvents()
    yield win
    for w in QApplication.topLevelWidgets():
        if isinstance(w, mw.SettleWindow):
            w.dirty = False
            w.close()
    app.processEvents()


def _wait_study(app, win, limit=60.0):
    start = time.time()
    while win.session.state()["job"] == "running" and time.time() - start < limit:
        app.processEvents()
        time.sleep(0.02)
    win._poll_study()


def test_the_window_opens_on_the_default_project_and_computes(window):
    assert window.result is not None
    assert window.result["total"] == pytest.approx(141.7, abs=0.2)
    assert "Toplam oturma" in window.summary.toPlainText()
    assert window.tree.topLevelItemCount() == 3
    assert window.windowTitle().startswith("Adsız")


def test_a_committed_input_recomputes(window):
    before = window.result["total"]
    window.form_load.editors["q"].setValue(150.0)
    window.compute()  # the debounce timer would do this
    assert window.values["q"] == 150.0
    assert window.result["total"] > before
    assert window.dirty and window.windowTitle().endswith("— SlipSurfaceIQ Settle")
    assert "*" in window.windowTitle()


def test_manual_mode_marks_the_results_stale(window):
    window.a_auto.setChecked(False)
    window.form_load.editors["q"].setValue(120.0)
    assert window.stale
    assert "F5" in window.summary.toPlainText()
    window.compute()
    assert not window.stale


def test_an_impossible_input_is_explained_not_raised(window):
    window.form_load.editors["Df"].setValue(45.0)  # below the profile
    window.compute()
    assert window.result is None
    assert "profil" in window.summary.toPlainText().lower()
    window.show_view("fig:schematic")
    assert not window.fig_views["schematic"].drawn


def test_the_embankment_shows_only_its_own_inputs(window):
    combo = window.form_load.editors["shape"]
    combo.setCurrentIndex(combo.findData("embankment"))
    window.compute()
    assert window.values["shape"] == "embankment"
    assert window.form_load.editors["B"].isHidden()
    assert not window.form_load.editors["emb_height"].isHidden()
    assert window.form_options.editors["rigidity"].isHidden()
    assert window.result is not None


def test_every_figure_draws(window):
    for key in PLOT_KEYS:
        window.show_view(f"fig:{key}")
        assert window.fig_views[key].drawn, key
        assert window.fig_views[key].figure.axes, key


def test_the_layer_table_adds_moves_and_removes_layers(window):
    n = len(window.values["soil_profile"])
    window.layer_table.add_row()
    assert len(window.values["soil_profile"]) == n + 1
    window.layer_table.table.selectRow(0)
    window.layer_table.move_row(1)
    names = [row["material"] for row in window.values["soil_profile"]]
    assert names[1] == "Fill"
    window.layer_table.table.selectRow(n)
    window.layer_table.remove_row()
    assert len(window.values["soil_profile"]) == n


def test_a_bad_number_in_the_layer_table_is_refused(window):
    col = window.layer_table.keys.index("thickness")
    item = window.layer_table.table.item(2, col)
    item.setText("abc")
    assert item.text() == "6"
    item.setText("7,5")  # a decimal comma is accepted
    assert window.values["soil_profile"][2]["thickness"] == 7.5


def test_a_layer_takes_another_material_and_drainage_follows_it(window):
    col = window.layer_table.keys.index("material")
    drainage = window.layer_table.table.cellWidget(1, window.layer_table.keys.index("drainage"))
    assert not drainage.isEnabled()  # a sand
    combo = window.layer_table.table.cellWidget(1, col)
    combo.setCurrentIndex(combo.findData("Soft clay"))
    window.compute()
    assert window.values["soil_profile"][1]["material"] == "Soft clay"
    assert drainage.isEnabled()
    assert window.layer_table.table.cellWidget(1, col).itemIcon(0).isNull() is False


def _materials_dialog(window, monkeypatch, edit):
    """Opens the materials dialog, lets `edit` work on it, and accepts it."""
    from PySide6.QtWidgets import QDialog

    import slipsurface.settle.ui.mainwindow as mw

    real = mw.MaterialsDialog

    class Driven(real):
        def exec(self):
            edit(self)
            self._accept()
            return QDialog.Accepted if self.result() == QDialog.Accepted else QDialog.Rejected

    monkeypatch.setattr(mw, "MaterialsDialog", Driven)
    window.define_materials()


def test_a_clay_defined_by_mv_changes_the_settlement(window, monkeypatch):
    before = window.result["total"]

    def edit(dlg):
        dlg.list.setCurrentRow(2)
        assert dlg.spins["Cc"].isVisibleTo(dlg) and not dlg.spins["mv"].isVisibleTo(dlg)
        dlg.compression.setCurrentIndex(dlg.compression.findData("mv"))
        assert dlg.spins["mv"].isVisibleTo(dlg) and not dlg.spins["Cc"].isVisibleTo(dlg)
        dlg.spins["mv"].setValue(2.0)

    _materials_dialog(window, monkeypatch, edit)
    window.compute()
    clay = window.values["materials"][2]
    assert clay["compression"] == "mv" and clay["mv"] == 2.0
    assert window.result["total"] > before
    assert window.dirty and window.a_undo.isEnabled()


def test_an_incompressible_material_shows_only_its_weights(window, monkeypatch):
    def edit(dlg):
        dlg._add()
        dlg.name.setText("Kireçtaşı")
        dlg._name_edited("Kireçtaşı")
        dlg.behaviour.setCurrentIndex(dlg.behaviour.findData("incompressible"))
        shown = [k for k, s in dlg.spins.items() if s.isVisibleTo(dlg)]
        assert shown == ["gamma", "gamma_sat"]
        assert not dlg.compression.isVisibleTo(dlg)

    _materials_dialog(window, monkeypatch, edit)
    assert window.values["materials"][-1]["name"] == "Kireçtaşı"
    window.layer_table.add_row()
    combo = window.layer_table.table.cellWidget(4, 0)
    combo.setCurrentIndex(combo.findData("Kireçtaşı"))
    window.compute()
    rock = [row for row in window.session.analysis.results["layers"] if row["name"] == "Kireçtaşı"]
    assert rock and rock[0]["immediate"] == 0.0 and rock[0]["method"] == "incompressible"


def test_renaming_a_material_renames_its_layers(window, monkeypatch):
    def edit(dlg):
        dlg.list.setCurrentRow(2)
        dlg.name.setText("Yumuşak kil")
        dlg._name_edited("Yumuşak kil")

    _materials_dialog(window, monkeypatch, edit)
    assert window.values["soil_profile"][2]["material"] == "Yumuşak kil"
    assert window.result is not None


def test_a_material_in_use_cannot_be_deleted(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    shown = []
    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: shown.append(a[2]))

    def edit(dlg):
        dlg.list.setCurrentRow(0)
        dlg._delete()
        assert len(dlg.mats) == 4

    _materials_dialog(window, monkeypatch, edit)
    assert shown and "Fill" in shown[0]


def test_duplicate_material_names_are_refused(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from slipsurface.settle.ui.dialogs import MaterialsDialog

    warned = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: warned.append(a[2]))
    dlg = MaterialsDialog(window.values["materials"], {}, window)
    dlg.list.setCurrentRow(1)
    dlg._name_edited("Fill")
    dlg._accept()
    from PySide6.QtWidgets import QDialog

    assert warned and dlg.result() != QDialog.Accepted


def test_there_is_no_bottom_band(window):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QDockWidget

    docks = window.findChildren(QDockWidget)
    assert [window.dockWidgetArea(d) for d in docks] == [Qt.LeftDockWidgetArea]


def test_undo_and_redo_restore_the_inputs(window):
    window.form_load.editors["B"].setValue(10.0)
    window.form_load.editors["L"].setValue(20.0)
    assert window.a_undo.isEnabled()
    window.undo()
    assert window.values["L"] == 16.0 and window.values["B"] == 10.0
    assert window.form_load.editors["L"].value() == 16.0
    window.undo()
    assert window.values["B"] == 8.0
    window.redo()
    window.redo()
    assert window.values["L"] == 20.0


def test_a_project_saves_and_opens_again(window, tmp_path):
    window.form_project.editors["title"].setText("Deneme")
    window.form_project.editors["title"].editingFinished.emit()
    window.layer_table.add_row()
    path = tmp_path / "deneme.settle"
    assert window._write(path)
    assert not window.dirty and window.windowTitle().startswith("deneme.settle")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["format"] == forms.FILE_FORMAT
    assert data["project_info"]["title"] == "Deneme"

    window.new_project()
    assert window.values["title"] != "Deneme"
    assert window.load_file(path)
    assert window.values["title"] == "Deneme"
    assert len(window.values["soil_profile"]) == 5
    assert window.form_project.editors["title"].text() == "Deneme"


@pytest.mark.parametrize(
    "name", ["raft_soft_clay", "strip_on_sand", "embankment_soft_clay", "circular_tank"]
)
def test_every_example_opens_and_computes(window, name):
    from slipsurface.settle.ui.mainwindow import EXAMPLES_DIR

    assert window.load_file(EXAMPLES_DIR / f"{name}.settle", as_example=True)
    assert window.path is None and not window.dirty
    assert window.result is not None, window.error
    assert window.result["total"] > 0


def _add_variable(window, monkeypatch):
    """Adds one study variable through the Study Variables dialog."""
    from PySide6.QtWidgets import QDialog

    import slipsurface.settle.ui.mainwindow as mw

    monkeypatch.setattr(mw.StudyVariablesDialog, "exec", lambda self: QDialog.Accepted)
    window.define_study_variables()  # an empty table opens with one row


def test_a_study_runs_in_the_background_and_is_shown(app, window, monkeypatch):
    window.form_study.editors["study_n"].setValue(40)
    _add_variable(window, monkeypatch)
    assert window.values["study_variables"]
    assert window.values["study_variables"][0]["label"] in window.vars_list.text()
    window.start_study()
    _wait_study(app, window)
    assert window.session.study is not None and len(window.session.study.rows) == 40
    assert window.study_view_combo.count() >= 2
    assert window.study_figure.drawn
    assert "ÇALIŞMA SONUÇLARI" in window.study_text.toPlainText()
    assert window.study_table.rowCount() == 40
    assert window.workflow.current == 5
    for i in range(window.study_view_combo.count()):
        window.study_view_combo.setCurrentIndex(i)
        assert window.study_figure.drawn


def test_a_study_variable_takes_its_input_s_project_value(window, monkeypatch):
    _add_variable(window, monkeypatch)
    row = window.values["study_variables"][0]
    choices = forms.variable_choices(window.values, "tr")
    choice = next(c for c in choices if c["value"] == row["path"])
    assert row["mean"] == pytest.approx(choice["base"])
    assert row["label"] == choice["label"]


def test_a_study_without_variables_says_so(window, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    shown = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: shown.append(a[2]))
    window.values["study_variables"] = []
    window.start_study()
    assert shown and "değişken" in shown[0]


def test_changing_the_language_keeps_the_work(app, window):
    import slipsurface.settle.ui.mainwindow as mw

    window.form_load.editors["q"].setValue(130.0)
    window.change_language("en")
    app.processEvents()
    windows = [
        w
        for w in QApplication.topLevelWidgets()
        if isinstance(w, mw.SettleWindow) and w.isVisible()
    ]
    assert len(windows) == 1 and windows[0] is not window
    new = windows[0]
    assert new.values["q"] == 130.0 and new.dirty
    assert new.a_undo.isEnabled()
    assert "Total settlement" in new.summary.toPlainText()
    assert new.menuBar().actions()[0].text() == "&File"
    from slipsurface.settle.ui import texts

    texts.set_language("tr")


def test_the_dark_theme_rebuilds_the_window(app, window):
    import slipsurface.settle.ui.mainwindow as mw
    from slipsurface.settle.ui import preferences

    window.a_dark.setChecked(True)
    app.processEvents()
    new = [
        w
        for w in QApplication.topLevelWidgets()
        if isinstance(w, mw.SettleWindow) and w.isVisible()
    ][0]
    assert preferences.is_dark() and new.a_dark.isChecked()
    new.show_view("fig:stress")
    assert new.fig_views["stress"].figure.get_facecolor()[0] < 0.3  # dark background
    preferences.apply_theme(False)


def test_every_interface_text_exists_in_both_languages():
    from slipsurface.settle.ui import texts

    for key, pair in texts.UI.items():
        assert len(pair) == 2 and all(pair), key
    used = set()
    for path in UI.glob("*.py"):
        used.update(re.findall(r'\bt\("([a-z_A-Z0-9]+)"[,)]', path.read_text(encoding="utf-8")))
    for lang in ("en", "tr"):
        texts.set_language(lang)
        missing = [key for key in used if texts.t(key) == key]
        assert not missing, (lang, missing)
    texts.set_language("tr")
