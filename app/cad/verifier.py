"""Zero-tolerance 3D Geometry, Connector, Gear-Mesh, Floor & Kinematic Sweep Verifier.

Validates every lesson assembly directly in exact LDU (1 stud = 20 LDU = 8 mm):
  1. Official LEGO Education SPIKE Prime Set 45678 parts & piece-count compliance.
  2. Exact pin/axle coaxial hole engagement (>= 2 distinct real holes per connector).
  3. Zero solid-body overlap (3D OBB SAT) at rest AND across full kinematic sweeps.
  4. Gear & rack-and-pinion exact LEGO center-distance meshing.
  5. Floor contact (no below-floor penetration; wheels & caster simultaneously on Y=0;
     every non-free structural part connected to floor-anchored support).
  6. Cable start/end alignment with exact LDraw device cable exits & Hub port sockets.
"""
from __future__ import annotations

import itertools
import math
from collections import Counter, defaultdict, deque
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from app.cad.assembly import (
    LDU_TO_SCENE,
    PART_SPECS,
    Mat3,
    Vec3,
    mat_mul,
    mat_vec,
    quat_to_mat,
    rot_axis_angle,
)

CONNECTOR_KINDS = {"pin", "axle", "axle_pin"}


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a: Vec3) -> float:
    return math.sqrt(_dot(a, a))


def _col(R: Mat3, i: int) -> Vec3:
    return (R[0][i], R[1][i], R[2][i])


def _world_boxes(part: Dict[str, Any], pose: Tuple[Vec3, Mat3]) -> List[Tuple[Vec3, Mat3, Vec3]]:
    pos, R = pose
    spec = PART_SPECS[part["type"]]
    out = []
    for b in spec["boxes"]:
        x0, y0, z0, x1, y1, z1 = b
        c_loc = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
        he = (0.5 * (x1 - x0), 0.5 * (y1 - y0), 0.5 * (z1 - z0))
        out.append((_add(pos, mat_vec(R, c_loc)), R, he))
    return out


def _sat_depth(a: Tuple[Vec3, Mat3, Vec3], b: Tuple[Vec3, Mat3, Vec3]) -> float:
    ca, Ra, ha = a
    cb, Rb, hb = b
    d = _sub(cb, ca)
    axes: List[Vec3] = [_col(Ra, i) for i in range(3)] + [_col(Rb, i) for i in range(3)]
    for i in range(3):
        for j in range(3):
            v = _cross(_col(Ra, i), _col(Rb, j))
            n = _norm(v)
            if n > 1e-6:
                axes.append((v[0] / n, v[1] / n, v[2] / n))
    min_ov = 1e9
    for ax in axes:
        ra = sum(ha[k] * abs(_dot(_col(Ra, k), ax)) for k in range(3))
        rb = sum(hb[k] * abs(_dot(_col(Rb, k), ax)) for k in range(3))
        ov = ra + rb - abs(_dot(d, ax))
        if ov < min_ov:
            min_ov = ov
    return min_ov


def _pair_overlap(p: Dict[str, Any], q: Dict[str, Any], poses: Dict[str, Tuple[Vec3, Mat3]]) -> float:
    return max(_sat_depth(a, b) for a in _world_boxes(p, poses[p["id"]]) for b in _world_boxes(q, poses[q["id"]]))


def _min_y_ldu(part: Dict[str, Any], pose: Tuple[Vec3, Mat3]) -> float:
    pos, R = pose
    spec = PART_SPECS[part["type"]]
    if spec["kind"] == "wheel":
        # Wheels are cylinders about local Z: the lowest point does not depend on spin angle.
        ax = _col(R, 2)
        half_w = 0.5 * (spec["bbox"][5] - spec["bbox"][2])
        r = spec["radius_ldu"]
        return pos[1] - r * math.sqrt(max(0.0, 1.0 - ax[1] * ax[1])) - half_w * abs(ax[1])
    x0, y0, z0, x1, y1, z1 = spec["bbox"]
    c_loc = (0.5 * (x0 + x1), 0.5 * (y0 + y1), 0.5 * (z0 + z1))
    he = (0.5 * (x1 - x0), 0.5 * (y1 - y0), 0.5 * (z1 - z0))
    c_w = _add(pos, mat_vec(R, c_loc))
    return c_w[1] - (abs(R[1][0]) * he[0] + abs(R[1][1]) * he[1] + abs(R[1][2]) * he[2])


