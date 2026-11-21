#!/usr/bin/env python3
"""Pack official LEGO LDraw parts for SPIKE Prime (45678) into self-contained MPD files
and extract exact Y-up LDU specifications (bboxes, sub-boxes, pin/axle holes, ports).

Coordinate convention used throughout SPIKE Prime Studio CAD:
  - Right-handed Y-up in LDU (1 LEGO stud = 20 LDU = 8 mm; 1 plate = 8 LDU = 3.2 mm).
  - Conversion from LDraw native (Y-down): (x, y, z)_up = (x, -y, -z)_ldraw
    (a proper 180° rotation about X with det = +1, preserving triangle winding).
  - Three.js scene scale: 1 LDU = 0.02 scene units (so 1 stud = 0.40 scene units).
"""
import json
import math
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
LDRAW_ZIP = Path("/tmp/ldraw_complete.zip")
OUT_LDRAW = ROOT / "app" / "static" / "ldraw"
OUT_PARTS = OUT_LDRAW / "parts"
OUT_SPECS = ROOT / "app" / "cad" / "part_specs.json"

# Catalog of SPIKE Prime (Set 45678) parts used across the curriculum.
# Each entry maps our internal `type` key to:
#   ldraw_src: source .dat in official LDraw library
#   mpd_name:  output .mpd basename under app/static/ldraw/parts/
#   lego_id:   official LEGO Design/Element ID shown in BOM
#   color:     default official LDraw color code matching Set 45678
#   qty_45678: max quantity in 1× LEGO Education SPIKE Prime Set 45678
#   kind:      'part' | 'pin' | 'axle' | 'axle_pin' | 'gear' | 'motor' | 'sensor' | 'hub'
#   sub_mpds:  optional moving sub-assemblies (motor rotor, force sensor plunger)
PART_CATALOG: Dict[str, dict] = {
    "hub": {
        "ldraw_src": "45601c01.dat",
        "mpd_name": "45601c01",
        "lego_id": "45601",
        "color": 15,  # White top (yellow bottom & battery hardcoded in 45601c01)
        "qty_45678": 1,
        "kind": "hub",
    },
    "medium_motor": {
        "ldraw_src": "54696p01.dat",
        "mpd_name": "54696_body",
        "body_src": "u9364c01.dat",
        "rotor_src": "u9363p01.dat",
        "rotor_mpd": "54696_rotor",
        "rotor_color": 322,  # Medium Azure (matches 54696p01.dat line 2)
        "rotor_offset_ldu": [0.0, 50.0, 0.0],  # Y-up from LDraw (0, -50, 0)
        "rotor_axis": [0.0, 1.0, 0.0],
        "lego_id": "45603",
        "color": 15,  # White housing + Medium Azure back
        "qty_45678": 2,
        "kind": "motor",
        "cable_exit_ldu": [0.0, 0.0, -148.0],
    },
    "large_motor": {
        "ldraw_src": "54675.dat",
        "mpd_name": "54675_body",
        "body_src": "u9367c01.dat",
        "rotor_src": "u9363.dat",
        "rotor_mpd": "54675_rotor",
        "rotor_color": 322,
        "rotor_offset_ldu": [0.0, 50.0, 0.0],
        "rotor_axis": [0.0, 1.0, 0.0],
        "lego_id": "45602",
        "color": 15,
        "qty_45678": 1,
        "kind": "motor",
        "cable_exit_ldu": [0.0, 0.0, -148.0],
    },
    "distance_sensor": {
        "ldraw_src": "37316.dat",
        "mpd_name": "37316",
        "lego_id": "45604",
        "color": 15,
        "qty_45678": 1,
        "kind": "sensor",
        "cable_exit_ldu": [0.0, 0.0, -8.0],
    },
    "color_sensor": {
        "ldraw_src": "37308.dat",
        "mpd_name": "37308",
        "lego_id": "45605",
        "color": 15,
        "qty_45678": 1,
        "kind": "sensor",
        "cable_exit_ldu": [0.0, 0.0, -8.0],
    },
    "force_sensor": {
        "ldraw_src": "37312.dat",
        "mpd_name": "37312_body",
        "body_src": "u9461c01.dat",
        "plunger_src": "u9462.dat",
        "plunger_mpd": "37312_plunger",
        "plunger_color": 0,  # Black plunger button
        "plunger_offset_ldu": [0.0, 0.0, 70.0],  # Y-up from LDraw (0, 0, -70)
        "lego_id": "45606",
        "color": 15,
        "qty_45678": 1,
        "kind": "sensor",
        "cable_exit_ldu": [0.0, 0.0, -48.0],
    },
    "wheel": {
        "ldraw_src": "39367p01.dat",
        "mpd_name": "39367p01",
        "lego_id": "39367",
        "color": 15,  # White spokes + integral Medium Azure tire (hardcoded 10322)
        "qty_45678": 2,
        "kind": "wheel",
        "radius_ldu": 70.0,
    },
    "caster": {
        "ldraw_src": "39370c01.dat",
        "mpd_name": "39370c01",
        "lego_id": "39370",
        "color": 322,  # Medium Azure housing + white 19mm ball
        "qty_45678": 1,
        "kind": "caster",
    },
    # Frames & panels (all in 45678)
    "frame_5x7": {
        "ldraw_src": "64179.dat",
        "mpd_name": "64179",
        "lego_id": "64179",
        "color": 71,  # Light Bluish Grey (also black in 45678; LBG reads crisply in 3D)
        "qty_45678": 2,
        "kind": "frame",
    },
    "frame_7x11": {
        "ldraw_src": "39794.dat",
        "mpd_name": "39794",
        "lego_id": "39794",
        "color": 26,  # Magenta (signature SPIKE Prime 45678 color)
        "qty_45678": 2,
        "kind": "frame",
    },
    "frame_11x15": {
        "ldraw_src": "39790.dat",
        "mpd_name": "39790",
        "lego_id": "39790",
        "color": 71,  # Light Bluish Grey
        "qty_45678": 2,
        "kind": "frame",
    },
    "baseplate_11x19": {
        "ldraw_src": "39369.dat",
        "mpd_name": "39369",
        "lego_id": "39369",
        "color": 322,  # Medium Azure
        "qty_45678": 2,
        "kind": "part",
    },
    "biscuit_3x3": {
        "ldraw_src": "39793.dat",
        "mpd_name": "39793",
        "lego_id": "39793",
        "color": 26,  # Magenta
        "qty_45678": 6,
        "kind": "part",
    },
    # Straight Technic Beams (all in 45678)
    "beam_3": {"ldraw_src": "32523.dat", "mpd_name": "32523", "lego_id": "32523", "color": 14, "qty_45678": 6, "kind": "beam"},
    "beam_5": {"ldraw_src": "32316.dat", "mpd_name": "32316", "lego_id": "32316", "color": 26, "qty_45678": 4, "kind": "beam"},
    "beam_7": {"ldraw_src": "32524.dat", "mpd_name": "32524", "lego_id": "32524", "color": 1, "qty_45678": 6, "kind": "beam"},
    "beam_9": {"ldraw_src": "40490.dat", "mpd_name": "40490", "lego_id": "40490", "color": 14, "qty_45678": 4, "kind": "beam"},
    "beam_11": {"ldraw_src": "32525.dat", "mpd_name": "32525", "lego_id": "32525", "color": 322, "qty_45678": 4, "kind": "beam"},
    "beam_13": {"ldraw_src": "41239.dat", "mpd_name": "41239", "lego_id": "41239", "color": 26, "qty_45678": 4, "kind": "beam"},
    "beam_15": {"ldraw_src": "32278.dat", "mpd_name": "32278", "lego_id": "32278", "color": 14, "qty_45678": 6, "kind": "beam"},
    # Bent & T Beams (all in 45678)
    "beam_l_3x5": {"ldraw_src": "32526.dat", "mpd_name": "32526", "lego_id": "32526", "color": 322, "qty_45678": 6, "kind": "beam_bent"},
    "beam_l_2x4": {"ldraw_src": "32140.dat", "mpd_name": "32140", "lego_id": "32140", "color": 14, "qty_45678": 6, "kind": "beam_bent"},
    "beam_t_3x3": {"ldraw_src": "60484.dat", "mpd_name": "60484", "lego_id": "60484", "color": 71, "qty_45678": 4, "kind": "beam_bent"},
    # Connectors (all in 45678)
    "conn_perp_3x3": {"ldraw_src": "55615.dat", "mpd_name": "55615", "lego_id": "55615", "color": 72, "qty_45678": 4, "kind": "part"},
    "conn_1x3_4pin": {"ldraw_src": "48989.dat", "mpd_name": "48989", "lego_id": "48989", "color": 71, "qty_45678": 6, "kind": "part"},
    "conn_axle_pin_1x2": {"ldraw_src": "6536.dat", "mpd_name": "6536", "lego_id": "6536", "color": 4, "qty_45678": 8, "kind": "part"},
    # Pins (all in 45678)
    "pin_black": {"ldraw_src": "2780.dat", "mpd_name": "2780", "lego_id": "2780", "color": 0, "qty_45678": 72, "kind": "pin", "conn_len": 40.0},
    "pin_grey": {"ldraw_src": "3673.dat", "mpd_name": "3673", "lego_id": "3673", "color": 71, "qty_45678": 16, "kind": "pin", "conn_len": 40.0},
    "pin_blue_3l": {"ldraw_src": "6558.dat", "mpd_name": "6558", "lego_id": "6558", "color": 1, "qty_45678": 16, "kind": "pin", "conn_len": 60.0},
    "axle_pin_blue": {"ldraw_src": "43093.dat", "mpd_name": "43093", "lego_id": "43093", "color": 1, "qty_45678": 16, "kind": "axle_pin", "conn_len": 40.0},
    # Axles & Bushes (all in 45678)
    "axle_2": {"ldraw_src": "32062.dat", "mpd_name": "32062", "lego_id": "32062", "color": 4, "qty_45678": 12, "kind": "axle", "conn_len": 40.0},
    "axle_3": {"ldraw_src": "4519.dat", "mpd_name": "4519", "lego_id": "4519", "color": 71, "qty_45678": 10, "kind": "axle", "conn_len": 60.0},
    "axle_4": {"ldraw_src": "3705.dat", "mpd_name": "3705", "lego_id": "3705", "color": 0, "qty_45678": 8, "kind": "axle", "conn_len": 80.0},
    "axle_5": {"ldraw_src": "32073.dat", "mpd_name": "32073", "lego_id": "32073", "color": 71, "qty_45678": 6, "kind": "axle", "conn_len": 100.0},
    "axle_6": {"ldraw_src": "3706.dat", "mpd_name": "3706", "lego_id": "3706", "color": 0, "qty_45678": 4, "kind": "axle", "conn_len": 120.0},
    "axle_7": {"ldraw_src": "44294.dat", "mpd_name": "44294", "lego_id": "44294", "color": 71, "qty_45678": 4, "kind": "axle", "conn_len": 140.0},
    "bush": {"ldraw_src": "3713.dat", "mpd_name": "3713", "lego_id": "3713", "color": 71, "qty_45678": 12, "kind": "bush"},
    "half_bush": {"ldraw_src": "32123a.dat", "mpd_name": "32123a", "lego_id": "32123", "color": 14, "qty_45678": 10, "kind": "bush"},
    # Gears & Gear Rack (all in 45678!)
    "gear_12": {"ldraw_src": "32270.dat", "mpd_name": "32270", "lego_id": "32270", "color": 0, "qty_45678": 3, "kind": "gear", "teeth": 12, "pitch_radius_ldu": 15.0},
    "gear_20": {"ldraw_src": "32269.dat", "mpd_name": "32269", "lego_id": "32269", "color": 19, "qty_45678": 2, "kind": "gear", "teeth": 20, "pitch_radius_ldu": 25.0},
    "gear_36": {"ldraw_src": "32498.dat", "mpd_name": "32498", "lego_id": "32498", "color": 0, "qty_45678": 2, "kind": "gear", "teeth": 36, "pitch_radius_ldu": 45.0},
    "gear_rack_13": {"ldraw_src": "64781.dat", "mpd_name": "64781", "lego_id": "64781", "color": 0, "qty_45678": 2, "kind": "gear_rack", "tooth_pitch_ldu": 8.0},
    # Bricks & Tiles (all in 45678!)
    "brick_2x4_technic": {"ldraw_src": "39789.dat", "mpd_name": "39789", "lego_id": "39789", "color": 4, "qty_45678": 10, "kind": "brick"},
    "tile_1x3": {"ldraw_src": "63864.dat", "mpd_name": "63864", "lego_id": "63864", "color": 15, "qty_45678": 12, "kind": "tile"},
    "tile_1x2": {"ldraw_src": "3069b.dat", "mpd_name": "3069b", "lego_id": "3069", "color": 0, "qty_45678": 8, "kind": "tile"},
}


