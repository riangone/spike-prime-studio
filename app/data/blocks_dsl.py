"""Tiny DSL that emits Blockly XML for the SPIKE word-block programs shown in the Scratch tab.

Block types are defined in app/static/js/blocks.js; keep the type/field/input names in sync.
Arguments that are int/float become editable number shadows, str values are taken as nested block XML.
"""
from typing import Dict, Optional, Sequence, Union
from xml.sax.saxutils import escape

Value = Union[int, float, str]


def _num_shadow(v: Union[int, float]) -> str:
    return f'<shadow type="math_number"><field name="NUM">{v}</field></shadow>'


def _value(name: str, v: Value) -> str:
    if isinstance(v, (int, float)):
        inner = _num_shadow(v)
    else:
        inner = v
    return f'<value name="{name}">{inner}</value>'


def block(
    type_: str,
    fields: Optional[Dict[str, str]] = None,
    values: Optional[Dict[str, Value]] = None,
    statements: Optional[Dict[str, Sequence[str]]] = None,
) -> str:
    """One block without its <next>; chain() links statement blocks together."""
    parts = [f'<block type="{type_}">']
    for k, v in (fields or {}).items():
        parts.append(f'<field name="{k}">{escape(str(v))}</field>')
    for k, v in (values or {}).items():
        parts.append(_value(k, v))
    for k, body in (statements or {}).items():
        if body:
            parts.append(f'<statement name="{k}">{chain(*body)}</statement>')
    parts.append("</block>")
    return "".join(parts)


def chain(*blocks: str) -> str:
    """Nest each statement block inside the previous one's <next>."""
    out = ""
    for b in reversed(blocks):
        if out:
            assert b.endswith("</block>")
            b = b[: -len("</block>")] + f"<next>{out}</next></block>"
        out = b
    return out


def program(*body: str, variables: Sequence[str] = ()) -> str:
    start = block("spike_start")
    start = start[: -len("</block>")] + (f"<next>{chain(*body)}</next></block>" if body else "</block>")
    start = start.replace('<block type="spike_start">', '<block type="spike_start" x="20" y="20">', 1)
    vars_xml = "".join(f"<variable>{escape(v)}</variable>" for v in variables)
    return f'<xml xmlns="https://developers.google.com/blockly/xml"><variables>{vars_xml}</variables>{start}</xml>'


# ---------------------------------------------------------------- reporters / operators
def text(s: str) -> str:
    return f'<shadow type="text"><field name="TEXT">{escape(s)}</field></shadow>'


def var(name: str) -> str:
    return f'<block type="variables_get"><field name="VAR">{escape(name)}</field></block>'


def arith(a: Value, op: str, b: Value) -> str:
    ops = {"+": "ADD", "-": "MINUS", "*": "MULTIPLY", "/": "DIVIDE"}
    return block("math_arithmetic", {"OP": ops[op]}, {"A": a, "B": b})


def compare(a: Value, op: str, b: Value) -> str:
    ops = {"==": "EQ", "!=": "NEQ", "<": "LT", "<=": "LTE", ">": "GT", ">=": "GTE"}
    return block("logic_compare", {"OP": ops[op]}, {"A": a, "B": b})


def logic(a: str, op: str, b: str) -> str:
    return block("logic_operation", {"OP": op.upper()}, {"A": a, "B": b})


def not_(a: str) -> str:
    return block("logic_negate", values={"BOOL": a})


def abs_(a: Value) -> str:
    return block("spike_abs", values={"NUM": a})


# ---------------------------------------------------------------- statements
def set_var(name: str, v: Value) -> str:
    return block("variables_set", {"VAR": name}, {"VALUE": v})


def change_var(name: str, v: Value) -> str:
    return block("math_change", {"VAR": name}, {"DELTA": v})


def wait(secs: Value) -> str:
    return block("spike_wait", values={"SECS": secs})


