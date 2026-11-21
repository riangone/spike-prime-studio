"""Tests for the official LEGO SPIKE Prime (45678) LDraw catalog, CAD assembly builder,
and zero-tolerance geometric/kinematic verifier across all 12 elementary lessons.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.cad import models as M
from app.cad.assembly import PART_SPECS, Assembly, rot_y
from app.cad.verifier import solve_poses, verify_lesson_geometry
from app.data.lessons import LESSONS

ROOT = Path(__file__).resolve().parents[1]
LDRAW_DIR = ROOT / "app" / "static" / "ldraw"
PARTS_DIR = LDRAW_DIR / "parts"


def _as_lesson(a: Assembly) -> dict:
    steps = sorted(a.steps_parts)
    return {
        "steps": [{"step": s, "parts": a.step_parts(s)} for s in steps],
        "cables": [dict(c) for c in a.cables],
        **a.export_scene_meta(),
    }


def test_ldraw_library_files_complete():
    assert (LDRAW_DIR / "LDConfig.ldr").is_file()
    assert len(PART_SPECS) >= 40
    for key, spec in PART_SPECS.items():
        mpd = PARTS_DIR / f"{spec['mpd_name']}.mpd"
        assert mpd.is_file() and mpd.stat().st_size > 100, f"Missing MPD for {key}: {mpd}"
        if "rotor_mpd" in spec:
            rmpd = PARTS_DIR / f"{spec['rotor_mpd']}.mpd"
            assert rmpd.is_file() and rmpd.stat().st_size > 100, f"Missing rotor MPD for {key}"
        if "plunger_mpd" in spec:
            pmpd = PARTS_DIR / f"{spec['plunger_mpd']}.mpd"
            assert pmpd.is_file() and pmpd.stat().st_size > 100, f"Missing plunger MPD for {key}"


@pytest.mark.parametrize("lesson_id,builder", list(M.MODEL_BUILDERS.items()), ids=list(M.MODEL_BUILDERS.keys()))
def test_all_12_cad_models_have_zero_errors(lesson_id, builder):
    asm = builder()
    errors = verify_lesson_geometry(_as_lesson(asm))
    assert errors == [], f"{lesson_id} failed CAD verification:\n" + "\n".join(errors)


@pytest.mark.parametrize("lesson", LESSONS, ids=lambda l: l["id"])
def test_all_12_curriculum_lessons_pass_zero_tolerance_cad_verifier(lesson):
    errors = verify_lesson_geometry(lesson)
    assert errors == [], f"Lesson {lesson['id']} failed CAD verification:\n" + "\n".join(errors)


def test_verifier_catches_collision():
    a = Assembly("c_")
    a.add("hub", "hub", (0, 0, 0), step=1)
    # Place a beam intersecting straight through the Hub body
    a.add("bad_beam", "beam_7", (0, 40, 0), M.BEAM_X_HOLES_Y, step=1)
    errs = verify_lesson_geometry(_as_lesson(a))
    assert any("COLLISION" in e for e in errs), errs


def test_verifier_catches_floating_part():
    a = Assembly("f_")
    a.add("hub", "hub", (0, 0, 0), step=1)
    a.add("float_beam", "beam_5", (0, 200, 0), M.BEAM_X_HOLES_Y, step=1)
    errs = verify_lesson_geometry(_as_lesson(a))
    assert any("FLOATING" in e for e in errs), errs


def test_verifier_catches_unengaged_pin():
    a = Assembly("p_")
    a.add("hub", "hub", (0, 0, 0), step=1)
    # Pin placed in empty air next to hub
    a.pin("loose_pin", (140, 50, 0), "x", step=1)
    errs = verify_lesson_geometry(_as_lesson(a))
    assert any("engages only" in e for e in errs), errs


def test_verifier_catches_exceeding_45678_kit_qty():
    a = Assembly("q_")
    a.add("hub1", "hub", (0, 0, 0), step=1)
    a.add("hub2", "hub", (200, 0, 0), step=1)
    errs = verify_lesson_geometry(_as_lesson(a))
    assert any("Exceeds LEGO 45678 kit qty" in e for e in errs), errs


def test_verifier_catches_bad_gear_mesh_distance():
    a = Assembly("g_")
    a.add("hub", "hub", (0, 0, 0), step=1)
    # Two 12T gears need center distance = (12 + 12) * 20 / 16 = 30 LDU; put them at 50 LDU
    a.add("g1", "gear_12", (0, 90, 0), rot_y(0), step=1)
    a.add("g2", "gear_12", (50, 90, 0), rot_y(0), step=1)
    a.add_gear_mesh("g1", "g2", "parallel")
    errs = verify_lesson_geometry(_as_lesson(a))
    assert any("Gear mesh" in e for e in errs), errs


def test_verifier_revolute_sign_matches_viewer3d_cw_positive():
    """Positive motor degrees rotate CW looking at +axis (= -angle right-handed about +axis).
    For L03 metronome arm on +Y axis starting at (+160, 90, 60) relative to pivot (100, 80, 60),
    +90 deg motor angle (CW from above) moves +X (+60, 0) toward +Z (0, +60)!
    """
    a = M.build_l03_metronome()
    d = _as_lesson(a)
    parts = [p for s in d["steps"] for p in s["parts"]]
    rest = solve_poses(parts, d["joints"], [], {})
    rot90 = solve_poses(parts, d["joints"], [], {"B": 90.0})
    px0, _, pz0 = rest["l03_arm"][0]
    px1, _, pz1 = rot90["l03_arm"][0]
    piv_x, _, piv_z = d["joints"][0]["pivot_ldu"]
    assert abs((px0 - piv_x) - 60.0) < 1e-3
    assert abs((px1 - piv_x) - 0.0) < 1e-3
    assert abs((pz1 - piv_z) - 60.0) < 1e-3