class LDrawArchive:
    def __init__(self, zip_path: Path):
        self.zf = zipfile.ZipFile(zip_path)
        self.idx = {n.lower(): n for n in self.zf.namelist()}

    def resolve(self, ref: str) -> Optional[Tuple[str, str]]:
        """Return (canonical_ref, text) for an LDraw file reference."""
        low = ref.replace("\\", "/").strip().lower()
        for cand in (f"ldraw/parts/{low}", f"ldraw/p/{low}", f"ldraw/{low}"):
            if cand in self.idx:
                txt = self.zf.read(self.idx[cand]).decode("utf-8", errors="replace")
                return low, txt
        return None

    def pack_mpd(self, root_ref: str) -> str:
        """Recursively collect root_ref and every dependency into a single self-contained MPD."""
        ordered: List[Tuple[str, str]] = []
        visited: Set[str] = set()

        def visit(ref: str):
            res = self.resolve(ref)
            if not res:
                return
            canon, txt = res
            if canon in visited:
                return
            visited.add(canon)
            # Rewrite backslash subfile refs to canonical lowercase forward-slash so MPD lookup is exact
            out_lines = []
            deps = []
            for raw in txt.splitlines():
                s = raw.strip()
                if s.startswith("1 "):
                    toks = s.split()
                    if len(toks) >= 15:
                        sub = " ".join(toks[14:]).replace("\\", "/").lower()
                        deps.append(sub)
                        out_lines.append(" ".join(toks[:14]) + " " + sub)
                        continue
                out_lines.append(raw.rstrip("\r\n"))
            ordered.append((canon, "\n".join(out_lines)))
            for d in deps:
                visit(d)

        visit(root_ref)
        chunks = []
        for canon, body in ordered:
            chunks.append(f"0 FILE {canon}\n{body}\n0 NOFILE")
        return "\n".join(chunks) + "\n"


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def tpt(M, p):
    x, y, z = p
    return (
        M[0][0] * x + M[0][1] * y + M[0][2] * z + M[0][3],
        M[1][0] * x + M[1][1] * y + M[1][2] * z + M[1][3],
        M[2][0] * x + M[2][1] * y + M[2][2] * z + M[2][3],
    )


