/**
 * SPIKE Prime Studio — 3D assembly viewer.
 *
 * Every part is rendered from the official LDraw library (app/static/ldraw/parts/*.mpd), placed with the
 * exact pose computed by app/cad/assembly.py (1 stud = 20 LDU = 0.4 scene units, floor at y = 0, Y-up).
 * Motion is never hand-animated here: the simulator feeds motor angles and the viewer applies the lesson's
 * kinematic description (revolute / prismatic joints, crank linkages, differential-drive chassis).
 */
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LDrawLoader } from 'three/addons/loaders/LDrawLoader.js';

const LDU = 0.02; // scene units per LDU
const HIGHLIGHT = new THREE.Color(0xffaa00);
const DEFAULT_CAMERA = { pos: [6.5, 5.2, 7.0], target: [0, 1.0, 0] };
const BASE = () => window.SPIKE_BASE_PATH || '';

// ---------------------------------------------------------------------------------------------
// LDraw part library: each (mpd, colour) is parsed once, then cloned per instance.
// ---------------------------------------------------------------------------------------------
class PartLibrary {
  constructor() {
    this.loader = new LDrawLoader();
    this.loader.smoothNormals = true;
    this.templates = new Map();
    this.texts = new Map();
    this.ready = this.loader.preloadMaterials(`${BASE()}/static/ldraw/LDConfig.ldr`);
  }

  async text(mpd) {
    if (!this.texts.has(mpd)) {
      this.texts.set(mpd, fetch(`${BASE()}/static/ldraw/parts/${mpd}.mpd`).then((r) => {
        if (!r.ok) throw new Error(`LDraw part ${mpd}: HTTP ${r.status}`);
        return r.text();
      }).then((t) => t
        // LDrawLoader rewrites "s/x.dat" -> "parts/s/x.dat" and "48/x.dat" -> "p/48/x.dat" when resolving
        // sub-files, so the embedded FILE names must use the same prefixes.
        .replace(/^0 FILE s\//gm, '0 FILE parts/s/')
        .replace(/^0 FILE 48\//gm, '0 FILE p/48/')));
    }
    return this.texts.get(mpd);
  }

  /** Template group in native LDraw coordinates (Y-down). */
  async template(mpd, color) {
    const key = `${mpd}#${color}`;
    if (!this.templates.has(key)) {
      this.templates.set(key, (async () => {
        await this.ready;
        const body = await this.text(mpd);
        const root = body.match(/^0 FILE (.+)$/m)[1].trim();
        // Wrap the packed part in a one-line model so colour 16 (main colour) resolves to `color`.
        const wrapper = `0 FILE __main.ldr\n1 ${color} 0 0 0 1 0 0 0 1 0 0 0 1 ${root}\n0 NOFILE\n${body}`;
        const group = await new Promise((res, rej) => this.loader.parse(wrapper, res, rej));
        group.traverse((o) => {
          if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; }
        });
        return group;
      })());
    }
    return this.templates.get(key);
  }

  /** Y-up instance: LDraw (x,y,z) -> (x,-y,-z), scaled to scene units. */
  async instance(mpd, color) {
    const tpl = await this.template(mpd, color);
    const holder = new THREE.Group();
    holder.rotation.x = Math.PI;
    holder.scale.setScalar(LDU);
    holder.add(tpl.clone());
    return holder;
  }
}

const library = new PartLibrary();

// Highlight swaps each mesh to a shared emissive twin of its material (instances share materials).
const highlightTwins = new WeakMap();
let highlightStrength = 0.3;
function twinOf(mat) {
  if (!mat || !mat.emissive) return mat;
  let t = highlightTwins.get(mat);
  if (!t) {
    t = mat.clone();
    t.emissive = HIGHLIGHT.clone();
    t.userData = { ...mat.userData, isHighlightTwin: true };
    highlightTwins.set(mat, t);
  }
  t.emissiveIntensity = highlightStrength;
  return t;
}
function setHighlight(root, on) {
  root.traverse((o) => {
    if (!o.isMesh || o.userData.noHighlight) return;
    if (on) {
      if (!o.userData.baseMaterial) o.userData.baseMaterial = o.material;
      const base = o.userData.baseMaterial;
      o.material = Array.isArray(base) ? base.map(twinOf) : twinOf(base);
    } else if (o.userData.baseMaterial) {
      o.material = o.userData.baseMaterial;
    }
  });
}

function disposeOwned(root) {
  // Template geometry/materials are shared through the library cache: only dispose objects we created.
  root.traverse((o) => {
    if (!o.userData.owned) return;
    o.geometry?.dispose();
    const mats = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
    mats.forEach((m) => { m.map?.dispose(); m.dispose(); });
  });
}

function createFloatingLabel(text, bgColor = '#f59e0b', textColor = '#0f172a') {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 96;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = bgColor;
  ctx.beginPath();
  ctx.roundRect(8, 8, 240, 80, 22);
  ctx.fill();
  ctx.fillStyle = textColor;
  ctx.font = 'bold 44px system-ui, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 128, 50);
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false }));
  sprite.scale.set(0.9, 0.34, 1);
  sprite.renderOrder = 10;
  sprite.userData.owned = true;
  return sprite;
}

