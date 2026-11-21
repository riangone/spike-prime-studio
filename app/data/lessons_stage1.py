"""Stage 1 (Grades 1-2): Meet the Hub, First Motors & Engineering Basics.

Lessons:
  01. magic-hub      — Hub + twin-pin bumper rails | Sequence vs timing & button interaction
  02. lucky-spinner  — Hub + Motor A pointer       | Calibration zeroing & smooth deceleration
  03. metronome-arm  — Hub + Motor B + Force A     | Copy-paste drift vs variables & loops
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.cad.assembly import T
from app.cad.models import apply_model, build_model
from app.data import blocks_dsl as B


def _ver_pair(
    *,
    v1_problem: Dict[str, str],
    v1_why: Dict[str, str],
    v1_code: str,
    v1_comments: Dict[str, Dict[str, str]],
    v1_explanations: List[Dict[str, Any]],
    v1_blocks: str,
    v1_scratch: str,
    v1_scratch_vars: List[str],
    v2_fix: Dict[str, str],
    v2_code: str,
    v2_comments: Dict[str, Dict[str, str]],
    v2_explanations: List[Dict[str, Any]],
    v2_blocks: str,
    v2_scratch: str,
    v2_scratch_vars: List[str],
) -> Dict[str, Any]:
    return {
        "v1": {
            "id": "v1",
            "label": T("v1 基础版（发现问题）", "v1 Starter (Spot the Problem)", "v1 基本版（問題を発見）"),
            "badge": T("先跑跑看", "Try First", "まず実行"),
            "problem": v1_problem,
            "why": v1_why,
            "code": v1_code,
            "code_comments": v1_comments,
            "code_explanations": v1_explanations,
            "blocks": v1_blocks,
            "blocks_scratch": v1_scratch,
            "blocks_scratch_vars": v1_scratch_vars,
        },
        "v2": {
            "id": "v2",
            "label": T("v2 改进版（解决问题）", "v2 Improved (Problem Solved)", "v2 改良版（問題を解決）"),
            "badge": T("推荐方案", "Solved", "おすすめ"),
            "fix_summary": v2_fix,
            "code": v2_code,
            "code_comments": v2_comments,
            "code_explanations": v2_explanations,
            "blocks": v2_blocks,
            "blocks_scratch": v2_scratch,
            "blocks_scratch_vars": v2_scratch_vars,
        },
    }


def make_lesson(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Attach verified CAD geometry and expose v2 as the default top-level code/blocks."""
    v2 = spec["versions"]["v2"]
    spec["code"] = v2["code"]
    spec["code_comments"] = v2["code_comments"]
    spec["code_explanations"] = v2["code_explanations"]
    spec["blocks"] = v2["blocks"]
    return apply_model(spec, build_model(spec["id"]))