def tdir(M, d):
    x, y, z = d
    return (
        M[0][0] * x + M[0][1] * y + M[0][2] * z,
        M[1][0] * x + M[1][1] * y + M[1][2] * z,
        M[2][0] * x + M[2][1] * y + M[2][2] * z,
    )


I4 = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def extract_geometry(arc: LDrawArchive, root_ref: str) -> dict:
    """Extract exact Y-up LDU bbox and merged hole centers/axes from official LDraw .dat."""
    verts: List[Tuple[float, float, float]] = []
    raw_holes: List[Tuple[str, Tuple[float, float, float], Tuple[float, float, float]]] = []
    ports: List[Tuple[float, float, float]] = []

    def walk(ref: str, M):
        res = arc.resolve(ref)
        if not res:
            return
        _, txt = res
        for raw in txt.splitlines():
            t = raw.strip().split()
            if not t:
                continue
            c = t[0]
            if c in ("3", "4"):
                n = 9 if c == "3" else 12
                v = list(map(float, t[2 : 2 + n]))
                for i in range(0, n, 3):
                    x, y, z = tpt(M, (v[i], v[i + 1], v[i + 2]))
                    verts.append((x, -y, -z))
            elif c == "1" and len(t) >= 15:
                v = list(map(float, t[2:14]))
                sub = " ".join(t[14:]).replace("\\", "/").lower()
                x, y, z, a, b, cc, d, e, f, g, h, ii = v
                nM = mat_mul(M, [[a, b, cc, x], [d, e, f, y], [g, h, ii, z], [0, 0, 0, 1]])
                if sub in ("peghole.dat", "connhole.dat", "connhol2.dat", "connhol3.dat"):
                    ax = tdir(nM, (0, 1, 0))
                    ln = math.sqrt(sum(k * k for k in ax)) or 1.0
                    axn = tuple(round(abs(k / ln), 3) for k in ax)
                    # Snap tiny float jitter
                    axn = tuple(1.0 if k > 0.99 else (0.0 if k < 0.01 else k) for k in axn)
                    pos = (round(nM[0][3], 2), round(-nM[1][3], 2), round(-nM[2][3], 2))
                    raw_holes.append(("pin", pos, axn))
                elif sub.startswith("axlehol"):
                    ax = tdir(nM, (0, 1, 0))
                    ln = math.sqrt(sum(k * k for k in ax)) or 1.0
                    axn = tuple(round(abs(k / ln), 3) for k in ax)
                    axn = tuple(1.0 if k > 0.99 else (0.0 if k < 0.01 else k) for k in axn)
                    # Record both ends of the axle hole primitive so grouping computes exact center & depth
                    p0 = tpt(nM, (0, 0.0, 0))
                    p1 = tpt(nM, (0, 1.0, 0))
                    raw_holes.append(("axle", (round(p0[0], 2), round(-p0[1], 2), round(-p0[2], 2)), axn))
                    raw_holes.append(("axle", (round(p1[0], 2), round(-p1[1], 2), round(-p1[2], 2)), axn))
                if sub in ("u9320.dat", "23807.dat"):
                    ports.append((round(nM[0][3], 2), round(-nM[1][3], 2), round(-nM[2][3], 2)))
                walk(sub, nM)

    walk(root_ref, I4)
    xs = [p[0] for p in verts]
    ys = [p[1] for p in verts]
    zs = [p[2] for p in verts]
    bbox = [round(min(xs), 2), round(min(ys), 2), round(min(zs), 2),
            round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)]

    # Group coaxial hole faces (e.g. front face y=-10 and back face y=+10 of a 1-stud beam)
    # into clean hole intervals: {pos: center, axis: [ax,ay,az], kind, span: [t_min, t_max]}.
    grouped: Dict[Tuple[str, Tuple[float, float, float], Tuple[float, float]], List[float]] = {}
    for kind, pos, ax in raw_holes:
        if ax == (1.0, 0.0, 0.0):
            key = (kind, ax, (round(pos[1], 1), round(pos[2], 1)))
            grouped.setdefault(key, []).append(pos[0])
        elif ax == (0.0, 1.0, 0.0):
            key = (kind, ax, (round(pos[0], 1), round(pos[2], 1)))
            grouped.setdefault(key, []).append(pos[1])
        elif ax == (0.0, 0.0, 1.0):
            key = (kind, ax, (round(pos[0], 1), round(pos[1], 1)))
            grouped.setdefault(key, []).append(pos[2])

    holes = []
    for (kind, ax, perp), ts in sorted(grouped.items()):
        ts_sorted = sorted(set(round(v, 1) for v in ts))
        # Split into contiguous hole segments (gap > 22 LDU = separate coaxial holes across an open frame!)
        segs: List[List[float]] = []
        for t in ts_sorted:
            if not segs or t - segs[-1][-1] > 22.0:
                segs.append([t])
            else:
                segs[-1].append(t)
        for seg in segs:
            t0, t1 = min(seg), max(seg)
            if t1 - t0 < 5.0:
                # Single-face marker: expand to standard 10 LDU depth inward toward bbox center
                lo, hi = (bbox[0], bbox[3]) if ax == (1.0, 0.0, 0.0) else ((bbox[1], bbox[4]) if ax == (0.0, 1.0, 0.0) else (bbox[2], bbox[5]))
                mid_b = 0.5 * (lo + hi)
                if t0 <= mid_b:
                    t1 = min(hi, t0 + 20.0)
                else:
                    t0 = max(lo, t0 - 20.0)
            tc = round(0.5 * (t0 + t1), 2)
            depth = round(t1 - t0, 2)
            if ax == (1.0, 0.0, 0.0):
                p = [tc, perp[0], perp[1]]
            elif ax == (0.0, 1.0, 0.0):
                p = [perp[0], tc, perp[1]]
            else:
                p = [perp[0], perp[1], tc]
            holes.append({"kind": kind, "pos": p, "axis": list(ax), "depth": depth})

    return {"bbox": bbox, "holes": holes, "ports": sorted(ports)}


