import io
import json
import uuid
import zipfile
from datetime import datetime, timezone


def build_llsp3_bytes(project_name: str, python_code: str) -> bytes:
    """
    Build an official LEGO Education SPIKE 3 compatible .llsp3 Python project archive.
    """
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    project_id = str(uuid.uuid4())[:12]

    manifest = {
        "type": "python",
        "appType": "llsp3",
        "autoDelete": False,
        "created": now_iso,
        "id": project_id,
        "lastsaved": now_iso,
        "size": len(python_code.encode("utf-8")),
        "name": project_name,
        "slotIndex": 0,
        "workspaceX": 0,
        "workspaceY": 0,
        "zoomLevel": 1,
        "hardware": {
            "python": {
                "type": "flipper",
                "name": "SPIKE Prime Hub",
            }
        },
        "state": {
            "canvasDrawerOpen": False,
            "canvasDrawerTab": "knowledgeBaseTab",
        },
        "version": 3,
    }

    project_body = {
        "main": python_code,
    }

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("projectbody.json", json.dumps(project_body, ensure_ascii=False, indent=2))
    return buf.getvalue()