def repeat(times: Value, *body: str) -> str:
    return block("spike_repeat", values={"TIMES": times}, statements={"DO": body})


def forever(*body: str) -> str:
    return block("spike_forever", statements={"DO": body})


def repeat_until(cond: str, *body: str) -> str:
    return block("spike_repeat_until", values={"COND": cond}, statements={"DO": body})


def wait_until(cond: str) -> str:
    return block("spike_wait_until", values={"COND": cond})


def if_(cond: str, *body: str) -> str:
    return block("spike_if", values={"COND": cond}, statements={"DO": body})


def if_else(cond: str, then: Sequence[str], else_: Sequence[str]) -> str:
    return block("spike_if_else", values={"COND": cond}, statements={"DO": then, "ELSE": else_})


def show_image(img: str) -> str:
    return block("spike_show_image", {"IMAGE": img})


def write(s: str) -> str:
    return block("spike_write", values={"TEXT": text(s)})


def beep(freq: Value, ms: Value) -> str:
    return block("spike_beep", values={"FREQ": freq, "MS": ms})


def motor_run_for(port: str, deg: Value, speed: Value) -> str:
    return block("spike_motor_run_for", {"PORT": port}, {"DEG": deg, "SPEED": speed})


def motor_go_to(port: str, pos: Value, speed: Value) -> str:
    return block("spike_motor_go_to", {"PORT": port}, {"POS": pos, "SPEED": speed})


def motor_start(port: str, speed: Value) -> str:
    return block("spike_motor_start", {"PORT": port}, {"SPEED": speed})


def motor_stop(port: str) -> str:
    return block("spike_motor_stop", {"PORT": port})


def motor_position(port: str) -> str:
    return block("spike_motor_position", {"PORT": port})


def clear() -> str:
    return block("spike_clear")


def print_(v: Value) -> str:
    return block("spike_print", values={"VALUE": v})


def move_pair(left: str, right: str) -> str:
    return block("spike_move_pair", {"LEFT": left, "RIGHT": right})


def move_for(deg: Value, steer: Value, speed: Value) -> str:
    return block("spike_move_for", values={"DEG": deg, "STEER": steer, "SPEED": speed})


def move_start(steer: Value, speed: Value) -> str:
    return block("spike_move_start", values={"STEER": steer, "SPEED": speed})


def move_tank(left: Value, right: Value) -> str:
    return block("spike_move_tank", values={"LEFT": left, "RIGHT": right})


def move_stop() -> str:
    return block("spike_move_stop")


def reset_yaw() -> str:
    return block("spike_reset_yaw")


# ---------------------------------------------------------------- sensors
def distance(port: str) -> str:
    return block("spike_distance", {"PORT": port})


def color_is(port: str, color: str) -> str:
    return block("spike_color_is", {"PORT": port, "COLOR": color})


def reflection(port: str) -> str:
    return block("spike_reflection", {"PORT": port})


def button_pressed(btn: str = "LEFT") -> str:
    return block("spike_button_pressed", {"BUTTON": btn})


def force_pressed(port: str) -> str:
    return block("spike_force_pressed", {"PORT": port})


def yaw() -> str:
    return block("spike_yaw")


# ---------------------------------------------------------------- Scratch-flavour helpers
# Used by app/data/lessons_scratch.py: the variable block set and the named dropdowns of the
# official SPIKE Scratch blocks (ports, images, colours, sounds). Keep the names distinct from the
# Blockly helpers above (set_var / port / distance / color_is take different arguments).
def set_var_named(name: str, value: Value) -> str:
    return block("spike_setvar", {"NAME": name}, {"VALUE": value})


def get_var(name: str) -> str:
    return block("spike_getvar", {"NAME": name})


def port(type_: str, letter: str, **values: Value) -> str:
    return block(type_, {"PORT": letter}, values)


def playsound(choice: str) -> str:
    return block("spike_playsound", {"SOUND": choice})