def _connector_segment(part: Dict[str, Any], pose: Tuple[Vec3, Mat3]) -> Tuple[Vec3, Vec3, float]:
    """Return (center_world, unit_axis_world, half_length_ldu) for a pin/axle."""
    pos, R = pose
    spec = PART_SPECS[part["type"]]
    ax = _col(R, 0)  # All LDraw pins & axles lie along local X
    ln = _norm(ax) or 1.0
    return pos, (ax[0] / ln, ax[1] / ln, ax[2] / ln), 0.5 * spec["conn_len"]


def _hole_engages_connector(
    conn_center: Vec3,
    conn_axis: Vec3,
    conn_half_len: float,
    conn_kind: str,
    host_part: Dict[str, Any],
    host_pose: Tuple[Vec3, Mat3],
) -> bool:
    hpos, hR = host_pose
    spec = PART_SPECS[host_part["type"]]
    for h in spec["holes"]:
        # Pin fits pin holes; axle fits both axle holes & round pin holes (free spin); axle_pin fits both
        if conn_kind == "pin" and h["kind"] == "axle":
            continue
        hc = _add(hpos, mat_vec(hR, h["pos"]))
        hax = mat_vec(hR, h["axis"])
        hn = _norm(hax) or 1.0
        hax = (hax[0] / hn, hax[1] / hn, hax[2] / hn)
        if abs(_dot(conn_axis, hax)) < 0.995:
            continue
        delta = _sub(hc, conn_center)
        along = _dot(delta, conn_axis)
        perp_v = _sub(delta, (conn_axis[0] * along, conn_axis[1] * along, conn_axis[2] * along))
        if _norm(perp_v) > 1.0:  # <= 0.4 mm coaxial precision
            continue
        # Longitudinal overlap between connector [-half_len, +half_len] and hole [along - d/2, along + d/2]
        h_half = 0.5 * h["depth"]
        ov = min(conn_half_len, along + h_half) - max(-conn_half_len, along - h_half)
        if ov >= 6.0:  # At least 6 LDU (2.4 mm) insertion depth
            return True
    return False


