// LEGO SPIKE Prime (official SPIKE 3 firmware) device client.
// Protocol: https://lego.github.io/spike-prime-docs/  — COBS-framed binary messages.
// Transports: Web Bluetooth (documented by LEGO, recommended) and Web Serial (same framing, experimental).

// ---------------------------------------------------------------- framing
const DELIMITER = 0x02;
const NO_DELIMITER = 0xff;
const COBS_CODE_OFFSET = DELIMITER;
const MAX_BLOCK_SIZE = 84;
const XOR = 0x03;

export function cobsEncode(data) {
  const out = [];
  let codeIndex = 0;
  let block = 0;
  const beginBlock = () => {
    codeIndex = out.length;
    out.push(NO_DELIMITER);
    block = 1;
  };
  beginBlock();
  for (const byte of data) {
    if (byte > DELIMITER) {
      out.push(byte);
      block += 1;
    }
    if (byte <= DELIMITER || block > MAX_BLOCK_SIZE) {
      if (byte <= DELIMITER) out[codeIndex] = byte * MAX_BLOCK_SIZE + block + COBS_CODE_OFFSET;
      beginBlock();
    }
  }
  out[codeIndex] = block + COBS_CODE_OFFSET;
  return out;
}

function unescapeCode(code) {
  if (code === NO_DELIMITER) return [null, MAX_BLOCK_SIZE + 1];
  let value = Math.floor((code - COBS_CODE_OFFSET) / MAX_BLOCK_SIZE);
  let block = (code - COBS_CODE_OFFSET) % MAX_BLOCK_SIZE;
  if (block === 0) {
    block = MAX_BLOCK_SIZE;
    value -= 1;
  }
  return [value, block];
}

export function cobsDecode(data) {
  const out = [];
  let [value, block] = unescapeCode(data[0]);
  for (let i = 1; i < data.length; i++) {
    block -= 1;
    if (block > 0) {
      out.push(data[i]);
      continue;
    }
    if (value !== null) out.push(value);
    [value, block] = unescapeCode(data[i]);
  }
  return out;
}

export function pack(message) {
  const encoded = cobsEncode(message).map((b) => b ^ XOR);
  encoded.push(DELIMITER);
  return Uint8Array.from(encoded);
}

export function unpack(frame) {
  const start = frame[0] === 0x01 ? 1 : 0; // 0x01 = high-priority marker
  const body = Array.from(frame.slice(start, frame.length - 1), (b) => b ^ XOR);
  return Uint8Array.from(cobsDecode(body));
}

// ---------------------------------------------------------------- CRC32 (zlib), data zero-padded to 4 bytes
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

export function crc32Aligned(bytes, seed = 0) {
  const pad = (4 - (bytes.length % 4)) % 4;
  let crc = (seed ^ 0xffffffff) >>> 0;
  const step = (b) => {
    crc = CRC_TABLE[(crc ^ b) & 0xff] ^ (crc >>> 8);
  };
  for (const b of bytes) step(b);
  for (let i = 0; i < pad; i++) step(0);
  return (crc ^ 0xffffffff) >>> 0;
}

// ---------------------------------------------------------------- messages
const MSG = {
  InfoRequest: 0x00,
  InfoResponse: 0x01,
  StartFileUploadRequest: 0x0c,
  StartFileUploadResponse: 0x0d,
  TransferChunkRequest: 0x10,
  TransferChunkResponse: 0x11,
  ProgramFlowRequest: 0x1e,
  ProgramFlowResponse: 0x1f,
  ProgramFlowNotification: 0x20,
  ConsoleNotification: 0x21,
  ClearSlotRequest: 0x46,
  ClearSlotResponse: 0x47,
};

const u16 = (v) => [v & 0xff, (v >> 8) & 0xff];
const u32 = (v) => [v & 0xff, (v >>> 8) & 0xff, (v >>> 16) & 0xff, (v >>> 24) & 0xff];

