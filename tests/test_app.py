import ast
import io
import json
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.cad.assembly import PART_SPECS
from app.cad.verifier import verify_lesson_geometry
from app.data.lessons import (
    CONCEPTS,
    LESSONS,
    LEVELS,
    PROGRAM_MODES,
    find_lesson,
    get_lesson_version,
    lesson_blocks,
    lesson_variables,
    render_code,
)
from app.i18n import SUPPORTED_LANGS
from app.main import app
from app.scratch_export import FUNC_RUN, build_sb3

ROOT = Path(__file__).resolve().parents[1]
client = TestClient(app)

BLOCKS_JS = (ROOT / "app/static/js/blocks.js").read_text()
DEFINED_BLOCKS = set(re.findall(r"'(spike_\w+)'", BLOCKS_JS)) | {
    "math_number", "math_arithmetic", "math_change", "logic_compare", "logic_operation",
    "logic_negate", "text", "variables_get", "variables_set",
}


def all_parts(lesson):
    return [p for s in lesson["steps"] for p in s["parts"]]


@pytest.mark.parametrize("lang", list(SUPPORTED_LANGS))
@pytest.mark.parametrize("lesson", [l["id"] for l in LESSONS])
def test_pages_render(lesson, lang):
    r = client.get("/", params={"lesson": lesson, "lang": lang})
    assert r.status_code == 200
    assert f'data-lesson-id="{lesson}"' in r.text
    for n in range(1, len(next(l for l in LESSONS if l["id"] == lesson)["steps"]) + 1):
        r = client.get(f"/partials/lesson/{lesson}/step/{n}", params={"lang": lang})
        assert r.status_code == 200
        assert f'data-step="{n}"' in r.text


def test_index_step_param_is_clamped():
    assert 'data-step="3"' in client.get("/?lesson=driving-base&step=3").text
    assert 'data-step="5"' in client.get("/?lesson=driving-base&step=99").text
    assert 'data-step="1"' in client.get("/?lesson=driving-base&step=-4").text


@pytest.mark.parametrize("path", [
    "/partials/lesson/nope", "/partials/lesson/nope/step/1", "/api/lesson/nope/scene",
    "/download/nope.py", "/download/nope.llsp3", "/download/nope.sb3",
])
def test_unknown_lesson_is_404(path):
    assert client.get(path).status_code == 404


def test_downloads_are_localized_and_versioned():
    en_v2 = client.get("/download/obstacle-avoider.py?lang=en").text
    assert "0 < dist < 180" in en_v2 and "{{" not in en_v2
    en_v1 = client.get("/download/obstacle-avoider.py?lang=en&ver=v1").text
    assert "if dist < 180:" in en_v1 and "{{" not in en_v1
    r = client.get("/download/obstacle-avoider.llsp3?lang=ja")
    z = zipfile.ZipFile(io.BytesIO(r.content))
    body = json.loads(z.read("projectbody.json"))
    assert body["main"] == render_code(find_lesson("obstacle-avoider"), "ja", "v2")


def test_no_template_values_interpolated_into_inline_js():
    for f in (ROOT / "app/templates").rglob("*.html"):
        for m in re.finditer(r'on\w+="([^"]*)"', f.read_text()):
            assert "{{" not in m.group(1), f"{f.name}: {m.group(0)}"


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_lesson_data_integrity_and_100_percent_ldraw_parts(lesson):
    for ver in ("v1", "v2"):
        vdata = get_lesson_version(lesson, ver)
        n_lines = len(vdata["code"].splitlines())
        for lang in SUPPORTED_LANGS:
            assert len(render_code(lesson, lang, ver).splitlines()) == n_lines
        for exp in vdata["code_explanations"]:
            nums = [int(x) for x in exp["lines"].split("-")]
            assert 1 <= min(nums) <= max(nums) <= n_lines

    ports = {p["port"] for p in lesson["ports"]}
    for step in lesson["steps"]:
        for w in step.get("wiring", []):
            assert w["port"] in ports
    for c in lesson["cables"]:
        assert c["port"] in ports
        assert 1 <= c["step"] <= len(lesson["steps"])

    ids = [p["id"] for p in all_parts(lesson)]
    assert len(ids) == len(set(ids)), "duplicate part ids"
    for p in all_parts(lesson):
        assert p["type"] in PART_SPECS, f"Non-45678 part type: {p['type']}"
        assert "ldraw" in p, f"Part {p['id']} is missing official LDraw MPD reference"
        assert (ROOT / "app/static/ldraw/parts" / f"{p['ldraw']}.mpd").is_file()
        assert len(p.get("quat", [])) == 4
        assert set(p["name"]) >= set(SUPPORTED_LANGS)

    # Structure lab completeness
    lab = lesson.get("structure_lab")
    assert lab and set(lab["why"]) >= set(SUPPORTED_LANGS)
    assert len(lab["troubleshoot"]) >= 2
    assert len(lab["mod_ideas"]) >= 2


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_cables_and_geometry_pass_verifier(lesson):
    errs = verify_lesson_geometry(lesson)
    assert errs == [], errs