def collision_boxes_for(part_key: str, bbox: List[float]) -> List[List[float]]:
    """Return exact non-overlapping collision AABBs [x0,y0,z0,x1,y1,z1] in Y-up LDU.
    Open frames and bent beams are decomposed into their solid perimeter bars so
    parts legitimately fitting inside open windows or L-concavities never false-positive.
    A tiny 1.0 LDU (0.4 mm) plastic clearance margin is applied on outer faces matching LEGO tolerance.
    """
    if part_key == "frame_5x7":
        # 5x7 open frame: X=[-50,50], Y=[-10,10], Z=[-70,70], open center X=[-30,30], Z=[-50,50]
        return [
            [-49.5, -9.5, -69.5, -30.5, 9.5, 69.5],
            [30.5, -9.5, -69.5, 49.5, 9.5, 69.5],
            [-30.5, -9.5, -69.5, 30.5, 9.5, -50.5],
            [-30.5, -9.5, 50.5, 30.5, 9.5, 69.5],
        ]
    if part_key == "frame_7x11":
        # 7x11 open frame: X=[-70,70], Y=[-10,10], Z=[-110,110], open center X=[-50,50], Z=[-90,90]
        return [
            [-69.5, -9.5, -109.5, -50.5, 9.5, 109.5],
            [50.5, -9.5, -109.5, 69.5, 9.5, 109.5],
            [-50.5, -9.5, -109.5, 50.5, 9.5, -90.5],
            [-50.5, -9.5, 90.5, 50.5, 9.5, 109.5],
        ]
    if part_key == "frame_11x15":
        # 11x15 open frame: X=[-110,110], Y=[-10,10], Z=[-150,150], open center X=[-90,90], Z=[-130,130]
        return [
            [-109.5, -9.5, -149.5, -90.5, 9.5, 149.5],
            [90.5, -9.5, -149.5, 109.5, 9.5, 149.5],
            [-90.5, -9.5, -149.5, 90.5, 9.5, -130.5],
            [-90.5, -9.5, 130.5, 90.5, 9.5, 149.5],
        ]
    if part_key == "beam_l_3x5":
        # 32526 Y-up: X=[-9,49], Y=[-10,10], Z=[-89,9] (long leg along Z=[-89,9] at X=0; short leg along X=[0,49] at Z=-80)
        return [
            [-8.5, -9.5, -88.5, 8.5, 9.5, 8.5],
            [8.5, -9.5, -88.5, 48.5, 9.5, -71.5],
        ]
    if part_key == "beam_l_2x4":
        # 32140 Y-up: X=[-9,29], Y=[-10,10], Z=[-69,9]
        return [
            [-8.5, -9.5, -68.5, 8.5, 9.5, 8.5],
            [8.5, -9.5, -68.5, 28.5, 9.5, -51.5],
        ]
    if part_key == "beam_t_3x3":
        # 60484 Y-up: X=[-29,29], Y=[-10,10], Z=[-49,9]
        return [
            [-8.5, -9.5, -48.5, 8.5, 9.5, 8.5],
            [-28.5, -9.5, -48.5, 28.5, 9.5, -31.5],
        ]
    if part_key == "caster":
        # 39370c01 Y-up: H-frame legs at Z=±40 (X=[-10,10], Y=[-29,29]), cross-bridge + ball cup + ball (Y=[-70,10])
        return [
            [-10.0, -28.5, -48.5, 10.0, 28.5, -31.5],
            [-10.0, -28.5, 31.5, 10.0, 28.5, 48.5],
            [-27.5, -57.5, -31.5, 27.5, 10.0, 31.5],
            [-23.5, -69.5, -23.5, 23.5, -22.5, 23.5],
        ]
    if part_key == "medium_motor":
        # Body u9364c01: X=[-30,30], Y=[-30,35.5], Z=[-150,29] + rotor disc Y=[35.5,50], X/Z=[-29,29]
        return [
            [-29.5, -29.5, -149.5, 29.5, 35.0, 28.5],
            [-28.5, 35.0, -28.5, 28.5, 49.5, 28.5],
        ]
    if part_key == "large_motor":
        return [
            [-49.5, -29.5, -149.5, 49.5, 35.0, 29.5],
            [-28.5, 35.0, -28.5, 28.5, 49.5, 28.5],
        ]
    if part_key == "force_sensor":
        # Body + narrower plunger protruding to Z=+70
        return [
            [-29.5, -28.5, -49.5, 29.5, 29.5, 48.5],
            [-17.5, -8.5, 48.5, 17.5, 8.5, 69.5],
        ]
    if part_key == "gear_rack_13":
        # Solid spine Y=[-10, 2.5], plus endcaps X=[-130,-88] and [88,130] Y=[-10,10].
        # Teeth occupy Y=[2.5,10] in X=[-88,88] and mesh with pinion gear.
        return [
            [-129.5, -9.5, -9.5, -88.5, 9.5, 9.5],
            [88.5, -9.5, -9.5, 129.5, 9.5, 9.5],
            [-88.5, -9.5, -9.5, 88.5, 2.5, 9.5],
        ]
    if part_key == "wheel":
        # Cylindrical tire approximated conservatively for solid check (slightly inset on corners)
        return [[-69.0, -69.0, -17.0, 69.0, 69.0, 17.0]]
    # Default: tight inset of 0.5 LDU (0.2 mm) to represent LEGO clearance
    x0, y0, z0, x1, y1, z1 = bbox
    eps = 0.5
    return [[round(x0 + eps, 2), round(y0 + eps, 2), round(z0 + eps, 2),
             round(x1 - eps, 2), round(y1 - eps, 2), round(z1 - eps, 2)]]


