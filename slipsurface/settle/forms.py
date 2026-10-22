"""
Input schema and readers for SlipSurfaceIQ Settle.

Every input of the program is declared here once: key, bilingual label, unit,
range and default. The desktop interface builds its forms from this schema, and
`to_config()` turns the values that come back into the nested configuration
dictionary the analysis core expects. Labels therefore exist in one place
only, and there is no second copy to keep in step.

The flat field keys (``B``, ``water_depth``, ``depth_ratio`` …) are the ones
the interface uses; the nested keys of the configuration
(``foundation.B``, ``groundwater.depth`` …) are the ones the engine and the
``.settle`` project files use. `to_config()` and `from_config()` convert
between the two.

This module depends on neither HTTP nor the interface, and is tested directly.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import (
    BEHAVIOURS,
    COMPRESSION,
    DEFAULT_CONFIG,
    CV_TO_M2_PER_YEAR,
    CV_UNIT,
    DRAINAGE,
    IMMEDIATE_METHODS,
    MATERIAL_COLORS,
    MATERIAL_DEFAULT,
    MV_UNIT,
    RIGIDITY,
    SAMPLE_CONFIG,
    SHAPES,
    STRESS_METHODS,
)
from .i18n import TRANSLATIONS

#: Name and version written into project files
FILE_FORMAT = "slipsurface-settle"
# Project files saved before the product was renamed still open.
READ_FORMATS = (FILE_FORMAT, "slipsurface-settle")
# 0.2: materials, and layers that name one (0.1 carried the properties per layer)
# 0.3: cv in cm²/s and mv in m²/kN (before: m²/year and m²/MN)
FILE_VERSION = "0.3"
#: Factors that bring a pre-0.3 value to the present units
OLD_UNITS = {"cv": 1.0 / CV_TO_M2_PER_YEAR, "mv": 1e-3, "mv_ur": 1e-3}


def _t(lang: str, key: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# --------------------------------------------------------------------------- #
#  Schema data structures
# --------------------------------------------------------------------------- #


@dataclass
class Field:
    """One input field."""

    key: str
    label: str
    kind: str = "number"  # number | text | check | select
    default: Any = 0.0
    unit: str = ""
    min: float | None = None
    max: float | None = None
    step: float | None = None
    decimals: int = 2
    options: list[dict[str, str]] = field(default_factory=list)
    shapes: list[str] = field(default_factory=list)  # shown only for these shapes

    def to_dict(self) -> dict:
        """The field as a plain dictionary; empty values are left out."""
        keep = ("key", "label", "kind", "default", "decimals")
        return {k: v for k, v in asdict(self).items() if k in keep or v not in ("", None, [], 0.0)}


@dataclass
class Group:
    """A titled set of fields."""

    title: str
    fields: list[Field]
    note: str = ""
    shapes: list[str] = field(default_factory=list)  # shown only for these shapes

    def to_dict(self) -> dict:
        d = {"title": self.title, "fields": [f.to_dict() for f in self.fields]}
        if self.note:
            d["note"] = self.note
        if self.shapes:
            d["shapes"] = list(self.shapes)
        return d


def _num(key, label, default, lo=None, hi=None, unit="", dec=2, step=None):
    return Field(key, label, "number", default, unit, lo, hi, step, dec)


def _check(key, label, default=False):
    return Field(key, label, "check", default)


def _select(key, label, default, options):
    return Field(
        key, label, "select", default, options=[{"value": v, "label": t} for v, t in options]
    )


def _text(key, label, default=""):
    return Field(key, label, "text", default)


def _only(shapes: list[str], item):
    """Shows a field or a group only for some foundation shapes."""
    item.shapes = list(shapes)
    return item


#: The shapes that are foundations, as against an embankment
FOOTINGS = [s for s in SHAPES if s != "embankment"]


def _choices(lang: str, prefix: str, values: list[str]):
    return [(value, _t(lang, f"{prefix}_{value}")) for value in values]


# --------------------------------------------------------------------------- #
#  Input groups
# --------------------------------------------------------------------------- #


def project_groups(lang: str = "en") -> list[Group]:
    info = DEFAULT_CONFIG["project_info"]
    return [
        Group(
            _t(lang, "group_project"),
            [
                _text("title", _t(lang, "title_label"), info["title"]),
                _text("analyst", _t(lang, "analyst_label"), info["analyst"]),
            ],
        )
    ]


def foundation_groups(lang: str = "en") -> list[Group]:
    f = DEFAULT_CONFIG["foundation"]
    e = DEFAULT_CONFIG["embankment"]
    w = DEFAULT_CONFIG["groundwater"]
    return [
        Group(
            _t(lang, "group_foundation"),
            [
                _select(
                    "shape", _t(lang, "shape_label"), f["shape"], _choices(lang, "shape", SHAPES)
                ),
                _only(FOOTINGS, _num("B", _t(lang, "B_label"), f["B"], 0.1, 500, "m", 2, 0.1)),
                _only(["rectangle"], _num("L", _t(lang, "L_label"), f["L"], 0.1, 500, "m", 2, 0.1)),
                _only(FOOTINGS, _num("Df", _t(lang, "Df_label"), f["Df"], 0, 50, "m", 2, 0.1)),
                _only(FOOTINGS, _num("q", _t(lang, "q_label"), f["q"], 0, 5000, "kPa", 1, 5)),
                _only(FOOTINGS, _check("net_pressure", _t(lang, "net_label"), f["net_pressure"])),
            ],
        ),
        _only(
            ["embankment"],
            Group(
                _t(lang, "group_embankment"),
                [
                    _num("emb_crest", _t(lang, "emb_crest_label"), e["crest"], 0, 500, "m", 2, 0.5),
                    _num(
                        "emb_height",
                        _t(lang, "emb_height_label"),
                        e["height"],
                        0.1,
                        100,
                        "m",
                        2,
                        0.1,
                    ),
                    _num(
                        "emb_slope_left",
                        _t(lang, "emb_slope_left_label"),
                        e["slope_left"],
                        1,
                        90,
                        "°",
                        2,
                        0.5,
                    ),
                    _num(
                        "emb_slope_right",
                        _t(lang, "emb_slope_right_label"),
                        e["slope_right"],
                        1,
                        90,
                        "°",
                        2,
                        0.5,
                    ),
                    _num(
                        "emb_gamma", _t(lang, "emb_gamma_label"), e["gamma"], 1, 30, "kN/m³", 1, 0.5
                    ),
                ],
                note=_t(lang, "emb_note"),
            ),
        ),
        Group(
            _t(lang, "group_water"),
            [
                _num("water_depth", _t(lang, "water_depth_label"), w["depth"], 0, 500, "m", 2, 0.1),
                _num(
                    "gamma_water",
                    _t(lang, "gamma_w_label"),
                    w["gamma_water"],
                    9,
                    11,
                    "kN/m³",
                    2,
                    0.01,
                ),
            ],
        ),
    ]


def option_groups(lang: str = "en") -> list[Group]:
    o = DEFAULT_CONFIG["options"]
    c = DEFAULT_CONFIG["criteria"]
    return [
        Group(
            _t(lang, "group_options"),
            [
                _select(
                    "stress_method",
                    _t(lang, "stress_method_label"),
                    o["stress_method"],
                    _choices(lang, "stress", STRESS_METHODS),
                ),
                _select(
                    "immediate_method",
                    _t(lang, "immediate_method_label"),
                    o["immediate_method"],
                    _choices(lang, "immediate", IMMEDIATE_METHODS),
                ),
                _only(
                    FOOTINGS,
                    _select(
                        "rigidity",
                        _t(lang, "rigidity_label"),
                        o["rigidity"],
                        _choices(lang, "rigidity", RIGIDITY),
                    ),
                ),
                _num("sublayer", _t(lang, "sublayer_label"), o["sublayer"], 0.05, 5, "m", 2, 0.05),
                _num(
                    "depth_ratio",
                    _t(lang, "depth_ratio_label"),
                    o["depth_ratio"],
                    0,
                    1,
                    "",
                    2,
                    0.05,
                ),
                _num(
                    "design_life",
                    _t(lang, "design_life_label"),
                    o["design_life"],
                    0.1,
                    500,
                    "yr" if lang == "en" else "yıl",
                    1,
                    5,
                ),
                _check("creep", _t(lang, "creep_label"), o["creep"]),
            ],
            note=_t(lang, "options_note"),
        ),
        Group(
            _t(lang, "group_criteria"),
            [
                _num("s_allow", _t(lang, "s_allow_label"), c["s_allow"], 0, 2000, "mm", 1, 5),
                _num(
                    "distortion_allow",
                    _t(lang, "distortion_label"),
                    c["distortion_allow"],
                    0,
                    5000,
                    "",
                    0,
                    50,
                ),
            ],
            note=_t(lang, "criteria_note"),
        ),
    ]


def study_groups(lang: str = "en") -> list[Group]:
    from .study import METHODS

    return [
        Group(
            _t(lang, "group_study"),
            [
                _select(
                    "study_method",
                    _t(lang, "study_method"),
                    "lhs",
                    [(m, _t(lang, f"method_{m}")) for m in METHODS],
                ),
                _num("study_n", _t(lang, "study_n"), 500, 3, 100000, "", 0, 50),
                _num("study_seed", _t(lang, "study_seed"), 0, 0, 10**6, "", 0, 1),
            ],
            note=_t(lang, "study_note"),
        )
    ]


# --------------------------------------------------------------------------- #
#  Materials, soil layers, study variables
# --------------------------------------------------------------------------- #

#: Where a material property applies: a behaviour, or a cohesive description
GRANULAR, INDEX, MV, ROCK = "granular", "cohesive_index", "cohesive_mv", "incompressible"
SOILS = (GRANULAR, INDEX, MV)
CLAYS = (INDEX, MV)

#: The numeric properties of a material, in the order the dialog shows them:
#: (key, group, unit, decimals, min, max, step, applies to)
MATERIAL_NUMBERS = [
    ("gamma", "grp_mat_weight", "kN/m³", 2, 0.1, 40, 0.5, SOILS + (ROCK,)),
    ("gamma_sat", "grp_mat_weight", "kN/m³", 2, 0.1, 40, 0.5, SOILS + (ROCK,)),
    ("E", "grp_mat_elastic", "MPa", 2, 0, 1e5, 1, SOILS),
    ("nu", "grp_mat_elastic", "", 3, 0, 0.5, 0.01, SOILS),
    ("Cc", "grp_mat_cons", "", 4, 0, 10, 0.01, (INDEX,)),
    ("Cr", "grp_mat_cons", "", 4, 0, 10, 0.01, (INDEX,)),
    ("e0", "grp_mat_cons", "", 3, 0.01, 20, 0.05, (INDEX,)),
    ("mv", "grp_mat_cons", MV_UNIT, 7, 0, 1, 0.0001, (MV,)),
    ("mv_ur", "grp_mat_cons", MV_UNIT, 7, 0, 1, 0.00001, (MV,)),
    ("OCR", "grp_mat_cons", "", 2, 1, 50, 0.1, CLAYS),
    ("cv", "grp_mat_time", CV_UNIT, 7, 0, 10, 0.0001, CLAYS),
    ("Calpha", "grp_mat_time", "", 4, 0, 1, 0.001, (INDEX,)),
    ("Calpha_eps", "grp_mat_time", "", 5, 0, 1, 0.001, (MV,)),
]
MATERIAL_KEYS = [row[0] for row in MATERIAL_NUMBERS]


def material_kind(material: dict) -> str:
    """Which properties a material uses: granular, a clay by indices or by mv, or rock."""
    behaviour = material.get("behaviour", "granular")
    if behaviour == "cohesive":
        return MV if material.get("compression") == "mv" else INDEX
    return ROCK if behaviour == "incompressible" else GRANULAR


def material_fields(lang: str = "en") -> list[dict]:
    """The numeric properties of a material, labelled, with where they apply."""
    out = []
    for key, group, unit, dec, lo, hi, step, applies in MATERIAL_NUMBERS:
        out.append(
            {
                "key": key,
                "label": _t(lang, f"mat_{key}"),
                "group": group,
                "group_label": _t(lang, group),
                "unit": unit,
                "decimals": dec,
                "min": lo,
                "max": hi,
                "step": step,
                "applies": list(applies),
                "default": MATERIAL_DEFAULT[key],
            }
        )
    return out


def material_choices(lang: str = "en") -> dict[str, list[tuple[str, str]]]:
    """The two choice lists of a material: behaviour and consolidation description."""
    return {
        "behaviour": _choices(lang, "behaviour", BEHAVIOURS),
        "compression": _choices(lang, "compression", COMPRESSION),
    }


def layer_columns(lang: str = "en", materials: list[str] | None = None) -> list[dict]:
    """Columns of the soil profile table: material, thickness, drainage."""
    return [
        {
            "key": "material",
            "label": _t(lang, "col_material"),
            "kind": "select",
            "options": [{"value": m, "label": m} for m in (materials or [])],
        },
        {"key": "thickness", "label": _t(lang, "col_thickness"), "kind": "number"},
        {
            "key": "drainage",
            "label": _t(lang, "col_drainage"),
            "kind": "select",
            "options": [{"value": v, "label": _t(lang, f"drainage_{v}")} for v in DRAINAGE],
        },
    ]


def new_material(existing: list[dict], lang: str = "en") -> dict:
    """A fresh granular material with a name and a colour not yet in use."""
    names = {str(m.get("name", "")) for m in existing}
    base = _t(lang, "mat_new")
    n = len(existing) + 1
    while f"{base} {n}" in names:
        n += 1
    used = {str(m.get("color", "")).lower() for m in existing}
    color = next((c for c in MATERIAL_COLORS if c.lower() not in used), MATERIAL_COLORS[0])
    return {**MATERIAL_DEFAULT, "name": f"{base} {n}", "color": color}


def study_columns(lang: str = "en") -> list[dict]:
    """Columns of the study variable table."""
    from .study import DISTRIBUTIONS

    return [
        {"key": "path", "label": _t(lang, "col_param"), "kind": "select", "options": []},
        {
            "key": "mode",
            "label": _t(lang, "col_mode"),
            "kind": "select",
            "options": [
                {"value": "range", "label": _t(lang, "mode_range")},
                {"value": "dist", "label": _t(lang, "mode_dist")},
            ],
        },
        {"key": "min", "label": _t(lang, "col_min"), "kind": "number"},
        {"key": "max", "label": _t(lang, "col_max"), "kind": "number"},
        {
            "key": "dist",
            "label": _t(lang, "col_dist"),
            "kind": "select",
            "options": [{"value": d, "label": _t(lang, f"dist_{d}")} for d in DISTRIBUTIONS],
        },
        {"key": "mean", "label": _t(lang, "col_mean"), "kind": "number"},
        {"key": "cov", "label": _t(lang, "col_cov"), "kind": "number"},
        {"key": "n_points", "label": _t(lang, "col_points"), "kind": "number"},
    ]


def default_materials() -> list[dict]:
    return [dict(material) for material in DEFAULT_CONFIG["materials"]]


def default_soil_rows() -> list[dict]:
    return [dict(layer) for layer in DEFAULT_CONFIG["soil_profile"]]


# --------------------------------------------------------------------------- #
#  Schema collector
# --------------------------------------------------------------------------- #


def schema(lang: str = "en") -> dict:
    """The whole input schema as plain dictionaries, in one language."""
    return {
        "project": {"groups": [g.to_dict() for g in project_groups(lang)]},
        "foundation": {"groups": [g.to_dict() for g in foundation_groups(lang)]},
        "options": {"groups": [g.to_dict() for g in option_groups(lang)]},
        "study": {"groups": [g.to_dict() for g in study_groups(lang)]},
        "materials": {"fields": material_fields(lang), "rows": default_materials()},
        "soil": {
            "columns": layer_columns(lang, [m["name"] for m in default_materials()]),
            "rows": default_soil_rows(),
            "note": _t(lang, "soil_note"),
        },
        "study_vars": {"columns": study_columns(lang)},
    }


def _all_groups(lang: str = "en") -> list[Group]:
    return project_groups(lang) + foundation_groups(lang) + option_groups(lang) + study_groups(lang)


def defaults(lang: str = "en") -> dict[str, Any]:
    """Default values of every field, as one flat dictionary."""
    values: dict[str, Any] = {}
    for group in _all_groups(lang):
        for f in group.fields:
            values[f.key] = f.default
    values["materials"] = default_materials()
    values["soil_profile"] = default_soil_rows()
    values["study_variables"] = []
    return values


def sample(lang: str = "en") -> dict[str, Any]:
    """The sample project (a raft on soft clay between sands) as flat values.

    A new project has no materials; this is what `example` writes and what
    the tests analyse.
    """
    values = defaults(lang)
    values["title"] = SAMPLE_CONFIG["project_info"]["title"]
    values["materials"] = [dict(m) for m in SAMPLE_CONFIG["materials"]]
    values["soil_profile"] = [dict(row) for row in SAMPLE_CONFIG["soil_profile"]]
    return values


# --------------------------------------------------------------------------- #
#  Readers: flat values <-> configuration dictionary
# --------------------------------------------------------------------------- #


def _f(values: dict, key: str, default: float = 0.0) -> float:
    """A numeric field; missing or empty falls back to the default."""
    v = values.get(key, default)
    if v is None or v == "":
        return float(default)
    return float(v)


def _b(values: dict, key: str, default: bool = False) -> bool:
    v = values.get(key, default)
    return bool(default if v is None or v == "" else v)


def _s(values: dict, key: str, default: str = "", allowed: list[str] | None = None) -> str:
    v = values.get(key, default)
    text = str(default if v is None or v == "" else v)
    return text if allowed is None or text in allowed else default


def read_materials(values: dict) -> list[dict]:
    """The materials, every property filled in; names are unique and not empty."""
    materials, names = [], set()
    for row in values.get("materials") or []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip() or "Material"
        while name in names:
            name += "'"
        names.add(name)
        material = {
            "name": name,
            "color": str(row.get("color") or ""),
            "behaviour": _s(row, "behaviour", "granular", BEHAVIOURS),
            "compression": _s(row, "compression", "index", COMPRESSION),
        }
        for key in MATERIAL_KEYS:
            material[key] = _f(row, key, MATERIAL_DEFAULT[key])
        materials.append(material)
    return materials


def read_soil_profile(values: dict) -> list[dict]:
    """Soil layers from the table; rows without a usable thickness are dropped."""
    layers = []
    for row in values.get("soil_profile") or []:
        try:
            thickness = float(row.get("thickness"))
        except (TypeError, ValueError):
            continue
        if thickness <= 0:
            continue
        layers.append(
            {
                "material": str(row.get("material") or "").strip(),
                "thickness": thickness,
                "drainage": _s(row, "drainage", "double", DRAINAGE),
            }
        )
    return layers


#: Colours of migrated materials, by behaviour: sandy, greenish-grey, stone
BEHAVIOUR_COLORS = {
    "granular": ["#E3C98F", "#D9B36C", "#C7B39A", "#D4C9A8"],
    "cohesive": ["#A7B8A0", "#8FA88A", "#9DB4CC", "#A8A1C4"],
    "incompressible": ["#B9B4AE", "#C9A0A0"],
}


def _colour_for(behaviour: str, materials: list[dict]) -> str:
    """The next unused colour of a behaviour's family."""
    family = BEHAVIOUR_COLORS.get(behaviour, MATERIAL_COLORS)
    used = {str(m.get("color", "")).lower() for m in materials}
    return next((c for c in family if c.lower() not in used), family[len(materials) % len(family)])


