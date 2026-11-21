// Scratch-style block editor (Blockly) that mirrors the SPIKE App word blocks and generates
// official SPIKE 3 Python. Blockly (~1 MB) is lazy-loaded the first time the Blocks tab opens,
// or when the deploy panel asks for the block program.
// Lesson programs come from <script id="lesson-blocks-xml"> (built by app/data/blocks_dsl.py — keep
// block type / field / input names in sync with that file).

const BLOCKLY = 'https://unpkg.com/blockly@11.2.1';
const MSG_FILE = { zh: 'zh-hans', en: 'en', ja: 'ja' };
const STORE_PREFIX = 'spike_blocks_v1_';

const COLORS = {
  events: '#ffbf00',
  motors: '#0090f5',
  movement: '#ff4ccd',
  light: '#9966ff',
  sound: '#cf63cf',
  control: '#ffab19',
  sensors: '#4cbfe6',
  operators: '#59c059',
  variables: '#ff8c1a',
  more: '#ff6680',
};

// ---------------------------------------------------------------- labels
const L = {
  zh: {
    cat_events: '事件', cat_motors: '电机', cat_movement: '移动', cat_light: '灯光', cat_sound: '声音',
    cat_control: '控制', cat_sensors: '传感器', cat_operators: '运算', cat_variables: '变量', cat_more: '调试',
    start: '当程序开始',
    motor_run_for: '%1 电机转动 %2 度，速度 %3',
    motor_go_to: '%1 电机转到 %2 度位置，速度 %3',
    motor_start: '%1 电机以速度 %2 开始转动',
    motor_stop: '%1 电机停止',
    motor_position: '%1 电机的相对位置',
    move_pair: '设置移动电机为 %1 和 %2',
    move_for: '移动 %1 度，转向 %2，速度 %3',
    move_start: '开始移动，转向 %1，速度 %2',
    move_tank: '开始坦克移动，左轮速度 %1 右轮速度 %2',
    move_stop: '停止移动',
    show_image: '显示图案 %1',
    write: '写出 %1',
    clear: '关闭所有像素',
    beep: '播放音调 %1 Hz，持续 %2 毫秒',
    wait: '等待 %1 秒',
    repeat: '重复 %1 次',
    forever: '重复执行',
    repeat_until: '重复执行直到 %1',
    wait_until: '等待直到 %1',
    if: '如果 %1 那么',
    else: '否则',
    distance: '%1 距离 (毫米)',
    color_is: '%1 颜色是 %2 ?',
    reflection: '%1 反射光强度 (%)',
    force_pressed: '%1 力传感器被按下?',
    button_pressed: '%1 按钮被按下?',
    yaw: '偏航角 (度)',
    reset_yaw: '把偏航角设为 0',
    abs: '%1 的绝对值',
    print: '打印 %1',
    left: '左', right: '右',
    colors: { RED: '红色', GREEN: '绿色', BLUE: '蓝色', YELLOW: '黄色', BLACK: '黑色', WHITE: '白色' },
    images: {
      HEART: '爱心', HAPPY: '开心', SMILE: '微笑', SAD: '难过', SURPRISED: '惊讶', ASLEEP: '睡觉',
      YES: '对勾', NO: '叉号', ARROW_N: '向前箭头', ARROW_E: '向右箭头', ARROW_S: '向后箭头', ARROW_W: '向左箭头',
      SQUARE: '正方形', TRIANGLE: '三角形', DIAMOND: '菱形',
    },
    no_start: '# 把积木接到「当程序开始」下面才会生成程序',
    cat_spike: 'SPIKE Scratch',
    setvar: '把 %1 设为 %2',
    getvar: '%1',
    distance_lt: '距离 %1 小于 %2 毫米？',
    button_pressed_named: '%1 按钮被按下？',
    set_yaw: '把偏航角设为 %1',
    playsound: '播放声音 %1',
    sound_greeting: '问候', sound_animal_cat: '猫叫', sound_click: '咔哒', sound_horn: '喇叭',
  },
  en: {
    cat_events: 'Events', cat_motors: 'Motors', cat_movement: 'Movement', cat_light: 'Light', cat_sound: 'Sound',
    cat_control: 'Control', cat_sensors: 'Sensors', cat_operators: 'Operators', cat_variables: 'Variables', cat_more: 'Debug',
    start: 'when program starts',
    motor_run_for: '%1 run motor for %2 degrees at speed %3',
    motor_go_to: '%1 go to position %2 at speed %3',
    motor_start: '%1 start motor at speed %2',
    motor_stop: '%1 stop motor',
    motor_position: '%1 relative position',
    move_pair: 'set movement motors to %1 and %2',
    move_for: 'move %1 degrees, steering %2, speed %3',
    move_start: 'start moving, steering %1, speed %2',
    move_tank: 'start tank moving, left speed %1 right speed %2',
    move_stop: 'stop moving',
    show_image: 'turn on %1',
    write: 'write %1',
    clear: 'turn off pixels',
    beep: 'beep %1 Hz for %2 ms',
    wait: 'wait %1 seconds',
    repeat: 'repeat %1 times',
    forever: 'forever',
    repeat_until: 'repeat until %1',
    wait_until: 'wait until %1',
    if: 'if %1 then',
    else: 'else',
    distance: '%1 distance (mm)',
    color_is: '%1 is color %2 ?',
    reflection: '%1 reflection (%)',
    force_pressed: '%1 is force sensor pressed?',
    button_pressed: '%1 button pressed?',
    yaw: 'yaw angle (°)',
    reset_yaw: 'set yaw angle to 0',
    abs: 'abs of %1',
    print: 'print %1',
    left: 'left', right: 'right',
    colors: { RED: 'red', GREEN: 'green', BLUE: 'blue', YELLOW: 'yellow', BLACK: 'black', WHITE: 'white' },
    images: {
      HEART: 'heart', HAPPY: 'happy', SMILE: 'smile', SAD: 'sad', SURPRISED: 'surprised', ASLEEP: 'asleep',
      YES: 'yes ✓', NO: 'no ✗', ARROW_N: 'arrow forward', ARROW_E: 'arrow right', ARROW_S: 'arrow back', ARROW_W: 'arrow left',
      SQUARE: 'square', TRIANGLE: 'triangle', DIAMOND: 'diamond',
    },
    no_start: '# Attach blocks under "when program starts" to generate a program',
    cat_spike: 'SPIKE Scratch',
    setvar: 'set %1 to %2',
    getvar: '%1',
    distance_lt: 'distance to %1 < %2 mm?',
    button_pressed_named: 'button %1 pressed?',
    set_yaw: 'set yaw angle to %1',
    playsound: 'play sound %1',
    sound_greeting: 'greeting', sound_animal_cat: 'cat', sound_click: 'click', sound_horn: 'horn',
  },
  ja: {
    cat_events: 'イベント', cat_motors: 'モーター', cat_movement: '移動', cat_light: 'ライト', cat_sound: 'サウンド',
    cat_control: '制御', cat_sensors: 'センサー', cat_operators: '演算', cat_variables: '変数', cat_more: 'デバッグ',
    start: 'プログラムが始まったとき',
    motor_run_for: '%1 モーターを %2 度、速さ %3 で回す',
    motor_go_to: '%1 モーターを %2 度の位置へ、速さ %3',
    motor_start: '%1 モーターを速さ %2 で回し始める',
    motor_stop: '%1 モーターを止める',
    motor_position: '%1 の相対位置',
    move_pair: '移動モーターを %1 と %2 にする',
    move_for: '%1 度移動、ステアリング %2、速さ %3',
    move_start: '移動を始める、ステアリング %1、速さ %2',
    move_tank: 'タンク移動を始める、左 %1 右 %2',
    move_stop: '移動を止める',
    show_image: '%1 を表示',
    write: '%1 と書く',
    clear: 'ライトを消す',
    beep: '%1 Hz の音を %2 ミリ秒鳴らす',
    wait: '%1 秒待つ',
    repeat: '%1 回くり返す',
    forever: 'ずっと',
    repeat_until: '%1 までくり返す',
    wait_until: '%1 まで待つ',
    if: 'もし %1 なら',
    else: 'でなければ',
    distance: '%1 の距離 (mm)',
    color_is: '%1 の色は %2 ?',
    reflection: '%1 の反射光 (%)',
    force_pressed: '%1 のフォースセンサーが押された?',
    button_pressed: '%1 ボタンが押された?',
    yaw: 'ヨー角 (度)',
    reset_yaw: 'ヨー角を 0 にする',
    abs: '%1 の絶対値',
    print: '%1 をプリント',
    left: '左', right: '右',
    colors: { RED: '赤', GREEN: '緑', BLUE: '青', YELLOW: '黄', BLACK: '黒', WHITE: '白' },
    images: {
      HEART: 'ハート', HAPPY: 'うれしい', SMILE: 'にっこり', SAD: 'かなしい', SURPRISED: 'びっくり', ASLEEP: 'ねむい',
      YES: 'チェック ✓', NO: 'バツ ✗', ARROW_N: '前の矢印', ARROW_E: '右の矢印', ARROW_S: '後ろの矢印', ARROW_W: '左の矢印',
      SQUARE: '四角', TRIANGLE: '三角', DIAMOND: 'ひし形',
    },
    no_start: '# 「プログラムが始まったとき」の下にブロックをつなぐとプログラムが作られます',
    cat_spike: 'SPIKE Scratch',
    setvar: '%1 を %2 にする',
    getvar: '%1',
    distance_lt: '%1 の距離 < %2 mm？',
    button_pressed_named: '%1 ボタンが押された？',
    set_yaw: 'ヨー角を %1 にする',
    playsound: '音 %1 を再生',
    sound_greeting: 'あいさつ', sound_animal_cat: 'ネコ', sound_click: 'クリック', sound_horn: 'クラクション',
  },
};

