"""Command line interface.

With no subcommand the desktop interface opens; ``run``, ``study`` and
``example`` work without a display, for batch use and scripting.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import APP_NAME, __version__


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="slipsurface-settle",
        description="Settlement analysis of shallow foundations and embankments: stress "
        "distribution, immediate (elastic / Schmertmann), consolidation and "
        "secondary settlement, consolidation time, and parametric / reliability "
        "studies.",
    )
    parser.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    parser.set_defaults(project=None, smoke=None)
    sub = parser.add_subparsers(dest="command")

    gui = sub.add_parser("gui", help="open the desktop interface (the default)")
    gui.add_argument("project", nargs="?", default=None, help="a .settle project to open")
    gui.add_argument("--smoke", type=float, default=None, help=argparse.SUPPRESS)

    run = sub.add_parser("run", help="analyse a project file and print the results")
    run.add_argument("project", help="path to a .settle / .json project file")
    run.add_argument("-o", "--out", default=None, help="write a report here (.pdf / .html / .docx)")
    run.add_argument("--lang", default="en", choices=["en", "tr"])

    study = sub.add_parser("study", help="run the study defined in a project file")
    study.add_argument("project", help="path to a .settle / .json project file")
    study.add_argument("-o", "--out", default=None, help="write the samples here (.csv / .xlsx)")
    study.add_argument("--lang", default="en", choices=["en", "tr"])

    example = sub.add_parser("example", help="write a starter project file")
    example.add_argument("-o", "--out", default="project.settle")

    # `slipsurface-settle file.settle` opens the file in the interface.
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].lower().endswith((".settle", ".json")):
        argv = ["gui", *argv]

    args = parser.parse_args(argv)
    command = args.command or "gui"
    try:
        return _dispatch(command, args)
    except (ValueError, RuntimeError, OSError) as exc:
        # The analysis refuses impossible input with a sentence worth reading
        # (a foundation below the profile, a layer without a modulus, an
        # unreadable project file). A traceback would bury it, so only
        # unexpected failures keep theirs.
        print(f"{APP_NAME}: {exc}", file=sys.stderr)
        return 1


def _example_study(values: dict) -> list:
    """Two study variables for the starter project, so `study` has something to do."""
    return [
        {
            "path": "foundation.q",
            "label": "Foundation · q",
            "mode": "dist",
            "dist": "normal",
            "mean": values["q"],
            "cov": 0.10,
            "min": 0,
            "max": 0,
            "n_points": 5,
        },
        {
            "path": "materials.2.Cc",
            "label": "Soft clay · Cc",
            "mode": "dist",
            "dist": "lognormal",
            "mean": values["materials"][2]["Cc"],
            "cov": 0.25,
            "min": 0,
            "max": 0,
            "n_points": 5,
        },
    ]


def _dispatch(command: str, args) -> int:
    """Runs one command; raises on anything that goes wrong."""
    if command == "gui":
        from .ui.app import run

        return run(project_path=args.project, smoke=args.smoke)

    from . import forms

    if command == "example":
        values = forms.defaults()
        values["study_variables"] = _example_study(values)
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(forms.project_file(values), fh, indent=2, ensure_ascii=False)
        print(args.out)
        return 0

    with open(args.project, encoding="utf-8") as fh:
        data = json.load(fh)

    from .session import Session

    session = Session(lang=args.lang)
    values = session.load_project(data)["values"]

    if command == "run":
        result = session.analyse(values)
        print(result["text"])
        if args.out:
            fmt = args.out.lower().rsplit(".", 1)[-1]
            print(session.report(fmt if fmt in ("pdf", "html", "docx") else "pdf", args.out))
        return 0

    # A study: analyse the foundation first, so the report and the figures
    # have something to sit beside, then sample.
    session.analyse(values)
    started = session.start_study(values)
    if not started["ok"]:
        print(started["error"], file=sys.stderr)
        return 1
    import time

    last = -1
    while session.state()["job"] == "running":
        state = session.state()
        if state["total"] and state["done"] != last:
            last = state["done"]
            print(f"\r{state['done']} / {state['total']}", end="", file=sys.stderr, flush=True)
        time.sleep(0.2)
    print("", file=sys.stderr)
    state = session.state()
    if state["job"] == "error":
        print(state["error"], file=sys.stderr)
        return 1
    payload = session.study_payload()
    if not payload["ok"]:
        print(payload["error"], file=sys.stderr)
        return 1
    print(payload["text"])
    if args.out:
        kind = "xlsx" if args.out.lower().endswith(".xlsx") else "csv"
        print(session.export_study(kind, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
