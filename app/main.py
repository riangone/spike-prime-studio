import hashlib
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.data.lessons import (
    CONCEPTS,
    DEFAULT_LESSON_ID,
    DEFAULT_PROGRAM_VERSION,
    LESSONS,
    LEVELS,
    PROGRAM_MODES,
    find_lesson,
    get_lesson_by_id,
    get_lesson_version,
    lesson_blocks,
    lesson_variables,
    normalize_mode,
    normalize_version,
    render_code,
)
from app.i18n import SUPPORTED_LANGS, get_ui, normalize_lang, pick_i18n
from app.scratch_export import build_sb3
from app.spike_export import build_llsp3_bytes

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="SPIKE Prime 3D Studio")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _asset_version() -> str:
    h = hashlib.sha1()
    for f in sorted((BASE_DIR / "static").rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()[:10]


templates.env.globals["asset_v"] = _asset_version()


def resolve_lang(request: Request, lang: str | None = None) -> str:
    if lang:
        return normalize_lang(lang)
    cookie_lang = request.cookies.get("spike_lang")
    return normalize_lang(cookie_lang)


def get_base_path(request: Request) -> str:
    prefix = request.headers.get("x-forwarded-prefix", "").strip()
    if not prefix or prefix == "/":
        return ""
    return "/" + prefix.strip("/")


def require_lesson(lesson_id: str) -> Dict[str, Any]:
    lesson = find_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail=f"Unknown lesson: {lesson_id}")
    return lesson


def localize_lesson(
    lesson: Dict[str, Any],
    lang: str,
    mode: str = "blockly",
    ver: str = DEFAULT_PROGRAM_VERSION,
) -> Dict[str, Any]:
    current_mode = normalize_mode(mode)
    current_ver = normalize_version(ver)
    steps: List[Dict[str, Any]] = []
    total_parts = 0
    for s in lesson["steps"]:
        localized_parts = []
        bom_parts = []
        for p in s["parts"]:
            qty = p.get("qty", 1)
            total_parts += qty
            lp = {
                **p,
                "name": pick_i18n(p["name"], lang),
            }
            localized_parts.append(lp)
            if qty > 0:
                bom_parts.append(lp)
        localized_wiring = [
            {
                "port": w["port"],
                "device": pick_i18n(w["device"], lang),
                "route": pick_i18n(w["route"], lang),
                "check": pick_i18n(w["check"], lang),
            }
            for w in s.get("wiring", [])
        ]
        steps.append(
            {
                "step": s["step"],
                "title": pick_i18n(s["title"], lang),
                "instruction": pick_i18n(s["instruction"], lang),
                "substeps": [pick_i18n(sub, lang) for sub in s.get("substeps", [])],
                "wiring": localized_wiring,
                "tip": pick_i18n(s["tip"], lang),
                "parts": localized_parts,
                "bom_parts": bom_parts,
            }
        )

    raw_lab = lesson.get("structure_lab") or {}
    structure_lab = {
        "why": pick_i18n(raw_lab.get("why", ""), lang),
        "troubleshoot": [pick_i18n(x, lang) for x in raw_lab.get("troubleshoot", [])],
        "mod_ideas": [pick_i18n(x, lang) for x in raw_lab.get("mod_ideas", [])],
    }

    v1_raw = get_lesson_version(lesson, "v1")
    v2_raw = get_lesson_version(lesson, "v2")
    active_v = get_lesson_version(lesson, current_ver)
    code = render_code(lesson, lang, current_ver)

    return {
        "id": lesson["id"],
        "title": pick_i18n(lesson["title"], lang),
        "summary": pick_i18n(lesson["summary"], lang),
        "difficulty": pick_i18n(lesson["difficulty"], lang),
        "duration": pick_i18n(lesson["duration"], lang),
        "stars": lesson.get("stars", 1),
        "concepts": [pick_i18n(CONCEPTS[c], lang) for c in lesson.get("concepts", [])],
        "challenges": [pick_i18n(c, lang) for c in lesson.get("challenges", [])],
        "structure_lab": structure_lab,
        "program_version": current_ver,
        "version_info": {
            "v1_label": pick_i18n(v1_raw.get("label", ""), lang),
            "v2_label": pick_i18n(v2_raw.get("label", ""), lang),
            "v1_problem": pick_i18n(v1_raw.get("problem", ""), lang),
            "v1_why": pick_i18n(v1_raw.get("why", ""), lang),
            "v2_fix": pick_i18n(v2_raw.get("fix_summary", ""), lang),
        },
        "blocks_xml": lesson_blocks(lesson, current_mode, current_ver),
        "blocks_vars": lesson_variables(lesson, current_mode, current_ver),
        "program_modes": [
            {"id": key, "label": pick_i18n(label, lang)} for key, label in PROGRAM_MODES.items()
        ],
        "program_mode": current_mode,
        "total_parts": total_parts,
        "ports": [
            {
                "port": pt["port"],
                "device": pick_i18n(pt["device"], lang),
                "note": pick_i18n(pt.get("note", ""), lang),
            }
            for pt in lesson["ports"]
        ],
        "cables": lesson.get("cables", []),
        "steps": steps,
        "code": code,
        "code_lines": list(enumerate(code.splitlines(), start=1)),
        "code_explanations": [
            {
                "lines": item["lines"],
                "title": pick_i18n(item["title"], lang),
                "desc": pick_i18n(item["desc"], lang),
            }
            for item in active_v.get("code_explanations", lesson["code_explanations"])
        ],
    }


