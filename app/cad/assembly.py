"""Declarative LEGO Technic Grid Assembly Builder (LDU Y-up -> Three.js scene JSON).

Every part is placed in exact LEGO Design Units (1 stud = 20 LDU = 8 mm, floor Y = 0),
using proper right-handed rotation matrices (det = +1, zero mirrored parts).
Kinematic joints, gear meshes, crank linkages, cables, and floor props are emitted
alongside the parts so the Three.js viewer and SPIKE 3 Python VM drive real mechanisms.
"""
from __future__ import annotations

import copy
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

STUD = 20.0
LDU_TO_SCENE = 0.02  # 20 LDU (1 stud) = 0.40 scene units
SPECS_PATH = Path(__file__).resolve().parent / "part_specs.json"
PART_SPECS: Dict[str, Dict[str, Any]] = json.loads(SPECS_PATH.read_text(encoding="utf-8"))

# Standard SPIKE Prime official LDraw color codes -> display hex for BOM swatches
LDRAW_COLOR_HEX: Dict[int, str] = {
    0: "#1e293b",    # Black
    1: "#0055bf",    # Bright Blue
    2: "#237841",    # Dark Green
    4: "#c91a09",    # Red
    10: "#4b9f4a",   # Bright Green
    14: "#f2cd37",   # Yellow
    15: "#f8fafc",   # White
    19: "#e4cd9e",   # Tan
    25: "#fe8a18",   # Orange
    26: "#923978",   # Magenta (SPIKE Prime signature)
    71: "#a0a5a9",   # Light Bluish Grey
    72: "#6c6e68",   # Dark Bluish Grey
    322: "#36aebf",  # Medium Azure (SPIKE Prime signature)
}

Mat3 = Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]
Vec3 = Tuple[float, float, float]


def T(zh: str, en: str, ja: Optional[str] = None) -> Dict[str, str]:
    return {"zh": zh, "en": en, "ja": ja if ja is not None else en}


def _snap(v: float) -> float:
    return 0.0 if abs(v) < 1e-9 else round(v, 6)


def mat_mul(A: Mat3, B: Mat3) -> Mat3:
    return tuple(
        tuple(_snap(sum(A[i][k] * B[k][j] for k in range(3))) for j in range(3))
        for i in range(3)
    )  # type: ignore[return-value]


def mat_vec(R: Mat3, v: Sequence[float]) -> Vec3:
    return (
        R[0][0] * v[0] + R[0][1] * v[1] + R[0][2] * v[2],
        R[1][0] * v[0] + R[1][1] * v[1] + R[1][2] * v[2],
        R[2][0] * v[0] + R[2][1] * v[1] + R[2][2] * v[2],
    )


def rot_x(deg: float) -> Mat3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return ((1.0, 0.0, 0.0), (0.0, _snap(c), _snap(-s)), (0.0, _snap(s), _snap(c)))


def rot_y(deg: float) -> Mat3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return ((_snap(c), 0.0, _snap(s)), (0.0, 1.0, 0.0), (_snap(-s), 0.0, _snap(c)))


def rot_z(deg: float) -> Mat3:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    return ((_snap(c), _snap(-s), 0.0), (_snap(s), _snap(c), 0.0), (0.0, 0.0, 1.0))


def rot_xyz(rx_deg: float = 0.0, ry_deg: float = 0.0, rz_deg: float = 0.0) -> Mat3:
    """Standard Three.js XYZ Euler rotation: R = Rx(rx) @ Ry(ry) @ Rz(rz)."""
    return mat_mul(mat_mul(rot_x(rx_deg), rot_y(ry_deg)), rot_z(rz_deg))


def rot_zyx(rz_deg: float = 0.0, ry_deg: float = 0.0, rx_deg: float = 0.0) -> Mat3:
    """Apply Rx first, then Ry, then Rz in world axes: R = Rz @ Ry @ Rx."""
    return mat_mul(mat_mul(rot_z(rz_deg), rot_y(ry_deg)), rot_x(rx_deg))