function parseInfoResponse(m) {
  const dv = new DataView(m.buffer, m.byteOffset, m.byteLength);
  return {
    rpc: `${m[1]}.${m[2]}.${dv.getUint16(3, true)}`,
    firmware: `${m[5]}.${m[6]}.${dv.getUint16(7, true)}`,
    maxPacketSize: dv.getUint16(9, true),
    maxMessageSize: dv.getUint16(11, true),
    maxChunkSize: dv.getUint16(13, true),
    productGroupDevice: dv.getUint16(15, true),
  };
}

// ---------------------------------------------------------------- transports
const BLE_SERVICE = '0000fd02-0000-1000-8000-00805f9b34fb';
const BLE_RX_CHAR = '0000fd02-0001-1000-8000-00805f9b34fb'; // app -> hub (write without response)
const BLE_TX_CHAR = '0000fd02-0002-1000-8000-00805f9b34fb'; // hub -> app (notify)

class BleTransport {
  static supported() {
    return 'bluetooth' in navigator;
  }

  async open(onBytes, onClose) {
    this.device = await navigator.bluetooth.requestDevice({ filters: [{ services: [BLE_SERVICE] }] });
    this.device.addEventListener('gattserverdisconnected', onClose);
    const server = await this.device.gatt.connect();
    const service = await server.getPrimaryService(BLE_SERVICE);
    this.rx = await service.getCharacteristic(BLE_RX_CHAR);
    const tx = await service.getCharacteristic(BLE_TX_CHAR);
    tx.addEventListener('characteristicvaluechanged', (ev) => {
      const v = ev.target.value;
      onBytes(new Uint8Array(v.buffer, v.byteOffset, v.byteLength));
    });
    await tx.startNotifications();
    return this.device.name || 'SPIKE Hub';
  }

  async write(bytes) {
    if (this.rx.writeValueWithoutResponse) await this.rx.writeValueWithoutResponse(bytes);
    else await this.rx.writeValue(bytes);
  }

  async close() {
    if (this.device?.gatt?.connected) this.device.gatt.disconnect();
  }
}

class SerialTransport {
  static supported() {
    return 'serial' in navigator;
  }

  async open(onBytes, onClose) {
    this.port = await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x0694 }] }); // LEGO System A/S
    if (!this.port.readable) await this.port.open({ baudRate: 115200 });
    this.writer = this.port.writable.getWriter();
    this.reading = true;
    this.onClose = onClose;
    this.readLoop(onBytes);
    return 'SPIKE Hub (USB)';
  }

  async readLoop(onBytes) {
    try {
      while (this.reading && this.port.readable) {
        this.reader = this.port.readable.getReader();
        try {
          for (;;) {
            const { value, done } = await this.reader.read();
            if (done) break;
            if (value) onBytes(value);
          }
        } finally {
          this.reader.releaseLock();
          this.reader = null;
        }
      }
    } catch (_) {
      // device unplugged
    }
    if (this.reading) this.onClose?.();
  }

  async write(bytes) {
    await this.writer.write(bytes);
  }

  async close() {
    this.reading = false;
    try {
      await this.reader?.cancel();
    } catch (_) {}
    try {
      this.writer?.releaseLock();
    } catch (_) {}
    try {
      await this.port?.close();
    } catch (_) {}
  }
}

// ---------------------------------------------------------------- hub client
class SpikeHub {
  constructor() {
    this.transport = null;
    this.info = null;
    this.rxBuffer = [];
    this.pending = new Map(); // responseId -> {resolve, reject, timer}
    this.consoleLine = '';
    this.busy = false;
    this.listeners = new Set();
  }

  get connected() {
    return this.transport !== null;
  }

  on(fn) {
    this.listeners.add(fn);
  }

  emit(type, detail) {
    for (const fn of this.listeners) fn(type, detail);
  }

  async connect(kind) {
    if (this.transport) await this.disconnect();
    const transport = kind === 'ble' ? new BleTransport() : new SerialTransport();
    const name = await transport.open(
      (bytes) => this.onBytes(bytes),
      () => this.onTransportClosed()
    );
    this.transport = transport;
    this.rxBuffer = [];
    try {
      const resp = await this.request([MSG.InfoRequest], MSG.InfoResponse, 5000);
      this.info = parseInfoResponse(resp);
    } catch (err) {
      await this.disconnect();
      throw new Error(`Hub did not answer InfoRequest (${err.message}). Is it running SPIKE 3 firmware?`);
    }
    this.emit('state');
    this.emit('log', `${name}: firmware ${this.info.firmware}, RPC ${this.info.rpc}, chunk ${this.info.maxChunkSize}B`);
  }

