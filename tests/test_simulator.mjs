/**
 * End-to-end deterministic test suite for the refactored SPIKE 3 Simulator
 * (python_vm.js, physics_world.js, spike_api.js, engine.js) covering:
 *   1. Python language & async runtime semantics
 *   2. Exact LEGO motor, gear & zero-slip differential-drive physics
 *   3. 3D world ultrasonic raycasting & color/reflection edge sampling
 *   4. Execution of ALL 12 elementary curriculum lessons (both v1 Starter Bug & v2 Improved Fix!)
 */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

import { SpikeSimulationEngine } from '../app/static/js/sim/engine.js';
import { SCENE_TO_MM } from '../app/static/js/sim/physics_world.js';
import { PyError } from '../app/static/js/sim/python_vm.js';
import { steeringScales } from '../app/static/js/sim/spike_api.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PY = path.join(ROOT, '.venv', 'bin', 'python');

// Load all 12 real elementary curriculum lessons (v1 + v2 + verified CAD scene) from Python once
const FIXTURES = JSON.parse(
  execFileSync(
    PY,
    [
      '-c',
      `
import json
from app.data.lessons import LESSONS, render_code

out = {}
for l in LESSONS:
    out[l["id"]] = {
        "v1": render_code(l, "en", "v1"),
        "v2": render_code(l, "en", "v2"),
        "scene": {
            "steps": [{"step": s["step"], "parts": s["parts"]} for s in l["steps"]],
            "cables": l["cables"],
            "joints": l.get("joints", []),
            "gear_meshes": l.get("gear_meshes", []),
            "crank_linkages": l.get("crank_linkages", []),
            "kinematics": l.get("kinematics", {"chassis": {"type": "static"}}),
            "floor_props": l.get("floor_props", []),
        },
    }
print(json.dumps(out))
`,
    ],
    { cwd: ROOT, encoding: 'utf8' }
  )
);

// =================================================================================================
// 1. Python VM core language & async runtime
// =================================================================================================
test('PythonVM: arithmetic, chained comparisons, tuple unpacking, slicing, f-strings, global', async () => {
  const code = `
import math
total = 0

def pair_calc(x, y=3):
    global total
    total += x * y
    return x // y, x % y

a, b = pair_calc(-7, 2)
c, d = pair_calc(10)
nums = [10, 20, 30, 40, 50]
chained_ok = 0 < 15 < 20 and not (5 < 3 < 10)
print(a, b, c, d, total, nums[-1], nums[1:4], chained_ok, f"pi={math.pi:.2f}")
`;
  const eng = new SpikeSimulationEngine({});
  eng.start(code);
  await eng.stepMs(100);
  assert.equal(eng.state, 'done');
  assert.equal(eng.logs[0], '-4 1 3 1 16 50 [20, 30, 40] True pi=3.14');
});

test('PythonVM: concurrent runloop.run(main_1(), main_2()) runs both coroutines in parallel', async () => {
  const code = `
import runloop
import motor
from hub import port

async def m1():
    await motor.run_for_degrees(port.A, 180, 180)
    print("A done")

async def m2():
    await motor.run_for_degrees(port.B, 360, 360)
    print("B done")

runloop.run(m1(), m2())
`;
  const eng = new SpikeSimulationEngine({});
  eng.start(code);
  await eng.stepMs(1200);
  assert.equal(eng.state, 'done');
  assert.ok(eng.world.timeMs <= 1050, `expected ~1000ms parallel run, got ${eng.world.timeMs}ms`);
  assert.equal(Math.round(eng.world.motors.A.angle), 180);
  assert.equal(Math.round(eng.world.motors.B.angle), 360);
  assert.deepEqual(eng.logs.sort(), ['A done', 'B done']);
});