const lang = () => {
  const l = document.querySelector('[data-lesson-root]')?.dataset.lang || 'zh';
  return L[l] ? l : 'zh';
};
const T = () => L[lang()];
const PORTS = ['A', 'B', 'C', 'D', 'E', 'F'].map((p) => [p, p]);
// Variable names offered by the Scratch-flavour dropdowns: ports A…F plus the lesson's own
// variables. The options list of a JSON field_dropdown is snapshotted when the block type is
// defined (once per page), so these two blocks are registered per workspace instead (see
// registerScratchBlocks), which keeps the dropdown lists editable per lesson.

// ---------------------------------------------------------------- loader
let loading = null;
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = resolve;
    s.onerror = () => reject(new Error(`load failed: ${src}`));
    document.head.appendChild(s);
  });
}

function loadBlockly() {
  if (!loading) {
    loading = (async () => {
      for (const f of ['blockly_compressed.js', 'blocks_compressed.js', 'python_compressed.js', `msg/${MSG_FILE[lang()]}.js`]) {
        await loadScript(`${BLOCKLY}/${f}`);
      }
      defineBlocks();
      defineGenerators();
    })();
    loading.catch(() => {
      loading = null; // allow a retry after a network hiccup
    });
  }
  return loading;
}

// ---------------------------------------------------------------- block definitions
function portField(name = 'PORT') {
  return { type: 'field_dropdown', name, options: PORTS };
}
function num(name) {
  return { type: 'input_value', name, check: 'Number' };
}
function soundField(name = 'SOUND') {
  const t = T();
  return {
    type: 'field_dropdown', name,
    options: [
      [t.sound_greeting, 'GREETING'], [t.sound_animal_cat, 'ANIMAL_CAT'],
      [t.sound_click, 'CLICK'], [t.sound_horn, 'HORN'],
    ],
  };
}
function bool(name) {
  return { type: 'input_value', name, check: 'Boolean' };
}
function stmt(type, msg, args, colour, extra = {}) {
  return { type, message0: msg, args0: args, previousStatement: null, nextStatement: null, colour, inputsInline: true, ...extra };
}
function reporter(type, msg, args, colour, output = 'Number') {
  return { type, message0: msg, args0: args, output, colour, inputsInline: true };
}