  async disconnect() {
    const t = this.transport;
    this.transport = null;
    this.info = null;
    this.failPending(new Error('disconnected'));
    if (t) await t.close();
    this.emit('state');
  }

  onTransportClosed() {
    if (!this.transport) return;
    this.transport = null;
    this.info = null;
    this.failPending(new Error('disconnected'));
    this.emit('log', 'Hub disconnected.');
    this.emit('state');
  }

  failPending(err) {
    for (const [, p] of this.pending) {
      clearTimeout(p.timer);
      p.reject(err);
    }
    this.pending.clear();
  }

  onBytes(bytes) {
    for (const b of bytes) {
      this.rxBuffer.push(b);
      if (b !== DELIMITER) continue;
      const frame = Uint8Array.from(this.rxBuffer);
      this.rxBuffer = [];
      if (frame.length < 2) continue;
      try {
        this.onMessage(unpack(frame));
      } catch (err) {
        this.emit('log', `Bad frame: ${err.message}`);
      }
    }
  }

  onMessage(m) {
    const id = m[0];
    const waiter = this.pending.get(id);
    if (waiter) {
      this.pending.delete(id);
      clearTimeout(waiter.timer);
      waiter.resolve(m);
      return;
    }
    if (id === MSG.ConsoleNotification) {
      const end = m.indexOf(0, 1);
      this.consoleLine += new TextDecoder().decode(m.slice(1, end === -1 ? m.length : end));
      const parts = this.consoleLine.split('\n');
      this.consoleLine = parts.pop();
      for (const line of parts) this.emit('console', line);
    } else if (id === MSG.ProgramFlowNotification) {
      this.emit('log', m[1] ? 'Program finished / stopped.' : 'Program started.');
    }
    // DeviceNotification (0x3C) etc. are ignored.
  }

  async send(message) {
    const frame = pack(message);
    const size = this.info?.maxPacketSize || 20;
    for (let i = 0; i < frame.length; i += size) {
      await this.transport.write(frame.slice(i, i + size));
    }
  }

  request(message, responseId, timeoutMs = 5000) {
    if (!this.transport) return Promise.reject(new Error('not connected'));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(responseId);
        reject(new Error(`timeout waiting for 0x${responseId.toString(16)}`));
      }, timeoutMs);
      this.pending.set(responseId, { resolve, reject, timer });
      this.send(message).catch((err) => {
        clearTimeout(timer);
        this.pending.delete(responseId);
        reject(err);
      });
    });
  }

  static checkStatus(resp, what) {
    if (resp[1] !== 0x00) throw new Error(`${what} rejected by hub (NACK)`);
  }

  async uploadAndRun(code, slot) {
    if (!this.transport || !this.info) throw new Error('not connected');
    if (this.busy) throw new Error('busy');
    this.busy = true;
    this.emit('state');
    try {
      const program = new TextEncoder().encode(code);
      // Clearing an empty slot returns NACK, which is fine.
      await this.request([MSG.ClearSlotRequest, slot], MSG.ClearSlotResponse);

      const name = Array.from(new TextEncoder().encode('program.py'));
      const start = await this.request(
        [MSG.StartFileUploadRequest, ...name, 0x00, slot, ...u32(crc32Aligned(program))],
        MSG.StartFileUploadResponse
      );
      SpikeHub.checkStatus(start, 'StartFileUpload');

      let runningCrc = 0;
      const chunkSize = this.info.maxChunkSize;
      for (let i = 0; i < program.length; i += chunkSize) {
        const chunk = program.slice(i, i + chunkSize);
        runningCrc = crc32Aligned(chunk, runningCrc);
        const resp = await this.request(
          [MSG.TransferChunkRequest, ...u32(runningCrc), ...u16(chunk.length), ...chunk],
          MSG.TransferChunkResponse
        );
        SpikeHub.checkStatus(resp, 'TransferChunk');
        this.emit('progress', Math.min(100, Math.round(((i + chunk.length) / program.length) * 100)));
      }

      const run = await this.request([MSG.ProgramFlowRequest, 0x00, slot], MSG.ProgramFlowResponse);
      SpikeHub.checkStatus(run, 'ProgramFlow(start)');
    } finally {
      this.busy = false;
      this.emit('state');
    }
  }

  async stopProgram(slot) {
    const resp = await this.request([MSG.ProgramFlowRequest, 0x01, slot], MSG.ProgramFlowResponse);
    SpikeHub.checkStatus(resp, 'ProgramFlow(stop)');
  }
}

