"""
Configuration for SlipSurfaceIQ Settle: the default project, the choice lists, and
the theme and plot palette shared by the page and the figures.

The app name and version live in the package's ``__init__`` so that there is
one copy of each; the translations live in `slipsurface.settle.i18n`.
"""

from . import APP_NAME
from . import __version__ as APP_VERSION

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_CONFIG",
    "THEMES",
    "PLOT_PALETTE",
    "SOIL_FILL",
    "COMPRESSION",
    "MATERIAL_DEFAULT",
    "MATERIAL_COLORS",
    "SHAPES",
    "STRESS_METHODS",
    "IMMEDIATE_METHODS",
    "RIGIDITY",
    "BEHAVIOURS",
    "DRAINAGE",
    "ACCENT",
]

MM_PER_M = 1000.0

#: Units of the consolidation inputs: cv in cm²/s and mv in m²/kN, as on the
#: oedometer sheet. The analysis works in metres and years internally.
CV_UNIT = "cm²/s"
MV_UNIT = "m²/kN"
#: cm²/s -> m²/year (Julian year)
CV_TO_M2_PER_YEAR = 1e-4 * 365.25 * 86400.0

# --- Choice lists (the first entry is the default where one is needed) -----
SHAPES = ["rectangle", "strip", "circle", "embankment"]
STRESS_METHODS = ["boussinesq", "two_to_one"]
IMMEDIATE_METHODS = ["elastic", "schmertmann"]
RIGIDITY = ["flexible", "rigid"]
BEHAVIOURS = ["granular", "cohesive", "incompressible"]
#: How the consolidation of a cohesive material is described: compression
#: indices (Cc, Cr, e0) or coefficients of volume compressibility (mv, mv,ur)
COMPRESSION = ["index", "mv"]
DRAINAGE = ["double", "single"]

# --- Interface theme and plot palette --------------------------------------
# --- the desktop window (ui/preferences.py) uses the same colours as the  --
# --- other SlipSurfaceIQ desktop programs, and the figures follow it.     --
ACCENT = "#287ae6"  # selection blue of the SlipSurfaceIQ desktop programs

THEMES = {
    "dark": dict(
        bg="#202c3e",
        panel="#202c3e",
        input_bg="#161e2c",
        fg="#e6edf7",
        fg_dim="#9aa8bc",
        border="#36465d",
        hover="#2a3a52",
        btn="#2a3a52",
        muted="#6c7b90",
        accent="#5aa9f0",
        accent_hover="#7dbcf4",
    ),
    "light": dict(
        bg="#ffffff",
        panel="#ffffff",
        input_bg="#ffffff",
        fg="#243348",
        fg_dim="#5b6b80",
        border="#d9e2ed",
        hover="#f1f5f9",
        btn="#f1f5f9",
        muted="#a3b0c0",
        accent=ACCENT,
        accent_hover="#1f64c0",
    ),
}
# The report's figures: the light palette on white paper.
THEMES["paper"] = dict(THEMES["light"], bg="#FFFFFF", panel="#FFFFFF")

# Semantic colours: the same quantity is the same colour in every figure. Warm and
# muted, to sit on the paper-coloured page; terracotta marks the total.
PLOT_PALETTE = dict(
    immediate="#5B8DB8",
    consolidation="#8C6BB1",
    secondary="#D9A55B",
    total="#C6613F",
    stress="#4E9A8A",
    overburden="#73726C",
    preconsolidation="#5E8C4A",
    limit="#A26A12",
    water="#6FA8C7",
    footing="#8A8680",
    center="#C6613F",
    char="#8C6BB1",
    edge="#D9A55B",
    corner="#4E9A8A",
    shoulder="#8C6BB1",
    midslope="#D9A55B",
    toe="#4E9A8A",
    fill="#C9A876",
    allowable="#B0413E",
)

# Fill colours of the soil behaviours in the schematic, for layers whose
# material carries no colour of its own (theme-dependent, since a light sandy
# tone reads poorly on a dark background).
SOIL_FILL = {
    "light": {"granular": "#E3C98F", "cohesive": "#A7B8A0", "incompressible": "#B9B4AE"},
    "dark": {"granular": "#8A7250", "cohesive": "#5E6E58", "incompressible": "#6B665F"},
}

#: Colours offered to new materials, in turn (muted, readable in both themes)
MATERIAL_COLORS = [
    "#E3C98F",
    "#D9B36C",
    "#A7B8A0",
    "#8FA88A",
    "#C9A0A0",
    "#B9B4AE",
    "#9DB4CC",
    "#C7B39A",
    "#A8A1C4",
    "#D4C9A8",
]