function defineBlocks() {
  const t = T();
  const Blockly = window.Blockly;
  const colorOpts = Object.entries(t.colors).map(([k, v]) => [v, k]);
  const imageOpts = Object.entries(t.images).map(([k, v]) => [v, k]);
  const btnOpts = [[t.left, 'LEFT'], [t.right, 'RIGHT']];
  if (!Blockly.Extensions.isRegistered('spike_hat')) {
    Blockly.Extensions.register('spike_hat', function hat() {
      this.hat = 'cap'; // Scratch-style rounded "hat" on the start block
    });
  }

  Blockly.defineBlocksWithJsonArray([
    { type: 'spike_start', message0: t.start, nextStatement: null, colour: COLORS.events, extensions: ['spike_hat'] },

    stmt('spike_motor_run_for', t.motor_run_for, [portField(), num('DEG'), num('SPEED')], COLORS.motors),
    stmt('spike_motor_go_to', t.motor_go_to, [portField(), num('POS'), num('SPEED')], COLORS.motors),
    stmt('spike_motor_start', t.motor_start, [portField(), num('SPEED')], COLORS.motors),
    stmt('spike_motor_stop', t.motor_stop, [portField()], COLORS.motors),
    reporter('spike_motor_position', t.motor_position, [portField()], COLORS.motors),

    stmt('spike_move_pair', t.move_pair, [portField('LEFT'), portField('RIGHT')], COLORS.movement),
    stmt('spike_move_for', t.move_for, [num('DEG'), num('STEER'), num('SPEED')], COLORS.movement),
    stmt('spike_move_start', t.move_start, [num('STEER'), num('SPEED')], COLORS.movement),
    stmt('spike_move_tank', t.move_tank, [num('LEFT'), num('RIGHT')], COLORS.movement),
    stmt('spike_move_stop', t.move_stop, [], COLORS.movement),

    stmt('spike_show_image', t.show_image, [{ type: 'field_dropdown', name: 'IMAGE', options: imageOpts }], COLORS.light),
    stmt('spike_write', t.write, [{ type: 'input_value', name: 'TEXT' }], COLORS.light),
    stmt('spike_clear', t.clear, [], COLORS.light),

    stmt('spike_beep', t.beep, [num('FREQ'), num('MS')], COLORS.sound),

    stmt('spike_wait', t.wait, [num('SECS')], COLORS.control),
    {
      type: 'spike_repeat', message0: t.repeat, args0: [num('TIMES')],
      message1: '%1', args1: [{ type: 'input_statement', name: 'DO' }],
      previousStatement: null, nextStatement: null, colour: COLORS.control,
    },
    {
      type: 'spike_forever', message0: t.forever,
      message1: '%1', args1: [{ type: 'input_statement', name: 'DO' }],
      previousStatement: null, colour: COLORS.control,
    },
    {
      type: 'spike_repeat_until', message0: t.repeat_until, args0: [bool('COND')],
      message1: '%1', args1: [{ type: 'input_statement', name: 'DO' }],
      previousStatement: null, nextStatement: null, colour: COLORS.control,
    },
    stmt('spike_wait_until', t.wait_until, [bool('COND')], COLORS.control),
    {
      type: 'spike_if', message0: t.if, args0: [bool('COND')],
      message1: '%1', args1: [{ type: 'input_statement', name: 'DO' }],
      previousStatement: null, nextStatement: null, colour: COLORS.control,
    },
    {
      type: 'spike_if_else', message0: t.if, args0: [bool('COND')],
      message1: '%1', args1: [{ type: 'input_statement', name: 'DO' }],
      message2: t.else,
      message3: '%1', args3: [{ type: 'input_statement', name: 'ELSE' }],
      previousStatement: null, nextStatement: null, colour: COLORS.control,
    },

    reporter('spike_distance', t.distance, [portField()], COLORS.sensors),
    reporter('spike_color_is', t.color_is, [portField(), { type: 'field_dropdown', name: 'COLOR', options: colorOpts }], COLORS.sensors, 'Boolean'),
    reporter('spike_reflection', t.reflection, [portField()], COLORS.sensors),
    reporter('spike_force_pressed', t.force_pressed, [portField()], COLORS.sensors, 'Boolean'),
    reporter('spike_button_pressed', t.button_pressed, [{ type: 'field_dropdown', name: 'BUTTON', options: btnOpts }], COLORS.sensors, 'Boolean'),
    reporter('spike_yaw', t.yaw, [], COLORS.sensors),
    stmt('spike_reset_yaw', t.reset_yaw, [], COLORS.sensors),

    reporter('spike_abs', t.abs, [num('NUM')], COLORS.operators),
    stmt('spike_print', t.print, [{ type: 'input_value', name: 'VALUE' }], COLORS.more),

    // Scratch-flavour blocks (app/data/lessons_scratch.py): the SPIKE Scratch block set that the
    // official SPIKE App's Scratch edition exposes. `spike_getvar` is a typed variable reporter
    // (Number) so it can be dropped into number slots; both are read-only when a lesson wants the
    // Blockly program left untouched.
    reporter('spike_distance_lt', t.distance_lt, [portField(), num('LIMIT')], COLORS.sensors, 'Boolean'),
    reporter('spike_button_named', t.button_pressed_named, [{ type: 'field_dropdown', name: 'BUTTON', options: btnOpts }], COLORS.sensors, 'Boolean'),
    stmt('spike_set_yaw', t.set_yaw, [num('YAW')], COLORS.sensors),
    stmt('spike_playsound', t.playsound, [soundField()], COLORS.sound),
  ]);
}