// ---------------------------------------------------------------------------------------------
// Legacy fallback geometry (only used for un-rewritten lessons that lack `part.ldraw`).
// Once lessons are redesigned on app/cad/assembly.py, every part carries official LDraw data.
// ---------------------------------------------------------------------------------------------
function createLegacyFallbackPart(part) {
  const group = new THREE.Group();
  const color = new THREE.Color(part.color_hex || '#94a3b8');
  const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.08 });
  const addMesh = (geo, m = mat, pos = [0, 0, 0], rot = [0, 0, 0]) => {
    const mesh = new THREE.Mesh(geo, m);
    mesh.position.set(...pos);
    mesh.rotation.set(...rot);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.owned = true;
    group.add(mesh);
    return mesh;
  };
  const t = part.type;
  if (t === 'hub') {
    addMesh(new THREE.BoxGeometry(2.24, 0.94, 3.2), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 }));
    addMesh(new THREE.BoxGeometry(2.26, 0.32, 3.22), new THREE.MeshStandardMaterial({ color: 0xfacc15, roughness: 0.4 }), [0, -0.32, 0]);
    const leds = [];
    const geo = new THREE.PlaneGeometry(0.22, 0.22);
    for (let r = 0; r < 5; r++) {
      for (let c = 0; c < 5; c++) {
        const lm = new THREE.MeshStandardMaterial({ color: 0x111827, emissive: 0x000000, roughness: 0.4 });
        const led = new THREE.Mesh(geo, lm);
        led.rotation.x = -Math.PI / 2;
        led.position.set((c - 2) * 0.32, 0.48, (r - 2) * 0.32);
        led.userData.owned = true;
        led.userData.noHighlight = true;
        group.add(led);
        leds.push(led);
      }
    }
    group.userData.leds = leds;
  } else if (t === 'wheel') {
    const tire = new THREE.MeshStandardMaterial({ color: 0x36aebf, roughness: 0.7 });
    const rim = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 });
    addMesh(new THREE.CylinderGeometry(0.92, 0.92, 0.48, 28), tire, [0, 0, 0], [0, 0, Math.PI / 2]);
    addMesh(new THREE.CylinderGeometry(0.55, 0.55, 0.50, 20), rim, [0, 0, 0], [0, 0, Math.PI / 2]);
  } else if (t === 'caster') {
    addMesh(new THREE.BoxGeometry(0.6, 0.55, 0.8), mat, [0, 0.1, 0]);
    addMesh(new THREE.SphereGeometry(0.32, 16, 16), new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.6, roughness: 0.2 }), [0, -0.22, 0]);
  } else if (t === 'medium_motor' || t === 'large_motor') {
    const body = new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 });
    const accent = new THREE.MeshStandardMaterial({ color: 0x36aebf, roughness: 0.45 });
    addMesh(new THREE.BoxGeometry(0.96, 0.96, 1.92), body);
    addMesh(new THREE.CylinderGeometry(0.38, 0.38, 0.14, 20), accent, [-0.5, 0, 0.28], [0, 0, Math.PI / 2]);
  } else if (t === 'distance_sensor') {
    addMesh(new THREE.BoxGeometry(1.68, 0.84, 0.72), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 }));
    const eye = new THREE.MeshStandardMaterial({ color: 0x0f172a, roughness: 0.2 });
    addMesh(new THREE.CylinderGeometry(0.24, 0.24, 0.12, 16), eye, [-0.42, 0, 0.38], [Math.PI / 2, 0, 0]);
    addMesh(new THREE.CylinderGeometry(0.24, 0.24, 0.12, 16), eye, [0.42, 0, 0.38], [Math.PI / 2, 0, 0]);
  } else if (t === 'color_sensor') {
    addMesh(new THREE.BoxGeometry(1.04, 0.84, 0.8), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 }));
    addMesh(new THREE.CylinderGeometry(0.22, 0.22, 0.1, 16), new THREE.MeshStandardMaterial({ color: 0x0f172a }), [0, 0, 0.42], [Math.PI / 2, 0, 0]);
  } else if (t === 'force_sensor') {
    addMesh(new THREE.BoxGeometry(1.04, 0.72, 0.8), new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.35 }));
    addMesh(new THREE.CylinderGeometry(0.22, 0.22, 0.25, 16), new THREE.MeshStandardMaterial({ color: 0x1e293b }), [0, 0, 0.48], [Math.PI / 2, 0, 0]);
  } else if (t === 'frame_5x7') {
    addMesh(new THREE.BoxGeometry(2.0, 0.34, 2.8), mat);
  } else if (t === 'beam_15') {
    addMesh(new THREE.BoxGeometry(6.0, 0.34, 0.34), mat);
  } else if (t === 'beam_7') {
    addMesh(new THREE.BoxGeometry(2.8, 0.34, 0.34), mat);
  } else if (t === 'pin_black' || t === 'pin_blue_3l' || t === 'axle_3') {
    const len = t === 'pin_black' ? 0.65 : 1.1;
    addMesh(new THREE.CylinderGeometry(0.11, 0.11, len, 12), mat, [0, 0, 0], [0, 0, Math.PI / 2]);
  } else if (t === 'key_board') {
    addMesh(new THREE.BoxGeometry(4.4, 0.24, 1.8), mat);
  } else if (t === 'crane_hook') {
    addMesh(new THREE.CylinderGeometry(0.03, 0.03, 1.4, 8), new THREE.MeshStandardMaterial({ color: 0x334155 }), [0, 0.7, 0]);
    addMesh(new THREE.TorusGeometry(0.22, 0.06, 8, 16, Math.PI * 1.3), mat, [0, -0.1, 0]);
  } else {
    addMesh(new THREE.BoxGeometry(0.75, 0.75, 0.75), mat);
  }
  return group;
}