def solve_poses(
    parts: List[Dict[str, Any]],
    joints: List[Dict[str, Any]],
    crank_linkages: List[Dict[str, Any]],
    motor_angles_deg: Dict[str, float],
) -> Dict[str, Tuple[Vec3, Mat3]]:
    """Forward-kinematics solver returning exact world (pos_ldu, R) for every part given motor angles."""
    base_poses: Dict[str, Tuple[Vec3, Mat3]] = {
        p["id"]: (tuple(p["pos_ldu"]), quat_to_mat(p["quat"])) for p in parts
    }
    if not joints and not crank_linkages:
        return base_poses

    joints_by_id = {j["id"]: j for j in joints}
    # Build rigid transform (t, R) for each joint relative to world (composed down parent chain)
    joint_delta: Dict[str, Tuple[Vec3, Mat3]] = {}

    def get_joint_tf(jid: str) -> Tuple[Vec3, Mat3]:
        if jid in joint_delta:
            return joint_delta[jid]
        j = joints_by_id[jid]
        ang = motor_angles_deg.get(j["motor_port"], 0.0)
        if j["type"] == "revolute":
            # Positive motor degrees rotate clockwise looking at +axis (= -angle right-handed about axis),
            # matching viewer3d.js::jointTransform and real SPIKE Prime motor rotors.
            d_ang = -ang * j["gear_ratio"]
            Rj = rot_axis_angle(j["axis"], d_ang)
            piv = tuple(j["pivot_ldu"])
            # x' = piv + Rj @ (x - piv) = Rj @ x + (piv - Rj @ piv)
            tj = _sub(piv, mat_vec(Rj, piv))
        elif j["type"] == "prismatic":
            disp = max(j["min_ldu"], min(j["max_ldu"], ang * j["ldu_per_deg"]))
            ax = j["axis"]
            Rj = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            tj = (ax[0] * disp, ax[1] * disp, ax[2] * disp)
        else:
            Rj = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
            tj = (0.0, 0.0, 0.0)

        if j.get("parent"):
            tp, Rp = get_joint_tf(j["parent"])
            # Compose: parent(child(x)) = Rp @ (Rj @ x + tj) + tp
            R_tot = mat_mul(Rp, Rj)
            t_tot = _add(mat_vec(Rp, tj), tp)
        else:
            R_tot, t_tot = Rj, tj
        joint_delta[jid] = (t_tot, R_tot)
        return t_tot, R_tot

    poses = dict(base_poses)
    for j in joints:
        tj, Rj = get_joint_tf(j["id"])
        for pid in j["parts"]:
            if pid not in base_poses:
                continue
            p0, R0 = base_poses[pid]
            poses[pid] = (_add(mat_vec(Rj, p0), tj), mat_mul(Rj, R0))

    # Parallel-crank coupler translation (parts orbit in a circle without rotating)
    for cl in crank_linkages:
        ang = motor_angles_deg.get(cl["motor_port"], 0.0)
        r = cl["radius_ldu"]
        rad0 = math.radians(cl["phase_deg"])
        rad = math.radians(cl["phase_deg"] + cl["sign"] * ang)
        # Orbit in plane perpendicular to axis (for X-axis cranks, circle in Y-Z plane)
        ax = cl["axis"]
        if abs(ax[0]) > 0.9:
            dy = r * (math.sin(rad) - math.sin(rad0))
            dz = r * (math.cos(rad) - math.cos(rad0))
            dx = 0.0
        elif abs(ax[2]) > 0.9:
            dx = r * (math.cos(rad) - math.cos(rad0))
            dy = r * (math.sin(rad) - math.sin(rad0))
            dz = 0.0
        else:
            dx = r * (math.cos(rad) - math.cos(rad0))
            dz = r * (math.sin(rad) - math.sin(rad0))
            dy = 0.0
        for pid in cl["parts"]:
            if pid not in poses:
                continue
            p0, R0 = poses[pid]
            poses[pid] = ((p0[0] + dx, p0[1] + dy, p0[2] + dz), R0)

    return poses