def main():
    assert LDRAW_ZIP.exists(), f"Missing {LDRAW_ZIP}"
    OUT_PARTS.mkdir(parents=True, exist_ok=True)
    OUT_SPECS.parent.mkdir(parents=True, exist_ok=True)

    arc = LDrawArchive(LDRAW_ZIP)

    # Copy official LDConfig.ldr
    ldcfg = arc.zf.read(arc.idx["ldraw/ldconfig.ldr"])
    (OUT_LDRAW / "LDConfig.ldr").write_bytes(ldcfg)

    specs: Dict[str, dict] = {}
    total_bytes = 0
    for key, cfg in PART_CATALOG.items():
        # Pack main MPD (or split body + moving subpart)
        body_src = cfg.get("body_src", cfg["ldraw_src"])
        mpd_text = arc.pack_mpd(body_src)
        out_path = OUT_PARTS / f"{cfg['mpd_name']}.mpd"
        out_path.write_text(mpd_text, encoding="utf-8")
        total_bytes += len(mpd_text.encode("utf-8"))

        if "rotor_src" in cfg:
            rmpd = arc.pack_mpd(cfg["rotor_src"])
            (OUT_PARTS / f"{cfg['rotor_mpd']}.mpd").write_text(rmpd, encoding="utf-8")
            total_bytes += len(rmpd.encode("utf-8"))
        if "plunger_src" in cfg:
            pmpd = arc.pack_mpd(cfg["plunger_src"])
            (OUT_PARTS / f"{cfg['plunger_mpd']}.mpd").write_text(pmpd, encoding="utf-8")
            total_bytes += len(pmpd.encode("utf-8"))

        geom = extract_geometry(arc, cfg["ldraw_src"])

        # Supplement central axle holes for parts where LDraw builds the axle slot from custom geometry
        # rather than axlehol*.dat primitives (e.g. 54696 rotor, 39367 wheel, 32270 12T gear, 39789 brick)
        holes = list(geom["holes"])
        if key in ("medium_motor", "large_motor"):
            holes.append({"kind": "axle", "pos": [0.0, 10.0, 0.0], "axis": [0.0, 1.0, 0.0], "depth": 80.0, "is_rotor": True})
        elif key == "wheel":
            holes.append({"kind": "axle", "pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 1.0], "depth": 35.0})
        elif key == "gear_12":
            holes.append({"kind": "axle", "pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 1.0], "depth": 20.0})
        elif key == "bush":
            holes = [{"kind": "axle", "pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 1.0], "depth": 20.0}]
        elif key == "half_bush":
            holes = [{"kind": "axle", "pos": [0.0, 0.0, 0.0], "axis": [0.0, 0.0, 1.0], "depth": 10.0}]
        elif key == "brick_2x4_technic":
            # 39789: 3 vertical axle holes along X = -20, 0, +20 at Z = 0, Y in [-24, 0]
            for hx in (-20.0, 0.0, 20.0):
                holes.append({"kind": "axle", "pos": [hx, -12.0, 0.0], "axis": [0.0, 1.0, 0.0], "depth": 24.0})

        entry = {
            **cfg,
            "bbox": geom["bbox"],
            "boxes": collision_boxes_for(key, geom["bbox"]),
            "holes": holes,
        }
        if key == "hub":
            # Exact physical LEGO SPIKE Prime 45601 Hub port sockets in Y-up LDU:
            # Reading the Hub top upright (USB at -Z, Center Power Button at +Z):
            # Left (-X): A (USB end, z=-40), C (mid, z=0), E (Button end, z=+40)
            # Right (+X): B (USB end, z=-40), D (mid, z=0), F (Button end, z=+40)
            entry["hub_ports_ldu"] = {
                "A": [-69.0, 68.0, -40.0],
                "C": [-69.0, 68.0, 0.0],
                "E": [-69.0, 68.0, 40.0],
                "B": [69.0, 68.0, -40.0],
                "D": [69.0, 68.0, 0.0],
                "F": [69.0, 68.0, 40.0],
            }
            entry["led_matrix_ldu"] = {
                "y": 80.2,
                "cols_x": [-42.0, -21.0, 0.0, 21.0, 42.0],
                "rows_z": [-40.0, -20.0, 0.0, 20.0, 40.0],
                "size_xz": [15.5, 14.5],
            }
        specs[key] = entry

    OUT_SPECS.write_text(json.dumps(specs, indent=2), encoding="utf-8")
    print(f"Packed {len(PART_CATALOG)} LEGO 45678 parts -> {OUT_PARTS} ({total_bytes/1024/1024:.2f} MB total MPD)")
    print(f"Wrote exact geometry & hole specs -> {OUT_SPECS}")


if __name__ == "__main__":
    main()