// ---------------------------------------------------------------------------------------------
// Part instances (body + optional rotor / plunger / LED overlay)
// ---------------------------------------------------------------------------------------------
async function createPart(part) {
  const group = new THREE.Group();
  group.userData.partId = part.id;
  group.userData.type = part.type;
  group.userData.isLegacy = !part.ldraw;

  if (!part.ldraw) {
    const fallback = createLegacyFallbackPart(part);
    group.add(fallback);
    if (fallback.userData.leds) group.userData.leds = fallback.userData.leds;
    return group;
  }

  group.add(await library.instance(part.ldraw, part.ldraw_color));

  if (part.rotor) {
    // The output disc turns about the motor's local +Y axis; positive degrees = clockwise seen from the face.
    const pivot = new THREE.Group();
    pivot.position.set(...part.rotor.offset);
    pivot.add(await library.instance(part.rotor.ldraw, part.rotor.ldraw_color));
    group.add(pivot);
    group.userData.rotor = pivot;
    group.userData.rotorAxis = new THREE.Vector3(...part.rotor.axis);
  }
  if (part.plunger) {
    const pivot = new THREE.Group();
    pivot.position.set(...part.plunger.offset);
    pivot.add(await library.instance(part.plunger.ldraw, part.plunger.ldraw_color));
    group.add(pivot);
    group.userData.plunger = pivot;
    group.userData.plungerRest = pivot.position.clone();
    group.userData.plungerDir = new THREE.Vector3(...part.plunger.axis).multiplyScalar(part.plunger.travel);
  }
  if (part.led_matrix) {
    const m = part.led_matrix;
    const leds = [];
    const geo = new THREE.PlaneGeometry(m.size[0], m.size[1]);
    for (const z of m.rows_z) {
      for (const x of m.cols_x) {
        const mat = new THREE.MeshStandardMaterial({ color: 0x111827, emissive: 0x000000, roughness: 0.4 });
        const led = new THREE.Mesh(geo, mat);
        led.rotation.x = -Math.PI / 2;
        led.position.set(x, m.y, z);
        led.userData.owned = true;
        led.userData.noHighlight = true;
        group.add(led);
        leds.push(led);
      }
    }
    group.userData.leds = leds;
  }
  return group;
}

