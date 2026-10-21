"""
Tests for the things a green test suite would otherwise miss: the files that
have to travel inside the wheel and the installers, the version numbers that
have to agree, and the command line as a user meets it.
"""

import json
import os
import re

import slipsurface.settle
from slipsurface.settle import cli, forms

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(ROOT, "slipsurface", "settle")


def read(*parts) -> str:
    with open(os.path.join(ROOT, *parts), encoding="utf-8") as fh:
        return fh.read()


def test_the_version_is_read_from_the_package():
    assert 'version = { attr = "slipsurface.settle.__version__" }' in read("pyproject.toml")
    assert re.fullmatch(r"\d{4}\.\d+\.\d+", slipsurface.settle.__version__)


def test_the_installer_build_reads_the_same_version():
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "build", os.path.join(ROOT, "packaging", "build.py")
    )
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    assert build.version() == slipsurface.settle.__version__
    assert build.msi_version("2026.1.0") == "26.1.0"


def test_the_release_notes_name_the_version():
    assert slipsurface.settle.__version__ in read("RELEASE_NOTES.md")


def test_slipsurface_is_a_namespace_package():
    """Other SlipSurfaceIQ products may install `slipsurface.<product>` beside this one."""
    assert not os.path.exists(os.path.join(ROOT, "slipsurface", "__init__.py"))


def test_the_package_data_is_declared_and_present():
    text = read("pyproject.toml")
    assert '"slipsurface.settle" = ["fonts/*.ttf", "fonts/*.txt", "examples/*.settle"]' in text
    fonts = os.listdir(os.path.join(PACKAGE, "fonts"))
    for name in ("Regular", "SemiBold", "Bold", "Italic"):
        assert f"SourceSans3-{name}.ttf" in fonts
    examples = os.listdir(os.path.join(PACKAGE, "examples"))
    assert len([e for e in examples if e.endswith(".settle")]) >= 4


def test_the_entry_points_point_at_something_that_exists():
    text = read("pyproject.toml")
    assert 'slipsurface-settle = "slipsurface.settle.cli:main"' in text
    assert 'slipsurface-settle-cli = "slipsurface.settle.cli:main"' in text
    assert callable(cli.main)


def test_the_dependencies_are_the_ones_the_program_imports():
    """Nothing in the runtime path may need a package the wheel does not ask for."""
    text = read("pyproject.toml")
    hard = text.split("[project.optional-dependencies]")[0]
    for required in ("PySide6", "numpy", "matplotlib", "reportlab", "QtAwesome"):
        assert re.search(rf'"{required}>=', hard), f"{required} is not a dependency"
    for folder, _, files in os.walk(PACKAGE):
        for name in files:
            if name.endswith(".py"):
                source = open(os.path.join(folder, name), encoding="utf-8").read()
                assert not re.search(
                    r"^\s*(import|from)\s+(scipy|shapely|tkinter)", source, re.MULTILINE
                ), name


def test_the_optional_formats_are_optional():
    """python-docx and openpyxl are extras: importing the package must not need them."""
    text = read("pyproject.toml")
    assert 'docx = ["python-docx' in text and 'xlsx = ["openpyxl' in text
    hard = text.split("[project.optional-dependencies]")[0]
    for name in ("python-docx", "openpyxl"):
        assert name not in hard


def test_the_command_line_writes_runs_and_studies_a_project(tmp_path, capsys):
    path = tmp_path / "p.settle"
    assert cli.main(["example", "-o", str(path)]) == 0
    assert json.loads(path.read_text(encoding="utf-8"))["study"]["variables"]
    capsys.readouterr()
    assert cli.main(["run", str(path), "--lang", "tr"]) == 0
    assert "OTURMA ANALİZİ SONUÇLARI" in capsys.readouterr().out
    assert cli.main(["study", str(path), "-o", str(tmp_path / "s.csv")]) == 0
    assert "STUDY RESULTS" in capsys.readouterr().out
    assert (tmp_path / "s.csv").stat().st_size > 1000


def test_the_command_line_writes_a_report(tmp_path, capsys):
    path = tmp_path / "p.settle"
    cli.main(["example", "-o", str(path)])
    assert cli.main(["run", str(path), "-o", str(tmp_path / "r.html")]) == 0
    assert (tmp_path / "r.html").stat().st_size > 10000


def test_the_bare_command_opens_the_interface(monkeypatch):
    """`slipsurface-settle` with no subcommand, or with a project file, opens the window."""
    calls = []

    import slipsurface.settle.ui.app as app_module

    monkeypatch.setattr(
        app_module, "run", lambda project_path=None, smoke=None: calls.append(project_path) or 0
    )
    assert cli.main([]) == 0
    assert cli.main(["some/project.settle"]) == 0
    assert calls == [None, "some/project.settle"]


def test_a_refused_analysis_prints_a_message_not_a_traceback(tmp_path, capsys):
    values = forms.defaults()
    values["Df"] = 50.0  # below the soil profile
    path = tmp_path / "impossible.settle"
    path.write_text(json.dumps(forms.project_file(values)), encoding="utf-8")
    assert cli.main(["run", str(path)]) == 1
    captured = capsys.readouterr()
    assert "SlipSurfaceIQ Settle:" in captured.err
    assert "profile" in captured.err
    assert "Traceback" not in captured.err


def test_a_missing_project_file_is_reported_plainly(tmp_path, capsys):
    assert cli.main(["run", str(tmp_path / "nothing.settle")]) == 1
    assert "Traceback" not in capsys.readouterr().err


def test_main_checks_the_environment(capsys):
    import importlib.util

    spec = importlib.util.spec_from_file_location("main_module", os.path.join(ROOT, "main.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.main(["--check"]) == 0
    assert "Environment ready." in capsys.readouterr().out