def list_lessons_localized(lang: str) -> List[Dict[str, Any]]:
    """Lessons grouped by elementary stage, keeping the easiest-first order of LESSONS."""
    groups: List[Dict[str, Any]] = []
    for n, l in enumerate(LESSONS, start=1):
        if not groups or groups[-1]["key"] != l["level"]:
            groups.append({"key": l["level"], "title": pick_i18n(LEVELS[l["level"]], lang), "items": []})
        groups[-1]["items"].append(
            {
                "id": l["id"],
                "num": n,
                "title": pick_i18n(l["title"], lang),
                "difficulty": pick_i18n(l["difficulty"], lang),
                "duration": pick_i18n(l["duration"], lang),
                "stars": l.get("stars", 1),
                "steps_count": len(l["steps"]),
                "level": l["level"],
            }
        )
    return groups


@app.get("/manifest.webmanifest")
async def pwa_manifest(request: Request, lang: str | None = Query(default=None)):
    current_lang = resolve_lang(request, lang)
    ui = get_ui(current_lang)
    base = get_base_path(request)
    start_url = f"{base}/"
    return JSONResponse(
        {
            "id": start_url,
            "name": ui["app_title"],
            "short_name": "SPIKE 3D",
            "description": ui["app_subtitle"],
            "lang": current_lang,
            "start_url": start_url,
            "scope": start_url,
            "display": "standalone",
            "orientation": "any",
            "background_color": "#0f172a",
            "theme_color": "#fbbd23",
            "icons": [
                {
                    "src": f"{base}/static/icons/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": f"{base}/static/icons/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": f"{base}/static/icons/icon-maskable-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "maskable",
                },
                {
                    "src": f"{base}/static/icons/icon.svg",
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any",
                },
            ],
        },
        media_type="application/manifest+json",
    )


