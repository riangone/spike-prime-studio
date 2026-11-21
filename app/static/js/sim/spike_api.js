/**
 * Official LEGO SPIKE 3 Python Firmware API bindings backed by VirtualWorld.
 *
 * Implements:
 *   hub (port, light_matrix, sound, button, motion_sensor, light),
 *   motor, motor_pair, distance_sensor, color_sensor, color, force_sensor, runloop, time.
 */
import { IMAGE_CONSTANTS, IMAGE_NAMES, getImagePixels, sliceWindow, textToColumns } from './led_font.js';
import { SPIKE_COLORS } from './physics_world.js';
import { PyError, SimCancelledError, nativeFn, pyAwaitable, pyTruthy, pyTuple } from './python_vm.js';

const PORT_LIST = ['A', 'B', 'C', 'D', 'E', 'F'];

function resolvePort(portVal) {
  if (typeof portVal === 'string' && PORT_LIST.includes(portVal.toUpperCase())) {
    return portVal.toUpperCase();
  }
  const idx = Math.trunc(Number(portVal));
  if (idx >= 0 && idx < PORT_LIST.length) return PORT_LIST[idx];
  throw new PyError('ValueError', `invalid port: ${portVal}`);
}

/** Official LEGO SPIKE 3 steering law: steering in [-100, 100] -> wheel forward velocity scales. */
export function steeringScales(steering) {
  const s = Math.max(-100, Math.min(100, Number(steering) || 0));
  if (s >= 0) return { left: 1.0, right: 1.0 - s / 50.0 };
  return { left: 1.0 + s / 50.0, right: 1.0 };
}