def rot_axis_angle(axis: Sequence[float], deg: float) -> Mat3:
    ln = math.sqrt(axis[0] ** 2 + axis[1] ** 2 + axis[2] ** 2) or 1.0
    ux, uy, uz = axis[0] / ln, axis[1] / ln, axis[2] / ln
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    t = 1.0 - c
    return (
        (_snap(t * ux * ux + c), _snap(t * ux * uy - s * uz), _snap(t * ux * uz + s * uy)),
        (_snap(t * ux * uy + s * uz), _snap(t * uy * uy + c), _snap(t * uy * uz - s * ux)),
        (_snap(t * ux * uz - s * uy), _snap(t * uy * uz + s * ux), _snap(t * uz * uz + c)),
    )


def mat_to_quat(R: Mat3) -> List[float]:
    """Convert proper 3x3 rotation matrix to Three.js quaternion [x, y, z, w]."""
    m00, m01, m02 = R[0]
    m10, m11, m12 = R[1]
    m20, m21, m22 = R[2]
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m21 - m12) / s
        y = (m02 - m20) / s
        z = (m10 - m01) / s
    elif m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2.0
        w = (m21 - m12) / s
        x = 0.25 * s
        y = (m01 + m10) / s
        z = (m02 + m20) / s
    elif m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2.0
        w = (m02 - m20) / s
        x = (m01 + m10) / s
        y = 0.25 * s
        z = (m12 + m21) / s
    else:
        s = math.sqrt(1.0 + m22 - m00 - m11) * 2.0
        w = (m10 - m01) / s
        x = (m02 + m20) / s
        y = (m12 + m21) / s
        z = 0.25 * s
    ln = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    return [round(x / ln, 6), round(y / ln, 6), round(z / ln, 6), round(w / ln, 6)]