@app.get("/sw.js")
async def service_worker(request: Request):
    base = get_base_path(request)
    ver = templates.env.globals.get("asset_v", "v1")
    sw_code = f"""const CACHE_NAME = 'spike-studio-{ver}';
const BASE = {base!r};
const PRECACHE_URLS = [
  `${{BASE}}/`,
  `${{BASE}}/manifest.webmanifest`,
  `${{BASE}}/static/css/studio.css?v={ver}`,
  `${{BASE}}/static/js/app.js?v={ver}`,
  `${{BASE}}/static/js/progress.js?v={ver}`,
  `${{BASE}}/static/js/viewer3d.js?v={ver}`,
  `${{BASE}}/static/js/simulator.js?v={ver}`,
  `${{BASE}}/static/js/spike-device.js?v={ver}`,
  `${{BASE}}/static/js/blocks.js?v={ver}`,
  `${{BASE}}/static/icons/icon-192.png`,
  `${{BASE}}/static/icons/icon-512.png`,
  `${{BASE}}/static/icons/icon.svg`,
];

self.addEventListener('install', (event) => {{
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
}});

self.addEventListener('activate', (event) => {{
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k.startsWith('spike-studio-') && k !== CACHE_NAME).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
}});

self.addEventListener('fetch', (event) => {{
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // Cache-first for static assets (LDraw .mpd parts, JS, CSS, icons)
  if (url.pathname.startsWith(`${{BASE}}/static/`)) {{
    event.respondWith(
      caches.match(req).then((cached) => {{
        if (cached) return cached;
        return fetch(req).then((res) => {{
          if (res && res.status === 200) {{
            const copy = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, copy));
          }}
          return res;
        }});
      }})
    );
    return;
  }}

  // Network-first with cache fallback for HTML / API / partials
  event.respondWith(
    fetch(req)
      .then((res) => {{
        if (res && res.status === 200) {{
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy));
        }}
        return res;
      }})
      .catch(() => caches.match(req).then((cached) => cached || caches.match(`${{BASE}}/`)))
  );
}});
"""
    return Response(
        content=sw_code,
        media_type="application/javascript; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Service-Worker-Allowed": f"{base}/",
        },
    )


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    lesson: str = Query(default=DEFAULT_LESSON_ID),
    step: int = Query(default=1),
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    current_lang = resolve_lang(request, lang)
    current_mode = normalize_mode(mode)
    current_ver = normalize_version(ver)
    ui = get_ui(current_lang)
    raw_lesson = get_lesson_by_id(lesson)
    current_lesson = localize_lesson(raw_lesson, current_lang, current_mode, current_ver)
    total_steps = len(current_lesson["steps"])
    current_step = current_lesson["steps"][max(1, min(step, total_steps)) - 1]

    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "base": get_base_path(request),
            "ui": ui,
            "lang": current_lang,
            "supported_langs": SUPPORTED_LANGS,
            "lesson_groups": list_lessons_localized(current_lang),
            "lesson": current_lesson,
            "current_step": current_step,
            "total_steps": total_steps,
            "program_mode": current_mode,
            "program_version": current_ver,
        },
    )
    if lang:
        response.set_cookie("spike_lang", current_lang, max_age=60 * 60 * 24 * 365)
    return response