// ---------------------------------------------------------------- python generator
let imports = new Set();
let hubImports = new Set();
let declaredVars = new Set(); // `set <name> to` blocks may name a variable that only the running
// Scratch program declares (ports A…F, BLACK, state …) — the generator still needs `name = 0`.
const registerVar = (name) => declaredVars.add(name);
const use = (m) => imports.add(m);
const useHub = (m) => hubImports.add(m);

// Literal numbers are folded; anything else is wrapped in int() since SPIKE APIs expect ints.
function intArg(code) {
  if (/^-?\d+$/.test(code)) return code;
  if (/^-?\d+\.\d+$/.test(code)) return String(Math.round(Number(code)));
  return `int(${code})`;
}

function defineGenerators() {
  const Blockly = window.Blockly;
  const { pythonGenerator: g, Order } = window.python;
  g.INDENT = '    ';

  const origScrub = g.scrub_;
  g.scrub_ = function scrub(block, code, thisOnly) {
    if (block.type === 'spike_start') return code; // the hat generates its own body
    return origScrub.call(this, block, code, thisOnly);
  };

  const v = (b, name, order = Order.NONE, dflt = '0') => g.valueToCode(b, name, order) || dflt;
  const p = (b, name = 'PORT') => {
    useHub('port');
    return `port.${b.getFieldValue(name)}`;
  };
  const sleep = () => {
    use('runloop');
    return `${g.INDENT}await runloop.sleep_ms(10)\n`;
  };
  const body = (b, name) => g.statementToCode(b, name);
  const F = g.forBlock;

  F.spike_start = (b) => {
    const code = g.blockToCode(b.getNextBlock());
    const text = typeof code === 'string' ? code : '';
    return text ? g.prefixLines(text, g.INDENT) : g.PASS;
  };

  F.spike_motor_run_for = (b) => {
    use('motor');
    return `await motor.run_for_degrees(${p(b)}, ${intArg(v(b, 'DEG'))}, ${intArg(v(b, 'SPEED'))})\n`;
  };
  F.spike_motor_go_to = (b) => {
    use('motor');
    return `await motor.run_to_absolute_position(${p(b)}, ${intArg(v(b, 'POS'))}, ${intArg(v(b, 'SPEED'))})\n`;
  };
  F.spike_motor_start = (b) => {
    use('motor');
    return `motor.run(${p(b)}, ${intArg(v(b, 'SPEED'))})\n`;
  };
  F.spike_motor_stop = (b) => {
    use('motor');
    return `motor.stop(${p(b)})\n`;
  };
  F.spike_motor_position = (b) => {
    use('motor');
    return [`motor.relative_position(${p(b)})`, Order.FUNCTION_CALL];
  };

  F.spike_move_pair = (b) => {
    use('motor_pair');
    return `motor_pair.pair(motor_pair.PAIR_1, ${p(b, 'LEFT')}, ${p(b, 'RIGHT')})\n`;
  };
  F.spike_move_for = (b) => {
    use('motor_pair');
    return `await motor_pair.move_for_degrees(motor_pair.PAIR_1, ${intArg(v(b, 'DEG'))}, ${intArg(v(b, 'STEER'))}, velocity=${intArg(v(b, 'SPEED'))})\n`;
  };
  F.spike_move_start = (b) => {
    use('motor_pair');
    return `motor_pair.move(motor_pair.PAIR_1, ${intArg(v(b, 'STEER'))}, velocity=${intArg(v(b, 'SPEED'))})\n`;
  };
  F.spike_move_tank = (b) => {
    use('motor_pair');
    return `motor_pair.move_tank(motor_pair.PAIR_1, ${intArg(v(b, 'LEFT'))}, ${intArg(v(b, 'RIGHT'))})\n`;
  };
  F.spike_move_stop = () => {
    use('motor_pair');
    return 'motor_pair.stop(motor_pair.PAIR_1)\n';
  };

  F.spike_show_image = (b) => {
    useHub('light_matrix');
    return `light_matrix.show_image(light_matrix.IMAGE_${b.getFieldValue('IMAGE')})\n`;
  };
  F.spike_write = (b) => {
    useHub('light_matrix');
    const val = v(b, 'TEXT', Order.NONE, "''");
    const s = /^'.*'$|^".*"$/.test(val) ? val : `str(${val})`;
    return `await light_matrix.write(${s})\n`;
  };
  F.spike_clear = () => {
    useHub('light_matrix');
    return 'light_matrix.clear()\n';
  };
  F.spike_beep = (b) => {
    useHub('sound');
    return `await sound.beep(${intArg(v(b, 'FREQ'))}, ${intArg(v(b, 'MS'))}, 100)\n`;
  };

  F.spike_wait = (b) => {
    use('runloop');
    const s = v(b, 'SECS');
    const ms = /^-?\d+(\.\d+)?$/.test(s) ? String(Math.round(Number(s) * 1000)) : `int((${s}) * 1000)`;
    return `await runloop.sleep_ms(${ms})\n`;
  };
  F.spike_repeat = (b) => `for _ in range(${intArg(v(b, 'TIMES'))}):\n${body(b, 'DO') || g.PASS}`;
  F.spike_forever = (b) => `while True:\n${body(b, 'DO')}${sleep()}`;
  F.spike_repeat_until = (b) => `while not (${v(b, 'COND', Order.NONE, 'False')}):\n${body(b, 'DO')}${sleep()}`;
  F.spike_wait_until = (b) => `while not (${v(b, 'COND', Order.NONE, 'False')}):\n${sleep()}`;
  F.spike_if = (b) => `if ${v(b, 'COND', Order.NONE, 'False')}:\n${body(b, 'DO') || g.PASS}`;
  F.spike_if_else = (b) =>
    `if ${v(b, 'COND', Order.NONE, 'False')}:\n${body(b, 'DO') || g.PASS}else:\n${body(b, 'ELSE') || g.PASS}`;

  F.spike_distance = (b) => {
    use('distance_sensor');
    return [`distance_sensor.distance(${p(b)})`, Order.FUNCTION_CALL];
  };
  F.spike_color_is = (b) => {
    use('color_sensor');
    use('color');
    return [`color_sensor.color(${p(b)}) == color.${b.getFieldValue('COLOR')}`, Order.RELATIONAL];
  };
  F.spike_reflection = (b) => {
    use('color_sensor');
    return [`color_sensor.reflection(${p(b)})`, Order.FUNCTION_CALL];
  };
  F.spike_force_pressed = (b) => {
    use('force_sensor');
    return [`force_sensor.pressed(${p(b)})`, Order.FUNCTION_CALL];
  };
  F.spike_button_pressed = (b) => {
    useHub('button');
    return [`button.pressed(button.${b.getFieldValue('BUTTON')}) > 0`, Order.RELATIONAL];
  };
  F.spike_yaw = () => {
    useHub('motion_sensor');
    return ['motion_sensor.tilt_angles()[0] / 10', Order.MULTIPLICATIVE];
  };
  F.spike_reset_yaw = () => {
    useHub('motion_sensor');
    return 'motion_sensor.reset_yaw(0)\n';
  };
  F.spike_abs = (b) => [`abs(${v(b, 'NUM')})`, Order.FUNCTION_CALL];
  F.spike_print = (b) => `print(${v(b, 'VALUE', Order.NONE, "''")})\n`;

  // Scratch-flavour blocks -> the same SPIKE 3 Python as the Blockly editions.
  F.spike_setvar = (b) => {
    const name = b.getFieldValue('NAME');
    if (!PORTS.some(([p]) => p === name)) registerVar(name);
    return `${name} = ${v(b, 'VALUE')}\n`;
  };
  F.spike_getvar = (b) => [b.getFieldValue('NAME'), Order.ATOMIC];
  F.spike_distance_lt = (b) => {
    use('distance_sensor');
    return [`0 < distance_sensor.distance(${p(b)}) < ${intArg(v(b, 'LIMIT'))}`, Order.RELATIONAL];
  };
  F.spike_button_named = (b) => {
    useHub('button');
    return [`button.pressed(button.${b.getFieldValue('BUTTON')}) > 0`, Order.RELATIONAL];
  };
  F.spike_set_yaw = (b) => {
    useHub('motion_sensor');
    return `motion_sensor.reset_yaw(${intArg(v(b, 'YAW'))})\n`;
  };
  // The SPIKE 3 `sound` module has play() for the built-in sound bank next to beep().
  F.spike_playsound = (b) => {
    useHub('sound');
    const bank = { GREETING: 'HELLO', ANIMAL_CAT: 'MEOW', CLICK: 'CLICK', HORN: 'HONK' };
    return `sound.play(sound.${bank[b.getFieldValue('SOUND')] || 'HELLO'})\n`;
  };

  // MicroPython has no `numbers` module, which Blockly's default math_change relies on.
  F.math_change = (b) => {
    const name = g.getVariableName(b.getFieldValue('VAR'));
    return `${name} += ${v(b, 'DELTA', Order.ADDITIVE)}\n`;
  };

}

