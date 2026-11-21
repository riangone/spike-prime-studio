/**
 * SPIKE Prime Studio — Live 3D Simulator Controller (Browser UI Bridge).
 *
 * Executes REAL SPIKE 3 Python programs (from the Python Code tab or live Scratch/Blockly blocks)
 * through SpikeSimulationEngine (PythonVM + VirtualWorld + official SPIKE 3 APIs) and feeds
 * exact motor angles, chassis poses, LED matrix pixels, plungers, and audio to Spike3DViewer.
 *
 * Zero hardcoded per-lesson fake animations: every movement is driven strictly by executed code
 * and the lesson's physical CAD kinematics.
 */
import { SpikeSimulationEngine } from './sim/engine.js';

const SPEEDS = [0.5, 1, 2];

// Physical events from the virtual world (see sim/physics_world.js) explained in the page language.
const WARNING_TEXT = {
  limit: {
    zh: (w) => `⚠ ${w.port} 口机构撞到机械极限（${Math.round(w.angle)}°），真机会卡住堵转，电机停在这里。`,
    en: (w) => `⚠ Port ${w.port} mechanism hit its mechanical limit (${Math.round(w.angle)}°): a real robot jams and the motor stalls here.`,
    ja: (w) => `⚠ ポート${w.port}の機構が限界（${Math.round(w.angle)}°）に当たりました。実機でも引っかかってモーターが止まります。`,
  },
  bump: {
    zh: () => '⚠ 机器人撞上了障碍物，车轮在原地打滑！',
    en: () => '⚠ The robot ran into an obstacle and its wheels are slipping!',
    ja: () => '⚠ ロボットが障害物にぶつかり、タイヤが空回りしています！',
  },
  grip: {
    zh: (w) => `✋ 夹爪夹住了货物（${w.port} 口电机顶住货物后停转）。`,
    en: (w) => `✋ The gripper is holding the cargo (motor ${w.port} stalls against it).`,
    ja: (w) => `✋ グリッパーが荷物をつかみました（モーター${w.port}が荷物に当たって停止）。`,
  },
};

function describeWarning(w) {
  const lang = (document.documentElement.lang || 'zh').slice(0, 2);
  const t = WARNING_TEXT[w.kind];
  if (!t) return `⚠ ${w.kind}`;
  return (t[lang] || t.en)(w);
}

class SpikeSimulatorUI {
  constructor() {
    this.engine = null;
    this.running = false;
    this.paused = false;
    this.muted = false;
    this.speedIdx = 1; // 1x
    this.codeSource = 'auto'; // 'auto' | 'python' | 'blocks'
    this.rafId = null;
    this.lastTs = 0;
    this.audioCtx = null;
    this._ticking = false;
    this._highlightedPre = null;

    // Persistent manual sensor UI state (applied immediately to active engine.world)
    this.uiSensors = {
      distanceCm: 45,
      distanceAuto: true,
      color: 'RED',
      colorAuto: true,
      forcePressed: false,
      btnLeft: false,
      btnRight: false,
    };

    this._initMiniLedGrid();
    this._bindEvents();
  }

  get speedScale() {
    return SPEEDS[this.speedIdx];
  }

  _initMiniLedGrid() {
    const host = document.getElementById('sim-led-mini');
    if (!host || host.children.length === 25) return;
    host.innerHTML = '';
    for (let i = 0; i < 25; i++) {
      const dot = document.createElement('span');
      dot.className = 'w-1.5 h-1.5 rounded-[1px] bg-slate-800 transition-colors duration-75';
      host.appendChild(dot);
    }
  }

  _renderMiniLed(pixels) {
    this._initMiniLedGrid();
    const host = document.getElementById('sim-led-mini');
    if (!host) return;
    for (let i = 0; i < 25; i++) {
      const v = pixels ? pixels[i] || 0 : 0;
      const dot = host.children[i];
      if (!dot) continue;
      if (v > 0) {
        const a = Math.max(0.35, Math.min(1, v / 100));
        dot.style.backgroundColor = `rgba(251, 191, 36, ${a})`;
        dot.style.boxShadow = `0 0 3px rgba(251, 191, 36, ${a * 0.8})`;
      } else {
        dot.style.backgroundColor = '';
        dot.style.boxShadow = '';
      }
    }
  }