// ---------------------------------------------------------------------------------------------
// Floor props: line tracks, colour patches, walls and loose objects used by the sensors.
// ---------------------------------------------------------------------------------------------
function createProp(prop) {
  let mesh;
  if (prop.type === 'patch') {
    mesh = new THREE.Mesh(
      new THREE.PlaneGeometry(prop.size[0], prop.size[1]),
      new THREE.MeshStandardMaterial({ color: new THREE.Color(prop.color), roughness: 0.9 })
    );
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(prop.pos[0], 0.002 + (prop.layer || 0) * 0.001, prop.pos[2]);
    mesh.receiveShadow = true;
  } else if (prop.type === 'ring') {
    mesh = new THREE.Mesh(
      new THREE.RingGeometry(prop.radius - prop.width / 2, prop.radius + prop.width / 2, 96),
      new THREE.MeshStandardMaterial({ color: new THREE.Color(prop.color), roughness: 0.9 })
    );
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(prop.pos[0], 0.003, prop.pos[2]);
    mesh.receiveShadow = true;
  } else if (prop.type === 'box') {
    mesh = new THREE.Mesh(
      new THREE.BoxGeometry(...prop.size),
      new THREE.MeshStandardMaterial({ color: new THREE.Color(prop.color), roughness: 0.6 })
    );
    mesh.position.set(...prop.pos);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
  } else {
    return null;
  }
  mesh.userData.owned = true;
  mesh.userData.prop = prop;
  return mesh;
}

// ---------------------------------------------------------------------------------------------
// Kinematics (mirrors app/cad/verifier.py::solve_poses)
// ---------------------------------------------------------------------------------------------
const _q = new THREE.Quaternion();
const _v = new THREE.Vector3();

function jointTransform(j, angles, byId, cache) {
  if (cache.has(j.id)) return cache.get(j.id);
  const ang = angles[j.motor_port] || 0;
  let q = new THREE.Quaternion();
  let t = new THREE.Vector3();
  if (j.type === 'revolute') {
    // Positive motor degrees turn clockwise when looking at the output face, i.e. -angle about `axis`.
    q.setFromAxisAngle(new THREE.Vector3(...j.axis).normalize(), THREE.MathUtils.degToRad(-ang * j.gear_ratio));
    const piv = new THREE.Vector3(...j.pivot);
    t = piv.clone().sub(piv.clone().applyQuaternion(q));
  } else if (j.type === 'prismatic') {
    const d = THREE.MathUtils.clamp(ang * j.scale_per_deg, j.min_travel, j.max_travel);
    t = new THREE.Vector3(...j.axis).multiplyScalar(d);
  }
  if (j.parent && byId[j.parent]) {
    const [pq, pt] = jointTransform(byId[j.parent], angles, byId, cache);
    t = t.clone().applyQuaternion(pq).add(pt);
    q = pq.clone().multiply(q);
  }
  const res = [q, t];
  cache.set(j.id, res);
  return res;
}