function generate(ws) {
  const g = window.python.pythonGenerator;
  imports = new Set(['runloop']);
  hubImports = new Set();
  declaredVars = new Set();
  g.init(ws);

  const starts = ws.getTopBlocks(true).filter((b) => b.type === 'spike_start' && b.isEnabled());
  // First pass: collect the variables named by Scratch-flavour blocks (registered in declaredVars).
  ws.getTopBlocks(true).forEach((b) => g.blockToCode(b));
  declaredVars.delete('');
  declaredVars.delete(undefined);
  const vars = [...new Set([
    ...ws.getAllVariables().map((x) => g.getVariableName(x.getId())),
    ...declaredVars,
  ])].sort();

  const fns = starts.map((b, i) => {
    const name = starts.length > 1 ? `main_${i + 1}` : 'main';
    const globals = vars.length ? `${g.INDENT}global ${vars.join(', ')}\n` : '';
    return { name, code: `async def ${name}():\n${globals}${g.blockToCode(b)}` };
  });

  const order = ['runloop', 'motor', 'motor_pair', 'distance_sensor', 'color_sensor', 'force_sensor', 'color'];
  const head = [...imports].sort((a, b) => order.indexOf(a) - order.indexOf(b)).map((m) => `import ${m}`);
  if (hubImports.size) head.push(`from hub import ${[...hubImports].sort().join(', ')}`);

  let out = `${head.join('\n')}\n\n`;
  if (vars.length) out += `${vars.map((x) => `${x} = 0`).join('\n')}\n\n`;
  if (!fns.length) return `${out}${T().no_start}\n`;
  out += fns.map((f) => f.code).join('\n');
  out += `\nrunloop.run(${fns.map((f) => `${f.name}()`).join(', ')})\n`;
  return out;
}