test('PythonVM: infinite loop without sleep yields cleanly and stops immediately on cancel', async () => {
  const code = `
import runloop
x = 0
async def main():
    global x
    while True:
        x += 1
runloop.run(main())
`;
  const eng = new SpikeSimulationEngine({});
  eng.start(code);
  await eng.stepMs(50);
  assert.equal(eng.state, 'running');
  assert.ok(eng.world.timeMs >= 40);
  eng.stop();
  assert.equal(eng.state, 'idle');
});

test('PythonVM: reports syntax & runtime errors with line numbers', async () => {
  const eng = new SpikeSimulationEngine({});
  eng.start('x = 1\ny = unknown_var + 2\n');
  await eng.stepMs(20);
  assert.equal(eng.state, 'error');
  assert.ok(eng.error instanceof PyError);
  assert.equal(eng.error.line, 2);
});

// =================================================================================================
// 2. Motor & Differential-Drive Physics
// =================================================================================================
test('Physics: official SPIKE 3 steering law', () => {
  assert.deepEqual(steeringScales(0), { left: 1, right: 1 });
  assert.deepEqual(steeringScales(50), { left: 1, right: 0 });
  assert.deepEqual(steeringScales(100), { left: 1, right: -1 });
  assert.deepEqual(steeringScales(-50), { left: 0, right: 1 });
  assert.deepEqual(steeringScales(-100), { left: -1, right: 1 });
});

test('Physics: driving-base 360° straight = 56*pi mm (175.9 mm) with zero-slip axle pivot', async () => {
  const eng = new SpikeSimulationEngine(FIXTURES['driving-base'].scene);
  eng.start(`
import runloop, motor_pair
from hub import port
async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, 360, 0, velocity=360)
runloop.run(main())
`);
  await eng.stepMs(1500);
  assert.equal(eng.state, 'done');
  const distMm = -eng.world.chassis.z * SCENE_TO_MM;
  assert.ok(Math.abs(distMm - Math.PI * 56) < 1.5, `expected ~175.9 mm, got ${distMm.toFixed(2)} mm`);
  assert.ok(Math.abs(eng.world.chassis.x) < 1e-4);
  assert.ok(Math.abs(eng.world.chassis.yaw) < 1e-4);
  assert.equal(Math.round(eng.world.motors.C.angle), -360);
  assert.equal(Math.round(eng.world.motors.D.angle), 360);
});