# ==================================================================================================
# Lesson 01: Magic Emoji Hub
# ==================================================================================================
MAGIC_HUB = make_lesson(
    {
        "id": "magic-hub",
        "level": "stage1",
        "stars": 1,
        "camera": {"pos": [5.2, 4.4, 5.4], "target": [0.0, 0.8, 0.0]},
        "title": T("魔法表情机 (Magic Emoji Hub)", "Magic Emoji Hub", "まほうのひょうじょうハブ"),
        "summary": T(
            "认识 SPIKE Prime 主控并用双销加固侧边护杠；对比 v1 表情一闪而过的问题，学会用等待和按键做出会互动的表情机。",
            "Meet the SPIKE Hub and lock twin-pin side rails; fix flickering v1 icons using pauses and button interaction.",
            "SPIKEハブと2本ピン固定を学び、一瞬で消えるv1の表示を待機とボタン操作で改良します。",
        ),
        "difficulty": T("小学 1-2 年级", "Grades 1-2", "小学1〜2年"),
        "duration": T("10 分钟", "10 min", "10分"),
        "concepts": ["sequence", "light_sound", "event", "debug"],
        "ports": [],
        "steps": [
            {
                "step": 1,
                "title": T("摆好 SPIKE Prime 主控 Hub", "Place the SPIKE Prime Hub", "SPIKEハブを置く"),
                "instruction": T(
                    "将主控（45601）平放桌面，5×5 白色灯阵朝上，两侧留出插销孔。",
                    "Place the Hub (45601) flat with the 5×5 LED matrix facing up.",
                    "ハブ（45601）の5×5 LED面を上にして平らに置きます。",
                ),
                "substeps": [
                    T("把主控（45601）黄色底面平稳放在桌面，5×5 灯阵朝上。", "Set the Hub flat on the table, yellow base down, LEDs up.", "黄色い底を下にして机に置きます。"),
                    T("辨认顶部按键：中间圆形为电源/运行键，左右各有一个方向键。", "Locate the center power button and the Left/Right hub buttons.", "中央の電源ボタンと左右ボタンを確認します。"),
                ],
                "tip": T("后续所有课程都会用到这台主控，侧面和底部共有 44 个乐高标准销孔。", "This Hub has 44 standard Technic pin holes around its sides and base.", "ハブの側面と底面には合計44個のピン穴があります。"),
            },
            {
                "step": 2,
                "title": T("用 2 颗黑销装左侧 11 孔护杠", "Pin Left 11L Guard Rail with 2 Pins", "左側に11Lガードレールを固定"),
                "instruction": T(
                    "在主控左侧前后两端各插 1 颗黑销，再把 11 孔青蓝梁扣紧。",
                    "Insert 2 black pins into the Hub's left front and rear holes, then press on the 11L beam.",
                    "ハブ左側の前後穴に黒ピンを2本挿し、11Lビームを押し込みます。",
                ),
                "substeps": [
                    T("在主控左侧底层第 1 孔与最末孔（前后对称）各插入 1 颗黑色摩擦销（2780）。", "Push 2 black pins (2780) into the left lower front and rear holes.", "ハブ左側下段の前後2か所に黒ピン（2780）を挿します。"),
                    T("取 1 根 11 孔科技梁（32525），用第 2 孔和第 10 孔对准 2 颗黑销按紧。", "Align holes #2 and #10 of an 11L beam (32525) onto the two pins.", "11Lビーム（32525）の2番目と10番目の穴をピンに合わせます。"),
                ],
                "tip": T("试着用手拨一下：插 2 颗销后科技梁完全不会转动！", "Try wiggling it: with 2 pins, the beam cannot spin at all.", "2本ピンで留めるとビームが回らなくなります。"),
            },
            {
                "step": 3,
                "title": T("对称装右侧 11 孔护杠", "Mirror Right 11L Guard Rail", "右側にも11Lガードレールを固定"),
                "instruction": T(
                    "在主控右侧对称插入 2 颗黑销并装上第 2 根 11 孔护杠。",
                    "Mirror the same 2 pins and second 11L beam on the Hub's right side.",
                    "右側にも同じように黒ピン2本と11Lビームを取り付けます。",
                ),
                "substeps": [
                    T("在主控右侧底层前后两端对称插入 2 颗黑色摩擦销（2780）。", "Insert 2 black pins (2780) into the right lower front and rear holes.", "右側下段の前後穴に黒ピンを2本挿します。"),
                    T("扣紧第 2 根 11 孔科技梁（32525），检查左右齐平、不挡任何端口。", "Press on the second 11L beam (32525); verify all 6 ports stay clear.", "2本目の11Lビームを押し込み、A〜Fポートが塞がらないか確認します。"),
                ],
                "tip": T("护杠装在最底层，上方 A–F 六个插口全部保持通畅！", "Because the rails sit along the bottom row, all A–F ports remain accessible.", "下段に付けるのでA〜Fポートはすべて使えます。"),
            },
        ],
        "structure_lab": {
            "why": T(
                "乐高机械第 1 条铁律「两点防转动」：1 颗销是转轴，零件会绕着它甩来甩去；只有插上 2 颗相距较远的销，零件才会牢牢锁死。",
                "Rule #1 of Technic building: one pin acts as a hinge; two spaced-apart pins lock a beam rigidly so it cannot rotate.",
                "テクニック組立の基本ルール「2点固定」：ピン1本だと回転軸になってしまいますが、離れた2本で留めると動かなくなります。",
            ),
            "troubleshoot": [
                T("护杠会晃动？检查是否错用了浅灰无摩擦销（3673），固定结构必须用黑色摩擦销（2780）。", "Beam feels loose? Make sure you used black friction pins (2780), not smooth grey pins (3673).", "ぐらつく場合、灰色のスムースピンではなく黒のフリクションピン（2780）か確認しましょう。"),
                T("端口被挡住了？把 11 孔梁往下移到最底排销孔。", "Ports blocked? Move the 11L beams down to the lowest row of Hub holes.", "ポートが隠れたら、ビームを最下段の穴に付け替えてください。"),
            ],
            "mod_ideas": [
                T("创意提手：用 2 根 3×5 L 形梁（32526）加横梁，在主控上方搭出一个可手提的小手柄。", "Carry Handle: add two 3×5 L-beams (32526) and a crossbeam to carry your Hub like a radio.", "持ち手改造：3×5 L字ビーム2本と横梁でハブ用ハンドルを作ってみよう。"),
                T("斜放桌面支架：在主控尾部垫高 2 孔，让 5×5 表情灯阵微微朝向自己更容易看清。", "Desk Stand: raise the rear side by 2 studs so the 5×5 screen tilts toward you.", "スタンド改造：後ろ側を2ポッチ高くしてLED画面を見やすく傾けよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "点击「运行仿真」看看灯阵：代码写了爱心、笑脸、音符 3 个画面，结果前面 2 个一闪而过根本看不见，瞬间直接跳到了最后一个！",
                "Run the sim and watch the LEDs: you coded 3 icons, but the first two flash past in milliseconds and vanish immediately!",
                "シミュ実行してLEDを見てみよう：3つのアイコンを書いたのに、最初の2つが一瞬で消えて最後しか見えません！",
            ),
            v1_why=T(
                "电脑执行每行代码只要不到 1 毫秒！没有等待时间，后一条 show_image 会立刻把前一条画面盖掉。",
                "The Hub runs each line in under a millisecond! Without pauses, each show_image instantly overwrites the previous one.",
                "ハブは1行を1ミリ秒未満で実行します。待ち時間がないと次の表示がすぐ上書きしてしまいます。",
            ),
            v1_code="""import runloop
from hub import light_matrix

async def main():
    # {{show_three}}
    light_matrix.show_image(light_matrix.IMAGE_HEART)
    light_matrix.show_image(light_matrix.IMAGE_SURPRISED)
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)

runloop.run(main())
""",
            v1_comments={
                "show_three": T(
                    "连续切换 3 个图案，但没有加等待时间——观察仿真会发生什么！",
                    "Switch 3 icons back-to-back with NO pause — watch what happens!",
                    "待ち時間なしで3つのアイコンを連続表示——何が起きるか観察しよう！",
                ),
            },
            v1_explanations=[
                {
                    "lines": "5-8",
                    "title": T("连续切换没有停顿", "Back-to-back Icons Without Pauses", "待ち時間なしの連続表示"),
                    "desc": T("三行 show_image 紧挨着执行，肉眼根本来不及看到爱心和惊讶表情。", "All three show_image lines execute instantly, so your eyes never see the first two.", "3行の show_image が一瞬で実行されるので、最初の2つは目に見えません。"),
                },
            ],
            v1_blocks=B.program(
                B.show_image("HEART"),
                B.show_image("SURPRISED"),
                B.show_image("HAPPY"),
            ),
            v1_scratch=B.program(
                B.show_image("HEART"),
                B.show_image("SURPRISED"),
                B.show_image("HAPPY"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "在每个表情之间加入 await runloop.sleep_ms(700) 留出欣赏时间，配齐音调，并用左键触发惊喜彩蛋！运行后点击仿真条上的「◀ 左键」试试。",
                "Add await runloop.sleep_ms(700) between icons, pair each with a musical tone, and wait for the Hub Left button to trigger a surprise!",
                "各アイコンの間に sleep_ms(700) と音を入れ、左ボタン待ちでサプライズ演出を追加しました！",
            ),
            v2_code="""import runloop
from hub import button, light_matrix, sound

async def main():
    # {{heart}}
    light_matrix.show_image(light_matrix.IMAGE_HEART)
    await sound.beep(523, 250, 100)
    await runloop.sleep_ms(700)

    # {{surprised}}
    light_matrix.show_image(light_matrix.IMAGE_SURPRISED)
    await sound.beep(659, 250, 100)
    await runloop.sleep_ms(700)

    # {{wait_btn}}
    await light_matrix.write("GO")
    while button.pressed(button.LEFT) == 0:
        await runloop.sleep_ms(20)

    # {{happy}}
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)
    await sound.beep(784, 200, 100)
    await sound.beep(1046, 300, 100)

runloop.run(main())
""",
            v2_comments={
                "heart": T("先亮爱心，响 Do (523Hz)，再停留 0.7 秒让人看清", "Show heart, play C5 (523Hz), and hold 0.7s", "ハートを表示してド（523Hz）を鳴らし、0.7秒待つ"),
                "surprised": T("切换惊讶表情，响 Mi (659Hz)，同样停留 0.7 秒", "Switch to surprised face, play E5, hold 0.7s", "びっくり顔に切り替えてミ（659Hz）を鳴らし、0.7秒待つ"),
                "wait_btn": T("滚动提示 GO，并循环等待按下 Hub 左键", "Scroll GO and wait until Hub Left button is pressed", "GO をスクロール表示し、ハブ左ボタンが押されるまで待つ"),
                "happy": T("按键后亮出大笑脸并播放欢呼双音", "Celebrate with a happy face and two-note fanfare", "ボタンが押されたら笑顔と2音のファンファーレでお祝い"),
            },
            v2_explanations=[
                {
                    "lines": "6-8",
                    "title": T("表情 + 声音 + 停顿节拍", "Icon + Sound + Pause", "アイコン＋音＋待ち時間"),
                    "desc": T("sleep_ms(700) 让图案停留 0.7 秒，眼睛和耳朵都能跟上节奏。", "sleep_ms(700) holds the icon for 0.7 seconds so every expression is clearly seen.", "sleep_ms(700) でアイコンを0.7秒表示したままにし、どの表情もはっきり見えます。"),
                },
                {
                    "lines": "16-18",
                    "title": T("等待按键触发互动", "Wait for Left Button Press", "左ボタンが押されるのを待つ"),
                    "desc": T("while 循环每隔 20 毫秒检查一次左键；点仿真栏里的「◀ 左键」立刻进入下一步。", "Checks the Left button every 20 ms until pressed; click 'Left' in the sim bar to trigger.", "20msごとに左ボタンを調べます。シミュバーの「◀ 左」を押すと次へ進みます。"),
                },
            ],
            v2_blocks=B.program(
                B.show_image("HEART"),
                B.beep(523, 250),
                B.wait(0.7),
                B.show_image("SURPRISED"),
                B.beep(659, 250),
                B.wait(0.7),
                B.write("GO"),
                B.wait_until(B.button_pressed("LEFT")),
                B.show_image("HAPPY"),
                B.beep(784, 200),
                B.beep(1046, 300),
            ),
            v2_scratch=B.program(
                B.show_image("HEART"),
                B.beep(523, 250),
                B.wait(0.7),
                B.show_image("SURPRISED"),
                B.beep(659, 250),
                B.wait(0.7),
                B.write("GO"),
                B.wait_until(B.button_pressed("LEFT")),
                B.show_image("HAPPY"),
                B.beep(784, 200),
                B.beep(1046, 300),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("把等待时间改成 300 毫秒，再加第 4 个表情（如 IMAGE_SMILE）组成连环动画。", "Change pauses to 300 ms and add a 4th icon (IMAGE_SMILE) for a mini flipbook.", "待ち時間を300msにして4つ目のアイコンを追加しアニメを作ろう。"),
            T("改造成「左右双键表情切换器」：按左键开心、按右键难过。", "Turn it into a two-button mood switcher: Left = HAPPY, Right = SAD.", "左ボタンでHAPPY、右ボタンでSADに切り替える装置に改造しよう。"),
        ],
    }
)


# ==================================================================================================
# Lesson 02: Lucky Pointer Spinner
# ==================================================================================================
LUCKY_SPINNER = make_lesson(
    {
        "id": "lucky-spinner",
        "level": "stage1",
        "stars": 1,
        "camera": {"pos": [-5.2, 5.4, 5.8], "target": [-1.2, 1.2, 0.8]},
        "title": T("幸运大转盘 (Lucky Spinner)", "Lucky Pointer Spinner", "ラッキールーレット"),
        "summary": T(
            "给主控侧边装上中型电机与带箭头指针梁；解决 v1 每次起点乱飘、急停生硬的问题，加入回零校准与分段减速。",
            "Mount a medium motor and T-arrow pointer; fix v1's drifting start angle and abrupt stop using zero-calibration and staged deceleration.",
            "Mモーターと矢印針を組み立て、v1の原点ずれと急停止を「0度復帰＋段階減速」で改良します。",
        ),
        "difficulty": T("小学 1-2 年级", "Grades 1-2", "小学1〜2年"),
        "duration": T("12 分钟", "12 min", "12分"),
        "concepts": ["motor", "calibration", "loop", "debug"],
        "ports": [
            {
                "port": "A",
                "device": T("中型角度电机 (45603)", "Medium Angular Motor (45603)", "Mアンギュラーモーター (45603)"),
                "note": T("电机直立装在主控左侧，线缆接入左前端口 A", "Mounted upright on Hub left; cable to front-left Port A", "ハブ左側に垂直固定し、左前のポートAへ接続"),
            }
        ],
        "steps": [
            {
                "step": 1,
                "title": T("在主控左侧预插 4 颗黑销", "Pre-insert 4 Black Pins on Hub Left", "ハブ左側に黒ピン4本を挿す"),
                "instruction": T("在主控左侧前后上下 4 个角孔插入黑色摩擦销（2780），准备锁紧电机。", "Insert 4 black pins (2780) into the 4 corner holes on the Hub's left side.", "ハブ左側面の四隅の穴に黒ピン（2780）を4本差し込みます。"),
                "substeps": [
                    T("摆好 SPIKE 主控（45601），5×5 灯阵朝上。", "Place the Hub (45601) flat with LEDs facing up.", "ハブをLED面を上にして置きます。"),
                    T("在主控左侧面的前上、前下、后上、后下 4 个孔各插 1 颗黑销（2780）。", "Insert 4 black pins (2780) into the top/bottom front and rear left holes.", "左側面の上下前後4か所に黒ピンを挿します。"),
                ],
                "tip": T("4 颗销呈矩形分布，电机高速旋转时主控也不会跟着抖动。", "Four corner pins keep the motor rock-solid even at high RPM.", "四隅4本で留めることで高速回転時のブレを防ぎます。"),
            },
            {
                "step": 2,
                "title": T("扣紧中型电机并接端口 A", "Attach Medium Motor & Wire Port A", "Mモーターを装着しポートAへ配線"),
                "instruction": T("将中型电机（45603）输出盘朝上扣入左侧 4 颗销，线缆接入端口 A。", "Press the medium motor (45603) upright onto the 4 left pins and plug into Port A.", "Mモーターを回転盤上向きで4本のピンに押し込み、ポートAに接続します。"),
                "substeps": [
                    T("电机青蓝输出盘朝上，右侧面 4 个销孔对准主控左侧 4 颗黑销按紧。", "Face the teal rotor disc up and press the motor side holes onto the 4 pins.", "回転盤を上にしてハブ左側の4本ピンにしっかり押し込みます。"),
                    T("把电机线绕到上方插入左侧最前的【端口 A】。", "Route the cable cleanly into front-left Port A.", "ケーブルを左前の【ポートA】に差し込みます。"),
                ],
                "wiring": [
                    {
                        "port": "A",
                        "device": T("中型角度电机 (45603)", "Medium Motor (45603)", "Mモーター (45603)"),
                        "route": T("从电机底部引出，绕过侧边向上插入主控左前端口 A。", "Route along the outside up into Hub front-left Port A.", "モーター側面から上へ回し左前のポートAへ差し込みます。"),
                        "check": T("插头卡紧，线缆不要翘起妨碍上方指针旋转。", "Connector clicked in; keep cable clear of the spinning pointer above.", "コネクタが奥まで入り、上の針に当たらないことを確認。"),
                    }
                ],
                "tip": T("转动输出盘，留意盘面上的圆点标记就是电机的绝对 0° 零点。", "The printed dot on the rotor marks the motor's built-in 0° absolute zero.", "回転盤の丸印がモーターの絶対0度位置です。"),
            },
            {
                "step": 3,
                "title": T("在输出盘上组装带箭头指针", "Build the T-Tipped Pointer Arm", "回転盤に矢印付き針を組む"),
                "instruction": T("用 2 颗黑销把 7 孔洋红梁锁在输出盘上，末端再加黄色 3×3 T 形箭头。", "Pin a 7L magenta beam to the rotor with 2 pins, then top the outer tip with a yellow 3×3 T-beam.", "回転盤に黒ピン2本で7Lビームを固定し、先端に黄色いT字ビームを付けます。"),
                "substeps": [
                    T("在电机输出盘左右两个对称孔向上各插 1 颗黑销（2780）。", "Insert 2 black pins vertically into opposite holes on the rotor disc.", "回転盤の左右2穴に黒ピンを上向きに挿します。"),
                    T("将 7 孔洋红梁（32524）水平扣在 2 颗销上，向外伸出作指针。", "Press the 7L magenta beam (32524) flat onto both pins extending outward.", "7Lビーム（32524）を外向きに水平に押し込みます。"),
                    T("在指针最外端 2 个孔向上再插 2 颗黑销，扣上黄色 3×3 T 形梁（60484）做箭头。", "Pin the yellow 3×3 T-beam (60484) onto the outer two holes as an arrow head.", "先端2穴に黒ピン2本で黄色いT字ビーム（60484）を固定します。"),
                ],
                "tip": T("轻转指针一圈：它刚好从主控灯阵上方 1 格高处掠过，完全不擦碰！", "Spin it once by hand: the pointer clears the Hub top cleanly through all 360°.", "手で1周回してハブ上面に当たらないことを確認しましょう。"),
            },
        ],
        "structure_lab": {
            "why": T(
                "指针在电机输出盘上插了 2 颗销而不是 1 颗中心销，这样电机启停瞬间扭矩能 100% 传递，指针绝不会打滑偏位。",
                "Pinning the pointer into two off-center holes on the rotor disc transfers full torque without slipping during fast starts and stops.",
                "回転盤の2つの穴にピンを挿すことで、急加速・急停止でも針が空回りせず確実に回ります。",
            ),
            "troubleshoot": [
                T("指针转到主控上方会刮到线？把端口 A 的线缆往下压平贴紧侧面。", "Pointer hits the wire? Tuck the Port A cable down flush along the Hub side.", "針が線に当たる場合、ポートAのケーブルを側面に沿って押さえます。"),
                T("箭头歪了？检查 T 形梁是否同时插进了指针末端的 2 颗黑销。", "Arrow head twisting? Ensure the T-beam engages both outer black pins.", "矢印がズレる場合、先端2本のピン両方に挿さっているか確認しましょう。"),
            ],
            "mod_ideas": [
                T("对称风车：把指针居中安装（两侧各伸出 3 孔），让重心落在转轴上，高速旋转几乎零震动！", "Balanced Pinwheel: center the beam on the rotor so weight is balanced for vibration-free high-speed spinning.", "バランス風車：ビームを中央に付けて重心を軸に合わせ、高速でもブレない風車に！"),
                T("12 点时钟：在桌面画一圈 12 个数字，把程序改成每 30° 停一格的秒针表盘。", "Clock Dial: draw 12 numbers on paper around the motor and step 30° per tick.", "時計の文字盤：紙に12の数字を書いて30度ずつ進む秒針を作ろう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真观察指针：它不先回零就直接猛转 410° 急刹，再转 410°——连跑两次指针停的角度完全歪掉，也没有抽奖转盘渐渐停下来的感觉！",
                "Watch the pointer: without homing to 0°, spinning 410° at full blast stops abruptly at crooked angles every time!",
                "針を観察しよう：0度に戻さず410度ずつ全力で回して急停止するため、毎回ズレた位置で不自然に止まります。",
            ),
            v1_why=T(
                "没有调用 run_to_absolute_position 归零校准，且全程单一最高速（1000°/s），既没起点基准又缺乏层次感。",
                "Skipping absolute-zero homing leaves arbitrary starting offsets, and one constant max speed makes stopping abrupt.",
                "絶対位置0度へのリセットがなく、ずっと最高速のまま止めるため動きが単調になります。",
            ),
            v1_code="""import runloop
import motor
from hub import light_matrix, port

async def main():
    # {{blind_spin}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
    await motor.run_for_degrees(port.A, 410, 1000)
    await runloop.sleep_ms(300)
    await motor.run_for_degrees(port.A, 410, 1000)

runloop.run(main())
""",
            v1_comments={
                "blind_spin": T("不归零、全程最高速猛转两次 410°——停的位置每次都偏！", "No zeroing, full-speed 410° twice — stops off-mark!", "0度合わせなし・全速410°を2回——印から外れて止まる！"),
            },
            v1_explanations=[
                {
                    "lines": "7-10",
                    "title": T("盲目猛转与角度偏移", "Uncalibrated Full-Speed Spin", "キャリブレーションなしの全速回転"),
                    "desc": T("两次各转 410° 一共 820°（偏出 100°），且没有归零步骤，下次再跑起点全乱。", "Two 410° bursts total 820° (100° off) with no homing reset.", "410°を2回で合計820°（100°ずれ）、しかも原点に戻していません。"),
                },
            ],
            v1_blocks=B.program(
                B.show_image("ARROW_E"),
                B.motor_run_for("A", 410, 1000),
                B.wait(0.3),
                B.motor_run_for("A", 410, 1000),
            ),
            v1_scratch=B.program(
                B.show_image("ARROW_E"),
                B.motor_run_for("A", 410, 1000),
                B.wait(0.3),
                B.motor_run_for("A", 410, 1000),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "开局先 run_to_absolute_position(port.A, 0, 300) 精准回零；接着「高速 720° → 中速 360° → 慢速滴答 4 次各 90°」匀减速收尾，像真转盘一样稳稳停在整圈 0°！",
                "Home to 0° first, then decelerate in 3 stages (720° fast → 360° medium → 4 slow 90° ticks with beeps) so it lands crisply on target!",
                "最初に0度へ原点復帰し、高速720度→中速360度→低速90度×4回のチクタク減速で気持ちよくピタッと止まります。",
            ),
            v2_code="""import runloop
import motor
from hub import light_matrix, port, sound

async def main():
    # {{home}}
    await motor.run_to_absolute_position(port.A, 0, 300)
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)

    # {{fast_med}}
    await motor.run_for_degrees(port.A, 720, 900)
    await motor.run_for_degrees(port.A, 360, 480)

    # {{slow_ticks}}
    for _ in range(4):
        await motor.run_for_degrees(port.A, 90, 220)
        await sound.beep(660, 90, 100)
        await runloop.sleep_ms(120)

    # {{win}}
    light_matrix.show_image(light_matrix.IMAGE_YES)
    await sound.beep(988, 250, 100)

runloop.run(main())
""",
            v2_comments={
                "home": T("先用内置绝对编码器回到 0° 基准起点", "Calibrate pointer back to absolute 0° first", "まず針を絶対0°に戻してキャリブレーション"),
                "fast_med": T("第 1 段 900°/s 高速转 2 圈，第 2 段降到 480°/s 转 1 圈", "Stage 1 fast (2 turns) -> Stage 2 medium (1 turn)", "1段目は速く（2回転）→ 2段目は中速（1回転）"),
                "slow_ticks": T("最后 1 圈拆成 4 次慢速 90° 滴答声，模拟真实转盘阻力减速", "Final turn in 4 slow 90° ticks with beeps", "最後の1回転は90°ずつ4回ゆっくり、ピッ音つき"),
                "win": T("刚好停回整圈终点，亮对勾并响中奖音", "Land cleanly on 0°, show checkmark & chime", "0°ぴったりに止めてチェックマークとチャイム"),
            },
            v2_explanations=[
                {
                    "lines": "7",
                    "title": T("绝对位置回零校准", "Absolute-Zero Calibration", "絶対0°キャリブレーション"),
                    "desc": T("无论拼装完指针歪到哪，run_to_absolute_position(port.A, 0) 都会走最短路径归零。", "Regardless of where the pointer starts, absolute homing snaps it to 0° first.", "針がどこから始まっても、まず絶対位置で0°に戻します。"),
                },
                {
                    "lines": "11-18",
                    "title": T("三段式物理减速手感", "3-Stage Smooth Deceleration", "3段階のなめらか減速"),
                    "desc": T("速度从 900 → 480 → 220 逐级降低，总转角 720+360+4×90 = 1440°（整 4 圈），既顺滑又精准。", "Stepping speed 900 → 480 → 220 over 1440° (4 exact turns) gives realistic wheel inertia.", "速度を 900 → 480 → 220 と下げて1440°（ちょうど4回転）回すと、本物のルーレットのような惰性が出ます。"),
                },
            ],
            v2_blocks=B.program(
                B.motor_go_to("A", 0, 300),
                B.show_image("HAPPY"),
                B.motor_run_for("A", 720, 900),
                B.motor_run_for("A", 360, 480),
                B.repeat(4, B.motor_run_for("A", 90, 220), B.beep(660, 90), B.wait(0.12)),
                B.show_image("YES"),
                B.beep(988, 250),
            ),
            v2_scratch=B.program(
                B.motor_go_to("A", 0, 300),
                B.show_image("HAPPY"),
                B.motor_run_for("A", 720, 900),
                B.motor_run_for("A", 360, 480),
                B.repeat(4, B.motor_run_for("A", 90, 220), B.beep(660, 90), B.wait(0.12)),
                B.show_image("YES"),
                B.beep(988, 250),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("让转盘改成转完 3 圈后再停在 180°（半圈对面位置）。", "Modify the code so the pointer lands at 180° instead of 0°.", "最後に180度の位置で止まるように調整しよう。"),
            T("加入「等待按左键再开始抽奖」，变成多人轮流玩的派对转盘。", "Wrap the spin inside a loop waiting for the Left button so friends can take turns.", "左ボタンを押すたびに回るパーティー用ルーレットにしよう。"),
        ],
    }
)


# ==================================================================================================
# Lesson 03: Musical Metronome Arm
# ==================================================================================================
METRONOME_ARM = make_lesson(
    {
        "id": "metronome-arm",
        "level": "stage1",
        "stars": 2,
        "camera": {"pos": [4.6, 5.2, 6.2], "target": [1.0, 1.2, 0.4]},
        "title": T("音乐节拍摆臂 (Musical Metronome)", "Musical Metronome Arm", "リズムメトロノーム"),
        "summary": T(
            "搭建带力传感器启动按钮的节拍摆臂；修复 v1 复制粘贴导致角度越摆越歪的毛病，学会用变量与循环优雅调速。",
            "Build a swinging metronome with a force-sensor start button; replace v1's drifting copy-paste code with clean variables and loops.",
            "フォースセンサー付きメトロノームを組み立て、v1のコピペによる角度ズレを変数とループで解決します。",
        ),
        "difficulty": T("小学 2-3 年级", "Grades 2-3", "小学2〜3年"),
        "duration": T("15 分钟", "15 min", "15分"),
        "concepts": ["motor", "loop", "variable", "sensor"],
        "ports": [
            {
                "port": "B",
                "device": T("中型角度电机 (45603)", "Medium Angular Motor (45603)", "Mアンギュラーモーター (45603)"),
                "note": T("装在主控右侧，驱动 9 孔节拍摆臂", "Right side of Hub driving the 9L pendulum arm", "ハブ右側に取り付け、9L振り子を駆動"),
            },
            {
                "port": "A",
                "device": T("力传感器 (45606)", "Force Sensor (45606)", "フォースセンサー (45606)"),
                "note": T("装在主控左侧，作为实体节拍开关", "Left side of Hub as a tactile tempo button", "ハブ左側に取り付け、拍子スイッチとして使用"),
            },
        ],
        "steps": [
            {
                "step": 1,
                "title": T("主控右侧安装电机并接端口 B", "Mount Right Motor & Wire Port B", "ハブ右側にモーター装着・ポートB配線"),
                "instruction": T("用 4 颗黑销把中型电机（45603）直立锁在主控右侧，线缆接入端口 B。", "Lock the medium motor upright on the Hub's right side with 4 black pins and plug into Port B.", "ハブ右側に黒ピン4本でMモーターを垂直固定し、ポートBに接続します。"),
                "substeps": [
                    T("在主控右侧面 4 个角孔插入黑色摩擦销（2780）。", "Insert 4 black pins (2780) into the right side corners of the Hub.", "ハブ右側の四隅に黒ピンを4本挿します。"),
                    T("把中型电机（45603）输出盘朝上扣紧，线缆接入右前【端口 B】。", "Press the motor upright onto the pins and plug into front-right Port B.", "回転盤を上にして押し込み、右前の【ポートB】に接続します。"),
                ],
                "wiring": [
                    {
                        "port": "B",
                        "device": T("中型角度电机 (45603)", "Medium Motor (45603)", "Mモーター (45603)"),
                        "route": T("从右侧电机绕至主控右前端口 B。", "Route into Hub front-right Port B.", "右モーターからハブ右前のポートBへ接続。"),
                        "check": T("插紧卡扣，电线贴身不翘起。", "Connector clicks in flush.", "カチッと奥まで差し込みます。"),
                    }
                ],
                "tip": T("确认电机底部与主控底面齐平，整机平放桌面不翘角。", "Ensure the motor base sits flush with the Hub bottom on the table.", "モーター底面とハブ底面が揃うか確認します。"),
            },
            {
                "step": 2,
                "title": T("拼装 9 孔长摆臂与洋红锤头", "Assemble 9L Pendulum Arm & Mallet", "9L振り子アームとマレットを組む"),
                "instruction": T("在输出盘上用 2 颗黑销固定 9 孔青蓝梁，末端加洋红 3×3 T 形摆锤。", "Pin a 9L azure beam onto the rotor with 2 pins and cap the tip with a magenta 3×3 T-beam.", "回転盤に9Lビームを2本ピン固定し、先端にマゼンタのT字ヘッドを付けます。"),
                "substeps": [
                    T("在右电机输出盘插 2 颗黑销，扣上 9 孔青蓝梁（40490）向右伸出。", "Pin the 9L azure beam (40490) onto the rotor extending outward to the right.", "右回転盤に黒ピン2本で9Lビーム（40490）を外向きに固定します。"),
                    T("在 9 孔梁最外端 2 孔向上插 2 颗黑销，装上洋红 T 形梁（60484）做节奏锤头。", "Pin the magenta 3×3 T-beam (60484) onto the outer 2 holes as the mallet.", "先端2穴に黒ピン2本でT字ビーム（60484）を固定します。"),
                ],
                "tip": T("摆臂只在 ±60° 范围内左右摇摆，不会扫到左侧力传感器。", "The arm swings within ±60° so it always stays clear of the left sensor.", "アームは±60度で振れるため左側センサーに当たりません。"),
            },
            {
                "step": 3,
                "title": T("主控左侧加装力传感器并接端口 A", "Mount Force Sensor & Wire Port A", "左側にフォースセンサー装着・ポートA配線"),
                "instruction": T("在主控左前上下 2 孔插黑销，扣紧力传感器（45606）柱塞朝前，线缆接入端口 A。", "Pin the force sensor (45606) onto the Hub's front-left holes facing forward and wire Port A.", "ハブ左前の2穴にフォースセンサー（45606）を前向きに固定し、ポートAへ接続します。"),
                "substeps": [
                    T("在主控左前上下两孔各插 1 颗黑色摩擦销（2780）。", "Insert 2 black pins into the upper and lower front-left Hub holes.", "ハブ左前の上下2穴に黒ピンを挿します。"),
                    T("把力传感器（45606）黑色按压柱塞朝前，右侧两孔对准黑销按紧，线接入【端口 A】。", "Press the force sensor onto the pins with its plunger facing forward; plug into Port A.", "押しボタンを前向きにして押し込み、【ポートA】に接続します。"),
                ],
                "wiring": [
                    {
                        "port": "A",
                        "device": T("力传感器 (45606)", "Force Sensor (45606)", "フォースセンサー (45606)"),
                        "route": T("从力传感器尾部直接弯入左侧前端端口 A。", "Loop cleanly from rear of force sensor into Port A.", "センサー後部から左前のポートAへ接続。"),
                        "check": T("按压黑色柱塞有清晰弹性回弹感。", "Press the black plunger to confirm smooth spring return.", "ボタンがスムーズに押して戻ることを確認。"),
                    }
                ],
                "tip": T("在 3D 仿真里点击工具栏「🔘 力传感器」按钮就能实时按下柱塞！", "Click the 'Force' button in the simulator bar to press the 3D plunger live!", "シミュバーの「フォース」ボタンで3Dボタンをリアルタイムに押せます。"),
            },
        ],
        "structure_lab": {
            "why": T(
                "摆臂越长、末端锤头越重，旋转惯性越大，摆动看起来越有节拍器韵律；同时力传感器垂直于底座，手指按压时不会把整台机器推跑。",
                "A longer arm with mass at the tip increases rotational inertia for a crisp metronome beat, while side-pinning the force sensor resists finger push.",
                "アーム先端の重りで振り子らしいリズム感が生まれ、センサーを側面に2点固定することで押してもズレません。",
            ),
            "troubleshoot": [
                T("摆臂越摆越歪？不是积木装错，通常是程序里左转和右转角度写不一致造成的！", "Arm drifting crooked? Usually not a build error — check if left and right motor degrees match!", "だんだん傾く場合、左右の回転角度がプログラムで揃っていないことが多いです。"),
                T("按力传感器整机滑动？检查力传感器底面是否与主控齐平接触桌面。", "Whole unit slides when pressing? Check that the force sensor bottom sits flush on the desk.", "押すと動く場合、センサー底面が机にしっかり接しているか確認しましょう。"),
            ],
            "mod_ideas": [
                T("招财猫挥手：把摆臂竖起来（电机侧装），再在顶端贴一张手绘小猫爪卡片！", "Lucky Cat: mount the motor sideways so the arm waves up and down instead of left and right.", "招き猫改造：モーターを横向きに付けて上下に手を振るロボットにしよう。"),
                T("小鼓手：在摆锤前方立一个空纸杯当小鼓，调好角度让每拍刚好轻敲杯壁！", "Mini Drummer: place a paper cup in the swing path and tune the angle to tap it on every beat.", "ミニドラマー：紙コップを置いて毎拍ちょうど叩く角度を調整しよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真观察摆臂：程序员偷懒复制粘贴了 4 段左右摆动，还不小心把其中两次向左写成了 -45°（向右是 +60°）——结果摆臂越摆越歪，停下来彻底歪在一边，想改快慢还要手动改 8 个数字！",
                "Watch the arm: copy-pasting 4 beats introduced a typo (+60° vs -45°), so the arm drifts further off-center every beat, and changing tempo means editing 8 places!",
                "振り子を観察：コピペした4拍の中で角度を間違え（+60度と-45度）、どんどん傾いて戻らなくなります。テンポ変更も8か所修正が必要！",
            ),
            v1_why=T(
                "重复代码既容易手滑写错数字造成累积误差，又极难修改维护。这正是引入「变量」和「循环」的最佳理由。",
                "Duplicated code invites asymmetric typos that accumulate drift and makes tuning speed painful. Variables and loops solve both at once.",
                "同じ処理のコピペはタイプミスによる累積誤差と修正の手間を生みます。変数とループの出番です。",
            ),
            v1_code="""import runloop
import motor
from hub import light_matrix, port, sound

async def main():
    # {{copy_paste}}
    light_matrix.show_image(light_matrix.IMAGE_HEART)
    await motor.run_for_degrees(port.B, 60, 400)
    await sound.beep(660, 120, 100)
    await motor.run_for_degrees(port.B, -45, 400)
    await sound.beep(440, 120, 100)
    await motor.run_for_degrees(port.B, 60, 400)
    await sound.beep(660, 120, 100)
    await motor.run_for_degrees(port.B, -45, 400)
    await sound.beep(440, 120, 100)

runloop.run(main())
""",
            v1_comments={
                "copy_paste": T("复制粘贴写节拍：右转 60° 却只左回 45°，越摆越偏！", "Copy-pasted beats: +60° right but only -45° back — drifts crooked!", "コピペしたビート：右へ+60°なのに戻りは-45°——どんどん傾く！"),
            },
            v1_explanations=[
                {
                    "lines": "8-15",
                    "title": T("手滑不对称导致的累积偏移", "Accumulated Drift from Copy-Paste", "コピペによるずれの蓄積"),
                    "desc": T("每轮净偏移 +15°，两轮就偏了 +30°，而且改一次速度要改 4 行。", "Each cycle drifts +15° (+30° after 2 beats), and changing speed requires editing 4 lines.", "1往復ごとに+15°ずれ（2拍で+30°）、速度を変えるにも4行を直す必要があります。"),
                },
            ],
            v1_blocks=B.program(
                B.show_image("HEART"),
                B.motor_run_for("B", 60, 400),
                B.beep(660, 120),
                B.motor_run_for("B", -45, 400),
                B.beep(440, 120),
                B.motor_run_for("B", 60, 400),
                B.beep(660, 120),
                B.motor_run_for("B", -45, 400),
                B.beep(440, 120),
            ),
            v1_scratch=B.program(
                B.show_image("HEART"),
                B.motor_run_for("B", 60, 400),
                B.beep(660, 120),
                B.motor_run_for("B", -45, 400),
                B.beep(440, 120),
                B.motor_run_for("B", 60, 400),
                B.beep(660, 120),
                B.motor_run_for("B", -45, 400),
                B.beep(440, 120),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "用 swing 和 speed 两个变量统一管理，放进 for 循环自动完成 4/4 拍（强-弱-次强-弱）；按下力传感器还能实时切换快板，结束后自动精准归中到 0°！",
                "Extract swing & speed variables inside a clean 4-beat loop (accent on beat 1), let the force sensor boost tempo live, and auto-center to 0°!",
                "swing と speed を変数にして4拍ループに統一。フォースセンサー押下で倍速切替でき、終了時は0度へ綺麗に帰還します。",
            ),
            v2_code="""import runloop
import motor
import force_sensor
from hub import light_matrix, port, sound

async def main():
    # {{setup_vars}}
    swing = 55
    speed = 420
    await motor.run_to_absolute_position(port.B, 0, 300)

    # {{beat_loop}}
    for beat in range(4):
        if force_sensor.pressed(port.A):
            speed = 720
        light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
        await motor.run_for_degrees(port.B, swing, speed)
        await sound.beep(660 if beat == 0 else 440, 110, 100)

        light_matrix.show_image(light_matrix.IMAGE_ARROW_W)
        await motor.run_for_degrees(port.B, -swing, speed)
        await sound.beep(440, 110, 100)

    # {{center}}
    await motor.run_to_absolute_position(port.B, 0, 300)
    light_matrix.show_image(light_matrix.IMAGE_YES)

runloop.run(main())
""",
            v2_comments={
                "setup_vars": T("把摆幅和速度存进变量，改一处全局生效；先归零对齐", "Store swing & speed in variables and home to 0°", "振れ幅と速度を変数にまとめ、0°に戻す"),
                "beat_loop": T("4 拍循环：第 1 拍重音 660Hz，其余弱音 440Hz；按力传感器提速！", "4-beat loop: accent beat 1 (660Hz), press force sensor for fast tempo!", "4拍ループ：1拍目は強拍（660Hz）、フォースセンサーを押すとテンポアップ！"),
                "center": T("演奏完毕精准回中并亮对勾", "Return cleanly to center 0° and show YES", "中央0°にきれいに戻って YES を表示"),
            },
            v2_explanations=[
                {
                    "lines": "8-10",
                    "title": T("变量集中管理参数", "Centralized Variables", "変数でまとめて管理"),
                    "desc": T("用同一个 swing 变量做 +swing 和 -swing，从根源消灭左右不对称偏移。", "Reusing one swing variable for +swing and -swing eliminates asymmetry forever.", "+swing と -swing に同じ変数を使うので、左右のずれが二度と起きません。"),
                },
                {
                    "lines": "13-22",
                    "title": T("循环 + 力传感器实时变速", "Loop + Live Force-Sensor Tempo Boost", "ループ＋フォースセンサーでリアルタイムにテンポアップ"),
                    "desc": T("for 循环让代码缩短一半；运行中点击「🔘 力传感器」立刻加速到 720°/s！", "The loop halves code length; toggling Force Sensor boosts speed to 720°/s live!", "ループでコードが半分になり、フォースセンサーを押すと速度が 720°/s に上がります！"),
                },
            ],
            v2_blocks=B.program(
                B.set_var("swing", 55),
                B.set_var("speed", 420),
                B.motor_go_to("B", 0, 300),
                B.repeat(
                    4,
                    B.if_(B.force_pressed("A"), B.set_var("speed", 720)),
                    B.show_image("ARROW_E"),
                    B.motor_run_for("B", B.var("swing"), B.var("speed")),
                    B.beep(660, 110),
                    B.show_image("ARROW_W"),
                    B.motor_run_for("B", B.arith(0, "-", B.var("swing")), B.var("speed")),
                    B.beep(440, 110),
                ),
                B.motor_go_to("B", 0, 300),
                B.show_image("YES"),
                variables=["swing", "speed"],
            ),
            v2_scratch=B.program(
                B.set_var_named("swing", 55),
                B.set_var_named("speed", 420),
                B.motor_go_to("B", 0, 300),
                B.repeat(
                    4,
                    B.if_(B.force_pressed("A"), B.set_var_named("speed", 720)),
                    B.show_image("ARROW_E"),
                    B.motor_run_for("B", B.get_var("swing"), B.get_var("speed")),
                    B.beep(660, 110),
                    B.show_image("ARROW_W"),
                    B.motor_run_for("B", B.arith(0, "-", B.get_var("swing")), B.get_var("speed")),
                    B.beep(440, 110),
                ),
                B.motor_go_to("B", 0, 300),
                B.show_image("YES"),
                variables=["swing", "speed"],
            ),
            v2_scratch_vars=["swing", "speed"],
        ),
        "challenges": [
            T("把 4/4 拍改成 3/4 拍圆舞曲（每 3 拍 1 个重音，循环 3 次）。", "Change from 4/4 time to a 3/4 waltz (3 beats per bar).", "4/4拍子を3/4拍子のワルツに書き換えよう。"),
            T("用变量 tone 让每一拍的音高递增 60 Hz，听听爬音阶效果。", "Use a tone variable that increases by +60 Hz each beat to climb a scale.", "変数 tone を毎拍+60Hz増やして音階を上がってみよう。"),
        ],
    }
)

STAGE1_LESSONS = [MAGIC_HUB, LUCKY_SPINNER, METRONOME_ARM]