// ---------------------------------------------------------------- toolbox
let scratchMode = false; // set by the lesson panel (data-blocks-mode="scratch")

/**
 * Blockly copies a JSON dropdown's `options` array into the field prototype when the block type
 * is defined, so a lesson's variables cannot be added by re-registering the type. Instead every
 * `spike_getvar` / `spike_setvar` NAME field is a dropdown whose options are (re)created here.
 */
let scratchPicks = []; // [label, value] pairs, set by the lesson panel before the workspace exists

/**
 * (Re)define the two Scratch-flavour variable blocks with the current `scratchPicks`.
 * Blockly throws on duplicate registration, so the old definition is removed first; workspaces are
 * created after this call and disposed before the next lesson, so no live block refers to them.
 */
function registerScratchBlocks() {
  const B = window.Blockly;
  const t = T();
  const opts = () => scratchPicks.map(([label, value]) => [label, value]);
  delete B.Blocks.spike_getvar;
  delete B.Blocks.spike_setvar;
  B.defineBlocksWithJsonArray([
    { type: 'spike_getvar', message0: t.getvar, args0: [{ type: 'field_dropdown', name: 'NAME', options: opts() }], output: 'Number', colour: COLORS.variables, inputsInline: true },
    {
      type: 'spike_setvar', message0: t.setvar,
      args0: [{ type: 'field_dropdown', name: 'NAME', options: opts() }, { type: 'input_value', name: 'VALUE', check: 'Number' }],
      previousStatement: null, nextStatement: null, colour: COLORS.variables, inputsInline: true,
    },
  ]);
}