export function createSpikeModules(world) {
  // ---------------- hub.port ----------------
  const portMod = { A: 0, B: 1, C: 2, D: 3, E: 4, F: 5 };

  // ---------------- hub.light_matrix ----------------
  const lightMatrixMod = {
    ...IMAGE_CONSTANTS,
    show_image: nativeFn(([imageId]) => {
      const pixels = getImagePixels(imageId);
      const name = IMAGE_NAMES[imageId] || `#${imageId}`;
      world.setLeds(pixels, name, '');
      return null;
    }),
    show: nativeFn(([pixels]) => {
      const arr = Array.from({ length: 25 }, (_, i) => Math.max(0, Math.min(100, Number(pixels?.[i]) || 0)));
      world.setLeds(arr, 'CUSTOM', '');
      return null;
    }),
    set_pixel: nativeFn(([x, y, intensity]) => {
      const ix = Math.trunc(x);
      const iy = Math.trunc(y);
      if (ix >= 0 && ix < 5 && iy >= 0 && iy < 5) {
        const next = world.leds.slice();
        next[iy * 5 + ix] = Math.max(0, Math.min(100, Number(intensity) || 0));
        world.setLeds(next, 'PIXEL', world.ledText);
      }
      return null;
    }),
    get_pixel: nativeFn(([x, y]) => {
      const ix = Math.trunc(x);
      const iy = Math.trunc(y);
      if (ix >= 0 && ix < 5 && iy >= 0 && iy < 5) return world.leds[iy * 5 + ix] || 0;
      return 0;
    }),
    clear: nativeFn(() => {
      world.setLeds(new Array(25).fill(0), '', '');
      return null;
    }),
    write: nativeFn(([text, intensity = 100, timePerChar = 420], kw) => {
      const str = String(text ?? '');
      const bright = kw.intensity ?? intensity;
      const tChar = kw.time_per_character ?? timePerChar;
      const cols = textToColumns(str, bright);
      const stepMs = Math.max(40, Math.round(tChar / 4));
      return pyAwaitable((async () => {
        for (let off = 0; off <= Math.max(0, cols.length - 5); off++) {
          world.setLeds(sliceWindow(cols, off), 'TEXT', str);
          await world.sleepMs(stepMs);
        }
        world.setLeds(new Array(25).fill(0), '', str);
      })());
    }),
  };

  // ---------------- hub.sound ----------------
  const SOUND_MAP = { HELLO: 660, MEOW: 740, CLICK: 1200, HONK: 330 };
  const soundMod = {
    HELLO: 'HELLO',
    MEOW: 'MEOW',
    CLICK: 'CLICK',
    HONK: 'HONK',
    beep: nativeFn(([freq = 440, duration = 500, volume = 100], kw) => {
      const f = Number(kw.freq ?? freq) || 440;
      const d = Math.max(0, Number(kw.duration ?? duration) || 500);
      const v = Number(kw.volume ?? volume) || 100;
      world.emitBeep(f, d, v);
      return pyAwaitable(world.sleepMs(d));
    }),
    play: nativeFn(([soundId = 'HELLO']) => {
      const freq = SOUND_MAP[soundId] || 587;
      world.emitBeep(freq, 220, 90);
      return null;
    }),
    stop: nativeFn(() => null),
  };

  // ---------------- hub.button ----------------
  const buttonMod = {
    LEFT: 0,
    RIGHT: 1,
    pressed: nativeFn(([btn]) => {
      const side = btn === 1 || btn === 'RIGHT' ? 'RIGHT' : 'LEFT';
      return world.getButtonPressedMs(side);
    }),
  };

  // ---------------- hub.motion_sensor ----------------
  const motionSensorMod = {
    tilt_angles: nativeFn(() => pyTuple(world.getTiltAnglesDecideg())),
    reset_yaw: nativeFn(([angle = 0]) => {
      world.resetYaw(angle);
      return null;
    }),
    gesture: nativeFn(() => 0),
  };

  // ---------------- hub.light ----------------
  const lightMod = {
    POWER: 0,
    CONNECT: 1,
    color: nativeFn(() => null),
  };

  // ---------------- motor ----------------
  const motorMod = {
    READY: 0,
    RUNNING: 1,
    STALLED: 2,
    CANCELED: 3,
    ERROR: 4,
    DISCONNECTED: 5,
    COAST: 0,
    BRAKE: 1,
    HOLD: 2,
    CONTINUE: 3,
    SMART_COAST: 4,
    SMART_BRAKE: 5,
    CLOCKWISE: 0,
    COUNTERCLOCKWISE: 1,
    SHORTEST_PATH: 2,
    LONGEST_PATH: 3,

    run: nativeFn(([p, velocity], kw) => {
      const port = resolvePort(p);
      world.motors[port].run(kw.velocity ?? velocity);
      return null;
    }),
    stop: nativeFn(([p]) => {
      const port = resolvePort(p);
      world.motors[port].stop();
      return null;
    }),
    run_for_degrees: nativeFn(([p, degrees, velocity], kw) => {
      const port = resolvePort(p);
      const deg = Number(kw.degrees ?? degrees) || 0;
      const vel = Number(kw.velocity ?? velocity) || 0;
      const m = world.motors[port];
      if (deg === 0 || vel === 0) return pyAwaitable(Promise.resolve(0));
      // Official SPIKE 3: direction is sign(degrees) * sign(velocity)
      const signedDelta = Math.abs(deg) * Math.sign(deg) * Math.sign(vel);
      return pyAwaitable(m.driveTo(m.angle + signedDelta, Math.abs(vel), world));
    }),
    run_for_time: nativeFn(([p, durationMs, velocity], kw) => {
      const port = resolvePort(p);
      const dur = Math.max(0, Number(kw.duration ?? durationMs) || 0);
      const vel = Number(kw.velocity ?? velocity) || 0;
      const m = world.motors[port];
      const delta = (vel * dur) / 1000;
      return pyAwaitable(m.driveTo(m.angle + delta, Math.abs(vel), world));
    }),
    run_to_absolute_position: nativeFn(([p, position, velocity], kw) => {
      const port = resolvePort(p);
      const targetMod = (((Number(kw.position ?? position) || 0) % 360) + 360) % 360;
      const vel = Math.abs(Number(kw.velocity ?? velocity) || 360);
      const direction = kw.direction ?? 2; // SHORTEST_PATH
      const m = world.motors[port];
      const curMod = (((m.angle % 360) + 360) % 360);
      let delta = targetMod - curMod;
      if (direction === 0) { // CLOCKWISE (+)
        if (delta < 0) delta += 360;
      } else if (direction === 1) { // COUNTERCLOCKWISE (-)
        if (delta > 0) delta -= 360;
      } else if (direction === 3) { // LONGEST_PATH
        if (delta >= 0 && delta < 180) delta -= 360;
        else if (delta < 0 && delta > -180) delta += 360;
      } else { // SHORTEST_PATH
        if (delta > 180) delta -= 360;
        if (delta < -180) delta += 360;
      }
      return pyAwaitable(m.driveTo(m.angle + delta, vel, world));
    }),
    run_to_relative_position: nativeFn(([p, position, velocity], kw) => {
      const port = resolvePort(p);
      const relPos = Number(kw.position ?? position) || 0;
      const vel = Math.abs(Number(kw.velocity ?? velocity) || 360);
      const m = world.motors[port];
      return pyAwaitable(m.driveTo(m.relZero + relPos, vel, world));
    }),
    relative_position: nativeFn(([p]) => world.motors[resolvePort(p)].relativePosition()),
    absolute_position: nativeFn(([p]) => world.motors[resolvePort(p)].absolutePosition()),
    reset_relative_position: nativeFn(([p, position = 0]) => {
      const m = world.motors[resolvePort(p)];
      m.relZero = m.angle - (Number(position) || 0);
      return null;
    }),
    velocity: nativeFn(([p]) => Math.round(world.motors[resolvePort(p)].velocity)),
  };

  // ---------------- motor_pair ----------------
  function requirePair(pairId) {
    const pair = world.pairs[pairId];
    if (!pair) throw new PyError('ValueError', `motor_pair ${pairId} is not paired`);
    return pair;
  }

  const motorPairMod = {
    PAIR_1: 0,
    PAIR_2: 1,
    PAIR_3: 2,
    pair: nativeFn(([pairId, leftP, rightP]) => {
      world.pairMotors(pairId, resolvePort(leftP), resolvePort(rightP));
      return null;
    }),
    unpair: nativeFn(([pairId]) => {
      world.unpairMotors(pairId);
      return null;
    }),
    stop: nativeFn(([pairId]) => {
      const pair = world.pairs[pairId];
      if (!pair) return null;
      world.motors[pair.leftPort].stop();
      world.motors[pair.rightPort].stop();
      return null;
    }),
    move: nativeFn(([pairId, steering], kw) => {
      const pair = requirePair(pairId);
      const vel = Number(kw.velocity ?? 360);
      const { left, right } = steeringScales(steering);
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);
      world.motors[pair.leftPort].run(leftSign * vel * left);
      world.motors[pair.rightPort].run(rightSign * vel * right);
      return null;
    }),
    move_tank: nativeFn(([pairId, leftVel, rightVel], kw) => {
      const pair = requirePair(pairId);
      const lv = Number(kw.left_velocity ?? leftVel) || 0;
      const rv = Number(kw.right_velocity ?? rightVel) || 0;
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);
      world.motors[pair.leftPort].run(leftSign * lv);
      world.motors[pair.rightPort].run(rightSign * rv);
      return null;
    }),
    move_for_degrees: nativeFn(([pairId, degrees, steering], kw) => {
      const pair = requirePair(pairId);
      const deg = Number(degrees) || 0;
      const vel = Number(kw.velocity ?? 360);
      if (deg === 0 || vel === 0) return pyAwaitable(Promise.resolve(0));
      const dir = Math.sign(deg) * Math.sign(vel);
      const magDeg = Math.abs(deg);
      const magVel = Math.abs(vel);
      const { left, right } = steeringScales(steering);
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);

      const mL = world.motors[pair.leftPort];
      const mR = world.motors[pair.rightPort];
      const dL = leftSign * dir * magDeg * left;
      const dR = rightSign * dir * magDeg * right;
      const vL = magVel * Math.abs(left);
      const vR = magVel * Math.abs(right);

      const waits = [];
      if (Math.abs(dL) > 1e-4 && vL > 1e-4) waits.push(mL.driveTo(mL.angle + dL, vL, world));
      else mL.stop();
      if (Math.abs(dR) > 1e-4 && vR > 1e-4) waits.push(mR.driveTo(mR.angle + dR, vR, world));
      else mR.stop();
      return pyAwaitable(Promise.all(waits).then(() => 0));
    }),
    move_for_time: nativeFn(([pairId, durationMs, steering], kw) => {
      const pair = requirePair(pairId);
      const dur = Math.max(0, Number(durationMs) || 0);
      const vel = Number(kw.velocity ?? 360);
      const { left, right } = steeringScales(steering);
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);
      const mL = world.motors[pair.leftPort];
      const mR = world.motors[pair.rightPort];
      const dL = (leftSign * vel * left * dur) / 1000;
      const dR = (rightSign * vel * right * dur) / 1000;
      const waits = [];
      if (Math.abs(dL) > 1e-4) waits.push(mL.driveTo(mL.angle + dL, Math.abs(vel * left), world));
      else mL.stop();
      if (Math.abs(dR) > 1e-4) waits.push(mR.driveTo(mR.angle + dR, Math.abs(vel * right), world));
      else mR.stop();
      return pyAwaitable(Promise.all(waits).then(() => 0));
    }),
    move_tank_for_degrees: nativeFn(([pairId, degrees, leftVel, rightVel]) => {
      const pair = requirePair(pairId);
      const lv = Number(leftVel) || 0;
      const rv = Number(rightVel) || 0;
      const maxV = Math.max(Math.abs(lv), Math.abs(rv));
      if (!degrees || maxV < 1e-4) return pyAwaitable(Promise.resolve(0));
      const durSec = Math.abs(degrees) / maxV;
      const sign = Math.sign(degrees);
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);
      const mL = world.motors[pair.leftPort];
      const mR = world.motors[pair.rightPort];
      const dL = leftSign * sign * lv * durSec;
      const dR = rightSign * sign * rv * durSec;
      const waits = [];
      if (Math.abs(dL) > 1e-4) waits.push(mL.driveTo(mL.angle + dL, Math.abs(lv), world));
      else mL.stop();
      if (Math.abs(dR) > 1e-4) waits.push(mR.driveTo(mR.angle + dR, Math.abs(rv), world));
      else mR.stop();
      return pyAwaitable(Promise.all(waits).then(() => 0));
    }),
    move_tank_for_time: nativeFn(([pairId, durationMs, leftVel, rightVel]) => {
      const pair = requirePair(pairId);
      const durSec = Math.max(0, Number(durationMs) || 0) / 1000;
      const lv = Number(leftVel) || 0;
      const rv = Number(rightVel) || 0;
      const { leftSign, rightSign } = world.getPairMotorSigns(pair);
      const mL = world.motors[pair.leftPort];
      const mR = world.motors[pair.rightPort];
      const waits = [];
      if (Math.abs(lv) > 1e-4 && durSec > 0) waits.push(mL.driveTo(mL.angle + leftSign * lv * durSec, Math.abs(lv), world));
      else mL.stop();
      if (Math.abs(rv) > 1e-4 && durSec > 0) waits.push(mR.driveTo(mR.angle + rightSign * rv * durSec, Math.abs(rv), world));
      else mR.stop();
      return pyAwaitable(Promise.all(waits).then(() => 0));
    }),
  };

  // ---------------- Sensors ----------------
  const distanceSensorMod = {
    distance: nativeFn(([p]) => world.readDistanceMm(resolvePort(p))),
    set_pixel: nativeFn(() => null),
    show: nativeFn(() => null),
    clear: nativeFn(() => null),
  };

  const colorSensorMod = {
    color: nativeFn(([p]) => world.readColorSample(resolvePort(p)).id),
    reflection: nativeFn(([p]) => world.readColorSample(resolvePort(p)).refl),
    rgbi: nativeFn(([p]) => {
      const s = world.readColorSample(resolvePort(p));
      return pyTuple([s.rgb[0] * 4, s.rgb[1] * 4, s.rgb[2] * 4, s.refl * 10]);
    }),
  };

  const colorMod = { ...SPIKE_COLORS };

  const forceSensorMod = {
    pressed: nativeFn(([p]) => world.readForcePressed(resolvePort(p))),
    force: nativeFn(([p]) => (world.readForcePressed(resolvePort(p)) ? 50 : 0)),
    raw: nativeFn(([p]) => (world.readForcePressed(resolvePort(p)) ? 512 : 0)),
  };

  // ---------------- runloop & time ----------------
  const runloopMod = {
    sleep_ms: nativeFn(([ms]) => pyAwaitable(world.sleepMs(ms))),
    until: nativeFn(([pred, timeout = 0], _kw, vm) => pyAwaitable((async () => {
      const start = world.timeMs;
      while (!world.cancelled) {
        const ok = await vm.callCallable(pred, [], {});
        if (pyTruthy(ok)) return true;
        if (timeout > 0 && world.timeMs - start >= timeout) return false;
        await world.sleepMs(10);
      }
      throw new SimCancelledError();
    })())),
    run: nativeFn((coros) => {
      const tasks = coros.map((c) => {
        if (c && typeof c.start === 'function') return c.start();
        if (c && typeof c.then === 'function') return c;
        return Promise.resolve(c);
      });
      return Promise.all(tasks);
    }),
  };

  const timeMod = {
    ticks_ms: nativeFn(() => Math.round(world.timeMs)),
    ticks_diff: nativeFn(([a, b]) => a - b),
    sleep: nativeFn(([s]) => world.sleepMs((Number(s) || 0) * 1000)),
    sleep_ms: nativeFn(([ms]) => world.sleepMs(ms)),
  };

  const hubMod = {
    port: portMod,
    light_matrix: lightMatrixMod,
    sound: soundMod,
    button: buttonMod,
    motion_sensor: motionSensorMod,
    light: lightMod,
  };

  return {
    hub: hubMod,
    motor: motorMod,
    motor_pair: motorPairMod,
    distance_sensor: distanceSensorMod,
    color_sensor: colorSensorMod,
    color: colorMod,
    force_sensor: forceSensorMod,
    runloop: runloopMod,
    time: timeMod,
  };
}