@pytest.mark.parametrize("ver", ["v1", "v2"])
@pytest.mark.parametrize("lang", list(SUPPORTED_LANGS))
@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_lesson_python_is_valid(lesson, lang, ver):
    ast.parse(render_code(lesson, lang, ver))


@pytest.mark.parametrize("ver", ["v1", "v2"])
@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_lesson_curriculum_fields_and_blocks(lesson, ver):
    assert lesson["level"] in LEVELS
    assert 1 <= lesson["stars"] <= 5
    assert all(c in CONCEPTS for c in lesson["concepts"])
    for ch in lesson.get("challenges", []):
        assert set(ch) >= set(SUPPORTED_LANGS)
    for mode in ("blockly", "scratch"):
        xml = lesson_blocks(lesson, mode, ver)
        root = ET.fromstring(xml)
        types = {b.get("type") for b in root.iter("{https://developers.google.com/blockly/xml}block")}
        types |= {b.get("type") for b in root.iter("{https://developers.google.com/blockly/xml}shadow")}
        assert "spike_start" in types
        assert types <= DEFINED_BLOCKS, types - DEFINED_BLOCKS
        if mode == "scratch":
            declared = set(lesson_variables(lesson, "scratch", ver))
            used = set(re.findall(r'<field name="(?:NAME|VAR)">([^<]*)</field>', xml))
            assert used <= declared, used - declared


def test_lessons_progress_from_stage1_to_stage4():
    assert len(LESSONS) == 12
    order = list(LEVELS)
    ranks = [(order.index(l["level"]), l["stars"]) for l in LESSONS]
    assert ranks == sorted(ranks)
    assert len({l["id"] for l in LESSONS}) == 12


def test_sidebar_is_grouped_and_tabs_are_buttons():
    html = client.get("/?lang=zh").text
    for title in (v["zh"] for v in LEVELS.values()):
        assert title in html
    assert 'type="radio"' not in html
    assert html.count("data-tab-panel=") == 4
    assert 'id="lesson-blocks-xml"' in html


def test_structure_lab_and_version_switcher_render():
    # Final build step of magic-hub (step 3) renders Structure & Mod Lab
    step3 = client.get("/partials/lesson/magic-hub/step/3?lang=zh").text
    assert "data-structure-lab" in step3
    assert "两点防转动" in step3

    # v1 vs v2 switching renders problem/why vs fix banner
    v1_html = client.get("/partials/lesson/driving-base?lang=zh&ver=v1").text
    assert 'data-program-version="v1"' in v1_html
    assert "原地疯狂打转" in v1_html
    v2_html = client.get("/partials/lesson/driving-base?lang=zh&ver=v2").text
    assert 'data-program-version="v2"' in v2_html
    assert "motor_pair.pair" in v2_html


def test_scene_exposes_lesson_camera_and_kinematics():
    s1 = client.get("/api/lesson/magic-hub/scene").json()
    assert s1["camera"]["target"]
    assert {"joints", "gear_meshes", "crank_linkages", "kinematics", "floor_props", "ports"} <= set(s1)
    assert client.get("/api/lesson/driving-base/scene").json()["camera"] is None