function toolbox() {
  const t = T();
  const n = (x) => ({ shadow: { type: 'math_number', fields: { NUM: x } } });
  const blk = (type, inputs = {}, fields = {}) => ({ kind: 'block', type, inputs, fields });
  return {
    kind: 'categoryToolbox',
    contents: [
      { kind: 'category', name: t.cat_events, colour: COLORS.events, contents: [blk('spike_start')] },
      {
        kind: 'category', name: t.cat_motors, colour: COLORS.motors,
        contents: [
          blk('spike_motor_run_for', { DEG: n(360), SPEED: n(500) }),
          blk('spike_motor_go_to', { POS: n(0), SPEED: n(500) }),
          blk('spike_motor_start', { SPEED: n(500) }),
          blk('spike_motor_stop'),
          blk('spike_motor_position'),
        ],
      },
      {
        kind: 'category', name: t.cat_movement, colour: COLORS.movement,
        contents: [
          blk('spike_move_pair', {}, { LEFT: 'C', RIGHT: 'D' }),
          blk('spike_move_for', { DEG: n(360), STEER: n(0), SPEED: n(400) }),
          blk('spike_move_start', { STEER: n(0), SPEED: n(300) }),
          blk('spike_move_tank', { LEFT: n(300), RIGHT: n(300) }),
          blk('spike_move_stop'),
        ],
      },
      {
        kind: 'category', name: t.cat_light, colour: COLORS.light,
        contents: [
          blk('spike_show_image'),
          blk('spike_write', { TEXT: { shadow: { type: 'text', fields: { TEXT: 'Hello' } } } }),
          blk('spike_clear'),
        ],
      },
      { kind: 'category', name: t.cat_sound, colour: COLORS.sound, contents: [blk('spike_beep', { FREQ: n(440), MS: n(500) })] },
      {
        kind: 'category', name: t.cat_control, colour: COLORS.control,
        contents: [
          blk('spike_wait', { SECS: n(1) }),
          blk('spike_repeat', { TIMES: n(10) }),
          blk('spike_forever'),
          blk('spike_if'),
          blk('spike_if_else'),
          blk('spike_wait_until'),
          blk('spike_repeat_until'),
        ],
      },
      {
        kind: 'category', name: t.cat_sensors, colour: COLORS.sensors,
        contents: [
          blk('spike_distance', {}, { PORT: 'F' }),
          blk('spike_color_is', {}, { PORT: 'E' }),
          blk('spike_reflection', {}, { PORT: 'E' }),
          blk('spike_force_pressed', {}, { PORT: 'B' }),
          blk('spike_button_pressed'),
          blk('spike_yaw'),
          blk('spike_reset_yaw'),
        ],
      },
      {
        kind: 'category', name: t.cat_operators, colour: COLORS.operators,
        contents: [
          blk('math_number'),
          blk('math_arithmetic', { A: n(1), B: n(1) }),
          blk('logic_compare', { A: n(0), B: n(0) }, { OP: 'LT' }),
          blk('logic_operation'),
          blk('logic_negate'),
          blk('spike_abs', { NUM: n(-5) }),
          blk('text'),
        ],
      },
      scratchMode
        ? { kind: 'category', name: t.cat_spike, colour: COLORS.variables, contents: [blk('spike_setvar'), blk('spike_getvar')] }
        : { kind: 'category', name: t.cat_variables, colour: COLORS.variables, custom: 'VARIABLE' },
      { kind: 'category', name: t.cat_more, colour: COLORS.more, contents: [blk('spike_print', { VALUE: { shadow: { type: 'text', fields: { TEXT: 'hi' } } } })] },
    ],
  };
}

// ---------------------------------------------------------------- workspace lifecycle
let ws = null;
let wsHost = null;
let wsLesson = null;

const currentLessonId = () => document.querySelector('[data-lesson-root]')?.dataset.lessonId;
const currentVersion = () => document.querySelector('[data-lesson-root]')?.dataset.programVersion || 'v2';
const currentStoreKey = (lessonId = currentLessonId(), ver = currentVersion()) =>
  `${lessonId || 'program'}_${ver}`;

/** Ports first, then the lesson's variables: [['A','A'], …, ['side','side']]. */
function readScratchPicks(host) {
  const node = document.getElementById('lesson-scratch-vars');
  let names = [];
  try {
    names = node ? JSON.parse(node.textContent) : [];
  } catch (_) {
    names = [];
  }
  const ports = PORTS.map(([v]) => [v, v]);
  const vars = names.filter((n) => !PORTS.some(([v]) => v === n)).map((n) => [n, n]);
  return [...ports, ...vars];
}
const lessonXml = () => document.getElementById('lesson-blocks-xml')?.textContent.trim() || '';

