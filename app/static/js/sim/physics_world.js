/**
 * Deterministic SPIKE Prime Virtual Physics & Sensor World (10 ms fixed substep).
 *
 * Units match app/cad/assembly.py & viewer3d.js exactly:
 *   1 stud = 20 LDU = 8 mm = 0.40 scene units  =>  1 scene unit = 20 mm (2 cm)
 *   Floor plane at Y = 0, Y-up, robot drives toward -Z at yaw = 0.
 *   Positive motor degrees rotate clockwise looking at the motor's output face.
 */
import { SimCancelledError } from './python_vm.js';

export const FIXED_STEP_MS = 10;
export const SCENE_TO_MM = 20.0; // 1 scene unit = 20 mm
export const MM_TO_SCENE = 1 / SCENE_TO_MM;

export const SPIKE_COLORS = {
  UNKNOWN: -1,
  BLACK: 0,
  MAGENTA: 1,
  PURPLE: 2,
  BLUE: 3,
  AZURE: 4,
  TURQUOISE: 5,
  GREEN: 6,
  YELLOW: 7,
  ORANGE: 8,
  RED: 9,
  WHITE: 10,
};

const COLOR_RGB_REFLECTION = {
  BLACK:     { id: 0,  rgb: [20, 24, 32],    refl: 8 },
  MAGENTA:   { id: 1,  rgb: [180, 45, 130],  refl: 42 },
  PURPLE:    { id: 2,  rgb: [120, 55, 180],  refl: 36 },
  BLUE:      { id: 3,  rgb: [35, 100, 235],  refl: 34 },
  AZURE:     { id: 4,  rgb: [54, 174, 191],  refl: 58 },
  TURQUOISE: { id: 5,  rgb: [20, 184, 166],  refl: 55 },
  GREEN:     { id: 6,  rgb: [34, 170, 74],   refl: 45 },
  YELLOW:    { id: 7,  rgb: [238, 195, 25],  refl: 82 },
  ORANGE:    { id: 8,  rgb: [249, 115, 22],  refl: 66 },
  RED:       { id: 9,  rgb: [225, 38, 38],   refl: 48 },
  WHITE:     { id: 10, rgb: [242, 245, 249], refl: 92 },
};

const PORTS = ['A', 'B', 'C', 'D', 'E', 'F'];