#: Every property a material may have, with its default. E [MPa] is the drained
#: modulus of a granular material and the undrained modulus of a cohesive one
#: (0: no immediate settlement); mv, mv_ur in m²/kN; cv in cm²/s;
#: OCR = σ'p / σ'v0; Calpha_eps = Cα / (1 + e0), for the mv description.
MATERIAL_DEFAULT = {
    "name": "Material",
    "color": "",
    "behaviour": "granular",
    "compression": "index",
    "gamma": 18.0,
    "gamma_sat": 19.0,
    "E": 10.0,
    "nu": 0.30,
    "Cc": 0.0,
    "Cr": 0.0,
    "e0": 0.6,
    "OCR": 1.0,
    "mv": 0.0,
    "mv_ur": 0.0,
    "cv": 0.0,
    "Calpha": 0.0,
    "Calpha_eps": 0.0,
}
SOIL_FILL["paper"] = SOIL_FILL["light"]

DEFAULT_CONFIG = {
    "project_info": {
        "title": "",
        "analyst": "",
    },
    "foundation": {
        "shape": "rectangle",
        "B": 8.0,  # width, or diameter of a circle [m]
        "L": 16.0,  # length of a rectangle [m]
        "Df": 1.5,  # depth of the foundation base [m]
        "q": 100.0,  # applied (gross) bearing pressure [kPa]
        "net_pressure": True,  # deduct the overburden removed by the excavation
    },
    # An embankment (shape "embankment"): a long trapezoidal fill on the ground
    # surface, loading it with γ·H under the crest and less under the slopes.
    "embankment": {
        "crest": 12.0,  # crest width [m]
        "height": 4.0,  # [m]
        "slope_left": 26.57,  # slope angles from the horizontal [°] (1V:2H)
        "slope_right": 26.57,
        "gamma": 20.0,  # unit weight of the fill [kN/m³]
    },
    "groundwater": {
        "depth": 2.0,  # below ground surface [m]
        "gamma_water": 9.81,  # [kN/m³]
    },
    # A new project starts without materials or layers: the user defines them.
    "materials": [],
    "soil_profile": [],
    "options": {
        "stress_method": "boussinesq",
        "immediate_method": "elastic",
        "rigidity": "flexible",
        "sublayer": 0.25,  # thickness of the calculation sublayers [m]
        "depth_ratio": 0.10,  # influence depth where Δσ = ratio · σ'v0 (0: whole profile)
        "design_life": 50.0,  # years, for secondary compression and creep
        "creep": True,  # Schmertmann's time factor C2
    },
    "criteria": {
        "s_allow": 150.0,  # allowable total settlement [mm] (0: no check)
        "distortion_allow": 500.0,  # allowable angular distortion 1 / x (0: no check)
    },
}


# The profile of the sample project (the command line's `example`, the tests and
# the bundled raft example): a raft on soft clay between sands. Not a default —
# a new project has no materials until the user defines them.
SAMPLE_MATERIALS = [
    {
        **MATERIAL_DEFAULT,
        "name": "Fill",
        "color": "#D9B36C",
        "gamma": 18.0,
        "gamma_sat": 19.0,
        "E": 10.0,
    },
    {
        **MATERIAL_DEFAULT,
        "name": "Medium dense sand",
        "color": "#E3C98F",
        "gamma": 18.5,
        "gamma_sat": 20.0,
        "E": 25.0,
    },
    {
        **MATERIAL_DEFAULT,
        "name": "Soft clay",
        "color": "#A7B8A0",
        "behaviour": "cohesive",
        "gamma": 17.0,
        "gamma_sat": 17.5,
        "E": 6.0,
        "nu": 0.50,
        "Cc": 0.32,
        "Cr": 0.05,
        "e0": 1.05,
        "OCR": 1.3,
        "mv": 0.001,
        "mv_ur": 0.00015,
        "cv": 4.75e-4,
        "Calpha": 0.010,
        "Calpha_eps": 0.005,
    },
    {
        **MATERIAL_DEFAULT,
        "name": "Dense sand",
        "color": "#C7B39A",
        "gamma": 19.5,
        "gamma_sat": 21.0,
        "E": 60.0,
        "e0": 0.5,
    },
]
SAMPLE_PROFILE = [
    {"material": "Fill", "thickness": 1.5, "drainage": "double"},
    {"material": "Medium dense sand", "thickness": 3.5, "drainage": "double"},
    {"material": "Soft clay", "thickness": 6.0, "drainage": "double"},
    {"material": "Dense sand", "thickness": 10.0, "drainage": "double"},
]
SAMPLE_CONFIG = {
    **DEFAULT_CONFIG,
    "project_info": {"title": "Project: Raft on soft clay", "analyst": ""},
    "materials": SAMPLE_MATERIALS,
    "soil_profile": SAMPLE_PROFILE,
}
