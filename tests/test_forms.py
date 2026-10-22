"""The input schema, the defaults and the conversions to and from project files."""

import pytest

from slipsurface.settle import forms
from slipsurface.settle.config import DEFAULT_CONFIG
from slipsurface.settle.engine import SettlementAnalysis


@pytest.mark.parametrize("lang", ["en", "tr"])
def test_every_field_of_the_schema_has_a_label_and_a_default(lang):
    schema = forms.schema(lang)
    values = forms.defaults(lang)
    for section in ("project", "foundation", "options", "study"):
        for group in schema[section]["groups"]:
            assert group["title"]
            for field in group["fields"]:
                assert field["label"] and field["key"] in values
    assert [c["key"] for c in schema["soil"]["columns"]] == ["material", "thickness", "drainage"]
    assert all(c["label"] for c in schema["soil"]["columns"])
    for f in schema["materials"]["fields"]:
        assert f["label"] and f["group_label"] and f["applies"], f["key"]


def test_the_languages_differ_where_they_should():
    en, tr = forms.schema("en"), forms.schema("tr")
    assert en["foundation"]["groups"][0]["title"] == "Foundation"
    assert tr["foundation"]["groups"][0]["title"] == "Temel"


def test_the_defaults_are_the_default_project():
    assert forms.to_config(forms.defaults()) == {
        **DEFAULT_CONFIG,
        "project_info": DEFAULT_CONFIG["project_info"],
    }


def test_a_project_file_round_trips():
    values = forms.defaults()
    values.update(B=6.5, water_depth=4.0, rigidity="rigid", s_allow=60.0, study_n=77)
    values["materials"][2]["Cc"] = 0.41
    values["materials"].append({"name": "Limestone", "behaviour": "incompressible"})
    values["soil_profile"].append({"material": "Limestone", "thickness": 5.0, "drainage": "single"})
    values["study_variables"] = [{"path": "foundation.q", "mode": "range", "min": 1, "max": 2}]
    project = forms.project_file(values)
    assert project["format"] == forms.FILE_FORMAT
    back = forms.from_config(project)
    for key in ("B", "water_depth", "rigidity", "s_allow", "study_n"):
        assert back[key] == values[key]
    assert back["materials"][2]["Cc"] == 0.41
    assert back["materials"][4]["behaviour"] == "incompressible"
    assert back["soil_profile"][4] == {
        "material": "Limestone",
        "thickness": 5.0,
        "drainage": "single",
    }
    assert back["study_variables"][0]["path"] == "foundation.q"


def test_a_partial_project_file_keeps_the_defaults():
    values = forms.from_config({"foundation": {"q": 250.0}})
    assert values["q"] == 250.0
    assert values["B"] == DEFAULT_CONFIG["foundation"]["B"]
    assert len(values["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])


def test_empty_and_unusable_table_rows_are_dropped():
    values = forms.defaults()
    values["soil_profile"] = values["soil_profile"] + [
        {"material": "Fill", "thickness": None},
        {"material": "Fill", "thickness": 0},
    ]
    assert len(forms.to_config(values)["soil_profile"]) == len(DEFAULT_CONFIG["soil_profile"])


def test_empty_cells_fall_back_to_defaults_and_unknown_choices_are_ignored():
    values = forms.defaults()
    values.update(q="", shape="hexagon", stress_method=None)
    values["materials"][0]["E"] = None
    values["materials"][1]["behaviour"] = "jelly"
    cfg = forms.to_config(values)
    assert cfg["foundation"]["q"] == DEFAULT_CONFIG["foundation"]["q"]
    assert cfg["foundation"]["shape"] == "rectangle"
    assert cfg["options"]["stress_method"] == "boussinesq"
    assert cfg["materials"][0]["E"] == 10.0
    assert cfg["materials"][1]["behaviour"] == "granular"
    SettlementAnalysis(cfg).run()


def test_variable_choices_carry_label_and_project_value():
    choices = forms.variable_choices(forms.defaults(), "en")
    by_path = {c["value"]: c for c in choices}
    assert by_path["foundation.q"]["base"] == DEFAULT_CONFIG["foundation"]["q"]
    assert by_path["materials.2.Cc"]["label"] == "Soft clay · Cc"
    assert by_path["materials.2.Cc"]["base"] == 0.32
    assert by_path["soil_profile.2.thickness"]["label"] == "3. Soft clay · t"
    assert "materials.1.Cc" not in by_path  # a sand has no Cc


def test_a_clay_described_by_mv_offers_mv_not_cc():
    values = forms.defaults()
    values["materials"][2]["compression"] = "mv"
    paths = {c["value"] for c in forms.variable_choices(values, "en")}
    assert {"materials.2.mv", "materials.2.mv_ur", "materials.2.Calpha_eps"} <= paths
    assert "materials.2.Cc" not in paths


def test_a_2026_0_0_project_with_properties_per_layer_is_converted():
    """Each distinct layer becomes a material; study variables follow."""
    old = {
        "soil_profile": [
            {"name": "Sand", "thickness": 2.0, "behaviour": "granular", "E": 20.0},
            {
                "name": "Clay",
                "thickness": 4.0,
                "behaviour": "cohesive",
                "Cc": 0.3,
                "e0": 1.0,
                "cv": 2.0,
                "drainage": "single",
            },
            {"name": "Sand", "thickness": 3.0, "behaviour": "granular", "E": 20.0},
            {"name": "Sand", "thickness": 3.0, "behaviour": "granular", "E": 40.0},
        ],
        "study": {
            "variables": [
                {"path": "soil_profile.1.Cc", "mode": "range"},
                {"path": "soil_profile.3.thickness", "mode": "range"},
            ]
        },
    }
    values = forms.from_config(old)
    assert [m["name"] for m in values["materials"]] == ["Sand", "Clay", "Sand (2)"]
    assert [r["material"] for r in values["soil_profile"]] == ["Sand", "Clay", "Sand", "Sand (2)"]
    assert values["soil_profile"][1]["drainage"] == "single"
    assert values["materials"][1]["Cc"] == 0.3 and values["materials"][1]["behaviour"] == "cohesive"
    assert [v["path"] for v in values["study_variables"]] == [
        "materials.1.Cc",
        "soil_profile.3.thickness",
    ]
    # the converted project gives the same answer as the old one read directly
    direct = SettlementAnalysis(
        {**forms.to_config(forms.defaults()), "materials": [], "soil_profile": old["soil_profile"]}
    )
    direct.run()
    converted = SettlementAnalysis(forms.to_config(values))
    converted.run()
    assert converted.results["total"] == pytest.approx(direct.results["total"])


def test_a_layer_naming_an_unknown_material_is_refused():
    from slipsurface.settle.engine import SettleError

    values = forms.defaults()
    values["soil_profile"][1]["material"] = "Nothing"
    with pytest.raises(SettleError) as err:
        SettlementAnalysis(forms.to_config(values))
    assert err.value.key == "err_material"
