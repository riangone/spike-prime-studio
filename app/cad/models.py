"""All 12 elementary curriculum models built from real LEGO SPIKE Prime (45678) parts on the exact LDraw grid.

Conventions (see assembly.py): Y-up LDU, floor at y = 0, 1 stud = 20 LDU (8 mm).
Robots drive toward -Z ("front"); the Hub lies flat with its USB end facing rear (+Z), so
ports A/B are at the front, C/D in the middle and E/F at the rear.

Every model here is checked by app/cad/verifier.py (tests/test_cad.py): pins engage two real
holes, no solid parts overlap at rest or anywhere along their motor sweeps, gear/rack pitches
match LEGO geometry, everything is connected to floor Y=0, and cables terminate at real sockets.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence

from app.cad.assembly import (
    LDU_TO_SCENE,
    PART_SPECS,
    Assembly,
    ldu_to_scene,
    mat_mul,
    rot_x,
    rot_y,
    rot_z,
)

# ---- Frequently used right-handed orientations (det = +1) ----------------------------------------
I3 = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
# Medium/large motor lying on its side, output disc facing -X (left) or +X (right), cable to rear (+Z).
MOTOR_OUT_LEFT = ((0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
MOTOR_OUT_RIGHT = ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
# Straight beam standing on edge, running left-right (X) with holes facing front/back (Z).
BEAM_X_HOLES_Z = ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0))
# Straight beam lying flat, running left-right (X) with vertical holes (Y).
BEAM_X_HOLES_Y = rot_y(90.0)
# Straight beam standing upright along Y, with holes facing left/right (X).
BEAM_Y_HOLES_X = mat_mul(rot_x(90.0), rot_z(90.0))
# Straight beam standing upright along Y, with holes facing front/back (Z).
BEAM_Y_HOLES_Z = rot_x(90.0)
# Straight beam lying on edge along Z, with holes facing left/right (X).
BEAM_Z_HOLES_X = rot_z(90.0)
# Colour sensor looking straight down (-Y), side pin holes facing front/back (Z).
COLOR_DOWN_HOLES_Z = ((0.0, -1.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0))

HUB_BOTTOM = 40.0  # Hub height on the driving base (wheel axle at y = 70 = wheel radius)
AXLE_Y = 70.0


def _scene(v: Sequence[float]) -> List[float]:
    return ldu_to_scene(v)


def _scene_rect(x0: float, x1: float, z0: float, z1: float) -> List[float]:
    """Robot-frame rectangle [xmin, xmax, zmin, zmax] in scene units from LDU."""
    return [round(v * LDU_TO_SCENE, 5) for v in (x0, x1, z0, z1)]


def _cable_via(start, end, *, lift: float = 130.0, side: float = 0.0):
    """Waypoints that lift a cable clear of the model and approach the Hub socket from outside."""
    sx, sy, sz = start
    ex, ey, ez = end
    out = 18.0 if ex > 0 else -18.0
    return [
        (sx + side, max(sy, lift), sz),
        (ex + out, max(ey, lift), ez),
        (ex + out, ey, ez),
    ]


def cable(
    a: Assembly,
    cid: str,
    device: str,
    hub: str,
    port: str,
    step: int,
    *,
    via: Optional[Sequence[Sequence[float]]] = None,
    lift: float = 130.0,
    color: str = "#64748b",
):
    dev = a.parts_by_id[f"{a.prefix}{device}"]
    start = a.world_point_on(device, PART_SPECS[dev["type"]]["cable_exit_ldu"])
    end = a.world_point_on(hub, PART_SPECS["hub"]["hub_ports_ldu"][port])
    a.add_cable(
        cid,
        device_part_id=device,
        hub_part_id=hub,
        port=port,
        step=step,
        color=color,
        via_ldu=via if via is not None else _cable_via(start, end, lift=lift),
        label=f"Port {port}",
    )


# ==================================================================================================
# Shared Driving Base helpers
# ==================================================================================================
def build_driving_base(prefix: str, *, step_map: Optional[Dict[str, int]] = None) -> Assembly:
    """Hub flat with USB end rear, two medium motors pinned straight onto the Hub sides
    (outputs outward), 56 mm wheels on 3L axles, and a ball caster pinned behind the Hub."""
    st = {"hub": 1, "left": 2, "right": 3, "wheels": 4, "caster": 5, "cables": 5}
    st.update(step_map or {})
    a = Assembly(prefix)
    hb = HUB_BOTTOM
    a.add("hub", "hub", (0, hb, 0), step=st["hub"], explode_ldu=(0, 60, 0))

    for side, s, R, port in (("l", -1.0, MOTOR_OUT_LEFT, "C"), ("r", 1.0, MOTOR_OUT_RIGHT, "D")):
        key = "left" if side == "l" else "right"
        a.add(
            f"motor_{side}", "medium_motor", (s * 100, AXLE_Y, -80), R,
            step=st[key], port=port, explode_ldu=(s * 90, 0, 0),
        )
        a.pin(f"pin_{side}1", (s * 70, hb + 10, -80), "x", step=st[key], qty=2, explode_ldu=(s * 45, 0, 0))
        a.pin(f"pin_{side}2", (s * 70, hb + 50, -80), "x", step=st[key], qty=0, explode_ldu=(s * 45, 0, 0))
        a.add(
            f"axle_{side}", "axle_3", (s * 165, AXLE_Y, -80), I3,
            step=st["wheels"], qty=2 if side == "l" else 0, explode_ldu=(s * 60, 0, 0),
        )
        a.add(
            f"wheel_{side}", "wheel", (s * 167.5, AXLE_Y, -80), rot_y(s * 90.0),
            step=st["wheels"], qty=2 if side == "l" else 0, explode_ldu=(s * 110, 0, 0),
        )
        a.add_revolute_joint(
            f"j_wheel_{side}",
            pivot_ldu=(s * 150, AXLE_Y, -80),
            axis=(s, 0, 0),
            motor_port=port,
            parts=[f"axle_{side}", f"wheel_{side}"],
            sweep_deg=(0.0, 360.0),
        )

    a.add("caster_beam", "beam_7", (0, 90, 120), BEAM_X_HOLES_Z, step=st["caster"], color=71, explode_ldu=(0, 0, 50))
    a.add("caster", "caster", (0, AXLE_Y, 140), rot_y(90.0), step=st["caster"], explode_ldu=(0, -30, 90))
    a.pin("pin_c1", (-40, 90, 125), "z", kind="pin_blue_3l", step=st["caster"], qty=2, explode_ldu=(0, 0, 110))
    a.pin("pin_c2", (40, 90, 125), "z", kind="pin_blue_3l", step=st["caster"], qty=0, explode_ldu=(0, 0, 110))

    cable(a, "cable_c", "motor_l", "hub", "C", step=st["cables"])
    cable(a, "cable_d", "motor_r", "hub", "D", step=st["cables"])
    a.kinematics = {
        "chassis": {
            "type": "differential",
            "wheels": [
                {
                    "port": "C",
                    "center": _scene((-167.5, AXLE_Y, -80)),
                    "axis": [-1.0, 0.0, 0.0],
                    "radius": round(70 * LDU_TO_SCENE, 5),
                },
                {
                    "port": "D",
                    "center": _scene((167.5, AXLE_Y, -80)),
                    "axis": [1.0, 0.0, 0.0],
                    "radius": round(70 * LDU_TO_SCENE, 5),
                },
            ],
            "pair_left": "C",
            "pair_right": "D",
        }
    }
    return a


def flattened_base(prefix: str) -> Assembly:
    """Complete wired driving base in step 1 (for lessons starting from the finished car)."""
    return build_driving_base(prefix, step_map={k: 1 for k in ("hub", "left", "right", "wheels", "caster", "cables")})


def add_front_beam(a: Assembly, y: float, step: int, *, beam_type: str = "beam_7", color: int = 71):
    a.add("front_beam", beam_type, (0, y, -120), BEAM_X_HOLES_Z, step=step, color=color, explode_ldu=(0, 0, -60))
    a.pin("pin_f1", (-40, y, -110), "z", step=step, qty=2, explode_ldu=(0, 0, -40))
    a.pin("pin_f2", (40, y, -110), "z", step=step, qty=0, explode_ldu=(0, 0, -40))


def add_distance_sensor_front(a: Assembly, step_beam: int, step_sensor: int, port: str = "F"):
    add_front_beam(a, 90.0, step_beam)
    a.add(
        "dist", "distance_sensor", (0, 90, -140), rot_y(180.0),
        step=step_sensor, port=port, explode_ldu=(0, 0, -90),
    )
    a.pin("pin_s1", (-60, 90, -130), "z", step=step_sensor, qty=2, explode_ldu=(0, 0, -50))
    a.pin("pin_s2", (60, 90, -130), "z", step=step_sensor, qty=0, explode_ldu=(0, 0, -50))
    cable(a, "cable_dist", "dist", "hub", port, step=step_sensor, lift=150, color="#0ea5e9")
    a.kinematics["sensors"] = {
        **a.kinematics.get("sensors", {}),
        port: {"type": "distance", "part": f"{a.prefix}dist", "dir": [0, 0, -1]},
    }


def add_color_sensor_front(a: Assembly, step_beam: int, step_sensor: int, port: str = "E"):
    """Colour sensor hanging in front of the Hub, lens 21 LDU (8.4 mm) above floor."""
    add_front_beam(a, 70.0, step_beam)
    a.add(
        "color", "color_sensor", (0, 70, -160), COLOR_DOWN_HOLES_Z,
        step=step_sensor, port=port, explode_ldu=(0, 0, -90),
    )
    a.pin("pin_s1", (-20, 70, -130), "z", step=step_sensor, qty=2, explode_ldu=(0, 0, -50))
    a.pin("pin_s2", (20, 70, -130), "z", step=step_sensor, qty=0, explode_ldu=(0, 0, -50))
    cable(a, "cable_color", "color", "hub", port, step=step_sensor, lift=150, color="#22c55e")
    a.kinematics["sensors"] = {
        **a.kinematics.get("sensors", {}),
        port: {"type": "color", "part": f"{a.prefix}color", "dir": [0, -1, 0]},
    }


# ==================================================================================================
# L01: Magic Emoji Hub (Hub + symmetric twin-pin side bumper rails)
# ==================================================================================================
def build_l01_magic_hub() -> Assembly:
    a = Assembly("l01_")
    a.add("hub", "hub", (0, 0, 0), step=1, explode_ldu=(0, 40, 0))
    # Step 2: Left 11L side guard beam pinned with 2 black pins (teaches two-pin anti-rotation)
    a.pin("pin_l1", (-70, 10, -80), "x", step=2, qty=2, explode_ldu=(-40, 0, 0))
    a.pin("pin_l2", (-70, 10, 80), "x", step=2, qty=0, explode_ldu=(-40, 0, 0))
    a.add("rail_l", "beam_11", (-80, 10, 0), BEAM_Z_HOLES_X, step=2, color=322, explode_ldu=(-70, 0, 0))
    # Step 3: Symmetric right 11L side guard beam
    a.pin("pin_r1", (70, 10, -80), "x", step=3, qty=2, explode_ldu=(40, 0, 0))
    a.pin("pin_r2", (70, 10, 80), "x", step=3, qty=0, explode_ldu=(40, 0, 0))
    a.add("rail_r", "beam_11", (80, 10, 0), BEAM_Z_HOLES_X, step=3, color=322, explode_ldu=(70, 0, 0))
    a.kinematics = {"chassis": {"type": "static"}}
    return a


# ==================================================================================================
# L02: Lucky Pointer Spinner (Hub + upright left motor Port A + pointer with T-arrow tip)
# ==================================================================================================
def build_l02_lucky_spinner() -> Assembly:
    a = Assembly("l02_")
    a.add("hub", "hub", (0, 0, 0), step=1, explode_ldu=(0, 30, 0))
    for i, (y, z) in enumerate([(10, 80), (50, 80), (10, -80), (50, -80)]):
        a.pin(f"pin_m{i + 1}", (-70, y, z), "x", step=1, qty=4 if i == 0 else 0, explode_ldu=(-45, 0, 0))

    a.add("motor", "medium_motor", (-100, 30, 60), I3, step=2, port="A", explode_ldu=(-80, 0, 0))
    cable(a, "cable_a", "motor", "hub", "A", step=2, lift=110)

    # Pointer beam + yellow T-tip sweeping cleanly above Hub (y=90 / y=110)
    a.pin("pin_p1", (-120, 80, 60), "y", step=3, qty=4, explode_ldu=(0, 45, 0))
    a.pin("pin_p2", (-80, 80, 60), "y", step=3, qty=0, explode_ldu=(0, 45, 0))
    a.add("pointer", "beam_7", (-140, 90, 60), BEAM_X_HOLES_Y, step=3, color=26, explode_ldu=(0, 65, 0))
    a.pin("pin_t1", (-180, 100, 60), "y", step=3, qty=0, explode_ldu=(0, 85, 0))
    a.pin("pin_t2", (-200, 100, 60), "y", step=3, qty=0, explode_ldu=(0, 85, 0))
    a.add("tip", "beam_t_3x3", (-160, 110, 60), rot_y(90.0), step=3, color=14, explode_ldu=(0, 105, 0))

    a.add_revolute_joint(
        "j_pointer",
        pivot_ldu=(-100, 80, 60),
        axis=(0, 1, 0),
        motor_port="A",
        parts=["pin_p1", "pin_p2", "pointer", "pin_t1", "pin_t2", "tip"],
        sweep_deg=(0.0, 360.0),
    )
    return a


# ==================================================================================================
# L03: Musical Metronome (Hub + right motor B with swinging mallet + left force sensor A)
# ==================================================================================================
def build_l03_metronome() -> Assembly:
    a = Assembly("l03_")
    a.add("hub", "hub", (0, 0, 0), step=1, explode_ldu=(0, 30, 0))
    for i, (y, z) in enumerate([(10, 80), (50, 80), (10, -80), (50, -80)]):
        a.pin(f"pin_m{i + 1}", (70, y, z), "x", step=1, qty=4 if i == 0 else 0, explode_ldu=(45, 0, 0))
    a.add("motor", "medium_motor", (100, 30, 60), I3, step=1, port="B", explode_ldu=(80, 0, 0))
    cable(a, "cable_b", "motor", "hub", "B", step=1, lift=110)

    # Step 2: Swinging 9L pendulum beam + magenta T-mallet on motor B disc
    a.pin("pin_a1", (80, 80, 60), "y", step=2, qty=4, explode_ldu=(0, 45, 0))
    a.pin("pin_a2", (120, 80, 60), "y", step=2, qty=0, explode_ldu=(0, 45, 0))
    a.add("arm", "beam_9", (160, 90, 60), BEAM_X_HOLES_Y, step=2, color=322, explode_ldu=(0, 65, 0))
    a.pin("pin_h1", (220, 100, 60), "y", step=2, qty=0, explode_ldu=(0, 85, 0))
    a.pin("pin_h2", (240, 100, 60), "y", step=2, qty=0, explode_ldu=(0, 85, 0))
    a.add("head", "beam_t_3x3", (200, 110, 60), rot_y(-90.0), step=2, color=26, explode_ldu=(0, 105, 0))
    a.add_revolute_joint(
        "j_arm",
        pivot_ldu=(100, 80, 60),
        axis=(0, 1, 0),
        motor_port="B",
        parts=["pin_a1", "pin_a2", "arm", "pin_h1", "pin_h2", "head"],
        sweep_deg=(-75.0, 75.0),
    )

    # Step 3: Force sensor on left side as tap-tempo start button (Port A)
    a.pin("pin_fs1", (-70, 10, -80), "x", step=3, qty=2, explode_ldu=(-45, 0, 0))
    a.pin("pin_fs2", (-70, 50, -80), "x", step=3, qty=0, explode_ldu=(-45, 0, 0))
    a.add("force", "force_sensor", (-100, 30, -40), rot_y(180.0), step=3, port="A", explode_ldu=(-80, 0, 0))
    cable(a, "cable_a", "force", "hub", "A", step=3, lift=110, color="#f59e0b")
    a.kinematics["sensors"] = {"A": {"type": "force", "part": f"{a.prefix}force"}}
    return a


# ==================================================================================================
# L04: Driving Base
# ==================================================================================================
def build_l04_driving_base() -> Assembly:
    a = build_driving_base("l04_")
    a.floor_props = [
        {"type": "patch", "pos": [0.0, 0.0, -1.6], "size": [7.5, 0.25], "color": "#94a3b8", "layer": 0},
        {"type": "patch", "pos": [0.0, 0.0, -10.4], "size": [7.5, 0.2], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [0.0, 0.0, -19.2], "size": [7.5, 3.6], "color": "#22c55e", "spike_color": "GREEN", "layer": 1},
    ]
    return a


# ==================================================================================================
# L05: Square Patrol Car (Driving base + wide 11L yellow front bumper)
# ==================================================================================================
def build_l05_square_patrol() -> Assembly:
    a = flattened_base("l05_")
    add_front_beam(a, 70.0, step=2, beam_type="beam_11", color=14)
    # Corner bumper caps (3L magenta beams on both ends of the 11L bumper)
    a.pin("pin_bl1", (-80, 70, -130), "z", step=3, qty=4, explode_ldu=(0, 0, -45))
    a.pin("pin_bl2", (-100, 70, -130), "z", step=3, qty=0, explode_ldu=(0, 0, -45))
    a.add("cap_l", "beam_3", (-80, 70, -140), BEAM_X_HOLES_Z, step=3, color=26, qty=2, explode_ldu=(0, 0, -80))
    a.pin("pin_br1", (80, 70, -130), "z", step=3, qty=0, explode_ldu=(0, 0, -45))
    a.pin("pin_br2", (100, 70, -130), "z", step=3, qty=0, explode_ldu=(0, 0, -45))
    a.add("cap_r", "beam_3", (80, 70, -140), BEAM_X_HOLES_Z, step=3, color=26, qty=0, explode_ldu=(0, 0, -80))

    # Floor guide: 29.3 cm (14.66 scene units) square matching side=600 deg (axle starts at x=0, z=-1.6)
    s = 14.66
    z0 = -1.6
    a.floor_props = [
        {"type": "patch", "pos": [0.0, 0.0, z0 - s / 2], "size": [0.3, s], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s / 2, 0.0, z0 - s], "size": [s, 0.3], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s, 0.0, z0 - s / 2], "size": [0.3, s], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s / 2, 0.0, z0], "size": [s, 0.3], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [0.0, 0.0, z0], "size": [2.2, 2.2], "color": "#38bdf8", "layer": 1},
    ]
    return a


# ==================================================================================================
# L06: Gyro Precision Turn (Driving base + top front heading compass arrow)
# ==================================================================================================
def build_l06_gyro_precision() -> Assembly:
    a = flattened_base("l06_")
    # Step 2: 7L bridge across Hub top-front vertical holes (-60, 115, -100) and (60, 115, -100)
    a.pin("pin_g1", (-60, 120, -100), "y", step=2, qty=2, explode_ldu=(0, 45, 0))
    a.pin("pin_g2", (60, 120, -100), "y", step=2, qty=0, explode_ldu=(0, 45, 0))
    a.add("top_bar", "beam_7", (0, 130, -100), BEAM_X_HOLES_Y, step=2, color=71, explode_ldu=(0, 70, 0))
    # Step 3: Forward-pointing yellow heading indicator (T-beam + 5L nose pointer)
    a.pin("pin_p1", (-20, 140, -100), "y", step=3, qty=2, explode_ldu=(0, 85, 0))
    a.pin("pin_p2", (20, 140, -100), "y", step=3, qty=0, explode_ldu=(0, 85, 0))
    a.add("compass", "beam_t_3x3", (0, 150, -140), rot_y(180.0), step=3, color=14, explode_ldu=(0, 110, 0))

    s = 14.66
    z0 = -1.6
    a.floor_props = [
        {"type": "patch", "pos": [0.0, 0.0, z0 - s / 2], "size": [0.3, s], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s / 2, 0.0, z0 - s], "size": [s, 0.3], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s, 0.0, z0 - s / 2], "size": [0.3, s], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [s / 2, 0.0, z0], "size": [s, 0.3], "color": "#cbd5e1", "layer": 0},
        {"type": "patch", "pos": [0.0, 0.0, z0 - s], "size": [1.8, 1.8], "color": "#f59e0b", "layer": 1},
        {"type": "patch", "pos": [s, 0.0, z0 - s], "size": [1.8, 1.8], "color": "#f59e0b", "layer": 1},
        {"type": "patch", "pos": [s, 0.0, z0], "size": [1.8, 1.8], "color": "#f59e0b", "layer": 1},
        {"type": "patch", "pos": [0.0, 0.0, z0], "size": [2.2, 2.2], "color": "#22c55e", "layer": 1},
    ]
    return a


# ==================================================================================================
# L07: Ultrasonic Obstacle Avoider
# ==================================================================================================
def build_l07_obstacle_avoider() -> Assembly:
    a = flattened_base("l07_")
    add_distance_sensor_front(a, step_beam=2, step_sensor=3, port="F")
    a.floor_props = [
        {"type": "box", "pos": [0.0, 2.5, -18.0], "size": [14.0, 5.0, 1.6], "color": "#ef4444"},
        {"type": "box", "pos": [13.5, 2.5, -7.0], "size": [1.6, 5.0, 16.0], "color": "#f97316"},
    ]
    return a


# ==================================================================================================
# L08: Color Traffic Car
# ==================================================================================================
def build_l08_color_traffic() -> Assembly:
    a = flattened_base("l08_")
    add_color_sensor_front(a, step_beam=2, step_sensor=3, port="E")
    a.floor_props = [
        {"type": "patch", "pos": [0.0, 0.0, -6.4], "size": [6.0, 2.6], "color": "#22c55e", "spike_color": "GREEN", "layer": 1},
        {"type": "patch", "pos": [0.0, 0.0, -10.2], "size": [6.0, 2.6], "color": "#eab308", "spike_color": "YELLOW", "layer": 1},
        {"type": "patch", "pos": [0.0, 0.0, -14.0], "size": [6.0, 2.6], "color": "#3b82f6", "spike_color": "BLUE", "layer": 1},
        {"type": "patch", "pos": [0.0, 0.0, -17.2], "size": [6.0, 1.1], "color": "#ef4444", "spike_color": "RED", "layer": 2},
    ]
    return a


# ==================================================================================================
# L09: Line Follower Challenge
# ==================================================================================================
def build_l09_line_follower() -> Assembly:
    a = flattened_base("l09_")
    add_color_sensor_front(a, step_beam=2, step_sensor=3, port="E")
    # Black ring track: outer right edge passes directly underneath the color sensor at (0, -3.2)
    a.floor_props = [
        {"type": "ring", "pos": [-10.0, 0.0, -3.2], "radius": 10.0, "width": 1.4, "color": "#111827", "spike_color": "BLACK", "layer": 1},
    ]
    return a


# ==================================================================================================
# L10: Geared Parking Gate (Baseplate + Hub + Force Sensor B + Motor A + 12T->36T 3:1 Geared Boom)
# ==================================================================================================
def build_l10_gear_gate() -> Assembly:
    """Real 12T -> 36T (3:1 reduction) parking gate on the iconic 11x19 teal baseplate.
    Exact center distance between 12T (y=50) and 36T (y=110) = 60.0 LDU = 3 studs."""
    a = Assembly("l10_")
    # Step 1: 11x19 Azure Baseplate flat on floor (y in [0, 20], x in [-150, 230], z in [-110, 110])
    # + Hub mounted on top at (0, 20, 0) with 4 black pins
    a.add("base", "baseplate_11x19", (40, 10, 0), rot_y(90.0), step=1, explode_ldu=(0, -30, 0))
    for i, (x, z) in enumerate([(-60, -100), (60, -100), (-60, 100), (60, 100)]):
        a.pin(f"pin_h{i + 1}", (x, 20, z), "y", step=1, qty=4 if i == 0 else 0, explode_ldu=(0, 35, 0))
    a.add("hub", "hub", (0, 20, 0), step=1, explode_ldu=(0, 70, 0))

    # Step 2: Force sensor (Port B) on left of Hub as arrival/manual button
    a.pin("pin_fs1", (-70, 30, -80), "x", step=2, qty=2, explode_ldu=(-45, 0, 0))
    a.pin("pin_fs2", (-70, 70, -80), "x", step=2, qty=0, explode_ldu=(-45, 0, 0))
    a.add("force", "force_sensor", (-100, 50, -40), rot_y(180.0), step=2, port="B", explode_ldu=(-80, 0, 0))
    cable(a, "cable_b", "force", "hub", "B", step=2, lift=130, color="#f59e0b")
    a.kinematics["sensors"] = {"B": {"type": "force", "part": f"{a.prefix}force"}}

    # Step 3: Medium Motor (Port A) on right side of Hub (output disc at x=150, y=50, z=-80)
    a.pin("pin_m1", (70, 30, -80), "x", step=3, qty=2, explode_ldu=(45, 0, 0))
    a.pin("pin_m2", (70, 70, -80), "x", step=3, qty=0, explode_ldu=(45, 0, 0))
    a.add("motor", "medium_motor", (100, 50, -80), MOTOR_OUT_RIGHT, step=3, port="A", explode_ldu=(80, 0, 0))
    cable(a, "cable_a", "motor", "hub", "A", step=3, lift=130)

    # Step 4: Vertical gear-tower column at x=180 anchored to baseplate via twin 3x3 biscuits
    # Biscuit with rot_z(90) -> local x->y ([-30,30]), y->-x ([-10,10]), z->z ([-29,29])
    # Wait: holes of biscuit under I3: Y-holes at (±20,0,0), (0,0,±20), (0,0,0); X-holes at (±25,0,±20).
    # Rotate biscuit by rot_y(90) -> flat on baseplate at y=30? No, use rot_z(90):
    #   Y-holes (now X-axis) at (180, 50, -80), (180, 30, -80), (180, 70, -80), (180, 50, -100), (180, 50, -60)
    #   X-holes (now Y-axis) at (180, 25, -100) and (180, 25, -60) -> PIN DIRECTLY DOWN INTO BASEPLATE!!
    a.pin("pin_tb1", (180, 20, -100), "y", step=4, qty=2, explode_ldu=(0, 35, 0))
    a.pin("pin_tb2", (180, 20, -60), "y", step=4, qty=0, explode_ldu=(0, 35, 0))
    a.add("tower_base", "biscuit_3x3", (180, 50, -80), rot_z(90.0), step=4, color=71, explode_ldu=(0, 55, 0))
    # Vertical 7L tower beam pinned flush on outside (+X) of biscuit at x=200 (holes at y=30..150)
    a.pin("pin_tw1", (190, 30, -80), "x", step=4, qty=2, explode_ldu=(40, 0, 0))
    a.pin("pin_tw2", (190, 70, -80), "x", step=4, qty=0, explode_ldu=(40, 0, 0))
    a.add("tower_col", "beam_7", (200, 90, -80), BEAM_Y_HOLES_X, step=4, color=71, explode_ldu=(70, 0, 0))

    # Step 5: 12T driving gear on Motor A (y=50) meshing with 36T driven gear (y=110, 60 LDU above!) + 13L gate boom
    # Drive shaft (4L axle along X, x in [120.5, 199.5] -> wait: motor disc is x=150, tower_base is x=180 (hole at 180,50,-80)!)
    # Put 4L axle centered at (165, 50, -80): spans x in [125.5, 204.5] -> engages motor (x<=150), gear_12 (x=160), tower_base (x=180), tower_col (x=200)!
    a.add("axle_drv", "axle_4", (165, 50, -80), I3, step=5, explode_ldu=(50, 0, 0))
    a.add("gear_drv", "gear_12", (160, 50, -80), rot_y(90.0), step=5, explode_ldu=(60, 0, 0))
    a.add_revolute_joint(
        "j_gear_drv",
        pivot_ldu=(150, 50, -80),
        axis=(1, 0, 0),
        motor_port="A",
        parts=["axle_drv", "gear_drv"],
        gear_ratio=1.0,
        sweep_deg=(-300.0, 300.0),
    )

    # Upper driven shaft at (185, 110, -80): 4L axle spans x in [145.5, 224.5] -> engages gear_36 (x=160), tower_col (x=200), L-arm (x=220)!
    # Wait: bush at x=180 keeps gear_36 cleanly spaced from tower_col (x=200)!
    a.add("axle_gate", "axle_4", (185, 110, -80), I3, step=5, explode_ldu=(60, 0, 0))
    a.add("gear_gate", "gear_36", (160, 110, -80), rot_y(90.0), step=5, explode_ldu=(40, 0, 0))
    a.add("bush_gate", "bush", (180, 110, -80), rot_y(90.0), step=5, explode_ldu=(50, 0, 0))
    a.add_gear_mesh("gear_drv", "gear_gate", "parallel")

    # Gate arm hub: beam_l_2x4 has an AXLE hole at local (0,0,0)!
    # With BEAM_Z_HOLES_X (rot_z(90)): local (x,y,z) -> (-y, x, z), axle hole at (0,0,0) along X,
    # pin holes at (0,0,-20), (0,0,-40), (0,0,-60) and (0,20,-60).
    # Placed at (220, 110, -80): extends forward (-Z) to z=-140!
    a.add("arm_hub", "beam_l_2x4", (220, 110, -80), BEAM_Z_HOLES_X, step=5, color=14, explode_ldu=(80, 0, 0))
    # 13L bright yellow/red barrier boom pinned to arm_hub along -Z at x=240 (two pins at z=-100 and z=-140)
    a.pin("pin_bm1", (230, 110, -100), "x", step=5, qty=2, explode_ldu=(95, 0, 0))
    a.pin("pin_bm2", (230, 110, -140), "x", step=5, qty=0, explode_ldu=(95, 0, 0))
    a.add("boom", "beam_13", (240, 110, -200), BEAM_Z_HOLES_X, step=5, color=14, explode_ldu=(110, 0, 0))

    # Meshing gears reverse rotation direction: gear_ratio = -12 / 36 = -1/3!
    # So +270 deg on Motor A raises the horizontal (-Z) boom UP by +90 deg cleanly above the gate!
    a.add_revolute_joint(
        "j_gate",
        pivot_ldu=(200, 110, -80),
        axis=(1, 0, 0),
        motor_port="A",
        parts=["axle_gate", "gear_gate", "bush_gate", "arm_hub", "pin_bm1", "pin_bm2", "boom"],
        gear_ratio=-12.0 / 36.0,
        sweep_deg=(-70.0, 470.0),
    )
    # Hard stops (Motor A degrees, gate = -motor/3): at -70 the boom tip (249 LDU from the pivot)
    # touches the road in front (boom 23.3 deg below level); nothing blocks it going up, so past
    # vertical it keeps falling backwards until the tip touches the floor behind at +470 (156.7 deg).
    a.kinematics["limits"] = {"A": {"min": -70.0, "max": 470.0}}

    # Road lane stripe passing in front of the parking booth
    a.floor_props = [
        {"type": "patch", "pos": [4.8, 0.0, -4.6], "size": [3.8, 12.0], "color": "#475569", "layer": 0},
        {"type": "patch", "pos": [4.8, 0.0, -4.6], "size": [0.22, 11.2], "color": "#facc15", "layer": 1},
    ]
    return a


# ==================================================================================================
# L11: Rack & Pinion Pusher / Sorter (Baseplate + Hub + Large Motor A + 12T Pinion + 13L Rack + Color E)
# ==================================================================================================
def build_l11_rack_pusher() -> Assembly:
    """Real 12T pinion meshing with 13L gear rack (exact 20.0 LDU normal pitch distance),
    driven by Large Angular Motor (45602, Port A), with Color Sensor (Port E) inspecting items."""
    a = Assembly("l11_")
    # Step 1: Baseplate + Hub at (0, 20, 0)
    a.add("base", "baseplate_11x19", (40, 10, 0), rot_y(90.0), step=1, explode_ldu=(0, -30, 0))
    for i, (x, z) in enumerate([(-60, -100), (60, -100), (-60, 100), (60, 100)]):
        a.pin(f"pin_h{i + 1}", (x, 20, z), "y", step=1, qty=4 if i == 0 else 0, explode_ldu=(0, 35, 0))
    a.add("hub", "hub", (0, 20, 0), step=1, explode_ldu=(0, 70, 0))

    # Step 2: Large Angular Motor (Port A) upright on right side of Hub (x in [70, 170], y in [20, 100], z in [-90, 90])
    # All 4 side holes at x=75, y=30/70, z=±80 align directly with Hub right-side holes!
    for i, (y, z) in enumerate([(30, -80), (70, -80), (30, 80), (70, 80)]):
        a.pin(f"pin_lm{i + 1}", (70, y, z), "x", step=2, qty=4 if i == 0 else 0, explode_ldu=(45, 0, 0))
    a.add("motor", "large_motor", (120, 50, 60), I3, step=2, port="A", explode_ldu=(85, 0, 0))
    cable(a, "cable_a", "motor", "hub", "A", step=2, lift=155)

    # Step 3: Guide rail channel along the rear (z=100, y=110) supported from Hub top corners & baseplate
    # Rear upright posts at x=-60 and x=60 on Hub top rear holes (y=95) -> wait: Hub top is y=100!
    # Pin a 15L guide rail beam flat along X at (40, 110, 100) using pins into Hub top (-60, 100, 100) & (60, 100, 100)!
    a.pin("pin_gr1", (-60, 100, 100), "y", step=3, qty=2, explode_ldu=(0, 45, 0))
    a.pin("pin_gr2", (60, 100, 100), "y", step=3, qty=0, explode_ldu=(0, 45, 0))
    a.add("guide_rail", "beam_15", (40, 110, 100), BEAM_X_HOLES_Y, step=3, color=71, explode_ldu=(0, 70, 0))
    # Front-end stop pillar on baseplate at (200, 60, 100) so the rail is supported on both sides?
    # No, Hub already anchors it solidly with 2 pins 120 LDU apart! Add a smooth sliding rail cap? Already sleek!

    # Step 4: 12T Pinion on Large Motor A vertical axle + 13L Gear Rack sliding along X!
    # Vertical axle_4 along Y (rot_z(90)) at (120, 90, 60): engages motor axle hole (y in [20, 100]) + gear_12 at y=110!
    a.add("axle_pinion", "axle_4", (120, 90, 60), rot_z(90.0), step=4, explode_ldu=(0, 55, 0))
    a.add("gear_pinion", "gear_12", (120, 110, 60), rot_x(90.0), step=4, explode_ldu=(0, 80, 0))
    a.add_revolute_joint(
        "j_pinion",
        pivot_ldu=(120, 100, 60),
        axis=(0, 1, 0),
        motor_port="A",
        parts=["axle_pinion", "gear_pinion"],
        gear_ratio=1.0,
        sweep_deg=(-260.0, 260.0),
    )

    # 13L Gear Rack at (120, 110, 80) with rot_x(-90): local +Y (teeth) -> world -Z (toward pinion at z=60)!
    # Normal distance = 20.0 LDU EXACT! Back of rack (z=89.5) slides smoothly along guide_rail front (z=90.5)!
    # Pusher head on left tip of rack (x=0, y=110, z=80): pin a 5L bright magenta pusher paddle!
    # Note: under rot_x(-90), rack end pin holes are at (±120, 0, 0) along local Y -> world Z!
    # Wait: rack axle holes are at (±100, 0, 0) along local Z -> world Y (vertical!).
    # So put a 2L red axle at (20, 120, 80) vertically + 2x4 Technic brick pusher head on top at (0, 144, 80)!
    a.add("rack", "gear_rack_13", (120, 110, 80), rot_x(-90.0), step=4, color=72, explode_ldu=(0, 95, 0))
    a.add("axle_push", "axle_2", (20, 120, 80), rot_z(90.0), step=4, explode_ldu=(0, 115, 0))
    a.add("pusher_head", "brick_2x4_technic", (0, 144, 80), I3, step=4, color=26, explode_ldu=(0, 135, 0))
    a.add_gear_mesh("gear_pinion", "rack", "rack")

    # Kinematics: Looking from +Y down at pinion, +ang turns CW -> tooth on +Z side (meshing with rack at z=80)
    # moves toward -X! Pitch radius = 15.0 LDU => 15 * pi / 180 = 0.2618 LDU/deg along -X.
    # Safe travel: 0..240 deg => rack pushes 62.8 LDU toward -X (completely clear of Hub LED and baseplate)!
    a.add_prismatic_joint(
        "j_rack",
        axis=(-1, 0, 0),
        motor_port="A",
        ldu_per_deg=15.0 * math.pi / 180.0,
        min_ldu=-70.0,
        max_ldu=110.0,
        parts=["rack", "axle_push", "pusher_head"],
    )
    # Hard stops (Motor A degrees = travel / 0.2618 LDU/deg): at -70 LDU the pusher brick runs into the
    # vertical pinion axle; past +110 LDU the rack end reaches the pinion and the rack drops off it.
    a.kinematics["limits"] = {"A": {"min": round(-70.0 / (15.0 * math.pi / 180.0), 1),
                                    "max": round(110.0 / (15.0 * math.pi / 180.0), 1)}}

    # Step 5: Color sensor (Port E) mounted on left side of Hub facing -X (inspection gate!)
    # Color sensor default: lens +Z, back holes (±20, 0, -5) along Z, side holes (±25, ±20, 0) along X.
    # Place at (-100, 50, -60) with rot_y(-90)? Check rot_y(-90): (x,y,z) -> (-z, y, x):
    #   lens (+Z) -> -X (outward left!), back (-Z, x_loc=±20) -> world x=-95, z=-60±20=-80/-40 (axis X)!
    #   Wait: Hub left holes at y=50 are ONLY at z=±80! At y=30: z=±80; at y=70: z=±80!
    #   With rot_z(90) @ rot_y(-90): local (x,y,z) -> (-y, -z, x)? No: use rot_y(-90) @ rot_z(90):
    #     first rot_z(90): (-y, x, z), then rot_y(-90): (-z, x, -y)!
    #     Check back holes (±20, 0, -5) -> world (+5, ±20, 0) -> at (-100, 50, -80):
    #       world x = -95? Wait (-100 + 5 = -95? No, color_sensor back is z=-10..+49, so at (-100, 50, -80)
    #       with local z -> -x, local z=-10 -> world x=-90, local z=+49 -> world x=-149!
    #       Shift x to -80: local z=-10 -> world x=-70 (FLUSH with Hub!), back holes at x=-75, y=50±20=30 & 70, z=-80!
    #       ENGAGES HUB LEFT SIDE HOLES (-65, 30, -80) AND (-65, 70, -80) DIRECTLY WITH 2 BLACK PINS!!
    R_COLOR_LEFT = mat_mul(rot_y(-90.0), rot_z(90.0))
    a.pin("pin_cs1", (-70, 30, -80), "x", step=5, qty=2, explode_ldu=(-45, 0, 0))
    a.pin("pin_cs2", (-70, 70, -80), "x", step=5, qty=0, explode_ldu=(-45, 0, 0))
    a.add("color", "color_sensor", (-80, 50, -80), R_COLOR_LEFT, step=5, port="E", explode_ldu=(-85, 0, 0))
    cable(a, "cable_e", "color", "hub", "E", step=5, lift=145, color="#22c55e")
    a.kinematics["sensors"] = {"E": {"type": "color", "part": f"{a.prefix}color", "dir": [-1, 0, 0]}}
    return a


# ==================================================================================================
# L12: Smart Gripper Transporter (Driving Base + Front Large Motor A + Geared Sweeper Claw + Distance F)
# ==================================================================================================
def build_l12_smart_gripper() -> Assembly:
    """Capstone elementary robot:
    - Differential Driving Base (Ports C & D)
    - Large Angular Motor (Port A) bolted flush to all 4 front corners of the Hub!
    - Twin-beam sweeping gripper jaw on Motor A (plus fixed left cargo guide)
    - Ultrasonic Distance Sensor (Port F) perched on top of the front frame scanning for cargo."""
    a = flattened_base("l12_")

    # Step 2: Large Angular Motor (Port A) mounted horizontally across the front of the Hub!
    # Under rot_y(90): local (x,y,z) -> (z, y, -x). At (60, 70, -160):
    #   x in [-90, 90], y in [40, 120], z in [-210, -110] (rear face flush with Hub front z=-110!)
    #   All 4 rear side holes at x=±40, y=50/90, z=-115 align with Hub front holes (±40, 50/90, -105)!
    for i, (x, y) in enumerate([(-40, 50), (40, 50), (-40, 90), (40, 90)]):
        a.pin(f"pin_gm{i + 1}", (x, y, -110), "z", step=2, qty=4 if i == 0 else 0, explode_ldu=(0, 0, -45))
    a.add("motor_arm", "large_motor", (60, 70, -160), rot_y(90.0), step=2, port="A", explode_ldu=(0, 0, -85))
    cable(a, "cable_a", "motor_arm", "hub", "A", step=2, lift=165, color="#ec4899")

    # Step 3: Fixed left cargo guide jaw at y=130 (same height as moving right jaw!), anchored to
    # Hub top-left (-60, 115, -100) and Large Motor top-left (-60, 95, -200) via a 3L blue pin!
    a.pin("pin_lf1", (-60, 120, -100), "y", step=3, qty=1, explode_ldu=(0, 45, 0))
    a.pin("pin_lf2", (-60, 110, -200), "y", kind="pin_blue_3l", step=3, qty=1, explode_ldu=(0, 50, 0))
    a.add("left_jaw", "beam_9", (-60, 130, -180), I3, step=3, color=322, explode_ldu=(0, 75, 0))

    # Step 4: Motorized right sweeping jaw pinned directly to Large Motor A output disc at (60, 120, -160)!
    # Output disc pin holes (local y=45 -> world y=115, axis Y): at (60, 115, -140) and (60, 115, -180)!
    # Put a 9L magenta clamping arm flat along Z at (60, 130, -200) pinned to BOTH disc holes!
    # Plus a yellow 2x4 L-tip finger bending inward (-X) at the front end to hook the cargo!
    a.pin("pin_rj1", (60, 120, -140), "y", step=4, qty=2, explode_ldu=(0, 50, 0))
    a.pin("pin_rj2", (60, 120, -180), "y", step=4, qty=0, explode_ldu=(0, 50, 0))
    a.add("right_jaw", "beam_9", (60, 130, -200), I3, step=4, color=26, explode_ldu=(0, 75, 0))
    a.pin("pin_rt1", (60, 140, -260), "y", step=4, qty=2, explode_ldu=(0, 95, 0))
    a.pin("pin_rt2", (60, 140, -280), "y", step=4, qty=0, explode_ldu=(0, 95, 0))
    a.add("jaw_tip", "beam_l_2x4", (60, 150, -220), rot_z(180.0), step=4, color=14, explode_ldu=(0, 115, 0))
    # Sweep: 0 deg = open straight ahead (-Z), -45 deg (CCW from above = swings inward toward -X to clamp cargo!)
    # Wait: +ang = CW from above (swings outward +X, wide open!), -ang = CCW (swings inward -X, clamped!)
    a.add_revolute_joint(
        "j_jaw",
        pivot_ldu=(60, 120, -160),
        axis=(0, 1, 0),
        motor_port="A",
        parts=["pin_rj1", "pin_rj2", "right_jaw", "pin_rt1", "pin_rt2", "jaw_tip"],
        gear_ratio=1.0,
        sweep_deg=(-45.0, 55.0),
    )

    # Step 5: Ultrasonic Distance Sensor (Port F) on a rear "mast", looking forward OVER both jaws.
    # Why rear-top: the cargo must slide between the jaws right up to the Large Motor's front face
    # (z = -210). A front-mounted sensor would sit in that path and block the cargo.
    # Two upright 9L posts pin into the free rear Hub side holes (x = +/-65, y = 50/90, z = +80);
    # their top holes (y = 170 / 210) take the sensor's side pin holes (x = +/-65, y = 190 +/- 20).
    for side, s in (("l", -1.0), ("r", 1.0)):
        a.pin(f"pin_mp{side}1", (s * 70, 50, 80), "x", step=5, qty=4 if side == "l" else 0, explode_ldu=(s * 40, 0, 0))
        a.pin(f"pin_mp{side}2", (s * 70, 90, 80), "x", step=5, qty=0, explode_ldu=(s * 40, 0, 0))
        a.add(f"mast_{side}", "beam_9", (s * 80, 130, 80), BEAM_Y_HOLES_X, step=5, color=71, qty=2 if side == "l" else 0,
              explode_ldu=(s * 70, 0, 0))
        a.pin(f"pin_ds{side}1", (s * 70, 170, 80), "x", step=5, qty=4 if side == "l" else 0, explode_ldu=(s * 40, 40, 0))
        a.pin(f"pin_ds{side}2", (s * 70, 210, 80), "x", step=5, qty=0, explode_ldu=(s * 40, 40, 0))
    a.add("dist", "distance_sensor", (0, 190, 80), rot_y(180.0), step=5, port="F", explode_ldu=(0, 90, 0))
    cable(a, "cable_f", "dist", "hub", "F", step=5, lift=240, color="#0ea5e9")
    a.kinematics["sensors"] = {
        "F": {"type": "distance", "part": f"{a.prefix}dist", "dir": [0, 0, -1]},
    }
    # Hard stops of the jaw (motor degrees): wider than this the jaw hits the cable/mast region,
    # narrower than this it hits the fixed left jaw. The simulator stalls the motor here.
    a.kinematics["limits"] = {"A": {"min": -45.0, "max": 55.0}}
    # Cargo grip: cargo is 80 LDU (3.2 cm) square. Open jaws (>= +30 deg) leave a 4 cm+ gap; closing
    # toward 0 deg the yellow hook touches the cargo at about -1 deg (pinning it against the left jaw) and the motor stalls there.
    # Zone = where the cargo centre must be (robot frame, scene units) for the jaws to close around it.
    a.kinematics["gripper"] = {
        "port": "A",
        "zone": _scene_rect(-60, 40, -340, -180),
        "contact_deg": -1.0,
        "release_deg": 15.0,
        # Jaw mouth (between the jaws, y 130-160 LDU) is solid once the jaws are shut: a closed gripper
        # pushes the cargo instead of swallowing it.
        "closed_box": [round(v * LDU_TO_SCENE, 5) for v in (-51, 130, -290, 51, 160, -210)],
    }

    # Floor props: a tall slim cargo tower (3.2 x 3.2 x 9.2 cm, taller than the 7.6 cm sensor line)
    # straight ahead, and a green delivery zone to the right.
    a.floor_props = [
        {"type": "box", "pos": [-0.2, 2.3, -14.0], "size": [1.6, 4.6, 1.6], "color": "#ef4444", "movable": True, "id": "cargo"},
        {"type": "patch", "pos": [12.0, 0.0, -9.5], "size": [5.5, 5.5], "color": "#22c55e", "spike_color": "GREEN", "layer": 1},
    ]
    return a


# ==================================================================================================
# Registry & export helpers
# ==================================================================================================
MODEL_BUILDERS = {
    "magic-hub": build_l01_magic_hub,
    "lucky-spinner": build_l02_lucky_spinner,
    "metronome-arm": build_l03_metronome,
    "driving-base": build_l04_driving_base,
    "square-patrol": build_l05_square_patrol,
    "gyro-precision": build_l06_gyro_precision,
    "obstacle-avoider": build_l07_obstacle_avoider,
    "color-traffic": build_l08_color_traffic,
    "line-follower": build_l09_line_follower,
    "gear-gate": build_l10_gear_gate,
    "rack-pusher": build_l11_rack_pusher,
    "smart-gripper": build_l12_smart_gripper,
}


def build_model(lesson_id: str) -> Assembly:
    return MODEL_BUILDERS[lesson_id]()


def apply_model(
    lesson: Dict[str, Any],
    a: Assembly,
    floor_props: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Attach verified LDraw assembly parts, cables, joints, kinematics and floor_props to a lesson."""
    for s in lesson["steps"]:
        s["parts"] = a.step_parts(s["step"])
    meta = a.export_scene_meta()
    lesson["cables"] = [dict(c) for c in a.cables]
    lesson["joints"] = meta["joints"]
    lesson["gear_meshes"] = meta["gear_meshes"]
    lesson["crank_linkages"] = meta["crank_linkages"]
    lesson["kinematics"] = meta["kinematics"]
    lesson["floor_props"] = floor_props if floor_props is not None else meta["floor_props"]
    lesson["kinematics"]["collision_boxes"] = robot_collision_boxes(a)
    return lesson