def migrate_layers(cfg: dict) -> tuple[list[dict], list[dict], dict[int, int]]:
    """Materials and layer rows from a 2026.0.0 profile, whose layers carried
    their properties themselves: each distinct layer becomes a material.

    Returns the materials, the rows and, per layer, the index of its material
    (to carry study variables over).
    """
    materials: list[dict] = []
    rows: list[dict] = []
    index_of: dict[int, int] = {}
    for i, layer in enumerate(cfg.get("soil_profile") or []):
        if not isinstance(layer, dict):
            continue
        props = {**MATERIAL_DEFAULT, **{k: v for k, v in layer.items() if k in MATERIAL_DEFAULT}}
        props["name"] = str(layer.get("name") or "").strip() or f"Layer {i + 1}"
        same = [
            j
            for j, m in enumerate(materials)
            if all(m[k] == props[k] for k in MATERIAL_KEYS + ["behaviour"])
            and m["name"].split(" (")[0] == props["name"]
        ]
        if same:
            j = same[0]
        else:
            names = {m["name"] for m in materials}
            base, n = props["name"], 2
            while props["name"] in names:
                props["name"] = f"{base} ({n})"
                n += 1
            if not props.get("color"):
                props["color"] = _colour_for(props["behaviour"], materials)
            materials.append(props)
            j = len(materials) - 1
        index_of[i] = j
        rows.append(
            {
                "material": materials[j]["name"],
                "thickness": layer.get("thickness", 0.0),
                "drainage": layer.get("drainage", "double"),
            }
        )
    return materials, rows, index_of