// ---------------------------------------------------------------- UI binding (event delegation; survives HTMX swaps)
const hub = new SpikeHub();
window.spikeHub = hub;

function panel() {
  return document.getElementById('device-panel');
}

function t(key) {
  try {
    return JSON.parse(panel()?.dataset.i18n || '{}')[key] || key;
  } catch (_) {
    return key;
  }
}

function log(msg) {
  const el = document.getElementById('device-log');
  if (!el) return;
  el.textContent += `[${new Date().toLocaleTimeString()}] ${msg}\n`;
  el.scrollTop = el.scrollHeight;
}

function renderState() {
  const p = panel();
  if (!p) return;
  const badge = p.querySelector('[data-device-status]');
  if (badge) {
    const state = hub.busy ? 'busy' : hub.connected ? 'connected' : 'disconnected';
    badge.textContent = t(`status_${state}`);
    badge.className = `badge ${state === 'connected' ? 'badge-success' : state === 'busy' ? 'badge-warning' : 'badge-ghost'}`;
  }
  p.querySelectorAll('[data-needs-hub]').forEach((btn) => {
    btn.disabled = !hub.connected || hub.busy;
  });
  const progress = p.querySelector('[data-device-progress]');
  if (progress && !hub.busy) progress.classList.add('hidden');
}

hub.on((type, detail) => {
  if (type === 'state') renderState();
  else if (type === 'log') log(detail);
  else if (type === 'console') log(`> ${detail}`);
  else if (type === 'progress') {
    const bar = panel()?.querySelector('[data-device-progress]');
    if (bar) {
      bar.classList.remove('hidden');
      bar.value = detail;
    }
  }
});

function selectedSlot() {
  const v = parseInt(panel()?.querySelector('[data-device-slot]')?.value ?? '0', 10);
  return Number.isInteger(v) && v >= 0 && v <= 19 ? v : 0;
}

const actions = {
  async 'connect-ble'() {
    if (!BleTransport.supported()) return log(t('not_supported_ble'));
    await hub.connect('ble');
  },
  async 'connect-usb'() {
    if (!SerialTransport.supported()) return log(t('not_supported_serial'));
    await hub.connect('usb');
  },
  async disconnect() {
    await hub.disconnect();
    log(t('status_disconnected'));
  },
  async 'upload-run'() {
    if (!hub.connected) return log(t('need_connect'));
    const source = panel()?.querySelector('[data-code-source]')?.value;
    const code = source === 'blocks' && window.SpikeBlocks
      ? await window.SpikeBlocks.getPython()
      : document.getElementById('spike-python-code')?.textContent || '';
    const slot = selectedSlot();
    log(`Uploading ${new TextEncoder().encode(code).length} bytes to slot ${slot}…`);
    await hub.uploadAndRun(code, slot);
    log(t('upload_done'));
  },
  async stop() {
    if (!hub.connected) return log(t('need_connect'));
    await hub.stopProgram(selectedSlot());
    log(t('program_stopped'));
  },
};

document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('[data-device-action]');
  if (!btn) return;
  const fn = actions[btn.dataset.deviceAction];
  if (!fn) return;
  try {
    await fn();
  } catch (err) {
    if (err?.name === 'NotFoundError') return; // user closed the device chooser
    log(`Error: ${err.message}`);
  }
});

document.addEventListener('htmx:afterSettle', renderState);
renderState();