def robot_collision_boxes(a: Assembly) -> List[List[float]]:
    """Rest-pose AABBs [xmin, ymin, zmin, xmax, ymax, zmax] (robot frame, scene units) of every rigid
    body part, used by the simulator for robot-vs-obstacle contact. Parts on motor joints are left out,
    except wheels (their box does not change while spinning); a gripper's jaws are handled separately."""
    from app.cad.verifier import _world_boxes  # local import: verifier imports assembly too

    wheel_ports = {w["port"] for w in a.kinematics.get("chassis", {}).get("wheels", [])}
    moving = {pid for j in a.joints if j["motor_port"] not in wheel_ports for pid in j["parts"]}
    out = []
    for p in a.all_parts():
        if p["id"] in moving or PART_SPECS[p["type"]]["kind"] in ("pin", "axle", "axle_pin", "bush"):
            continue
        R = _quat_mat(p["quat"])
        lo = [1e9] * 3
        hi = [-1e9] * 3
        for c, Rb, he in _world_boxes(p, (tuple(p["pos_ldu"]), R)):
            for k in range(3):
                r = sum(abs(Rb[k][m]) * he[m] for m in range(3))
                lo[k] = min(lo[k], c[k] - r)
                hi[k] = max(hi[k], c[k] + r)
        out.append([round(v * LDU_TO_SCENE, 4) for v in lo + hi])
    return out


def _quat_mat(q):
    from app.cad.verifier import quat_to_mat

    return quat_to_mat(q)