def to_config(values: dict) -> dict[str, Any]:
    """The nested configuration the analysis core takes, from flat values."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    d = DEFAULT_CONFIG
    cfg["project_info"] = {
        "title": _s(values, "title", d["project_info"]["title"]),
        "analyst": str(values.get("analyst") or ""),
    }
    cfg["foundation"] = {
        "shape": _s(values, "shape", d["foundation"]["shape"], SHAPES),
        "B": _f(values, "B", d["foundation"]["B"]),
        "L": _f(values, "L", d["foundation"]["L"]),
        "Df": _f(values, "Df", d["foundation"]["Df"]),
        "q": _f(values, "q", d["foundation"]["q"]),
        "net_pressure": _b(values, "net_pressure", d["foundation"]["net_pressure"]),
    }
    e = d["embankment"]
    cfg["embankment"] = {key: _f(values, f"emb_{key}", e[key]) for key in e}
    cfg["groundwater"] = {
        "depth": _f(values, "water_depth", d["groundwater"]["depth"]),
        "gamma_water": _f(values, "gamma_water", d["groundwater"]["gamma_water"]),
    }
    cfg["materials"] = read_materials(values)
    cfg["soil_profile"] = read_soil_profile(values)
    o = d["options"]
    cfg["options"] = {
        "stress_method": _s(values, "stress_method", o["stress_method"], STRESS_METHODS),
        "immediate_method": _s(
            values, "immediate_method", o["immediate_method"], IMMEDIATE_METHODS
        ),
        "rigidity": _s(values, "rigidity", o["rigidity"], RIGIDITY),
        "sublayer": _f(values, "sublayer", o["sublayer"]),
        "depth_ratio": _f(values, "depth_ratio", o["depth_ratio"]),
        "design_life": _f(values, "design_life", o["design_life"]),
        "creep": _b(values, "creep", o["creep"]),
    }
    cfg["criteria"] = {
        "s_allow": _f(values, "s_allow", d["criteria"]["s_allow"]),
        "distortion_allow": _f(values, "distortion_allow", d["criteria"]["distortion_allow"]),
    }
    return cfg


#: Flat key <- (section, key) of the configuration
_MAP = (
    [("title", "project_info", "title"), ("analyst", "project_info", "analyst")]
    + [(k, "foundation", k) for k in ("shape", "B", "L", "Df", "q", "net_pressure")]
    + [(f"emb_{k}", "embankment", k) for k in DEFAULT_CONFIG["embankment"]]
    + [("water_depth", "groundwater", "depth"), ("gamma_water", "groundwater", "gamma_water")]
    + [
        (k, "options", k)
        for k in (
            "stress_method",
            "immediate_method",
            "rigidity",
            "sublayer",
            "depth_ratio",
            "design_life",
            "creep",
        )
    ]
    + [(k, "criteria", k) for k in ("s_allow", "distortion_allow")]
)


def from_config(cfg: dict, base: dict | None = None) -> dict[str, Any]:
    """Flat values from a nested configuration — reads a `.settle` project file.

    Whatever the file does not carry keeps its default.
    """
    values = dict(base) if base is not None else defaults()
    for flat, section, key in _MAP:
        if key in (cfg.get(section) or {}):
            values[flat] = cfg[section][key]
    index_of: dict[int, int] = {}
    layers = [layer for layer in cfg.get("soil_profile") or [] if isinstance(layer, dict)]
    if cfg.get("materials"):
        values["materials"] = [
            {**MATERIAL_DEFAULT, **m} for m in cfg["materials"] if isinstance(m, dict)
        ]
        values["soil_profile"] = [
            {
                "material": layer.get("material", ""),
                "thickness": layer.get("thickness", 0.0),
                "drainage": layer.get("drainage", "double"),
            }
            for layer in layers
        ]
    elif layers:
        values["materials"], values["soil_profile"], index_of = migrate_layers(cfg)
    old_units = str(cfg.get("version", "")) in ("0.1", "0.2")
    if old_units:
        for material in values.get("materials") or []:
            for key, factor in OLD_UNITS.items():
                if key in material:
                    material[key] = _f(material, key, 0.0) * factor
    study = cfg.get("study") or {}
    for src, dst in (("method", "study_method"), ("n", "study_n"), ("seed", "study_seed")):
        if src in study:
            values[dst] = study[src]
    if "variables" in study:
        variables = []
        for spec in study["variables"]:
            spec = dict(spec)
            parts = str(spec.get("path", "")).split(".")
            # a 2026.0.0 layer property is now its material's property
            if (
                index_of
                and len(parts) == 3
                and parts[0] == "soil_profile"
                and parts[2] != "thickness"
                and parts[1].isdigit()
                and int(parts[1]) in index_of
            ):
                spec["path"] = f"materials.{index_of[int(parts[1])]}.{parts[2]}"
            factor = OLD_UNITS.get(parts[-1]) if old_units else None
            if factor:
                for key in ("min", "max", "mean"):
                    if spec.get(key) not in (None, ""):
                        spec[key] = float(spec[key]) * factor
            variables.append(spec)
        values["study_variables"] = variables
    return values


def study_spec(values: dict) -> dict[str, Any]:
    """The study block of a project file: options plus the variable table."""
    from .study import METHODS

    return {
        "method": _s(values, "study_method", "lhs", METHODS),
        "n": int(_f(values, "study_n", 500)),
        "seed": int(_f(values, "study_seed", 0)),
        "variables": [dict(spec) for spec in values.get("study_variables") or []],
    }


def project_file(values: dict) -> dict[str, Any]:
    """What `Save` writes: the configuration plus the study definition."""
    cfg = to_config(values)
    return {"format": FILE_FORMAT, "version": FILE_VERSION, **cfg, "study": study_spec(values)}


def study_variables(values: dict):
    """The study variables as `study.StudyVariable` objects."""
    from .study import StudyVariable

    return [StudyVariable.from_dict(spec) for spec in values.get("study_variables") or []]


def variable_choices(values: dict, lang: str = "en") -> list[dict]:
    """Every input a study may vary, with a readable label and its project value."""
    from .study import available_variables, get_value, pretty_label

    cfg = to_config(values)
    L = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return [
        {"value": path, "label": pretty_label(cfg, path, L), "base": float(get_value(cfg, path))}
        for path, _ in available_variables(cfg)
    ]