function loadInto(target, lessonId) {
  const Blockly = window.Blockly;
  let saved = null;
  try {
    saved = JSON.parse(localStorage.getItem(STORE_PREFIX + lessonId) || 'null');
  } catch (_) {}
  if (saved) {
    try {
      Blockly.serialization.workspaces.load(saved, target);
      return;
    } catch (err) {
      console.warn('saved blocks unreadable, falling back to the lesson example', err);
      target.clear();
    }
  }
  const xml = lessonXml();
  if (xml) Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(xml), target);
}

function renderPython() {
  const pre = document.getElementById('blocks-python');
  if (pre && ws) pre.textContent = generate(ws);
}

function disposeIfDetached() {
  if (ws && (!wsHost || !wsHost.isConnected)) {
    ws.dispose();
    ws = null;
    wsHost = null;
    wsLesson = null;
  }
}

async function ensureWorkspace() {
  const host = document.getElementById('blockly-host');
  if (!host) return;
  disposeIfDetached();
  if (ws && wsHost === host) {
    window.Blockly.svgResize(ws);
    return;
  }
  const status = host.querySelector('[data-blocks-status]');
  try {
    await loadBlockly();
  } catch (err) {
    console.error(err);
    if (status) status.textContent = JSON.parse(host.dataset.blocksI18n || '{}').blocks_load_failed || err.message;
    return;
  }
  if (!host.isConnected || host.hidden) return;
  const Blockly = window.Blockly;
  disposeIfDetached(); // the workspace of a previous lesson lives in another DOM node
  scratchPicks = readScratchPicks(host);
  scratchMode = host.dataset.blocksMode === 'scratch';
  registerScratchBlocks(); // before inject(): the toolbox references the freshly defined blocks
  host.innerHTML = '';
  ws = Blockly.inject(host, {
    toolbox: toolbox(),
    renderer: 'zelos',
    theme: Blockly.Themes.Zelos || undefined,
    trashcan: true,
    zoom: { controls: true, wheel: true, startScale: 0.72, maxScale: 2, minScale: 0.3 },
    move: { scrollbars: true, drag: true, wheel: false },
    grid: { spacing: 24, length: 2, colour: '#e2e8f0', snap: true },
  });
  wsHost = host;
  wsLesson = currentStoreKey(host.dataset.lessonId, host.dataset.blocksVersion || 'v2');
  loadInto(ws, wsLesson);
  ws.addChangeListener((e) => {
    if (e.isUiEvent) return;
    renderPython();
    try {
      localStorage.setItem(STORE_PREFIX + wsLesson, JSON.stringify(Blockly.serialization.workspaces.save(ws)));
    } catch (_) {}
  });
  renderPython();
}

// Used by the deploy panel: works even if the Blocks tab was never opened.
async function getPython() {
  await loadBlockly();
  disposeIfDetached();
  const key = currentStoreKey();
  if (ws && wsLesson === key) return generate(ws);
  const host = document.getElementById('blockly-host');
  scratchPicks = readScratchPicks(host);
  scratchMode = host?.dataset.blocksMode === 'scratch';
  registerScratchBlocks();
  const tmp = new window.Blockly.Workspace();
  try {
    loadInto(tmp, key);
    return generate(tmp);
  } finally {
    tmp.dispose();
  }
}

window.SpikeBlocks = { getPython, ensureWorkspace, generate: (w) => generate(w) };

document.addEventListener('spike:tab', (ev) => {
  if (ev.detail.name === 'blocks') ensureWorkspace();
});
document.addEventListener('htmx:afterSettle', () => {
  disposeIfDetached();
  if (window.SpikeTabs?.active === 'blocks') ensureWorkspace();
});

document.addEventListener('click', async (ev) => {
  const btn = ev.target.closest('[data-blocks-action]');
  if (!btn) return;
  const action = btn.dataset.blocksAction;
  const host = document.getElementById('blockly-host');
  const ui = JSON.parse(host?.dataset.blocksI18n || '{}');

  if (action === 'reset') {
    if (!ws || !confirm(ui.blocks_reset_confirm)) return;
    localStorage.removeItem(STORE_PREFIX + wsLesson);
    ws.clear();
    loadInto(ws, wsLesson);
    renderPython();
  } else if (action === 'copy') {
    try {
      await navigator.clipboard.writeText(await getPython());
    } catch (_) {
      return;
    }
    const orig = btn.dataset.origLabel || btn.textContent;
    btn.dataset.origLabel = orig;
    btn.textContent = btn.dataset.copiedLabel;
    setTimeout(() => {
      btn.textContent = orig;
    }, 1800);
  } else if (action === 'download') {
    const blob = new Blob([await getPython()], { type: 'text/x-python' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `spike3_${(currentLessonId() || 'program').replace(/-/g, '_')}_blocks.py`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  } else if (action === 'to-hub') {
    const sel = document.querySelector('[data-code-source]');
    if (sel) sel.value = 'blocks';
    window.SpikeTabs?.show('deploy');
    document.getElementById('device-panel')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
});
