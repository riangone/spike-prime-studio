"""Elementary 12-lesson curriculum registry (Grades 1 to 6), ordered from easiest to capstone.

Every lesson:
  1. Uses 100% official LEGO SPIKE Prime (45678) LDraw parts verified by app.cad.verifier (0 collisions,
     0 floating parts, exact pin/axle hole engagement, exact gear/rack pitch distances).
  2. Includes a Structure & Mod Lab (`structure_lab`: why it's built this way, troubleshooting, mod ideas).
  3. Provides dual runnable program versions (`versions.v1` starter with a real visible bug in 3D sim,
     `versions.v2` improved solution) in both Python and Blockly / SPIKE Scratch dialects.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from app.data.lessons_stage1 import LUCKY_SPINNER, MAGIC_HUB, METRONOME_ARM, STAGE1_LESSONS
from app.data.lessons_stage2 import DRIVING_BASE, GYRO_PRECISION, SQUARE_PATROL, STAGE2_LESSONS
from app.data.lessons_stage3 import COLOR_TRAFFIC, LINE_FOLLOWER, OBSTACLE_AVOIDER, STAGE3_LESSONS
from app.data.lessons_stage4 import GEAR_GATE, RACK_PUSHER, SMART_GRIPPER, STAGE4_LESSONS
from app.i18n import pick_i18n

LESSONS: List[Dict[str, Any]] = [
    *STAGE1_LESSONS,
    *STAGE2_LESSONS,
    *STAGE3_LESSONS,
    *STAGE4_LESSONS,
]

PROGRAM_MODES: Dict[str, Dict[str, str]] = {
    "blockly": {"zh": "Blockly 积木", "en": "Blockly", "ja": "Blockly ブロック"},
    "scratch": {"zh": "SPIKE Scratch", "en": "SPIKE Scratch", "ja": "SPIKE Scratch"},
}
DEFAULT_PROGRAM_MODE = "blockly"

PROGRAM_VERSIONS: Tuple_or_Dict = ("v1", "v2")
DEFAULT_PROGRAM_VERSION = "v2"

DEFAULT_LESSON_ID = MAGIC_HUB["id"]

LEVELS: Dict[str, Dict[str, str]] = {
    "stage1": {
        "zh": "第一阶段（1-2 年级）· 认识主控与第一个动作",
        "en": "Stage 1 (Grades 1–2) · Meet the Hub & First Motion",
        "ja": "ステージ1（小1〜2）· ハブと最初の動き",
    },
    "stage2": {
        "zh": "第二阶段（2-4 年级）· 差速小车与精准走位",
        "en": "Stage 2 (Grades 2–4) · Driving Base & Precision Moves",
        "ja": "ステージ2（小2〜4）· ドライブベースと精密走行",
    },
    "stage3": {
        "zh": "第三阶段（3-5 年级）· 传感器与聪明决策",
        "en": "Stage 3 (Grades 3–5) · Sensors & Smart Decisions",
        "ja": "ステージ3（小3〜5）· センサーと賢い判断",
    },
    "stage4": {
        "zh": "第四阶段（4-6 年级）· 奇妙机械与综合挑战",
        "en": "Stage 4 (Grades 4–6) · Mechanical Marvels & Capstone",
        "ja": "ステージ4（小4〜6）· メカ機構と総合チャレンジ",
    },
}

CONCEPTS: Dict[str, Dict[str, str]] = {
    "sequence": {"zh": "顺序执行", "en": "Sequence", "ja": "順次実行"},
    "light_sound": {"zh": "灯光与声音", "en": "Light & Sound", "ja": "光と音"},
    "event": {"zh": "按键互动", "en": "Button Events", "ja": "ボタン操作"},
    "motor": {"zh": "电机控制", "en": "Motors", "ja": "モーター"},
    "movement": {"zh": "差速移动", "en": "Driving", "ja": "差動走行"},
    "loop": {"zh": "重复循环", "en": "Loops", "ja": "くり返し"},
    "forever": {"zh": "持续巡航", "en": "Forever Loop", "ja": "ずっとくり返す"},
    "variable": {"zh": "变量管理", "en": "Variables", "ja": "変数"},
    "condition": {"zh": "条件判断", "en": "Conditions", "ja": "条件分岐"},
    "sensor": {"zh": "传感器感知", "en": "Sensors", "ja": "センサー"},
    "calibration": {"zh": "实验标定", "en": "Calibration", "ja": "キャリブレーション"},
    "feedback": {"zh": "比例反馈", "en": "Feedback Control", "ja": "フィードバック制御"},
    "gear": {"zh": "齿轮与齿条", "en": "Gears & Racks", "ja": "ギアとラック"},
    "state": {"zh": "状态顺序", "en": "State Sequence", "ja": "状態シーケンス"},
    "threshold": {"zh": "阈值与边缘", "en": "Thresholds", "ja": "しきい値"},
    "debug": {"zh": "问题排查改进", "en": "Debug & Improve", "ja": "デバッグと改良"},
}

_COMMENT_RE = re.compile(r"\{\{(\w+)\}\}")


def normalize_mode(mode: str | None) -> str:
    return mode if mode in PROGRAM_MODES else DEFAULT_PROGRAM_MODE


def normalize_version(ver: str | None) -> str:
    return ver if ver in ("v1", "v2") else DEFAULT_PROGRAM_VERSION


def get_lesson_version(lesson: Dict[str, Any], ver: str | None = None) -> Dict[str, Any]:
    vkey = normalize_version(ver)
    versions = lesson.get("versions", {})
    if vkey in versions:
        return versions[vkey]
    return {
        "id": "v2",
        "code": lesson["code"],
        "code_comments": lesson.get("code_comments", {}),
        "code_explanations": lesson.get("code_explanations", []),
        "blocks": lesson.get("blocks", ""),
        "blocks_scratch": lesson.get("blocks", ""),
        "blocks_scratch_vars": [],
    }


def lesson_blocks(
    lesson: Dict[str, Any],
    mode: str = DEFAULT_PROGRAM_MODE,
    ver: str = DEFAULT_PROGRAM_VERSION,
) -> str:
    """Return the Blockly XML for the requested dialect and version (v1 or v2)."""
    vdata = get_lesson_version(lesson, ver)
    if normalize_mode(mode) == "scratch" and vdata.get("blocks_scratch"):
        return vdata["blocks_scratch"]
    return vdata.get("blocks", lesson.get("blocks", ""))


def lesson_variables(
    lesson: Dict[str, Any],
    mode: str = DEFAULT_PROGRAM_MODE,
    ver: str = DEFAULT_PROGRAM_VERSION,
) -> List[str]:
    vdata = get_lesson_version(lesson, ver)
    if normalize_mode(mode) == "scratch":
        return list(vdata.get("blocks_scratch_vars", []))
    return re.findall(r"<variable>([^<]*)</variable>", vdata.get("blocks", ""))


def render_code(lesson: Dict[str, Any], lang: str, ver: str = DEFAULT_PROGRAM_VERSION) -> str:
    """Fill localized comment placeholders for the requested version (v1 or v2)."""
    vdata = get_lesson_version(lesson, ver)
    comments = vdata.get("code_comments", {})
    return _COMMENT_RE.sub(lambda m: pick_i18n(comments[m.group(1)], lang), vdata["code"])


def find_lesson(lesson_id: str) -> Optional[Dict[str, Any]]:
    return next((lesson for lesson in LESSONS if lesson["id"] == lesson_id), None)


def get_lesson_by_id(lesson_id: str) -> Dict[str, Any]:
    """Lenient lookup for the landing page: unknown ids fall back to the default lesson."""
    return find_lesson(lesson_id) or MAGIC_HUB