function parseHexRgb(hex) {
  const s = String(hex || '#f1f5f9').replace('#', '');
  const full = s.length === 3 ? s.split('').map((c) => c + c).join('') : s;
  const n = parseInt(full, 16);
  if (Number.isNaN(n)) return [241, 245, 249];
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

export function classifyHexColor(hex, explicitName = null) {
  if (explicitName && COLOR_RGB_REFLECTION[explicitName.toUpperCase()]) {
    const k = explicitName.toUpperCase();
    return { name: k, ...COLOR_RGB_REFLECTION[k] };
  }
  const [r, g, b] = parseHexRgb(hex);
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const luma = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  const refl = Math.round(Math.max(4, Math.min(96, luma * 94)));
  const sat = max === 0 ? 0 : (max - min) / max;

  if (max < 70 || (sat < 0.22 && luma < 0.25)) return { name: 'BLACK', id: SPIKE_COLORS.BLACK, rgb: [r, g, b], refl: Math.min(refl, 14) };
  if (sat < 0.18 && luma >= 0.72) return { name: 'WHITE', id: SPIKE_COLORS.WHITE, rgb: [r, g, b], refl: Math.max(refl, 86) };

  // Hue in [0, 360)
  let h = 0;
  const d = max - min || 1;
  if (max === r) h = 60 * (((g - b) / d) % 6);
  else if (max === g) h = 60 * ((b - r) / d + 2);
  else h = 60 * ((r - g) / d + 4);
  if (h < 0) h += 360;

  let name = 'UNKNOWN';
  if (h < 16 || h >= 338) name = 'RED';
  else if (h < 42) name = 'ORANGE';
  else if (h < 72) name = 'YELLOW';
  else if (h < 155) name = 'GREEN';
  else if (h < 185) name = 'TURQUOISE';
  else if (h < 208) name = 'AZURE';
  else if (h < 252) name = 'BLUE';
  else if (h < 292) name = 'PURPLE';
  else name = 'MAGENTA';

  return { name, id: SPIKE_COLORS[name], rgb: [r, g, b], refl };
}

// Quaternion helpers (pure JS so physics_world works identically in Node.js without Three.js)
function quatRotateVec(q, v) {
  const [qx, qy, qz, qw] = q;
  const [vx, vy, vz] = v;
  const tx = 2 * (qy * vz - qz * vy);
  const ty = 2 * (qz * vx - qx * vz);
  const tz = 2 * (qx * vy - qy * vx);
  return [
    vx + qw * tx + (qy * tz - qz * ty),
    vy + qw * ty + (qz * tx - qx * tz),
    vz + qw * tz + (qx * ty - qy * tx),
  ];
}

function rotateY(v, yaw) {
  const c = Math.cos(yaw);
  const s = Math.sin(yaw);
  return [v[0] * c + v[2] * s, v[1], -v[0] * s + v[2] * c];
}

function rayIntersectAabb(origin, dir, boxMin, boxMax) {
  let tmin = -Infinity;
  let tmax = Infinity;
  for (let i = 0; i < 3; i++) {
    if (Math.abs(dir[i]) < 1e-8) {
      if (origin[i] < boxMin[i] || origin[i] > boxMax[i]) return null;
    } else {
      let t1 = (boxMin[i] - origin[i]) / dir[i];
      let t2 = (boxMax[i] - origin[i]) / dir[i];
      if (t1 > t2) [t1, t2] = [t2, t1];
      tmin = Math.max(tmin, t1);
      tmax = Math.min(tmax, t2);
      if (tmin > tmax) return null;
    }
  }
  if (tmax < 0) return null;
  return tmin >= 0 ? tmin : 0;
}

class MotorChannel {
  constructor(port) {
    this.port = port;
    this.angle = 0;          // continuous physical angle (deg)
    this.relZero = 0;        // offset for relative_position()
    this.velocity = 0;       // current angular speed (deg/s)
    this.mode = 'idle';      // 'idle' | 'run' | 'target'
    this.targetAngle = 0;
    this.targetVel = 0;      // signed deg/s toward target
    this.pending = null;     // { resolve }
  }

  _cancelPending(status = 3) { // 3 = motor.CANCELED
    if (this.pending) {
      const p = this.pending;
      this.pending = null;
      p.cleanup?.();
      p.resolve(status);
    }
  }

  run(velocity) {
    this._cancelPending(3);
    this.mode = 'run';
    this.velocity = Math.max(-1050, Math.min(1050, Number(velocity) || 0));
  }

  stop() {
    this._cancelPending(3);
    this.mode = 'idle';
    this.velocity = 0;
  }

  driveTo(targetAngle, speedAbs, world) {
    this._cancelPending(3);
    const delta = targetAngle - this.angle;
    const spd = Math.min(1050, Math.abs(Number(speedAbs) || 0));
    if (Math.abs(delta) < 1e-4 || spd < 1e-4) {
      this.mode = 'idle';
      this.velocity = 0;
      return Promise.resolve(0); // 0 = motor.READY
    }
    this.mode = 'target';
    this.targetAngle = targetAngle;
    this.targetVel = Math.sign(delta) * spd;
    this.velocity = this.targetVel;
    return new Promise((resolve, reject) => {
      const pending = { resolve, reject, cleanup: null };
      pending.cleanup = () => world._unregisterPending(pending);
      this.pending = pending;
      world._registerPending(pending);
    });
  }

  step(dtSec) {
    const prev = this.angle;
    if (this.mode === 'run') {
      this.angle += this.velocity * dtSec;
    } else if (this.mode === 'target') {
      const stepDeg = this.targetVel * dtSec;
      const rem = this.targetAngle - this.angle;
      if (Math.abs(stepDeg) >= Math.abs(rem)) {
        this.angle = this.targetAngle;
        this.velocity = 0;
        this.mode = 'idle';
        if (this.pending) {
          const p = this.pending;
          this.pending = null;
          p.cleanup?.();
          p.resolve(0); // motor.READY
        }
      } else {
        this.angle += stepDeg;
      }
    }
    return this.angle - prev;
  }

  relativePosition() {
    return Math.round(this.angle - this.relZero);
  }

  absolutePosition() {
    let a = ((Math.round(this.angle) % 360) + 360) % 360;
    if (a >= 180) a -= 360; // Official SPIKE 3: [-180, 179]
    return a;
  }
}

export class VirtualWorld {
  constructor(sceneData = null, callbacks = {}) {
    this.sceneData = sceneData || {};
    this.callbacks = callbacks; // { onBeep, onLed, onPlunger, onPrint }
    this.timeMs = 0;
    this.cancelled = false;

    this.motors = Object.fromEntries(PORTS.map((p) => [p, new MotorChannel(p)]));
    this.pairs = {}; // pairId -> { leftPort, rightPort }

    // Chassis state in floor plane (scene units, yaw radians about +Y, forward = -Z at yaw=0)
    this.chassis = { x: 0, z: 0, yaw: 0 };
    this.axleWorld = { x: 0, z: 0 };
    this.axleLocal = { x: 0, z: 0 };
    this.yawOffsetRad = 0;
    this.yawBiasDecideg = 0;

    // LED matrix (25 values, 0..100) & text banner
    this.leds = new Array(25).fill(0);
    this.ledText = '';
    this.ledImageName = '';

    // Hub buttons (pressed since virtual time, or null)
    this.buttons = { LEFT: null, RIGHT: null };

    // Virtual / manual sensor overrides
    this.manualSensors = {
      distanceCm: 45,
      distanceAuto: true,
      color: 'RED',
      colorAuto: true,
      forcePressed: false,
      forceByPort: {},
    };

    // Pending timers & motor promises (cancelled cleanly on stop)
    this._timers = [];
    this._pendings = new Set();

    // Indexed scene parts & kinematics
    this._indexScene(this.sceneData);
  }

  _indexScene(scene) {
    this.partsById = {};
    for (const st of scene.steps || []) {
      for (const p of st.parts || []) {
        this.partsById[p.id] = p;
      }
    }
    // Deep-copied so movable props (cargo) can be pushed / carried without touching sceneData.
    this.floorProps = (scene.floor_props || []).map((p) => ({ ...p, pos: [...(p.pos || [0, 0, 0])] }));
    this.kinematics = scene.kinematics || { chassis: { type: 'static' } };
    // Mechanical hard stops in motor degrees ({ A: { min, max } }): past them the real mechanism jams.
    this.limits = this.kinematics.limits || {};
    this.gripper = this.kinematics.gripper || null;
    this.heldProp = null; // { prop, local: [x, z] } while the gripper holds a movable prop
    this.collisionBoxes = this.kinematics.collision_boxes || [];
    this.warnings = [];
    this._warned = new Set();
    this.hasWorldObstacles = this.floorProps.some((p) => p.type === 'box');
    this.hasWorldColorProps = this.floorProps.some((p) => p.type === 'patch' || p.type === 'ring');

    // Compute local axle midpoint for exact zero-slip differential pivoting
    const ch = this.kinematics.chassis || { type: 'static' };
    if (ch.type === 'differential' && Array.isArray(ch.wheels) && ch.wheels.length >= 2) {
      const [w0, w1] = ch.wheels;
      this.axleLocal = {
        x: 0.5 * (w0.center[0] + w1.center[0]),
        z: 0.5 * (w0.center[2] + w1.center[2]),
      };
    } else {
      this.axleLocal = { x: 0, z: 0 };
    }
    this.axleWorld = { x: this.axleLocal.x, z: this.axleLocal.z };
    this.chassis = { x: 0, z: 0, yaw: 0 };
  }

  _registerPending(p) {
    this._pendings.add(p);
  }

  _unregisterPending(p) {
    this._pendings.delete(p);
  }

  cancel() {
    this.cancelled = true;
    const err = new SimCancelledError();
    for (const t of this._timers) t.reject(err);
    this._timers = [];
    for (const p of this._pendings) {
      if (p.reject) p.reject(err);
    }
    this._pendings.clear();
    for (const m of Object.values(this.motors)) {
      m.pending = null;
      m.mode = 'idle';
      m.velocity = 0;
    }
  }

  sleepMs(ms) {
    if (this.cancelled) return Promise.reject(new SimCancelledError());
    const dur = Math.max(0, Number(ms) || 0);
    if (dur === 0) return Promise.resolve();
    const wakeAt = this.timeMs + dur;
    return new Promise((resolve, reject) => {
      this._timers.push({ wakeAt, resolve, reject });
    });
  }

  pairMotors(pairId, leftPort, rightPort) {
    this.pairs[pairId] = { leftPort, rightPort };
    // Fallback for un-rewritten legacy scenes without explicit CAD chassis kinematics:
    // if the program pairs two motors, enable standard 56mm differential kinematics so real code still drives!
    if (!this.kinematics.chassis || this.kinematics.chassis.type === 'static') {
      const hasAnyJoint = (this.sceneData.joints || []).length > 0;
      if (!hasAnyJoint) {
        this.kinematics = {
          ...this.kinematics,
          chassis: {
            type: 'differential',
            wheels: [
              { port: leftPort, center: [-3.35, 1.4, 0], axis: [-1, 0, 0], radius: 1.4 },
              { port: rightPort, center: [3.35, 1.4, 0], axis: [1, 0, 0], radius: 1.4 },
            ],
            pair_left: leftPort,
            pair_right: rightPort,
          },
        };
      }
    }
  }

  unpairMotors(pairId) {
    delete this.pairs[pairId];
  }

  /** Sign mapping from forward wheel travel to physical motor angle on a differential pair. */
  getPairMotorSigns(pair) {
    const ch = this.kinematics.chassis;
    if (ch?.type === 'differential' && Array.isArray(ch.wheels)) {
      const wl = ch.wheels.find((w) => w.port === pair.leftPort);
      const wr = ch.wheels.find((w) => w.port === pair.rightPort);
      // Wheel with axis [-1,0,0] rolls forward (-Z) for negative motor angle; [+1,0,0] for positive angle
      const leftSign = wl ? (wl.axis[0] < 0 ? -1 : 1) : -1;
      const rightSign = wr ? (wr.axis[0] < 0 ? -1 : 1) : 1;
      return { leftSign, rightSign };
    }
    return { leftSign: -1, rightSign: 1 };
  }

  /** Advance physics & timers by one fixed substep (dtMs). */
  advanceSubstep(dtMs = FIXED_STEP_MS) {
    if (this.cancelled) return;
    this.timeMs += dtMs;
    const dtSec = dtMs / 1000;

    // 1. Step all 6 motors
    const dAngles = {};
    for (const port of PORTS) {
      dAngles[port] = this.motors[port].step(dtSec);
    }
    this._applyHardStops(dAngles);

    // 2. Integrate chassis kinematics (+ obstacle contact, pushing and carrying props)
    const before = { x: this.chassis.x, z: this.chassis.z, yaw: this.chassis.yaw, ax: this.axleWorld.x, az: this.axleWorld.z };
    this._integrateChassis(dAngles);
    this._resolveContacts(before);

    // 3. Fire due virtual-clock timers
    if (this._timers.length > 0) {
      const remaining = [];
      const ready = [];
      for (const t of this._timers) {
        if (t.wakeAt <= this.timeMs + 1e-6) ready.push(t);
        else remaining.push(t);
      }
      this._timers = remaining;
      for (const t of ready) t.resolve();
    }
  }

  /** Report a physical problem once per kind/port (shown in the sim console). */
  _warn(kind, port, detail = {}) {
    const key = `${kind}:${port || ''}`;
    if (this._warned.has(key)) return;
    this._warned.add(key);
    const w = { kind, port, t: this.timeMs, ...detail };
    this.warnings.push(w);
    this.callbacks.onWarning?.(w);
  }

  /** Stall a motor at an angle: a running/target command stops there and a pending await returns STALLED (2). */
  _stallAt(m, angle, dAngles) {
    dAngles[m.port] += angle - m.angle;
    m.angle = angle;
    m.velocity = 0;
    if (m.mode === 'target') {
      m.mode = 'idle';
      if (m.pending) {
        const p = m.pending;
        m.pending = null;
        p.cleanup?.();
        p.resolve(2); // motor.STALLED
      }
    }
  }

  _applyHardStops(dAngles) {
    for (const [port, lim] of Object.entries(this.limits)) {
      const m = this.motors[port];
      if (!m) continue;
      if (m.angle > lim.max + 1e-6) {
        this._stallAt(m, lim.max, dAngles);
        this._warn('limit', port, { angle: lim.max });
      } else if (m.angle < lim.min - 1e-6) {
        this._stallAt(m, lim.min, dAngles);
        this._warn('limit', port, { angle: lim.min });
      }
    }
    const g = this.gripper;
    if (!g) return;
    const m = this.motors[g.port];
    if (!m) return;
    if (this.heldProp && m.angle > g.release_deg) {
      this.heldProp = null;
      this._warned.delete('grip:' + g.port);
    }
    // Grab only at the moment the jaws close past the contact angle with the cargo between them;
    // jaws that are already shut act as a solid wall instead (see _resolveContacts).
    const prevAngle = m.angle - dAngles[g.port];
    if (m.angle < g.contact_deg && (this.heldProp || prevAngle >= g.contact_deg)) {
      if (!this.heldProp) {
        const prop = this.floorProps.find((p) => p.type === 'box' && p.movable && this._inGripZone(p));
        if (prop) {
          const [lx, lz] = this._worldToRobot(prop.pos[0], prop.pos[2]);
          this.heldProp = { prop, local: [lx, lz] };
        }
      }
      // Jaws closing on a held prop cannot pass through it: the motor stalls at the contact angle.
      if (this.heldProp) {
        this._stallAt(m, g.contact_deg, dAngles);
        this._warn('grip', g.port);
      }
    }
  }

  _worldToRobot(wx, wz) {
    const dx = wx - this.chassis.x;
    const dz = wz - this.chassis.z;
    // inverse of rotateY(v, yaw)
    const c = Math.cos(this.chassis.yaw);
    const s = Math.sin(this.chassis.yaw);
    return [dx * c - dz * s, dx * s + dz * c];
  }

  _robotToWorld(lx, lz) {
    const [x, , z] = rotateY([lx, 0, lz], this.chassis.yaw);
    return [x + this.chassis.x, z + this.chassis.z];
  }

  _inGripZone(prop) {
    const [x0, x1, z0, z1] = this.gripper.zone;
    const [lx, lz] = this._worldToRobot(prop.pos[0], prop.pos[2]);
    return lx >= x0 && lx <= x1 && lz >= z0 && lz <= z1;
  }

  /** Penetration test between the robot's rest-pose part boxes and an axis-aligned world box prop. */
  _robotHitsProp(prop) {
    const [cx, cy, cz] = prop.pos;
    const [sx, sy, sz] = prop.size;
    const eps = 0.02; // 0.4 mm: touching is not penetrating
    const c = Math.cos(this.chassis.yaw);
    const s = Math.sin(this.chassis.yaw);
    const boxes = this.collisionBoxes;
    const g = this.gripper;
    const jawsShut = g?.closed_box && this.motors[g.port] && this.motors[g.port].angle < g.contact_deg;
    for (const b of jawsShut ? [...boxes, g.closed_box] : boxes) {
      const [x0, y0, z0, x1, y1, z1] = b;
      if (y1 <= cy - sy / 2 + eps || y0 >= cy + sy / 2 - eps) continue;
      // Robot box centre / half extents in robot frame, then in world (rotated rectangle)
      const hx = (x1 - x0) / 2;
      const hz = (z1 - z0) / 2;
      const [wx, wz] = this._robotToWorld((x0 + x1) / 2, (z0 + z1) / 2);
      // Robot box axes in world: local +X -> (c, -s), local +Z -> (s, c)
      const axes = [[1, 0], [0, 1], [c, -s], [s, c]];
      let separated = false;
      for (const [ax, az] of axes) {
        const rProp = (sx / 2) * Math.abs(ax) + (sz / 2) * Math.abs(az);
        const rRob = hx * Math.abs(ax * c - az * s) + hz * Math.abs(ax * s + az * c);
        const dist = Math.abs((wx - cx) * ax + (wz - cz) * az);
        if (dist >= rProp + rRob - eps) { separated = true; break; }
      }
      if (!separated) return true;
    }
    return false;
  }

  _resolveContacts(before) {
    if (this.kinematics?.chassis?.type === 'static' || !this.collisionBoxes.length) return;
    const held = this.heldProp;
    if (held) {
      const [x, z] = this._robotToWorld(held.local[0], held.local[1]);
      held.prop.pos[0] = x;
      held.prop.pos[2] = z;
    }
    const moved = Math.abs(this.chassis.x - before.x) + Math.abs(this.chassis.z - before.z) + Math.abs(this.chassis.yaw - before.yaw);
    if (moved < 1e-9) return;
    for (const prop of this.floorProps) {
      if (prop.type !== 'box' || (held && prop === held.prop)) continue;
      if (!this._robotHitsProp(prop)) continue;
      if (prop.movable) {
        // Push a loose prop along with the robot's motion (it slides on the floor).
        const dx = this.chassis.x - before.x;
        const dz = this.chassis.z - before.z;
        const nx = -Math.sin(this.chassis.yaw);
        const nz = -Math.cos(this.chassis.yaw);
        const fwd = Math.max(0, dx * nx + dz * nz) + 1e-4;
        prop.pos[0] += nx * fwd;
        prop.pos[2] += nz * fwd;
        if (!this._robotHitsProp(prop)) continue;
      }
      // Fixed obstacle: the robot is stopped (its wheels slip) — restore the previous pose.
      this.chassis.x = before.x;
      this.chassis.z = before.z;
      this.chassis.yaw = before.yaw;
      this.axleWorld.x = before.ax;
      this.axleWorld.z = before.az;
      if (held) {
        const [x, z] = this._robotToWorld(held.local[0], held.local[1]);
        held.prop.pos[0] = x;
        held.prop.pos[2] = z;
      }
      this._warn('bump', null);
      return;
    }
  }

  getPropPositions() {
    return this.floorProps.map((p) => [...p.pos]);
  }

  _integrateChassis(dAngles) {
    const ch = this.kinematics?.chassis;
    if (!ch || ch.type === 'static') return;

    if (ch.type === 'differential' && Array.isArray(ch.wheels) && ch.wheels.length >= 2) {
      // Find left wheel (smaller x) and right wheel (larger x)
      const sorted = [...ch.wheels].sort((a, b) => a.center[0] - b.center[0]);
      const wl = sorted[0];
      const wr = sorted[sorted.length - 1];
      const track = Math.max(0.5, wr.center[0] - wl.center[0]);
      const dThetaL = ((dAngles[wl.port] || 0) * Math.PI) / 180;
      const dThetaR = ((dAngles[wr.port] || 0) * Math.PI) / 180;
      // Positive motor angle = CW looking along wheel.axis => for axis=(-1,0,0), forward (-Z) is negative motor angle!
      const signL = wl.axis[0] < 0 ? -1 : 1;
      const signR = wr.axis[0] < 0 ? -1 : 1;
      const dsL = signL * dThetaL * wl.radius;
      const dsR = signR * dThetaR * wr.radius;

      const ds = 0.5 * (dsL + dsR);
      const dYaw = (dsR - dsL) / track;

      const yawMid = this.chassis.yaw + 0.5 * dYaw;
      this.axleWorld.x += -Math.sin(yawMid) * ds;
      this.axleWorld.z += -Math.cos(yawMid) * ds;
      this.chassis.yaw += dYaw;

      // Soft arena clamp (±26 scene units = ±5.2 m)
      this.axleWorld.x = Math.max(-26, Math.min(26, this.axleWorld.x));
      this.axleWorld.z = Math.max(-26, Math.min(26, this.axleWorld.z));

      // Convert world axle center back to robotRoot origin (exact zero-slip pivot!)
      const c = Math.cos(this.chassis.yaw);
      const s = Math.sin(this.chassis.yaw);
      this.chassis.x = this.axleWorld.x - (this.axleLocal.x * c + this.axleLocal.z * s);
      this.chassis.z = this.axleWorld.z - (-this.axleLocal.x * s + this.axleLocal.z * c);
    } else if (ch.type === 'walker') {
      const lp = ch.left_port || 'C';
      const rp = ch.right_port || 'D';
      const stride = ch.stride_per_deg || 0.008;
      const turn = ch.turn_per_deg || 0.003;
      const dL = (ch.left_sign ?? -1) * (dAngles[lp] || 0);
      const dR = (ch.right_sign ?? 1) * (dAngles[rp] || 0);
      const ds = 0.5 * (dL + dR) * stride;
      const dYaw = (dR - dL) * turn;
      const yawMid = this.chassis.yaw + 0.5 * dYaw;
      this.chassis.x = Math.max(-26, Math.min(26, this.chassis.x - Math.sin(yawMid) * ds));
      this.chassis.z = Math.max(-26, Math.min(26, this.chassis.z - Math.cos(yawMid) * ds));
      this.chassis.yaw += dYaw;
    }
  }

  getMotorAngles() {
    const out = {};
    for (const p of PORTS) out[p] = this.motors[p].angle;
    return out;
  }

  // ---------------- Hub LED / Sound / Buttons / IMU ----------------
  setLeds(pixels, imageName = '', text = '') {
    this.leds = pixels.slice(0, 25);
    this.ledImageName = imageName;
    this.ledText = text;
    this.callbacks.onLed?.(this.leds, imageName, text);
  }

  emitBeep(freq, durationMs, volume = 100) {
    this.callbacks.onBeep?.(freq, durationMs, volume);
  }

  setButton(side, pressed) {
    const k = side === 'RIGHT' ? 'RIGHT' : 'LEFT';
    if (pressed) {
      if (this.buttons[k] === null) this.buttons[k] = this.timeMs;
    } else {
      this.buttons[k] = null;
    }
  }

  getButtonPressedMs(side) {
    const k = side === 'RIGHT' ? 'RIGHT' : 'LEFT';
    if (this.buttons[k] === null) return 0;
    return Math.max(1, Math.round(this.timeMs - this.buttons[k]));
  }

  getTiltAnglesDecideg() {
    const relRad = this.chassis.yaw - this.yawOffsetRad;
    let yawD = Math.round(((relRad * 180) / Math.PI) * 10 + this.yawBiasDecideg);
    // Wrap to [-1800, 1800] (official SPIKE 3 range)
    yawD = ((((yawD + 1800) % 3600) + 3600) % 3600) - 1800;
    return [yawD, 0, 0];
  }

  resetYaw(angleDecideg = 0) {
    this.yawOffsetRad = this.chassis.yaw;
    this.yawBiasDecideg = Math.trunc(Number(angleDecideg) || 0);
  }

  // ---------------- 3D World Sensor Raycasting & Sampling ----------------
  _sensorWorldRay(port, fallbackDir = [0, 0, -1]) {
    const meta = this.kinematics?.sensors?.[port];
    const part = meta ? this.partsById[meta.part] : null;
    const localPos = part ? part.pos : [0, 1.5, -2.8];
    const localDir = meta?.dir || fallbackDir;

    // Transform local robot-frame point & direction by chassis pose (x, z, yaw)
    const rotPos = rotateY(localPos, this.chassis.yaw);
    const origin = [rotPos[0] + this.chassis.x, rotPos[1], rotPos[2] + this.chassis.z];
    const dir = rotateY(localDir, this.chassis.yaw);
    const ln = Math.hypot(dir[0], dir[1], dir[2]) || 1;
    return { origin, dir: [dir[0] / ln, dir[1] / ln, dir[2] / ln], part };
  }

  readDistanceMm(port) {
    if (this.manualSensors.distanceAuto) {
      if (!this.hasWorldObstacles) return -1;
      const { origin, dir, part } = this._sensorWorldRay(port, [0, 0, -1]);
      // Offset ray start to front ultrasonic lens (69 LDU = 1.38 scene units ahead of CAD origin)
      const frontOffset = part?.ldraw ? 1.38 : 0.4;
      const start = [
        origin[0] + dir[0] * frontOffset,
        origin[1] + dir[1] * frontOffset,
        origin[2] + dir[2] * frontOffset,
      ];
      let best = Infinity;
      for (const prop of this.floorProps) {
        if (prop.type !== 'box') continue;
        const [cx, cy, cz] = prop.pos;
        const [sx, sy, sz] = prop.size;
        const bmin = [cx - sx / 2, cy - sy / 2, cz - sz / 2];
        const bmax = [cx + sx / 2, cy + sy / 2, cz + sz / 2];
        const hit = rayIntersectAabb(start, dir, bmin, bmax);
        if (hit !== null && hit < best) best = hit;
      }
      if (best < Infinity) {
        const mm = Math.round(best * SCENE_TO_MM);
        return mm <= 2000 ? mm : -1;
      }
      return -1;
    }
    return Math.round(this.manualSensors.distanceCm * 10);
  }

  _sampleFloorPoint(wx, wz) {
    // Check patches and rings sorted by layer descending (top-most wins)
    const candidates = this.floorProps
      .filter((p) => p.type === 'patch' || p.type === 'ring')
      .map((p, idx) => ({ p, layer: p.layer ?? idx }))
      .sort((a, b) => b.layer - a.layer);

    for (const { p } of candidates) {
      if (p.type === 'patch') {
        const halfW = p.size[0] / 2;
        const halfD = p.size[1] / 2;
        if (Math.abs(wx - p.pos[0]) <= halfW && Math.abs(wz - p.pos[2]) <= halfD) {
          return classifyHexColor(p.color, p.spike_color);
        }
      } else if (p.type === 'ring') {
        const dist = Math.hypot(wx - p.pos[0], wz - p.pos[2]);
        if (Math.abs(dist - p.radius) <= p.width / 2) {
          return classifyHexColor(p.color, p.spike_color);
        }
      }
    }
    // Default bright studio floor
    return { name: 'WHITE', ...COLOR_RGB_REFLECTION.WHITE };
  }

  readColorSample(port) {
    if (this.manualSensors.colorAuto && this.hasWorldColorProps) {
      const { origin } = this._sensorWorldRay(port, [0, -1, 0]);
      const center = this._sampleFloorPoint(origin[0], origin[2]);
      // 9-point optical spot disk (radius 0.16 scene units = 3.2 mm) for smooth edge reflection
      const r = 0.16;
      let reflSum = center.refl * 2;
      let wSum = 2;
      for (let k = 0; k < 8; k++) {
        const a = (k * Math.PI) / 4;
        const s = this._sampleFloorPoint(origin[0] + Math.cos(a) * r, origin[2] + Math.sin(a) * r);
        reflSum += s.refl;
        wSum += 1;
      }
      return {
        ...center,
        refl: Math.round(reflSum / wSum),
      };
    }
    const key = String(this.manualSensors.color || 'RED').toUpperCase();
    const entry = COLOR_RGB_REFLECTION[key] || COLOR_RGB_REFLECTION.RED;
    return { name: key, ...entry };
  }

  setForcePressed(pressed, port = null) {
    if (port) {
      this.manualSensors.forceByPort[port] = !!pressed;
    } else {
      this.manualSensors.forcePressed = !!pressed;
    }
    // Notify viewer to animate real LDraw force sensor plunger(s)
    for (const p of Object.values(this.partsById)) {
      if (p.type === 'force_sensor') {
        if (!port || p.port === port) {
          this.callbacks.onPlunger?.(p.id, pressed ? 1.0 : 0.0);
        }
      }
    }
  }

  readForcePressed(port) {
    if (port in this.manualSensors.forceByPort) {
      return !!this.manualSensors.forceByPort[port];
    }
    return !!this.manualSensors.forcePressed;
  }
}
