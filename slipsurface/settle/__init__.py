"""
SlipSurfaceIQ Settle — settlement analysis of shallow foundations and embankments.

A desktop program (PySide6) that works out how much, and how fast, a shallow
foundation or an embankment settles on a layered soil profile:

    1. Stresses        — in-situ σ'v0 and σ'p; the stress increase beneath the
                         foundation by Boussinesq (rectangle, strip, circle) or 2:1,
                         and exactly beneath a trapezoidal embankment
    2. Immediate       — layered elastic (Steinbrenner) or Schmertmann (1978)
    3. Consolidation   — primary settlement of the clay layers from Cc, Cr, e0
                         and σ'p, and secondary compression from Cα
    4. Time            — Terzaghi's one-dimensional consolidation, per layer
    5. Checks          — total settlement and angular distortion

On top of it, a parametric or reliability study sweeps any input (a range, or
a distribution) and reports sensitivities and the probability of exceeding
the allowable settlement.

Package layout
--------------
    slipsurface.settle.config         app identity, defaults, themes, palette
    slipsurface.settle.i18n           every text of the program, English and Turkish
    slipsurface.settle.stress         Boussinesq, 2:1 and Steinbrenner solutions
    slipsurface.settle.consolidation  Terzaghi time factor, compression of clay
    slipsurface.settle.engine         the settlement analysis
    slipsurface.settle.study          parametric / reliability studies
    slipsurface.settle.plotting       analysis figures
    slipsurface.settle.study_plots    study figures
    slipsurface.settle.report         calculation report: HTML, PDF, DOCX
    slipsurface.settle.forms          input schema and readers (interface-independent)
    slipsurface.settle.session        one working session: analyse, study, report, files
    slipsurface.settle.ui             the desktop interface (PySide6)
    slipsurface.settle.cli            command line: gui, run, study, example

Run it:  slipsurface-settle            (or  python -m slipsurface.settle)
"""

__version__ = "2026.0.0"

APP_NAME = "SlipSurfaceIQ Settle"
ORG = "SlipSurface"

__all__ = ["__version__", "APP_NAME", "ORG"]