@app.get("/partials/lesson/{lesson_id}", response_class=HTMLResponse)
async def partial_lesson(
    request: Request,
    lesson_id: str,
    step: int = Query(default=1),
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    current_lang = resolve_lang(request, lang)
    current_mode = normalize_mode(mode)
    current_ver = normalize_version(ver)
    ui = get_ui(current_lang)
    current_lesson = localize_lesson(require_lesson(lesson_id), current_lang, current_mode, current_ver)
    total_steps = len(current_lesson["steps"])
    current_step = current_lesson["steps"][max(1, min(step, total_steps)) - 1]

    return templates.TemplateResponse(
        request=request,
        name="partials/lesson_panel.html",
        context={
            "base": get_base_path(request),
            "ui": ui,
            "lang": current_lang,
            "lesson": current_lesson,
            "current_step": current_step,
            "total_steps": total_steps,
            "program_mode": current_mode,
            "program_version": current_ver,
            "lesson_groups": list_lessons_localized(current_lang),
        },
    )


@app.get("/partials/lesson/{lesson_id}/step/{step_num}", response_class=HTMLResponse)
async def partial_step(
    request: Request,
    lesson_id: str,
    step_num: int,
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    current_lang = resolve_lang(request, lang)
    current_mode = normalize_mode(mode)
    current_ver = normalize_version(ver)
    ui = get_ui(current_lang)
    current_lesson = localize_lesson(require_lesson(lesson_id), current_lang, current_mode, current_ver)
    total_steps = len(current_lesson["steps"])
    safe_idx = max(1, min(step_num, total_steps)) - 1
    current_step = current_lesson["steps"][safe_idx]

    return templates.TemplateResponse(
        request=request,
        name="partials/step_detail.html",
        context={
            "base": get_base_path(request),
            "ui": ui,
            "lang": current_lang,
            "lesson": current_lesson,
            "current_step": current_step,
            "total_steps": total_steps,
            "program_mode": current_mode,
            "program_version": current_ver,
            "lesson_groups": list_lessons_localized(current_lang),
        },
    )


@app.get("/api/lesson/{lesson_id}/scene")
async def api_lesson_scene(lesson_id: str, lang: str = Query(default="zh")):
    current_lang = normalize_lang(lang)
    raw_lesson = require_lesson(lesson_id)
    current_lesson = localize_lesson(raw_lesson, current_lang)
    return JSONResponse(
        {
            "lesson_id": current_lesson["id"],
            "camera": raw_lesson.get("camera"),
            "cables": current_lesson["cables"],
            "joints": raw_lesson.get("joints", []),
            "gear_meshes": raw_lesson.get("gear_meshes", []),
            "crank_linkages": raw_lesson.get("crank_linkages", []),
            "kinematics": raw_lesson.get("kinematics", {"chassis": {"type": "static"}}),
            "floor_props": raw_lesson.get("floor_props", []),
            "ports": [
                {"port": pt["port"], "device": pick_i18n(pt["device"], current_lang)}
                for pt in raw_lesson.get("ports", [])
            ],
            "steps": [
                {
                    "step": s["step"],
                    "parts": s["parts"],
                }
                for s in current_lesson["steps"]
            ],
        }
    )


@app.get("/download/{lesson_id}.py")
async def download_py(
    request: Request,
    lesson_id: str,
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    lesson = require_lesson(lesson_id)
    current_ver = normalize_version(ver)
    ver_suffix = "_v1" if current_ver == "v1" else ""
    mode_suffix = "" if normalize_mode(mode) == "blockly" else "_scratch"
    filename = f"spike3_{lesson['id'].replace('-', '_')}{ver_suffix}{mode_suffix}.py"
    return Response(
        content=render_code(lesson, resolve_lang(request, lang), current_ver),
        media_type="text/x-python; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/download/{lesson_id}.llsp3")
async def download_llsp3(
    request: Request,
    lesson_id: str,
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    lesson = require_lesson(lesson_id)
    current_lang = resolve_lang(request, lang)
    current_ver = normalize_version(ver)
    title = pick_i18n(lesson["title"], current_lang)
    data = build_llsp3_bytes(title, render_code(lesson, current_lang, current_ver))
    ver_suffix = "_v1" if current_ver == "v1" else ""
    mode_suffix = "" if normalize_mode(mode) == "blockly" else "_scratch"
    filename = f"spike3_{lesson['id'].replace('-', '_')}{ver_suffix}{mode_suffix}.llsp3"
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/download/{lesson_id}.sb3")
async def download_sb3(
    request: Request,
    lesson_id: str,
    lang: str | None = Query(default=None),
    mode: str | None = Query(default=None),
    ver: str | None = Query(default=None),
):
    """Scratch 3 project mirroring the blocks (see app/scratch_export.py)."""
    lesson = require_lesson(lesson_id)
    current_lang = resolve_lang(request, lang)
    current_ver = normalize_version(ver)
    v_lesson = {**lesson, "blocks": lesson_blocks(lesson, "blockly", current_ver)}
    data = build_sb3(v_lesson, current_lang, var_defs={}, sprite_name="SPIKE Hub")
    ver_suffix = "_v1" if current_ver == "v1" else ""
    filename = f"spike3_{lesson['id'].replace('-', '_')}{ver_suffix}.sb3"
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