def test_simulator_node_suite():
    res = subprocess.run(
        ["node", "--test", str(ROOT / "tests" / "test_simulator.mjs")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert res.returncode == 0, f"Node simulator tests failed:\n{res.stdout}\n{res.stderr}"


@pytest.mark.parametrize("lang", list(SUPPORTED_LANGS))
@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_sb3_project_is_consistent(lesson, lang):
    data = build_sb3(lesson, lang, {})
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        project = json.loads(zf.read("project.json"))
        for name in zf.namelist():
            if name.endswith(".png"):
                assert len(zf.read(name)) > 0
    stage, sprite = project["targets"]
    assert project["extensions"] == ["s3studio"]
    blocks = sprite["blocks"]
    for bid, b in blocks.items():
        assert (b["next"] is None) or b["next"] in blocks, (bid, b["opcode"])
        for inp in b["inputs"].values():
            if isinstance(inp, list) and isinstance(inp[1], str):
                assert inp[1] in blocks, (bid, b["opcode"])
        if b["opcode"] == "data_variable":
            assert b["fields"]["VARIABLE"][1] in stage["variables"]
    tops = [b for b in blocks.values() if b["topLevel"]]
    assert len(tops) == 1 and tops[0]["opcode"] == "event_whenflagclicked"
    seen = set()

    def walk(bid):
        while bid and bid not in seen:
            seen.add(bid)
            b = blocks[bid]
            for inp in b["inputs"].values():
                if isinstance(inp, list) and isinstance(inp[1], str):
                    walk(inp[1])
            bid = b["next"]

    walk(next(k for k, b in blocks.items() if b["topLevel"]))
    assert seen == set(blocks), "every block must be reachable from the hat (no orphaned blocks)"
    assert any(b["opcode"] == FUNC_RUN for b in blocks.values()), "lesson program uses no SPIKE block"


@pytest.mark.parametrize("mode", list(PROGRAM_MODES))
def test_blocks_tab_serves_the_chosen_dialect(mode):
    html = client.get("/", params={"lesson": "gyro-precision", "mode": mode}).text
    assert f'data-blocks-mode="{mode}"' in html
    xml = lesson_blocks(find_lesson("gyro-precision"), mode, "v2")
    assert xml in html
    if mode == "scratch":
        assert '"remaining"' in html


def test_mode_and_tab_links_are_separate_from_language():
    html = client.get("/", params={"lesson": "gyro-precision", "step": 2, "mode": "scratch"}).text
    assert "lang=ja&mode=scratch" in html
    assert "/partials/lesson/driving-base?lang=zh&mode=scratch" in html


def test_reverse_proxy_prefix_and_pwa_endpoints():
    # Under reverse-proxy prefix (/spike), language links and PWA manifest/sw must keep the prefix
    r_idx = client.get("/", headers={"x-forwarded-prefix": "/spike"}, params={"lesson": "magic-hub", "lang": "en"})
    assert r_idx.status_code == 200
    assert 'href="/spike/?lesson=magic-hub&step=1&lang=ja"' in r_idx.text
    assert 'href="/spike/manifest.webmanifest?lang=en"' in r_idx.text
    assert 'window.SPIKE_BASE_PATH = "/spike";' in r_idx.text

    # app.js must not navigate to root-absolute `/?` which strips `/spike/`
    app_js = (ROOT / "app/static/js/app.js").read_text()
    assert "window.location.href = `/?`" not in app_js
    assert "`/?${params}`" not in app_js
    assert "SPIKE_BASE_PATH" in app_js

    # PWA manifest and Service Worker
    r_man = client.get("/manifest.webmanifest?lang=ja", headers={"x-forwarded-prefix": "/spike"})
    assert r_man.status_code == 200
    assert "application/manifest+json" in r_man.headers["content-type"]
    man = r_man.json()
    assert man["start_url"] == "/spike/"
    assert man["scope"] == "/spike/"
    assert man["display"] == "standalone"
    assert any(i["src"] == "/spike/static/icons/icon-192.png" for i in man["icons"])
    assert any(i["src"] == "/spike/static/icons/icon-512.png" for i in man["icons"])

    r_sw = client.get("/sw.js", headers={"x-forwarded-prefix": "/spike"})
    assert r_sw.status_code == 200
    assert "application/javascript" in r_sw.headers["content-type"]
    assert r_sw.headers.get("service-worker-allowed") == "/spike/"
    assert "const BASE = '/spike';" in r_sw.text

    for icon in ("icon-192.png", "icon-512.png", "icon-maskable-512.png", "apple-touch-icon.png", "icon.svg"):
        assert (ROOT / "app/static/icons" / icon).is_file()


def test_sb3_download_and_mode_suffixed_downloads():
    r = client.get("/download/gyro-precision.sb3?lang=ja")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"].endswith('spike3_gyro_precision.sb3"')
    assert "spike3_gyro_precision_scratch.py" in client.get("/download/gyro-precision.py?mode=scratch").headers["content-disposition"]
    assert "spike3_gyro_precision_v1.py" in client.get("/download/gyro-precision.py?ver=v1").headers["content-disposition"]
    assert "spike3_gyro_precision.py" in client.get("/download/gyro-precision.py").headers["content-disposition"]


def test_tabs_do_not_use_daisy_grid():
    """Regression: DaisyUI `.tabs` is a grid whose `span 9999` panels made the tab labels shrink."""
    html = client.get("/?lang=zh").text
    panel = re.search(r'<div data-tabs[^>]*>(.*?)data-tab-panel="build"', html, re.S).group(0)
    assert "tabs tabs" not in panel and 'class="tabs' in panel
    assert "tabs-lifted-row" in panel
    assert "/static/css/studio.css" in html


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_new_lesson_steps_narrate_real_parts(lesson):
    """A build step that mentions wiring must also show parts in 3D."""
    scene = client.get(f"/api/lesson/{lesson['id']}/scene").json()
    shown = {s["step"] for s in scene["steps"] if s["parts"]}
    for step in lesson["steps"]:
        if step.get("wiring"):
            assert step["step"] in shown, "wiring steps must show the attached parts"