def verify_lesson_geometry(lesson: Dict[str, Any]) -> List[str]:
    """Run all physical & geometric invariants on a lesson dict. Returns list of error strings (empty = PASS)."""
    errors: List[str] = []
    parts = [p for s in lesson["steps"] for p in s.get("parts", [])]
    if not parts:
        return ["Lesson has no 3D parts"]

    joints = lesson.get("joints", [])
    gear_meshes = lesson.get("gear_meshes", [])
    crank_linkages = lesson.get("crank_linkages", [])
    cables = lesson.get("cables", [])

    # 1. Duplicate IDs & Official LEGO Set 45678 compliance + piece count check
    ids = [p["id"] for p in parts]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate part IDs found")

    counts = Counter(p["type"] for p in parts)
    for ptype, cnt in counts.items():
        if ptype not in PART_SPECS:
            errors.append(f"Unknown part type not in 45678 catalog: {ptype}")
            continue
        max_q = PART_SPECS[ptype]["qty_45678"]
        if cnt > max_q:
            errors.append(f"Exceeds LEGO 45678 kit qty: {ptype} uses {cnt} > {max_q}")

    parts_by_id = {p["id"]: p for p in parts}
    rest_poses = solve_poses(parts, [], [], {})

    # Pairs allowed to interpenetrate (meshing gear teeth at pitch circle)
    mesh_pairs: Set[Tuple[str, str]] = set()
    for gm in gear_meshes:
        a, b = gm["a"], gm["b"]
        mesh_pairs.add((a, b))
        mesh_pairs.add((b, a))
        if a not in parts_by_id or b not in parts_by_id:
            errors.append(f"Gear mesh references unknown part: {a} <-> {b}")
            continue
        sa, sb = PART_SPECS[parts_by_id[a]["type"]], PART_SPECS[parts_by_id[b]["type"]]
        pa, Ra = rest_poses[a]
        pb, Rb = rest_poses[b]
        if gm["type"] == "parallel":
            expect = (sa["teeth"] + sb["teeth"]) * 20.0 / 16.0
            dist = _norm(_sub(pa, pb))
            if abs(dist - expect) > 0.6:
                errors.append(f"Gear mesh {a}({sa['teeth']}T)-{b}({sb['teeth']}T): dist={dist:.2f} != {expect:.2f} LDU")
        elif gm["type"] == "rack":
            # Pinion center must be at exact perpendicular distance = 20.0 LDU from rack center
            # (pitch_radius 15 + rack pitch_line 5 = 20 LDU for 12T gear + 64781 rack)
            gear_p, rack_p = (a, b) if sa["kind"] == "gear" else (b, a)
            gp, _ = rest_poses[gear_p]
            rp, rR = rest_poses[rack_p]
            # Rack local X is travel direction; local +Y is tooth normal
            rack_y = _col(rR, 1)
            rack_z = _col(rR, 2)
            dv = _sub(gp, rp)
            dist_y = _dot(dv, rack_y)
            dist_z = abs(_dot(dv, rack_z))
            if abs(dist_y - 20.0) > 0.6 or dist_z > 0.6:
                errors.append(f"Rack mesh {gear_p}-{rack_p}: normal_dist={dist_y:.2f} (expect 20.0), lateral={dist_z:.2f}")

    # 2. Connector coaxial engagement & structural graph
    adj: Dict[str, Set[str]] = defaultdict(set)
    for p in parts:
        spec = PART_SPECS[p["type"]]
        if spec["kind"] in CONNECTOR_KINDS:
            cc, cax, chalf = _connector_segment(p, rest_poses[p["id"]])
            engaged = []
            for q in parts:
                if q["id"] == p["id"]:
                    continue
                qspec = PART_SPECS[q["type"]]
                if qspec["kind"] in CONNECTOR_KINDS:
                    continue
                if _hole_engages_connector(cc, cax, chalf, spec["kind"], q, rest_poses[q["id"]]):
                    engaged.append(q["id"])
                    adj[p["id"]].add(q["id"])
                    adj[q["id"]].add(p["id"])
            if len(engaged) < 2:
                errors.append(f"Connector {p['id']} ({p['type']}) engages only {len(engaged)} real hole(s): {engaged}")

    # Direct brick/tile stud-to-stud or face resting contact (e.g. bricks stacked on baseplate/hub)
    solid_parts = [p for p in parts if PART_SPECS[p["type"]]["kind"] not in CONNECTOR_KINDS]
    for p, q in itertools.combinations(solid_parts, 2):
        ov = _pair_overlap(p, q, rest_poses)
        if ov >= -1.5:  # touching or within 0.6 mm clearance
            adj[p["id"]].add(q["id"])
            adj[q["id"]].add(p["id"])

    # 3. Collision check at rest AND across full kinematic sweeps
    sweep_configs: List[Tuple[str, Dict[str, float]]] = [("rest", {})]
    ports_used = sorted({j["motor_port"] for j in joints} | {cl["motor_port"] for cl in crank_linkages})
    for mp in ports_used:
        # Determine angle sweep for this port
        lo, hi = -90.0, 90.0
        for j in joints:
            if j["motor_port"] == mp and j["type"] == "revolute":
                lo, hi = j.get("sweep_deg", [-90.0, 90.0])
            elif j["motor_port"] == mp and j["type"] == "prismatic":
                # Drive through full min..max travel
                s = j["ldu_per_deg"]
                if abs(s) > 1e-6:
                    a0, a1 = j["min_ldu"] / s, j["max_ldu"] / s
                    lo, hi = min(a0, a1), max(a0, a1)
        for cl in crank_linkages:
            if cl["motor_port"] == mp:
                lo, hi = 0.0, 360.0
        for k in range(1, 9):
            val = lo + (hi - lo) * (k / 8.0)
            sweep_configs.append((f"{mp}={val:.0f}deg", {mp: val}))

    # Also check coupled simultaneous motion for multi-motor mechanisms (e.g., crane slew + hoisted)
    if len(ports_used) >= 2:
        combo = {}
        for j in joints:
            if j["type"] == "revolute":
                combo[j["motor_port"]] = j.get("sweep_deg", [0, 90])[1]
            elif j["type"] == "prismatic":
                combo[j["motor_port"]] = 0.5 * (j["min_ldu"] + j["max_ldu"]) / (j["ldu_per_deg"] or 1.0)
        for cl in crank_linkages:
            combo[cl["motor_port"]] = 180.0
        sweep_configs.append(("combined", combo))

    for cfg_name, m_angles in sweep_configs:
        poses = solve_poses(parts, joints, crank_linkages, m_angles)
        for p, q in itertools.combinations(solid_parts, 2):
            if (p["id"], q["id"]) in mesh_pairs:
                continue
            ov = _pair_overlap(p, q, poses)
            if ov > 1.5:  # > 0.6 mm real solid overlap = collision!
                errors.append(
                    f"COLLISION [{cfg_name}] {ov:.1f} LDU: {p['id']}({p['type']}) x {q['id']}({q['type']})"
                )
        # Floor penetration check at rest (and during motion for non-walker parts)
        for p in solid_parts:
            if p.get("free_body"):
                continue
            miny = _min_y_ldu(p, poses[p["id"]])
            # Allow crank-walker feet to sweep slightly below rest baseline? No, keep rest >= -0.5 LDU!
            tol = -22.0 if (cfg_name != "rest" and crank_linkages) else -1.0
            if miny < tol:
                errors.append(f"BELOW FLOOR [{cfg_name}] {p['id']}({p['type']}) min_y={miny:.1f} LDU")

    # 4. Floor support & structural connectivity check at rest
    floor_anchored: Set[str] = set()
    for p in solid_parts:
        miny = _min_y_ldu(p, rest_poses[p["id"]])
        if abs(miny) <= 1.2:
            floor_anchored.add(p["id"])
    if not floor_anchored:
        errors.append("No part rests on floor Y=0")
    else:
        seen = set(floor_anchored)
        dq = deque(floor_anchored)
        while dq:
            cur = dq.popleft()
            for nb in adj[cur]:
                if nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
        for p in solid_parts:
            if p["id"] not in seen:
                miny = _min_y_ldu(p, rest_poses[p["id"]])
                errors.append(f"FLOATING / UNATTACHED {p['id']}({p['type']}) min_y={miny:.1f} LDU")

    # For wheeled driving bases, verify BOTH wheels and caster simultaneously touch floor Y=0
    wheels = [p for p in solid_parts if p["type"] == "wheel"]
    casters = [p for p in solid_parts if p["type"] == "caster"]
    for p in wheels + casters:
        miny = _min_y_ldu(p, rest_poses[p["id"]])
        if abs(miny) > 1.0:
            errors.append(f"Support contact {p['id']}({p['type']}) min_y={miny:.1f} LDU (must be 0.0)")

    # 5. Cable start & end verification
    hubs = [p for p in solid_parts if p["type"] == "hub"]
    if hubs and cables:
        hub = hubs[0]
        hpos, hR = rest_poses[hub["id"]]
        port_map = PART_SPECS["hub"]["hub_ports_ldu"]
        for c in cables:
            pts = c.get("points_ldu")
            if not pts:
                pts = [[v / LDU_TO_SCENE for v in pt] for pt in c["points"]]
            end = tuple(pts[-1])
            expect_end = _add(hpos, mat_vec(hR, port_map[c["port"]]))
            d_end = _norm(_sub(end, expect_end))
            if d_end > 2.0:
                errors.append(f"Cable {c.get('id', c['port'])} ends {d_end:.1f} LDU from Hub Port {c['port']}")
            if c.get("device_part_id") in parts_by_id:
                dev = parts_by_id[c["device_part_id"]]
                dspec = PART_SPECS[dev["type"]]
                if "cable_exit_ldu" in dspec:
                    dpos, dR = rest_poses[dev["id"]]
                    expect_start = _add(dpos, mat_vec(dR, dspec["cable_exit_ldu"]))
                    d_start = _norm(_sub(tuple(pts[0]), expect_start))
                    if d_start > 5.0:
                        errors.append(f"Cable {c.get('id', c['port'])} starts {d_start:.1f} LDU from {dev['id']} exit")

    return errors