def quat_to_mat(q: Sequence[float]) -> Mat3:
    x, y, z, w = q
    return (
        (1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
        (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
        (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)),
    )


def mat_to_euler_xyz(R: Mat3) -> List[float]:
    """Convert rotation matrix to Three.js default XYZ Euler [rx, ry, rz] in radians."""
    sy = max(-1.0, min(1.0, R[0][2]))
    ry = math.asin(sy)
    if abs(sy) < 0.999999:
        rx = math.atan2(-R[1][2], R[2][2])
        rz = math.atan2(-R[0][1], R[0][0])
    else:
        rx = math.atan2(R[2][1], R[1][1])
        rz = 0.0
    return [round(rx, 6), round(ry, 6), round(rz, 6)]


def ldu_to_scene(v: Sequence[float]) -> List[float]:
    return [round(c * LDU_TO_SCENE, 5) for c in v]


DEFAULT_PART_NAMES: Dict[str, Dict[str, str]] = {
    "hub": T("SPIKE Prime 大型智能集线器 Hub", "SPIKE Prime Large Hub", "SPIKE プライム ラージハブ"),
    "medium_motor": T("中型角度电机", "Medium Angular Motor", "Mアンギュラーモーター"),
    "large_motor": T("大型角度电机", "Large Angular Motor", "Lアンギュラーモーター"),
    "distance_sensor": T("超声波距离传感器", "Ultrasonic Distance Sensor", "距離センサー"),
    "color_sensor": T("颜色传感器", "Color Sensor", "カラーセンサー"),
    "force_sensor": T("力传感器", "Force Sensor", "フォースセンサー"),
    "wheel": T("56mm 驱动轮 (白轮毂+青蓝胎)", "56mm Wheel with Integral Tire", "56mm 駆動輪（一体型タイヤ）"),
    "caster": T("万向钢珠轮组件 (支架+白球)", "Ball Caster Housing + 19mm Ball", "ボールキャスター（ホルダー＋球）"),
    "frame_5x7": T("5×7 科技开放框架", "Technic Frame 5×7 Open", "5×7 テクニックフレーム"),
    "frame_7x11": T("7×11 科技开放框架 (洋红)", "Technic Frame 7×11 Open (Magenta)", "7×11 テクニックフレーム（マゼンタ）"),
    "frame_11x15": T("11×15 科技开放框架", "Technic Frame 11×15 Open", "11×15 テクニックフレーム"),
    "baseplate_11x19": T("11×19 科技底板 (青蓝)", "Technic Baseplate 11×19 (Azure)", "11×19 テクニックベースプレート"),
    "biscuit_3x3": T("3×3 垂直连接块 (饼干块)", "Technic 3×3 Biscuit Connector", "3×3 垂直コネクターブロック"),
    "beam_3": T("3 孔科技梁", "Technic Beam 3L", "テクニックビーム 3L"),
    "beam_5": T("5 孔科技梁", "Technic Beam 5L", "テクニックビーム 5L"),
    "beam_7": T("7 孔科技梁", "Technic Beam 7L", "テクニックビーム 7L"),
    "beam_9": T("9 孔科技梁", "Technic Beam 9L", "テクニックビーム 9L"),
    "beam_11": T("11 孔科技梁", "Technic Beam 11L", "テクニックビーム 11L"),
    "beam_13": T("13 孔科技梁", "Technic Beam 13L", "テクニックビーム 13L"),
    "beam_15": T("15 孔科技梁", "Technic Beam 15L", "テクニックビーム 15L"),
    "beam_l_3x5": T("3×5 直角科技梁", "Technic Beam 3×5 Bent 90°", "3×5 L字テクニックビーム"),
    "beam_l_2x4": T("2×4 直角科技梁", "Technic Beam 2×4 Bent 90°", "2×4 L字テクニックビーム"),
    "beam_t_3x3": T("3×3 T 形科技梁", "Technic Beam 3×3 T-Shaped", "3×3 T字テクニックビーム"),
    "conn_perp_3x3": T("3×3 垂直直角连接器", "Perpendicular 3×3 Connector", "3×3 垂直コネクター"),
    "conn_1x3_4pin": T("1×3 四销垂直连接块", "1×3 Connector with 4 Pins", "1×3 4ピンコネクター"),
    "conn_axle_pin_1x2": T("1×2 轴销连接块", "1×2 Axle/Pin Connector", "1×2 軸ピンコネクター"),
    "pin_black": T("黑色摩擦销 2L", "Technic Friction Pin 2L (Black)", "黒フリクションピン 2L"),
    "pin_grey": T("浅灰无摩擦销 2L", "Technic Smooth Pin 2L (Light Grey)", "灰スムースピン 2L"),
    "pin_blue_3l": T("蓝色 3L 长摩擦销", "Technic Friction Pin 3L (Blue)", "青ロングピン 3L"),
    "axle_pin_blue": T("蓝色轴销连接器", "Technic Axle-Pin (Blue)", "青アクスルピン"),
    "axle_2": T("2L 红色十字轴", "Technic Axle 2L (Red)", "十字軸 2L（赤）"),
    "axle_3": T("3L 浅灰十字轴", "Technic Axle 3L (Grey)", "十字軸 3L（灰）"),
    "axle_4": T("4L 黑色十字轴", "Technic Axle 4L (Black)", "十字軸 4L（黒）"),
    "axle_5": T("5L 浅灰十字轴", "Technic Axle 5L (Grey)", "十字軸 5L（灰）"),
    "axle_6": T("6L 黑色十字轴", "Technic Axle 6L (Black)", "十字軸 6L（黒）"),
    "axle_7": T("7L 浅灰十字轴", "Technic Axle 7L (Grey)", "十字軸 7L（灰）"),
    "bush": T("十字轴套筒 (1L)", "Technic Bush (1L)", "テクニックブッシュ (1L)"),
    "half_bush": T("半宽十字轴套筒 (0.5L)", "Technic Half Bush (0.5L)", "ハーフブッシュ (0.5L)"),
    "gear_12": T("12 齿双斜面齿轮", "12-Tooth Double Bevel Gear", "12歯ダブルベベルギア"),
    "gear_20": T("20 齿双斜面齿轮", "20-Tooth Double Bevel Gear", "20歯ダブルベベルギア"),
    "gear_36": T("36 齿双斜面齿轮", "36-Tooth Double Bevel Gear", "36歯ダブルベベルギア"),
    "gear_rack_13": T("13 孔齿条 (带销/轴孔)", "1×13 Technic Gear Rack", "1×13 ギアラック"),
    "brick_2x4_technic": T("2×4 带十字孔科技砖", "2×4 Brick with Cross Holes", "2×4 十字穴付きブロック"),
    "tile_1x3": T("1×3 光面薄片 (琴键)", "1×3 Smooth Tile", "1×3 タイル"),
    "tile_1x2": T("1×2 光面薄片 (黑键)", "1×2 Smooth Tile", "1×2 タイル"),
}


class Assembly:
    """Declarative builder for a single LEGO SPIKE Prime lesson model in exact LDU."""

    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.steps_parts: Dict[int, List[Dict[str, Any]]] = {}
        self.parts_by_id: Dict[str, Dict[str, Any]] = {}
        self.joints: List[Dict[str, Any]] = []
        self.gear_meshes: List[Dict[str, Any]] = []
        self.crank_linkages: List[Dict[str, Any]] = []
        self.cables: List[Dict[str, Any]] = []
        self.kinematics: Dict[str, Any] = {"chassis": {"type": "static"}}
        self.floor_props: List[Dict[str, Any]] = []

    def add(
        self,
        part_id: str,
        part_type: str,
        pos_ldu: Sequence[float],
        rot_mat: Optional[Mat3] = None,
        *,
        step: int = 1,
        color: Optional[int] = None,
        name: Optional[Dict[str, str]] = None,
        qty: int = 1,
        explode_ldu: Sequence[float] = (0.0, 60.0, 0.0),
        port: Optional[str] = None,
        free_body: bool = False,
    ) -> Dict[str, Any]:
        assert part_type in PART_SPECS, f"Unknown part type: {part_type}"
        spec = PART_SPECS[part_type]
        R = rot_mat if rot_mat is not None else ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        ld_color = spec["color"] if color is None else color
        full_id = f"{self.prefix}{part_id}"
        assert full_id not in self.parts_by_id, f"Duplicate part id: {full_id}"

        part_dict: Dict[str, Any] = {
            "id": full_id,
            "type": part_type,
            "ldraw": spec["mpd_name"],
            "ldraw_color": ld_color,
            "part_no": spec["lego_id"],
            "color_hex": LDRAW_COLOR_HEX.get(ld_color, "#94a3b8"),
            "name": name or DEFAULT_PART_NAMES[part_type],
            "qty": qty,
            "pos": ldu_to_scene(pos_ldu),
            "pos_ldu": [round(float(c), 3) for c in pos_ldu],
            "rot": mat_to_euler_xyz(R),
            "quat": mat_to_quat(R),
            "explode": ldu_to_scene(explode_ldu),
        }
        if "led_matrix_ldu" in spec:
            m = spec["led_matrix_ldu"]
            part_dict["led_matrix"] = {
                "y": round((m["y"] + 0.3) * LDU_TO_SCENE, 5),
                "cols_x": [round(v * LDU_TO_SCENE, 5) for v in m["cols_x"]],
                "rows_z": [round(v * LDU_TO_SCENE, 5) for v in m["rows_z"]],
                "size": [round(v * LDU_TO_SCENE, 5) for v in m["size_xz"]],
            }
        if port:
            part_dict["port"] = port
        if free_body:
            part_dict["free_body"] = True
        if "rotor_mpd" in spec:
            part_dict["rotor"] = {
                "ldraw": spec["rotor_mpd"],
                "ldraw_color": spec["rotor_color"],
                "offset": ldu_to_scene(spec["rotor_offset_ldu"]),
                "axis": spec["rotor_axis"],
            }
        if "plunger_mpd" in spec:
            part_dict["plunger"] = {
                "ldraw": spec["plunger_mpd"],
                "ldraw_color": spec["plunger_color"],
                "offset": ldu_to_scene(spec["plunger_offset_ldu"]),
                "axis": [0.0, 0.0, -1.0],
                "travel": round(10.0 * LDU_TO_SCENE, 5),
            }

        self.steps_parts.setdefault(step, []).append(part_dict)
        self.parts_by_id[full_id] = part_dict
        return part_dict

    def pin(
        self,
        part_id: str,
        pos_ldu: Sequence[float],
        axis: str = "x",
        *,
        kind: str = "pin_black",
        step: int = 1,
        qty: int = 0,
        explode_ldu: Optional[Sequence[float]] = None,
        color: Optional[int] = None,
        name: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Place a Technic pin/axle centered at pos_ldu along 'x', 'y', or 'z'."""
        if axis == "x":
            R = rot_xyz(0, 0, 0)
            exp = explode_ldu or (40.0, 0.0, 0.0)
        elif axis == "y":
            R = rot_z(90.0)
            exp = explode_ldu or (0.0, 50.0, 0.0)
        elif axis == "z":
            R = rot_y(90.0)
            exp = explode_ldu or (0.0, 0.0, 50.0)
        else:
            raise ValueError(f"Unknown axis: {axis}")
        return self.add(part_id, kind, pos_ldu, R, step=step, qty=qty, explode_ldu=exp, color=color, name=name)

    def add_revolute_joint(
        self,
        joint_id: str,
        *,
        pivot_ldu: Sequence[float],
        axis: Sequence[float],
        motor_port: str,
        parts: Sequence[str],
        gear_ratio: float = 1.0,
        parent: Optional[str] = None,
        sweep_deg: Tuple[float, float] = (-90.0, 90.0),
    ):
        self.joints.append(
            {
                "id": f"{self.prefix}{joint_id}",
                "type": "revolute",
                "parent": f"{self.prefix}{parent}" if parent else None,
                "pivot": ldu_to_scene(pivot_ldu),
                "pivot_ldu": [round(float(c), 3) for c in pivot_ldu],
                "axis": [float(a) for a in axis],
                "motor_port": motor_port,
                "gear_ratio": float(gear_ratio),
                "parts": [f"{self.prefix}{p}" for p in parts],
                "sweep_deg": [float(sweep_deg[0]), float(sweep_deg[1])],
            }
        )

    def add_prismatic_joint(
        self,
        joint_id: str,
        *,
        axis: Sequence[float],
        motor_port: str,
        ldu_per_deg: float,
        min_ldu: float,
        max_ldu: float,
        parts: Sequence[str],
        parent: Optional[str] = None,
    ):
        self.joints.append(
            {
                "id": f"{self.prefix}{joint_id}",
                "type": "prismatic",
                "parent": f"{self.prefix}{parent}" if parent else None,
                "axis": [float(a) for a in axis],
                "motor_port": motor_port,
                "scale_per_deg": round(ldu_per_deg * LDU_TO_SCENE, 7),
                "ldu_per_deg": float(ldu_per_deg),
                "min_travel": round(min_ldu * LDU_TO_SCENE, 5),
                "max_travel": round(max_ldu * LDU_TO_SCENE, 5),
                "min_ldu": float(min_ldu),
                "max_ldu": float(max_ldu),
                "parts": [f"{self.prefix}{p}" for p in parts],
            }
        )

    def add_crank_linkage(
        self,
        linkage_id: str,
        *,
        motor_port: str,
        axis: Sequence[float],
        crank_radius_ldu: float,
        phase_deg: float,
        sign: float,
        coupler_parts: Sequence[str],
    ):
        """Parallel-crank parallelogram coupler: all coupler parts translate in an exact circle
        of radius crank_radius_ldu perpendicular to axis without rotating."""
        self.crank_linkages.append(
            {
                "id": f"{self.prefix}{linkage_id}",
                "motor_port": motor_port,
                "axis": [float(a) for a in axis],
                "radius": round(crank_radius_ldu * LDU_TO_SCENE, 5),
                "radius_ldu": float(crank_radius_ldu),
                "phase_deg": float(phase_deg),
                "sign": float(sign),
                "parts": [f"{self.prefix}{p}" for p in coupler_parts],
            }
        )

    def add_gear_mesh(self, part_a: str, part_b: str, mesh_type: str = "parallel"):
        self.gear_meshes.append(
            {"a": f"{self.prefix}{part_a}", "b": f"{self.prefix}{part_b}", "type": mesh_type}
        )

    def world_point_on(self, part_id: str, local_ldu: Sequence[float]) -> Vec3:
        p = self.parts_by_id[f"{self.prefix}{part_id}"]
        R = quat_to_mat(p["quat"])
        off = mat_vec(R, local_ldu)
        pl = p["pos_ldu"]
        return (pl[0] + off[0], pl[1] + off[1], pl[2] + off[2])

    def add_cable(
        self,
        cable_id: str,
        *,
        device_part_id: str,
        hub_part_id: str,
        port: str,
        step: int,
        color: str = "#64748b",
        label: Optional[str] = None,
        via_ldu: Sequence[Sequence[float]] = (),
    ):
        dev = self.parts_by_id[f"{self.prefix}{device_part_id}"]
        dev_spec = PART_SPECS[dev["type"]]
        start_ldu = self.world_point_on(device_part_id, dev_spec["cable_exit_ldu"])
        hub_ports = PART_SPECS["hub"]["hub_ports_ldu"]
        end_ldu = self.world_point_on(hub_part_id, hub_ports[port])
        # Build clean spline points from device exit -> intermediate waypoints -> Hub port socket
        pts_ldu = [start_ldu] + [tuple(v) for v in via_ldu] + [end_ldu]
        self.cables.append(
            {
                "id": f"{self.prefix}{cable_id}",
                "step": step,
                "port": port,
                "label": label or f"Port {port}",
                "color": color,
                "points": [ldu_to_scene(pt) for pt in pts_ldu],
                "points_ldu": [[round(c, 2) for c in pt] for pt in pts_ldu],
                "device_part_id": dev["id"],
                "hub_part_id": f"{self.prefix}{hub_part_id}",
            }
        )

    def step_parts(self, step: int) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.steps_parts.get(step, []))

    def all_parts(self) -> List[Dict[str, Any]]:
        out = []
        for s in sorted(self.steps_parts):
            out.extend(copy.deepcopy(self.steps_parts[s]))
        return out

    def export_scene_meta(self) -> Dict[str, Any]:
        return {
            "joints": copy.deepcopy(self.joints),
            "gear_meshes": copy.deepcopy(self.gear_meshes),
            "crank_linkages": copy.deepcopy(self.crank_linkages),
            "kinematics": copy.deepcopy(self.kinematics),
            "floor_props": copy.deepcopy(self.floor_props),
        }


def clone_assembly(src: Assembly, new_prefix: str, flatten_to_step: int = 1) -> Assembly:
    """Clone an entire verified Assembly under a new id prefix (used when lessons build on Driving Base)."""
    dst = Assembly(prefix="")
    old_p = src.prefix

    def remap(pid: Optional[str]) -> Optional[str]:
        if pid is None:
            return None
        base = pid[len(old_p):] if old_p and pid.startswith(old_p) else pid
        return f"{new_prefix}{base}"

    for s in sorted(src.steps_parts):
        for p in src.steps_parts[s]:
            cp = copy.deepcopy(p)
            cp["id"] = remap(cp["id"])
            cp["explode"] = [round(v * 0.75, 5) for v in cp["explode"]]
            target_step = flatten_to_step if flatten_to_step is not None else s
            dst.steps_parts.setdefault(target_step, []).append(cp)
            dst.parts_by_id[cp["id"]] = cp

    for j in src.joints:
        cj = copy.deepcopy(j)
        cj["id"] = remap(cj["id"])
        cj["parent"] = remap(cj["parent"])
        cj["parts"] = [remap(pid) for pid in cj["parts"]]
        dst.joints.append(cj)

    for gm in src.gear_meshes:
        dst.gear_meshes.append({"a": remap(gm["a"]), "b": remap(gm["b"]), "type": gm["type"]})

    for cl in src.crank_linkages:
        ccl = copy.deepcopy(cl)
        ccl["id"] = remap(ccl["id"])
        ccl["parts"] = [remap(pid) for pid in ccl["parts"]]
        dst.crank_linkages.append(ccl)

    for c in src.cables:
        cc = copy.deepcopy(c)
        cc["id"] = remap(cc["id"])
        cc["step"] = flatten_to_step if flatten_to_step is not None else cc["step"]
        cc["device_part_id"] = remap(cc["device_part_id"])
        cc["hub_part_id"] = remap(cc["hub_part_id"])
        dst.cables.append(cc)

    dst.kinematics = copy.deepcopy(src.kinematics)
    dst.floor_props = copy.deepcopy(src.floor_props)
    dst.prefix = new_prefix
    return dst