  beep(freq = 660, durationMs = 120, volume = 100) {
    if (this.muted) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      if (!this.audioCtx) this.audioCtx = new AudioCtx();
      if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      const durSec = Math.max(0.04, Math.min(1.5, durationMs / 1000 / this.speedScale));
      const amp = 0.07 * Math.max(0.1, Math.min(1, volume / 100));
      osc.type = 'sine';
      osc.frequency.value = Math.max(80, Math.min(4000, freq));
      gain.gain.setValueAtTime(amp, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0008, this.audioCtx.currentTime + durSec);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + durSec);
    } catch (_) {}
  }

  setStatus(text, isError = false) {
    const el = document.getElementById('sim-status-text');
    if (!el) return;
    el.textContent = text;
    el.classList.toggle('text-error', isError);
    el.classList.toggle('font-bold', isError);
  }

  appendConsole(line, isError = false) {
    const out = document.getElementById('sim-console-log');
    const wrap = document.getElementById('sim-console-wrap');
    if (!out) return;
    if (wrap) wrap.classList.remove('hidden');
    const row = document.createElement('div');
    row.textContent = line;
    if (isError) row.className = 'text-error';
    out.appendChild(row);
    while (out.children.length > 80) out.removeChild(out.firstChild);
    out.scrollTop = out.scrollHeight;
  }

  clearConsole() {
    const out = document.getElementById('sim-console-log');
    const wrap = document.getElementById('sim-console-wrap');
    if (out) out.innerHTML = '';
    if (wrap) wrap.classList.add('hidden');
  }

  highlightLine(lineNo) {
    if (this._highlightedPre) {
      this._highlightedPre.classList.remove('bg-warning/20', 'text-warning-content');
      this._highlightedPre = null;
    }
    if (!lineNo) return;
    const pre = document.querySelector(`#tab-panel-code pre[data-prefix="${lineNo}"]`);
    if (pre) {
      pre.classList.add('bg-warning/20');
      this._highlightedPre = pre;
    }
  }

  async resolveProgramSource() {
    const activeTab = window.SpikeTabs?.active || 'build';
    const useBlocks = this.codeSource === 'blocks' || (this.codeSource === 'auto' && activeTab === 'blocks');
    if (useBlocks && window.SpikeBlocks?.getPython) {
      try {
        const code = await window.SpikeBlocks.getPython();
        if (code && code.trim()) return { code, label: 'Blocks' };
      } catch (err) {
        console.warn('Failed to get block Python, falling back to lesson code', err);
      }
    }
    const codeEl = document.getElementById('spike-python-code');
    return { code: codeEl ? codeEl.textContent : '', label: 'Python' };
  }

  async start() {
    const viewer = window.SpikeViewer;
    if (!viewer) return;
    if (this.paused && this.engine) {
      this.resume();
      return;
    }
    this.stop(false);
    this.clearConsole();

    const { code, label } = await this.resolveProgramSource();
    if (!code.trim()) {
      this.setStatus('No Python code to run', true);
      return;
    }

    viewer.showAllForSim();
    viewer.clearTrail();

    this.engine = new SpikeSimulationEngine(viewer.sceneData || {}, {
      onBeep: (freq, dur, vol) => this.beep(freq, dur, vol),
      onLed: (pixels) => {
        viewer.setLedMatrix(pixels);
        this._renderMiniLed(pixels);
      },
      onPlunger: (partId, pressed01) => viewer.setPlunger(partId, pressed01),
      onPrint: (msg) => this.appendConsole(msg, false),
      onWarning: (w) => this.appendConsole(describeWarning(w), true),
      onLine: (ln) => this.highlightLine(ln),
      onDone: () => {
        this.running = false;
        this.paused = false;
        if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
        this.highlightLine(0);
        this._syncFrameToViewer(viewer);
        this._updateUi();
        const t = ((this.engine?.world.timeMs || 0) / 1000).toFixed(1);
        this.setStatus(`✓ Done (${t}s · ${label})`);
      },
      onError: (err) => {
        this.running = false;
        this.paused = false;
        if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
        this.appendConsole(err.message, true);
        this._updateUi();
        this.setStatus(`⚠ ${err.message}`, true);
      },
    });

    // Apply current sensor UI state into the newly created virtual world
    const w = this.engine.world;
    w.manualSensors.distanceCm = this.uiSensors.distanceCm;
    w.manualSensors.distanceAuto = this.uiSensors.distanceAuto;
    w.manualSensors.color = this.uiSensors.color;
    w.manualSensors.colorAuto = this.uiSensors.colorAuto;
    w.setForcePressed(this.uiSensors.forcePressed);
    w.setButton('LEFT', this.uiSensors.btnLeft);
    w.setButton('RIGHT', this.uiSensors.btnRight);

    this.running = true;
    this.paused = false;
    this._updateUi();
    this._updateSensorModeBadges();
    this.setStatus(`▶ ${label} · 0.0s`);

    this.engine.start(code);
    this.lastTs = performance.now();
    this._scheduleLoop(viewer, label);
  }

  pause() {
    if (!this.running || !this.engine) return;
    this.paused = true;
    this.engine.pause();
    if (this.rafId) { cancelAnimationFrame(this.rafId); this.rafId = null; }
    this._updateUi();
    const t = ((this.engine.world.timeMs || 0) / 1000).toFixed(1);
    this.setStatus(`⏸ Paused (${t}s)`);
  }

  resume() {
    const viewer = window.SpikeViewer;
    if (!this.paused || !this.engine || !viewer) return;
    this.paused = false;
    this.engine.resume();
    this._updateUi();
    this.lastTs = performance.now();
    this._scheduleLoop(viewer, 'Python');
  }

  stop(resetScene = false) {
    this.running = false;
    this.paused = false;
    if (this.rafId) {
      cancelAnimationFrame(this.rafId);
      this.rafId = null;
    }
    if (this.engine) {
      this.engine.stop();
      if (resetScene) this.engine = null;
    }
    this.highlightLine(0);
    const viewer = window.SpikeViewer;
    if (viewer) {
      if (resetScene) {
        viewer.resetSim();
        this._renderMiniLed(new Array(25).fill(0));
        this.clearConsole();
        const tel = document.getElementById('sim-telemetry');
        if (tel) tel.textContent = '';
      } else {
        viewer.simActive = false;
      }
    }
    this._updateUi();
    this.setStatus(resetScene ? '↺ Reset' : '⏹ Stopped');
  }

  _scheduleLoop(viewer, label) {
    const loop = async (ts) => {
      if (!this.running || this.paused || !this.engine) return;
      if (this._ticking) {
        this.rafId = requestAnimationFrame(loop);
        return;
      }
      this._ticking = true;
      try {
        const dtRealMs = Math.min(ts - this.lastTs, 80);
        this.lastTs = ts;
        await this.engine.stepMs(dtRealMs * this.speedScale);
        if (this.engine) {
          this._syncFrameToViewer(viewer);
          if (this.running) {
            const snap = this.engine.getSnapshot();
            const t = (snap.timeMs / 1000).toFixed(1);
            const banner = snap.ledText ? ` · "${snap.ledText}"` : (snap.ledImageName ? ` · ${snap.ledImageName}` : '');
            this.setStatus(`▶ ${label} · ${t}s${banner}`);
          }
        }
      } finally {
        this._ticking = false;
      }
      if (this.running && !this.paused) {
        this.rafId = requestAnimationFrame(loop);
      }
    };
    this.rafId = requestAnimationFrame(loop);
  }

  _syncFrameToViewer(viewer) {
    if (!this.engine) return;
    const snap = this.engine.getSnapshot();
    viewer.setMotorAngles(snap.motorAngles);
    viewer.setChassisPose(snap.chassis.x, snap.chassis.z, snap.chassis.yaw);
    viewer.setPropPositions?.(snap.props);
    if (this.engine.world.kinematics?.chassis?.type !== 'static') {
      viewer.appendTrailPoint(snap.chassis.x, snap.chassis.z);
    }
    this._renderTelemetry(snap);
  }

  _renderTelemetry(snap) {
    const el = document.getElementById('sim-telemetry');
    if (!el || !this.engine) return;
    const parts = [];
    for (const [port, ang] of Object.entries(snap.motorAngles)) {
      const vel = snap.motorVelocities[port] || 0;
      if (Math.abs(ang) > 0.5 || Math.abs(vel) > 0.5) {
        parts.push(`${port}:${Math.round(ang)}°`);
      }
    }
    if (this.engine.world.kinematics?.chassis?.type !== 'static') {
      parts.push(`Yaw:${snap.yawDeg}°`);
    }
    el.textContent = parts.join('  ');
  }

  _updateSensorModeBadges() {
    const w = this.engine?.world;
    const distBadge = document.getElementById('sim-dist-mode');
    if (distBadge) {
      const isAuto = !!(w?.hasWorldObstacles && this.uiSensors.distanceAuto);
      distBadge.textContent = isAuto ? 'AUTO' : 'MAN';
      distBadge.classList.toggle('badge-info', isAuto);
      distBadge.classList.toggle('badge-ghost', !isAuto);
    }
    const colorBadge = document.getElementById('sim-color-mode');
    if (colorBadge) {
      const isAuto = !!(w?.hasWorldColorProps && this.uiSensors.colorAuto);
      colorBadge.textContent = isAuto ? 'AUTO' : 'MAN';
      colorBadge.classList.toggle('badge-info', isAuto);
      colorBadge.classList.toggle('badge-ghost', !isAuto);
    }
  }

  _updateUi() {
    const runBtn = document.getElementById('sim-btn-run');
    const pauseBtn = document.getElementById('sim-btn-pause');
    const stopBtn = document.getElementById('sim-btn-stop');
    const controls = document.getElementById('sim-sensor-bar');
    const active = this.running || this.paused;
    if (runBtn) runBtn.classList.toggle('hidden', this.running && !this.paused);
    if (pauseBtn) pauseBtn.classList.toggle('hidden', !(this.running && !this.paused));
    if (stopBtn) stopBtn.classList.toggle('hidden', !active);
    if (controls) controls.classList.toggle('hidden', !active);
  }

  _bindEvents() {
    // Button clicks (event delegation across HTMX swaps)
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('[data-sim-action]');
      if (!btn) return;
      const action = btn.dataset.simAction;
      if (action === 'run') {
        this.start();
      } else if (action === 'pause') {
        this.pause();
      } else if (action === 'stop') {
        this.stop(false);
      } else if (action === 'reset') {
        this.stop(true);
      } else if (action === 'speed') {
        this.speedIdx = (this.speedIdx + 1) % SPEEDS.length;
        btn.textContent = `${this.speedScale}×`;
      } else if (action === 'mute') {
        this.muted = !this.muted;
        btn.textContent = this.muted ? '🔇' : '🔊';
      } else if (action === 'source') {
        const order = ['auto', 'python', 'blocks'];
        this.codeSource = order[(order.indexOf(this.codeSource) + 1) % order.length];
        btn.textContent = this.codeSource === 'python' ? '🐍 PY' : this.codeSource === 'blocks' ? '🧩 BLK' : '⚡ Auto';
      } else if (action === 'color') {
        this.uiSensors.color = btn.dataset.simColor || 'RED';
        this.uiSensors.colorAuto = false;
        if (this.engine) {
          this.engine.world.manualSensors.color = this.uiSensors.color;
          this.engine.world.manualSensors.colorAuto = false;
        }
        document.querySelectorAll('[data-sim-color]').forEach((b) => b.classList.remove('ring-2', 'ring-primary'));
        btn.classList.add('ring-2', 'ring-primary');
        this._updateSensorModeBadges();
      } else if (action === 'toggle-dist-auto') {
        this.uiSensors.distanceAuto = !this.uiSensors.distanceAuto;
        if (this.engine) this.engine.world.manualSensors.distanceAuto = this.uiSensors.distanceAuto;
        this._updateSensorModeBadges();
      } else if (action === 'toggle-color-auto') {
        this.uiSensors.colorAuto = !this.uiSensors.colorAuto;
        if (this.engine) this.engine.world.manualSensors.colorAuto = this.uiSensors.colorAuto;
        this._updateSensorModeBadges();
      } else if (action === 'force') {
        this.uiSensors.forcePressed = !this.uiSensors.forcePressed;
        btn.classList.toggle('btn-warning', this.uiSensors.forcePressed);
        btn.classList.toggle('btn-outline', !this.uiSensors.forcePressed);
        if (this.engine) this.engine.world.setForcePressed(this.uiSensors.forcePressed);
        if (this.uiSensors.forcePressed) this.beep(988, 80, 60);
      } else if (action === 'hub-left' || action === 'hub-right') {
        // Click pulse (300 ms) so a single tap reliably triggers `while button.pressed(...) == 0:`
        const side = action === 'hub-right' ? 'RIGHT' : 'LEFT';
        const key = side === 'RIGHT' ? 'btnRight' : 'btnLeft';
        this.uiSensors[key] = true;
        btn.classList.add('btn-primary');
        if (this.engine) this.engine.world.setButton(side, true);
        setTimeout(() => {
          this.uiSensors[key] = false;
          btn.classList.remove('btn-primary');
          if (this.engine) this.engine.world.setButton(side, false);
        }, 320);
      }
    });

    // Distance slider input
    document.addEventListener('input', (e) => {
      const slider = e.target.closest('[data-sim-distance]');
      if (!slider) return;
      const val = Number(slider.value);
      this.uiSensors.distanceCm = val;
      this.uiSensors.distanceAuto = false;
      if (this.engine) {
        this.engine.world.manualSensors.distanceCm = val;
        this.engine.world.manualSensors.distanceAuto = false;
      }
      const out = document.getElementById('sim-distance-val');
      if (out) out.textContent = `${val} cm`;
      this._updateSensorModeBadges();
    });

    // Stop cleanly when switching lessons
    document.body.addEventListener('htmx:beforeSwap', (e) => {
      if (e.detail?.target?.id === 'lesson-workspace') {
        this.stop(true);
      }
    });
  }
}

window.SpikeSimulator = new SpikeSimulatorUI();
