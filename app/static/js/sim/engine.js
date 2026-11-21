/**
 * Headless-capable SPIKE 3 Simulation Engine combining PythonVM + VirtualWorld + SPIKE 3 API.
 * Runs identically in Node.js (deterministic tests) and in the browser (driven by simulator.js).
 */
import { FIXED_STEP_MS, VirtualWorld } from './physics_world.js';
import { PyError, PythonVM, SimCancelledError } from './python_vm.js';
import { createSpikeModules } from './spike_api.js';

// Zero-delay macrotask yield that completely drains the JS microtask queue
// (unthrottled in both Node.js via setImmediate and browsers via MessageChannel).
const flushMicrotasks = (() => {
  if (typeof setImmediate === 'function') {
    return () => new Promise((resolve) => setImmediate(resolve));
  }
  if (typeof MessageChannel === 'function') {
    const ch = new MessageChannel();
    const queue = [];
    ch.port1.onmessage = () => {
      const fn = queue.shift();
      if (fn) fn();
    };
    return () => new Promise((resolve) => {
      queue.push(resolve);
      ch.port2.postMessage(null);
    });
  }
  return () => new Promise((resolve) => setTimeout(resolve, 0));
})();

export class SpikeSimulationEngine {
  constructor(sceneData, callbacks = {}) {
    this.callbacks = callbacks;
    this.world = new VirtualWorld(sceneData, {
      onBeep: (f, d, v) => callbacks.onBeep?.(f, d, v),
      onLed: (leds, img, text) => callbacks.onLed?.(leds, img, text),
      onPlunger: (partId, pressed01) => callbacks.onPlunger?.(partId, pressed01),
      onWarning: (w) => callbacks.onWarning?.(w),
    });
    this.modules = createSpikeModules(this.world);
    this.logs = [];
    this.beeps = [];
    this.currentLine = 0;
    this.state = 'idle'; // 'idle' | 'running' | 'paused' | 'done' | 'error'
    this.error = null;
    this._runPromise = null;
    this._accumMs = 0;

    // Wrap beep callback so headless tests can also inspect played tones
    const origBeep = this.world.callbacks.onBeep;
    this.world.callbacks.onBeep = (f, d, v) => {
      this.beeps.push({ t: this.world.timeMs, freq: f, durationMs: d, volume: v });
      origBeep?.(f, d, v);
    };

    this.vm = new PythonVM({
      modules: this.modules,
      onPrint: (line) => {
        this.logs.push(line);
        callbacks.onPrint?.(line);
      },
      onLine: (ln) => {
        this.currentLine = ln;
        callbacks.onLine?.(ln);
      },
      yieldTick: () => this.world.sleepMs(FIXED_STEP_MS),
      isCancelled: () => this.world.cancelled,
    });
  }

  /** Start executing Python source code asynchronously on the virtual clock. */
  start(source) {
    this.state = 'running';
    this.error = null;
    this._accumMs = 0;
    this._runPromise = this.vm
      .run(source)
      .then(() => {
        if (!this.world.cancelled && this.state === 'running') {
          this.state = 'done';
          this.callbacks.onDone?.();
        }
      })
      .catch((err) => {
        if (err instanceof SimCancelledError || this.world.cancelled) return;
        this.state = 'error';
        this.error = err;
        this.callbacks.onError?.(err);
      });
    return this._runPromise;
  }

  /**
   * Advance the simulation by `dtMs` virtual milliseconds in deterministic 10 ms substeps,
   * flushing microtasks after each substep so awaiting Python coroutines stay lock-stepped.
   */
  async stepMs(dtMs) {
    if (this.state !== 'running') return;
    this._accumMs += dtMs;
    // Drain all microtasks so synchronous setup & initial commands run before first physics tick
    await flushMicrotasks();
    while (this._accumMs >= FIXED_STEP_MS && this.state === 'running') {
      this._accumMs -= FIXED_STEP_MS;
      this.world.advanceSubstep(FIXED_STEP_MS);
      await flushMicrotasks();
    }
  }

  pause() {
    if (this.state === 'running') this.state = 'paused';
  }

  resume() {
    if (this.state === 'paused') this.state = 'running';
  }

  stop() {
    this.world.cancel();
    if (this.state === 'running' || this.state === 'paused') {
      this.state = 'idle';
    }
  }

  getSnapshot() {
    const w = this.world;
    return {
      state: this.state,
      timeMs: w.timeMs,
      line: this.currentLine,
      chassis: { ...w.chassis },
      motorAngles: w.getMotorAngles(),
      motorVelocities: Object.fromEntries(Object.entries(w.motors).map(([k, m]) => [k, Math.round(m.velocity)])),
      yawDeg: Math.round(w.getTiltAnglesDecideg()[0] / 10),
      leds: w.leds.slice(),
      ledImageName: w.ledImageName,
      ledText: w.ledText,
      props: w.getPropPositions(),
      heldProp: w.heldProp ? w.floorProps.indexOf(w.heldProp.prop) : -1,
      warnings: w.warnings.slice(),
      error: this.error ? this.error.message : null,
    };
  }
}

export { PyError, SimCancelledError };