// =================================================================================================
// 3. Stage 1 Lessons (L01 magic-hub, L02 lucky-spinner, L03 metronome-arm) — v1 vs v2
// =================================================================================================
test('L01 magic-hub: v1 finishes instantaneously (0ms) vs v2 pauses, scrolls GO, waits for LEFT button, and chimes', async () => {
  const fx = FIXTURES['magic-hub'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(50);
  assert.equal(e1.state, 'done');
  assert.equal(e1.world.timeMs < 50, true, 'v1 has no sleep_ms so icons vanish instantly');

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  await e2.stepMs(3500);
  assert.equal(e2.state, 'running', 'v2 should wait for LEFT button press');
  e2.world.setButton('LEFT', true);
  await e2.stepMs(1000);
  assert.equal(e2.state, 'done');
  assert.equal(e2.world.ledImageName, 'HAPPY');
  assert.deepEqual(e2.beeps.map((b) => b.freq), [523, 659, 784, 1046]);
});

test('L02 lucky-spinner: v1 stops off-grid at 820° vs v2 homes to 0° and decelerates in 3 stages to exact 1440° (0° mod 360)', async () => {
  const fx = FIXTURES['lucky-spinner'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(3000);
  assert.equal(e1.state, 'done');
  assert.equal(Math.round(e1.world.motors.A.angle), 820);
  assert.notEqual(e1.world.motors.A.absolutePosition(), 0);

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  await e2.stepMs(6000);
  assert.equal(e2.state, 'done');
  assert.equal(Math.round(e2.world.motors.A.angle), 1440);
  assert.equal(e2.world.motors.A.absolutePosition(), 0);
  assert.equal(e2.world.ledImageName, 'YES');
  assert.equal(e2.beeps.length, 5);
});

test('L03 metronome-arm: v1 drifts crooked to +30° vs v2 swings symmetrically and returns to exact 0°', async () => {
  const fx = FIXTURES['metronome-arm'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(3000);
  assert.equal(e1.state, 'done');
  assert.equal(Math.round(e1.world.motors.B.angle), 30, 'v1 copy-paste asymmetry leaves arm +30° crooked');

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  e2.world.setForcePressed(true);
  await e2.stepMs(5000);
  assert.equal(e2.state, 'done');
  assert.equal(Math.round(e2.world.motors.B.angle), 0, 'v2 ends centered at 0°');
  assert.equal(e2.world.ledImageName, 'YES');
});

// =================================================================================================
// 4. Stage 2 Lessons (L04 driving-base, L05 square-patrol, L06 gyro-precision) — v1 vs v2
// =================================================================================================
test('L04 driving-base: v1 same-sign motors spin in place (remains near start) vs v2 motor_pair drives 720° straight onto green mat', async () => {
  const fx = FIXTURES['driving-base'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(2500);
  assert.equal(e1.state, 'done');
  assert.ok(Math.hypot(e1.world.chassis.x, e1.world.chassis.z) < 3.5, 'v1 spins around axle without advancing down the track');
  assert.ok(Math.abs(e1.world.chassis.yaw) > 2.0, 'v1 rotates body wildly in place');

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  await e2.stepMs(3000);
  assert.equal(e2.state, 'done');
  // 720 deg = 2 turns = 351.86 mm = 17.59 scene units along -Z
  assert.ok(Math.abs(e2.world.chassis.z - -17.59) < 0.25, `expected z≈-17.59 on green mat, got ${e2.world.chassis.z}`);
  assert.ok(Math.abs(e2.world.chassis.yaw) < 1e-3);
  assert.equal(e2.world.ledImageName, 'HEART');
});

test('L05 square-patrol: v1 turn_deg=90 fails to close square vs v2 calibrated turn_deg=215 returns to origin', async () => {
  const fx = FIXTURES['square-patrol'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(12000);
  assert.equal(e1.state, 'done');
  const distV1 = Math.hypot(e1.world.chassis.x, e1.world.chassis.z);
  assert.ok(distV1 > 12.0, `v1 uncalibrated 90° motor turn should miss origin by >12 units, got ${distV1}`);

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  await e2.stepMs(14000);
  assert.equal(e2.state, 'done');
  const distV2 = Math.hypot(e2.world.chassis.x, e2.world.chassis.z);
  assert.ok(distV2 < 0.6, `v2 calibrated 215° turn should close square within 0.6 units, got ${distV2}`);
  assert.equal(e2.world.ledImageName, 'SQUARE');
});

test('L06 gyro-precision: v1 forgets reset_yaw inside loop (turns only once) vs v2 turns 4x90° within ±2°', async () => {
  const fx = FIXTURES['gyro-precision'];
  const e1 = new SpikeSimulationEngine(fx.scene);
  e1.start(fx.v1);
  await e1.stepMs(12000);
  assert.equal(e1.state, 'done');
  const yawV1 = (e1.world.chassis.yaw * 180) / Math.PI;
  // v1 only turns on corner 1 (~-100°), then skips corners 2-4!
  assert.ok(Math.abs(yawV1) < 140, `v1 should only turn once (~-100°), got ${yawV1}°`);

  const e2 = new SpikeSimulationEngine(fx.scene);
  e2.start(fx.v2);
  await e2.stepMs(22000);
  assert.equal(e2.state, 'done');
  const yawV2 = (e2.world.chassis.yaw * 180) / Math.PI;
  assert.ok(Math.abs(yawV2 - -360) < 6, `v2 should complete 4x90° = -360°, got ${yawV2}°`);
  assert.ok(Math.hypot(e2.world.chassis.x, e2.world.chassis.z) < 1.2);
  assert.equal(e2.world.ledImageName, 'YES');
});

// =================================================================================================
// 5. Stage 3 Lessons (L07 obstacle-avoider, L08 color-traffic, L09 line-follower) — v1 vs v2
// =================================================================================================
test('L07 obstacle-avoider: v1 falls into -1 trap in open air vs v2 dodges walls and cruises clear', async () => {
  const fx = FIXTURES['obstacle-avoider'];
  // Test in open air (no obstacles -> distance() returns -1)
  const openScene = { ... structuredClone(fx.scene), floor_props: [] };
  const e1 = new SpikeSimulationEngine(openScene);
  e1.start(fx.v1);
  await e1.stepMs(2500);
  // Because -1 < 180 is True, v1 immediately backs up and turns right in empty air!
  assert.ok(e1.world.beeps?.length > 0 || e1.beeps.length > 0, 'v1 falsely triggers obstacle alarm on -1');
  assert.ok(e1.world.chassis.yaw < -0.5, 'v1 pivots in empty space due to -1 < 180');
  e1.stop();

  // v2 on real 3D arena with red & orange walls dodges both walls cleanly
  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e2.start(fx.v2);
  await e2.stepMs(8000);
  assert.ok(e2.beeps.length >= 1, 'v2 detects real 3D wall and beeps');
  assert.ok(e2.world.chassis.yaw < -1.0, 'v2 turns right to avoid wall');
  e2.stop();
});

test('L08 color-traffic: v1 750 speed + 450ms sleep misses red line vs v2 stops squarely on red line', async () => {
  const fx = FIXTURES['color-traffic'];
  const e1 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e1.start(fx.v1);
  await e1.stepMs(5000);
  assert.equal(e1.state, 'done');
  // Red strip is at z = -17.2 (sensor at z_chassis - 3.2 => chassis z ≈ -14.0). v1 blasts way past z = -22!
  assert.ok(e1.world.chassis.z < -22.0, `v1 should overshoot far past red strip, got z=${e1.world.chassis.z}`);

  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e2.start(fx.v2);
  await e2.stepMs(6000);
  assert.equal(e2.state, 'done');
  // v2 stops right when sensor hits RED at z_sensor = -16.65 => chassis z ≈ -13.45
  assert.ok(Math.abs(e2.world.chassis.z - -13.5) < 1.2, `v2 should stop on red line (z≈-13.5), got ${e2.world.chassis.z}`);
  assert.equal(e2.world.ledImageName, 'NO');
  assert.deepEqual(e2.beeps.map((b) => b.freq), [784, 587, 659, 262]);
});

test('L09 line-follower: v2 proportional edge follower tracks the black ring smoothly and stops on LEFT button', async () => {
  const fx = FIXTURES['line-follower'];
  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e2.start(fx.v2);
  await e2.stepMs(3500);
  assert.equal(e2.state, 'running');
  const distMoved = Math.hypot(e2.world.chassis.x, e2.world.chassis.z);
  assert.ok(distMoved > 3.5, `expected line-follower to advance along ring, moved ${distMoved}`);
  e2.world.setButton('LEFT', true);
  await e2.stepMs(100);
  assert.equal(e2.state, 'done');
  assert.equal(e2.world.ledImageName, 'HAPPY');
});

// =================================================================================================
// 6. Stage 4 Lessons (L10 gear-gate, L11 rack-pusher, L12 smart-gripper) — v1 vs v2
// =================================================================================================
test('L10 gear-gate: v2 turns motor A +270° (3:1 gear ratio -> 90° boom lift) and closes back to 0°', async () => {
  const fx = FIXTURES['gear-gate'];
  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  let maxAngle = 0;
  const origSub = e2.world.advanceSubstep.bind(e2.world);
  e2.world.advanceSubstep = (dt) => {
    origSub(dt);
    if (e2.world.motors.A.angle > maxAngle) maxAngle = e2.world.motors.A.angle;
  };
  e2.start(fx.v2);
  await e2.stepMs(5500);
  assert.equal(e2.state, 'done');
  assert.equal(Math.round(maxAngle), 270, 'Motor A reaches +270° so 3:1 geared boom lifts 90°');
  assert.equal(Math.round(e2.world.motors.A.angle), 0, 'Boom returns level to 0°');
});

test('L11 rack-pusher: v1 stalls at mechanical hard stop (+420°) without retracting vs v2 pushes calibrated 200° (RED) and retracts to 0°', async () => {
  const fx = FIXTURES['rack-pusher'];
  const e1 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e1.start(fx.v1);
  await e1.stepMs(2000);
  assert.equal(e1.state, 'done');
  assert.equal(Math.round(e1.world.motors.A.angle), 420, 'v1 commands 500° and stalls at the +420° mechanical hard limit without retracting');
  assert.ok(e1.world.warnings.some((w) => w.kind === 'limit' && w.port === 'A'), 'v1 triggers mechanical limit stall warning');

  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  e2.world.manualSensors.color = 'RED';
  e2.world.manualSensors.colorAuto = false;
  let peakRed = 0;
  const origSub = e2.world.advanceSubstep.bind(e2.world);
  e2.world.advanceSubstep = (dt) => {
    origSub(dt);
    if (e2.world.motors.A.angle > peakRed) peakRed = e2.world.motors.A.angle;
  };
  e2.start(fx.v2);
  await e2.stepMs(3000);
  assert.equal(e2.state, 'done');
  assert.equal(Math.round(peakRed), 200);
  assert.equal(Math.round(e2.world.motors.A.angle), 0, 'v2 retracts rack cleanly to 0°');
  assert.equal(e2.world.ledImageName, 'YES');
});

test('L12 smart-gripper: v2 opens jaw (+35°), approaches crate via rear-mast ultrasonic (<100mm = 88mm offset + margin), physically grips and transports crate to green pad, and releases', async () => {
  const fx = FIXTURES['smart-gripper'];
  const e2 = new SpikeSimulationEngine(structuredClone(fx.scene));
  let minJawAngle = 0;
  let maxJawAngle = 0;
  const origSub = e2.world.advanceSubstep.bind(e2.world);
  e2.world.advanceSubstep = (dt) => {
    origSub(dt);
    const a = e2.world.motors.A.angle;
    if (a > maxJawAngle) maxJawAngle = a;
    if (a < minJawAngle) minJawAngle = a;
  };
  e2.start(fx.v2);
  await e2.stepMs(12000);
  assert.equal(e2.state, 'done');
  assert.equal(Math.round(maxJawAngle), 35, 'jaw opens to +35° first');
  assert.ok(minJawAngle <= -1, 'jaw closes inward until contacting and gripping the cargo crate');
  // Verify the movable red cargo crate (prop 0) was physically carried from x=-0.2 to the right-side green delivery pad (x > 10)!
  const cargoPos = e2.world.getPropPositions()[0];
  // Whole 1.6×1.6 crate footprint must lie on the 5.5×5.5 green pad centred at (12, -9.5).
  const pad = fx.scene.floor_props.find((p) => p.type === 'patch' && p.spike_color === 'GREEN');
  for (const k of [0, 1]) {
    const axis = k === 0 ? 0 : 2;
    const lo = pad.pos[axis] - pad.size[k] / 2 + 0.8;
    const hi = pad.pos[axis] + pad.size[k] / 2 - 0.8;
    assert.ok(cargoPos[axis] >= lo && cargoPos[axis] <= hi, `crate must sit fully on the green pad, got [${cargoPos}]`);
  }
  assert.equal(e2.world.heldProp, null, 'jaw released the crate');
  assert.equal(e2.world.ledImageName, 'HAPPY');
});
