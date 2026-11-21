"""Re-read the Blockly XML produced by blocks_dsl.py into plain dicts, so a lesson can offer its
program as a Scratch 3 project (.sb3) as well as a Blockly workspace.

Only the nodes the DSL emits are needed: <block>, <field>, <value>, <statement>, <next>, <shadow>
and the <variables> list. Unknown tags are ignored rather than raising, so a future DSL change
degrades to a partial Scratch project instead of breaking the lesson page.

Node shape: {"type": str, "x": float?, "y": float?,
             "fields": {name: text}, "values": {name: node}, "statements": {name: [node, ...]}}
A statement list is flattened: each node keeps only its own nested parts, the chain order is the list.
"""
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

NS = "{https://developers.google.com/blockly/xml}"


def _tag(el: ET.Element) -> str:
    return el.tag.replace(NS, "")


def _text(el: ET.Element) -> str:
    return (el.text or "").strip()


def parse_var_names(xml_text: str) -> List[str]:
    root = ET.fromstring(xml_text)
    return [_text(v) for v in root.findall(f"{NS}variables/{NS}variable")]


def parse_blocks(xml_text: str) -> List[Dict[str, Any]]:
    root = ET.fromstring(xml_text)
    return [_parse_block(el) for el in root if _tag(el) == "block"]


def _parse_block(el: ET.Element) -> Dict[str, Any]:
    node: Dict[str, Any] = {"type": el.get("type"), "fields": {}, "values": {}, "statements": {}}
    if el.get("x") is not None:
        node["x"] = float(el.get("x"))
    if el.get("y") is not None:
        node["y"] = float(el.get("y"))
    for child in el:
        tag = _tag(child)
        if tag == "field":
            node["fields"][child.get("name")] = _text(child)
        elif tag == "value":
            sub: Optional[Dict[str, Any]] = None
            for c in child:
                if _tag(c) in ("block", "shadow"):
                    sub = _parse_block(c)
                    break
            if sub is not None:
                node["values"][child.get("name")] = sub
        elif tag == "statement":
            node["statements"][child.get("name")] = _parse_chain(child)
        elif tag == "next":
            inner = _first_block(child)
            if inner is not None:
                node["next"] = _parse_block(inner)
    return node


def _first_block(container: ET.Element) -> Optional[ET.Element]:
    return next((c for c in container if _tag(c) == "block"), None)


def _parse_chain(container: ET.Element) -> List[Dict[str, Any]]:
    """Flatten the <next> chain inside a <statement> into a list (the `next` key is consumed)."""
    out: List[Dict[str, Any]] = []
    cur = _first_block(container)
    while cur is not None:
        node = _parse_block(cur)
        nxt = node.pop("next", None)
        out.append(node)
        cur = _next_element(nxt) if nxt else None
    return out


def _next_element(node: Dict[str, Any]) -> ET.Element:
    """Wrap a detached parsed node as a single <block> element (its own `<next>` preserved)."""
    el = ET.Element("block", {"type": node["type"]})
    for k, v in node["fields"].items():
        ET.SubElement(el, "field", {"name": k}).text = v
    for name, sub in node["values"].items():
        ET.SubElement(ET.SubElement(el, "value", {"name": name}), "block")
        _append_parsed(el.find(f"value[@name='{name}']/block"), sub)
    for name, blocks in node["statements"].items():
        st = ET.SubElement(el, "statement", {"name": name})
        _chain_into(st, blocks)
    if "next" in node:
        ET.SubElement(el, "next").append(_next_element(node["next"]))
    return el


def _append_parsed(target: Optional[ET.Element], node: Dict[str, Any]) -> None:
    if target is None:
        return
    target.set("type", node["type"])
    for k, v in node["fields"].items():
        ET.SubElement(target, "field", {"name": k}).text = v
    for name, sub in node["values"].items():
        _append_parsed(ET.SubElement(ET.SubElement(target, "value", {"name": name}), "block"), sub)
    for name, blocks in node["statements"].items():
        _chain_into(ET.SubElement(target, "statement", {"name": name}), blocks)


def _chain_into(container: ET.Element, blocks: List[Dict[str, Any]]) -> None:
    prev: Optional[ET.Element] = None
    for b in blocks:
        b_el = _next_element(b)
        (container if prev is None else ET.SubElement(prev, "next")).append(b_el)
        prev = b_el