// ---------------------------------------------------------------------------------------------
// Viewer
// ---------------------------------------------------------------------------------------------
class Spike3DViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.sceneData = null;
    this.currentStep = 1;
    this.exploded = false;
    this.showCables = true;
    this.partEntries = [];
    this.cableEntries = [];
    this.propEntries = [];
    this.lessonId = null;
    this.lang = null;
    this.loadSeq = 0;
    this.clock = new THREE.Clock();
    this.motorAngles = {};
    this.chassis = { x: 0, z: 0, yaw: 0 };
    this.simActive = false;
    if (!this.container) return;
    this.initThree();
    this.animate();
  }

  initThree() {
    const width = this.container.clientWidth || 640;
    const height = this.container.clientHeight || 460;
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xeef2f6);
    this.camera = new THREE.PerspectiveCamera(40, width / height, 0.05, 200);
    this.camera.position.set(...DEFAULT_CAMERA.pos);

    this.renderer = new THREE.WebGLRenderer({ antialias: true });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.container.innerHTML = '';
    this.container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.target.set(...DEFAULT_CAMERA.target);

    this.scene.add(new THREE.HemisphereLight(0xffffff, 0xcbd5e1, 1.6));
    const key = new THREE.DirectionalLight(0xffffff, 1.6);
    key.position.set(7, 14, 9);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { near: 1, far: 40, left: -10, right: 10, top: 10, bottom: -10 });
    this.scene.add(key);
    const fill = new THREE.DirectionalLight(0xdbeafe, 0.7);
    fill.position.set(-8, 6, -6);
    this.scene.add(fill);

    const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.ShadowMaterial({ opacity: 0.16 }));
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);
    // 1 grid cell = 1 stud (8 mm)
    const grid = new THREE.GridHelper(24, 60, 0x94a3b8, 0xd5dde7);
    grid.position.y = 0.001;
    this.scene.add(grid);

    this.propRoot = new THREE.Group();
    this.trailRoot = new THREE.Group();
    this.robotRoot = new THREE.Group(); // moves with a driving chassis
    this.modelRoot = new THREE.Group();
    this.cableRoot = new THREE.Group();
    this.robotRoot.add(this.modelRoot, this.cableRoot);
    this.scene.add(this.propRoot, this.trailRoot, this.robotRoot);
    this._trailPts = [];
    this._trailLine = null;

    new ResizeObserver(() => this.onResize()).observe(this.container);
  }

  onResize() {
    if (!this.container || !this.renderer) return;
    const width = this.container.clientWidth || 640;
    const height = this.container.clientHeight || 460;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  clearGroup(group) {
    while (group.children.length > 0) {
      const child = group.children[0];
      group.remove(child);
      disposeOwned(child);
    }
  }

  async loadLesson(lessonId, lang, step = 1) {
    const seq = ++this.loadSeq; // ignore responses from superseded lesson switches
    this.lessonId = lessonId;
    this.lang = lang;
    this.currentStep = step;
    const res = await fetch(`${BASE()}/api/lesson/${encodeURIComponent(lessonId)}/scene?lang=${encodeURIComponent(lang)}`);
    if (!res.ok) throw new Error(`scene ${lessonId}: HTTP ${res.status}`);
    const data = await res.json();
    if (seq !== this.loadSeq) return;
    const built = await this.buildSceneObjects(data);
    if (seq !== this.loadSeq) return;
    const lessonChanged = this.sceneData?.lesson_id !== data.lesson_id;
    this.sceneData = data;
    this.applyBuilt(built);
    if (lessonChanged) this.resetCamera();
    this.setStep(this.currentStep);
    window.dispatchEvent(new CustomEvent('spike:scene-loaded', { detail: { lessonId: data.lesson_id } }));
  }

  async buildSceneObjects(data) {
    const parts = [];
    for (const stepObj of data.steps) {
      for (const part of stepObj.parts) parts.push({ step: stepObj.step, part });
    }
    const meshes = await Promise.all(parts.map(({ part }) => createPart(part)));
    return { parts, meshes };
  }

  applyBuilt({ parts, meshes }) {
    this.partEntries = [];
    this.cableEntries = [];
    this.propEntries = [];
    this.clearGroup(this.modelRoot);
    this.clearGroup(this.cableRoot);
    this.clearGroup(this.propRoot);
    this.clearTrail();
    this.motorAngles = {};
    this.chassis = { x: 0, z: 0, yaw: 0 };
    this.applyChassis();

    parts.forEach(({ step, part }, i) => {
      const mesh = meshes[i];
      const basePos = new THREE.Vector3(...part.pos);
      const baseQuat = Array.isArray(part.quat) && part.quat.length === 4
        ? new THREE.Quaternion(...part.quat)
        : new THREE.Quaternion().setFromEuler(new THREE.Euler(...(part.rot || [0, 0, 0])));
      const explodeVec = new THREE.Vector3(...(part.explode || [0, 1, 0]));
      mesh.quaternion.copy(baseQuat);
      mesh.position.copy(basePos).add(explodeVec);
      mesh.visible = false;
      this.modelRoot.add(mesh);
      this.partEntries.push({
        step,
        part,
        mesh,
        basePos,
        baseQuat,
        targetPos: basePos.clone(),
        explodePos: basePos.clone().add(explodeVec),
        currentTarget: basePos.clone(),
      });
    });
    this.entryById = Object.fromEntries(this.partEntries.map((e) => [e.part.id, e]));

    for (const c of this.sceneData.cables || []) {
      const pts = c.points.map((p) => new THREE.Vector3(...p));
      const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 48, 0.035, 8, false),
        new THREE.MeshStandardMaterial({ color: new THREE.Color(c.color || '#475569'), roughness: 0.55 })
      );
      tube.castShadow = true;
      tube.userData.owned = true;
      const end = pts[pts.length - 1];
      const badge = createFloatingLabel(`Port ${c.port}`);
      badge.position.set(end.x + (end.x < 0 ? -0.45 : 0.45), end.y + 0.5, end.z);
      const g = new THREE.Group();
      g.add(tube, badge);
      g.visible = false;
      this.cableRoot.add(g);
      this.cableEntries.push({ step: c.step, group: g, cable: c });
    }

    (this.sceneData.floor_props || []).forEach((prop, index) => {
      const mesh = createProp(prop);
      if (!mesh) return;
      this.propRoot.add(mesh);
      this.propEntries.push({ prop, mesh, index, basePos: mesh.position.clone() });
    });
    this.setLedMatrix(new Array(25).fill(0));
  }

  get lastStep() {
    return Math.max(1, ...this.partEntries.map((e) => e.step));
  }

  setStep(stepNum) {
    this.currentStep = stepNum;
    for (const entry of this.partEntries) {
      const show = this.simActive || entry.step <= stepNum;
      entry.mesh.visible = show;
      if (show) {
        entry.currentTarget = this.exploded ? entry.explodePos : entry.targetPos;
        if (entry.step === stepNum && !this.exploded && !this.simActive) entry.mesh.position.copy(entry.explodePos);
      }
      entry.highlighted = !this.simActive && entry.step === stepNum;
      setHighlight(entry.mesh, entry.highlighted);
    }
    this.refreshCables();
  }

  refreshCables() {
    for (const c of this.cableEntries) {
      c.group.visible = this.showCables && !this.exploded && (this.simActive || c.step <= this.currentStep);
    }
  }

  toggleExplode() {
    if (this.simActive) return;
    this.exploded = !this.exploded;
    for (const e of this.partEntries) {
      if (e.mesh.visible) e.currentTarget = this.exploded ? e.explodePos : e.targetPos;
    }
    this.refreshCables();
  }

  toggleCables() {
    this.showCables = !this.showCables;
    this.refreshCables();
  }

  resetCamera() {
    const cam = this.sceneData?.camera || DEFAULT_CAMERA;
    this.camera.position.set(...cam.pos);
    this.controls.target.set(...cam.target);
    this.controls.update();
  }

  // ---------------- Simulation API (driven by simulator.js) ----------------
  showAllForSim() {
    this.simActive = true;
    this.exploded = false;
    for (const e of this.partEntries) {
      e.mesh.visible = true;
      e.highlighted = false;
      setHighlight(e.mesh, false);
    }
    this.refreshCables();
    this.setMotorAngles({});
  }

  resetSim() {
    this.simActive = false;
    this.chassis = { x: 0, z: 0, yaw: 0 };
    this.applyChassis();
    this.clearTrail();
    this.setMotorAngles({});
    for (const p of this.propEntries) p.mesh.position.copy(p.basePos);
    for (const e of this.partEntries) {
      if (e.mesh.userData.plunger) this.setPlunger(e.part.id, 0);
    }
    this.setLedMatrix(new Array(25).fill(0));
    this.setStep(this.currentStep);
  }

  clearTrail() {
    this._trailPts = [];
    if (this._trailLine) {
      this.trailRoot.remove(this._trailLine);
      this._trailLine.geometry?.dispose();
      this._trailLine.material?.dispose();
      this._trailLine = null;
    }
  }

  appendTrailPoint(x, z) {
    const last = this._trailPts[this._trailPts.length - 1];
    if (last && Math.hypot(x - last.x, z - last.z) < 0.12) return;
    this._trailPts.push(new THREE.Vector3(x, 0.025, z));
    if (this._trailPts.length > 1200) this._trailPts.shift();
    if (this._trailPts.length < 2) return;
    if (!this._trailLine) {
      const mat = new THREE.LineBasicMaterial({ color: 0x0ea5e9, transparent: true, opacity: 0.75 });
      this._trailLine = new THREE.Line(new THREE.BufferGeometry(), mat);
      this._trailLine.userData.owned = true;
      this.trailRoot.add(this._trailLine);
    }
    this._trailLine.geometry.dispose();
    this._trailLine.geometry = new THREE.BufferGeometry().setFromPoints(this._trailPts);
  }

  /** Chassis pose in the floor plane (scene units, yaw radians about +Y). */
  setChassisPose(x, z, yaw) {
    this.chassis = { x, z, yaw };
    this.applyChassis();
  }

  applyChassis() {
    this.robotRoot.position.set(this.chassis.x, 0, this.chassis.z);
    this.robotRoot.rotation.set(0, this.chassis.yaw, 0);
  }

  /** Apply motor angles (degrees by port letter) through joints, rotors and crank linkages. */
  setMotorAngles(angles) {
    this.motorAngles = { ...angles };
    const joints = this.sceneData?.joints || [];
    const cranks = this.sceneData?.crank_linkages || [];
    const byId = Object.fromEntries(joints.map((j) => [j.id, j]));
    const cache = new Map();
    const poses = new Map();
    for (const e of this.partEntries) poses.set(e.part.id, [e.basePos.clone(), e.baseQuat.clone()]);
    for (const j of joints) {
      const [q, t] = jointTransform(j, angles, byId, cache);
      for (const pid of j.parts) {
        const e = this.entryById[pid];
        if (!e) continue;
        poses.set(pid, [e.basePos.clone().applyQuaternion(q).add(t), q.clone().multiply(e.baseQuat)]);
      }
    }
    for (const cl of cranks) {
      const ang = angles[cl.motor_port] || 0;
      const r0 = THREE.MathUtils.degToRad(cl.phase_deg);
      const r1 = THREE.MathUtils.degToRad(cl.phase_deg + cl.sign * ang);
      const ax = cl.axis;
      let d;
      if (Math.abs(ax[0]) > 0.9) d = [0, cl.radius * (Math.sin(r1) - Math.sin(r0)), cl.radius * (Math.cos(r1) - Math.cos(r0))];
      else if (Math.abs(ax[2]) > 0.9) d = [cl.radius * (Math.cos(r1) - Math.cos(r0)), cl.radius * (Math.sin(r1) - Math.sin(r0)), 0];
      else d = [cl.radius * (Math.cos(r1) - Math.cos(r0)), 0, cl.radius * (Math.sin(r1) - Math.sin(r0))];
      for (const pid of cl.parts) {
        const p = poses.get(pid);
        if (p) p[0].add(_v.set(...d));
      }
    }
    for (const e of this.partEntries) {
      const [pos, quat] = poses.get(e.part.id);
      e.targetPos = pos;
      e.mesh.quaternion.copy(quat);
      if (this.simActive) {
        e.mesh.position.copy(pos);
        e.currentTarget = pos;
      }
      const rotor = e.mesh.userData.rotor;
      if (rotor) {
        const deg = e.part.port ? angles[e.part.port] || 0 : 0;
        rotor.quaternion.setFromAxisAngle(e.mesh.userData.rotorAxis, THREE.MathUtils.degToRad(-deg));
      }
      // Graceful wheel spin on legacy un-rewritten lessons that have no CAD `joints` metadata yet
      if (joints.length === 0 && e.mesh.userData.isLegacy && e.part.type === 'wheel') {
        const id = e.part.id || '';
        const deg = id.includes('_l') || id.includes('left') ? (angles.C || 0) : (angles.D || 0);
        const sign = id.includes('_l') || id.includes('left') ? 1 : -1;
        _q.setFromAxisAngle(_v.set(1, 0, 0), THREE.MathUtils.degToRad(sign * deg));
        e.mesh.quaternion.copy(e.baseQuat).multiply(_q);
      }
    }
  }

  setPlunger(partId, pressed01) {
    const e = this.entryById?.[partId];
    const ud = e?.mesh.userData;
    if (!ud?.plunger) return;
    ud.plunger.position.copy(ud.plungerRest).addScaledVector(ud.plungerDir, pressed01);
  }

  setLedMatrix(values) {
    const hub = this.partEntries.find((e) => Array.isArray(e.mesh.userData.leds));
    if (!hub) return;
    hub.mesh.userData.leds.forEach((led, i) => {
      const v = values ? values[i] || 0 : 0;
      const m = led.material;
      if (v > 0) {
        m.color.setHex(0xfff7d6);
        m.emissive.setHex(0xffb020);
        m.emissiveIntensity = 0.3 + 0.9 * Math.min(1, v / 100);
      } else {
        m.color.setHex(0x111827);
        m.emissive.setHex(0x000000);
        m.emissiveIntensity = 0;
      }
    });
  }

  /** World-space pose of a part (after chassis + joints), for sensors. */
  partWorld(partId) {
    const e = this.entryById?.[partId];
    if (!e) return null;
    this.robotRoot.updateMatrixWorld(true);
    const pos = new THREE.Vector3();
    const quat = new THREE.Quaternion();
    e.mesh.getWorldPosition(pos);
    e.mesh.getWorldQuaternion(quat);
    return { pos, quat };
  }

  /** Follow the simulator's prop positions (cargo pushed or carried by the robot). */
  setPropPositions(positions) {
    if (!positions) return;
    for (const e of this.propEntries) {
      const p = positions[e.index];
      if (p && e.prop.type === 'box') e.mesh.position.set(p[0], p[1], p[2]);
    }
  }

  /** Move a loose prop (e.g. cargo carried by a hook) in world space. */
  setPropPosition(index, pos) {
    const p = this.propEntries[index];
    if (p) p.mesh.position.copy(pos);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    highlightStrength = 0.15 + 0.2 * (0.5 + 0.5 * Math.sin(this.clock.getElapsedTime() * 4));
    if (!this.simActive) {
      for (const e of this.partEntries) {
        if (!e.mesh.visible) continue;
        e.mesh.position.lerp(e.currentTarget, 0.14);
        if (e.highlighted) setHighlight(e.mesh, true);
      }
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

// Sync the viewer with whatever lesson/step the server-rendered DOM currently shows.
function syncViewerWithDom() {
  const lessonEl = document.querySelector('[data-lesson-root]');
  if (!lessonEl) return;
  const stepEl = document.querySelector('[data-step-root]');
  const lessonId = lessonEl.dataset.lessonId;
  const lang = lessonEl.dataset.lang;
  const step = parseInt(stepEl?.dataset.step || '1', 10);
  if (!window.SpikeViewer) window.SpikeViewer = new Spike3DViewer('viewer3d-canvas');
  const viewer = window.SpikeViewer;
  if (viewer.lessonId !== lessonId || viewer.lang !== lang) {
    window.SpikeSimulator?.stop(true);
    viewer.loadLesson(lessonId, lang, step).catch((err) => console.error(err));
  } else if (viewer.currentStep !== step || !viewer.sceneData) {
    viewer.currentStep = step;
    if (viewer.sceneData && !viewer.simActive) viewer.setStep(step);
  }
}

window.Spike3DViewer = Spike3DViewer;
document.addEventListener('htmx:afterSettle', syncViewerWithDom);
syncViewerWithDom();
