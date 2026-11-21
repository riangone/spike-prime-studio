"""Stage 2 (Grades 2-4): Differential Driving Base & Precision Navigation.

Lessons:
  04. driving-base    — Classic 3-point Driving Base     | Same-sign spin bug vs motor_pair.pair
  05. square-patrol   — Driving Base + 11L front bumper  | Uncalibrated 90° bug vs wheelbase calibration
  06. gyro-precision  — Driving Base + compass arrow     | Full-speed gyro overshoot vs proportional braking
"""
from __future__ import annotations

from app.cad.assembly import T
from app.data import blocks_dsl as B
from app.data.lessons_stage1 import _ver_pair, make_lesson

# Shared Step 1 text for follow-up lessons that reuse the completed Driving Base
REUSE_BASE_STEP = {
    "step": 1,
    "title": T("沿用第 4 课完成的差速小车", "Start from Lesson 4 Driving Base", "レッスン4の基本ドライブベースを用意"),
    "instruction": T(
        "直接使用已装好左右轮、万向珠和 C/D 接线的经典差速小车作为底盘。",
        "Reuse your completed Driving Base with wheels, ball caster, and Ports C/D wired.",
        "タイヤ・キャスター・C/D配線済みの基本ドライブベースをそのまま使います。",
    ),
    "substeps": [
        T("检查左电机接端口 C、右电机接端口 D，车轮转动顺畅无刮擦。", "Verify Left Motor → Port C, Right Motor → Port D, wheels spin freely.", "左モーター→C、右モーター→Dを確認し、タイヤがスムーズに回るか見ます。"),
        T("确认主控前端两颗销孔空着，准备加装本课模块。", "Ensure the Hub's front pin holes are open for the new attachment.", "ハブ前面のピン穴が空いていることを確認します。"),
    ],
    "tip": T("模块化底盘的好处：不用每次拆车，几秒钟就能换装新任务模块！", "Modular chassis advantage: swap front attachments in seconds without rebuilding!", "モジュラー車台なら毎回解体せずに数秒で新モジュールを増設できます。"),
}

DRIVE_PORTS = [
    {
        "port": "C",
        "device": T("左驱动轮 · 中型电机 (45603)", "Left Drive · Medium Motor (45603)", "左駆動輪 · Mモーター (45603)"),
        "note": T("接入主控左侧中间端口 C", "Plug into Hub left-middle Port C", "ハブ左中央のポートCへ接続"),
    },
    {
        "port": "D",
        "device": T("右驱动轮 · 中型电机 (45603)", "Right Drive · Medium Motor (45603)", "右駆動輪 · Mモーター (45603)"),
        "note": T("接入主控右侧中间端口 D", "Plug into Hub right-middle Port D", "ハブ右中央のポートDへ接続"),
    },
]


# ==================================================================================================
# Lesson 04: Driving Base
# ==================================================================================================
DRIVING_BASE = make_lesson(
    {
        "id": "driving-base",
        "level": "stage2",
        "stars": 2,
        "camera": None,
        "title": T("经典差速小车 (Driving Base)", "Classic Driving Base", "基本ドライブベース"),
        "summary": T(
            "5 步拼出两轮一珠三点支撑差速小车；在 3D 里亲眼见证 v1 两轮同号导致原地打转，再用 motor_pair 稳稳驶入绿色停车区。",
            "Build a 3-point differential drive car in 5 steps; see why v1 spins in circles, then use motor_pair to park neatly on the green mat.",
            "5ステップで3点支持ドライブベースを組立。v1のその場回転バグを motor_pair で直進駐車へ改良します。",
        ),
        "difficulty": T("小学 2-3 年级", "Grades 2-3", "小学2〜3年"),
        "duration": T("15 分钟", "15 min", "15分"),
        "concepts": ["movement", "motor", "debug"],
        "ports": DRIVE_PORTS,
        "steps": [
            {
                "step": 1,
                "title": T("准备主控 Hub（车头朝前）", "Orient the Hub (USB Rear)", "ハブの向きを合わせる"),
                "instruction": T("将 SPIKE 主控（45601）水平放置，5×5 灯阵朝上，USB 充电口朝车尾方向。", "Hold the Hub (45601) flat with LEDs up and the USB port facing the rear.", "ハブのLED面を上に、USBポートを後ろ向きにします。"),
                "substeps": [
                    T("确认 A/B 端口靠车头、C/D 端口在正中、E/F 端口靠车尾。", "Check that Ports A/B are forward, C/D middle, and E/F rear.", "A/Bが前、C/Dが中央、E/Fが後ろ側になる向きを確認します。"),
                ],
                "tip": T("整车采用「主控兼作车架」的极简结构，零件少、重心稳、拆装超快！", "Using the Hub itself as the core frame keeps the chassis compact, rigid, and fast to build.", "ハブ自体をフレームにするため部品が少なく丈夫に組めます。"),
            },
            {
                "step": 2,
                "title": T("用 2 颗黑销固定左侧驱动电机", "Pin Left Medium Motor (Port C)", "左駆動モーターを固定（ポートC）"),
                "instruction": T("在主控左前侧上下两孔插黑销，扣紧左侧中型电机（45603），输出盘朝左外侧。", "Insert 2 black pins on the Hub's front-left side and mount the left motor with rotor facing left.", "ハブ左前の上下2穴に黒ピンを挿し、回転盤を左外側にして左モーターを固定します。"),
                "substeps": [
                    T("在主控左前侧上孔和下孔各插 1 颗黑色摩擦销（2780）。", "Insert 2 black pins (2780) into the upper and lower front-left Hub holes.", "ハブ左前の上下穴に黒ピン2本を挿します。"),
                    T("把左侧中型电机（45603）输出盘朝左、线缆朝后，对准 2 颗黑销按紧。", "Press the left motor onto the pins with its output disc facing left and cable trailing rear.", "回転盤を左、ケーブルを後ろに向けてしっかり押し込みます。"),
                ],
                "tip": T("电机本体向车尾延伸，与主控侧边贴得严丝合缝。", "The motor body runs neatly back along the Hub's left side.", "モーター本体がハブ側面にぴったり沿います。"),
            },
            {
                "step": 3,
                "title": T("对称固定右侧驱动电机", "Mirror Right Medium Motor (Port D)", "右駆動モーターを対称固定（ポートD）"),
                "instruction": T("在主控右前侧对称插 2 颗黑销，扣紧右侧中型电机（45603），输出盘朝右外侧。", "Mirror 2 black pins on the front-right side and press on the right motor facing outward.", "右側にも黒ピン2本を挿し、回転盤を右外側にして右モーターを対称固定します。"),
                "substeps": [
                    T("在主控右前侧上下两孔对称插入 2 颗黑色摩擦销（2780）。", "Insert 2 black pins into the upper and lower front-right holes.", "ハブ右前の上下穴に黒ピン2本を挿します。"),
                    T("把右侧中型电机（45603）输出盘朝右、线缆朝后按紧，确认左右完全对齐。", "Press the right motor flush with its rotor facing right; check left-right symmetry.", "回転盤を右、ケーブルを後ろに向けて左右対称に押し込みます。"),
                ],
                "tip": T("注意看：左右电机像照镜子一样面对面装，待会编程会揭晓这带来什么有趣现象！", "Notice both motors are mirrored — v1 code will show you a classic surprise this causes!", "左右が鏡合わせの向きになっている点に注目——v1のコードで面白い現象が起きます！"),
            },
            {
                "step": 4,
                "title": T("装十字轴与左右 56mm 驱动轮", "Mount 3L Axles & 56mm Drive Wheels", "3L十字軸と56mmタイヤを装着"),
                "instruction": T("在两侧电机输出盘中心插 3L 十字轴（4519），再套上两个 56mm 驱动轮（39367）。", "Insert two 3L axles (4519) into both rotors, then slide on the two 56mm wheels (39367).", "両モーター中心に3L十字軸（4519）を挿し、56mmタイヤ（39367）を押し込みます。"),
                "substeps": [
                    T("将 2 根 3L 浅灰十字轴（4519）分别插进左右电机中心十字孔到底。", "Push one 3L grey axle (4519) fully into each motor's center axle hole.", "3L十字軸を左右の回転盤中央の十字穴へ奥まで挿します。"),
                    T("套上 2 个 56mm 驱动轮（39367），轮毂与电机壳之间留约 1mm 缝隙防摩擦。", "Slide on both 56mm wheels (39367), leaving ~1 mm clearance from the motor casing.", "56mmタイヤを挿し、モーター本体との間に1mmほど隙間を空けます。"),
                ],
                "tip": T("56mm 车轮每转整 1 圈（360°），小车在地面正好前进 56 × 3.14 ≈ 17.6 厘米！", "One full turn (360°) of a 56 mm wheel rolls exactly 56 × π ≈ 17.6 cm!", "56mmタイヤ1回転（360度）で約17.6cm進みます！"),
            },
            {
                "step": 5,
                "title": T("装后部万向钢珠轮并完成 C/D 接线", "Attach Rear Ball Caster & Wire C / D", "後部キャスター装着とC/D配線"),
                "instruction": T("用 7 孔横梁和 2 颗蓝色 3L 长销把万向轮（39370）锁在车尾，再把左右电机插入端口 C 和 D。", "Lock the 7L rear beam and ball caster (39370) with two blue 3L pins (6558), then wire Ports C and D.", "7Lビームと青ロングピン2本で後部キャスター（39370）を固定し、C・Dへ配線します。"),
                "substeps": [
                    T("将 7 孔灰梁（32524）贴在主控尾部上方，后方对准万向轮支架（39370）两耳。", "Hold the 7L beam (32524) across the Hub rear with the caster housing (39370) behind it.", "ハブ後端に7Lビームを当て、その背後にキャスター（39370）を重ねます。"),
                    T("用 2 颗蓝色 3L 长销（6558）从后往前一次穿过万向轮 + 7 孔梁 + 主控尾孔锁死。", "Push 2 blue 3L pins (6558) forward through caster + 7L beam + Hub rear holes.", "青3Lピン2本でキャスター＋7Lビーム＋ハブを一気に貫通固定します。"),
                    T("把左电机插入【端口 C】，右电机插入【端口 D】。", "Plug Left Motor into Port C and Right Motor into Port D.", "左モーターを【ポートC】、右モーターを【ポートD】に接続します。"),
                ],
                "wiring": [
                    {
                        "port": "C",
                        "device": T("左驱动电机 (45603)", "Left Drive Motor (45603)", "左駆動モーター (45603)"),
                        "route": T("沿左侧上方接入主控左中端口 C。", "Route neatly up into Hub left-middle Port C.", "左側面上方から左中央のポートCへ接続。"),
                        "check": T("电线远离左轮橡胶胎。", "Keep cable clear of the left tire.", "左タイヤに当たらないことを確認。"),
                    },
                    {
                        "port": "D",
                        "device": T("右驱动电机 (45603)", "Right Drive Motor (45603)", "右駆動モーター (45603)"),
                        "route": T("沿右侧上方接入主控右中端口 D。", "Route neatly up into Hub right-middle Port D.", "右側面上方から右中央のポートDへ接続。"),
                        "check": T("电线远离右轮橡胶胎。", "Keep cable clear of the right tire.", "右タイヤに当たらないことを確認。"),
                    },
                ],
                "tip": T("放在桌面上看：前两轮和后钢珠刚好同时落地，车身完全水平！", "Set it on the floor: both 56 mm wheels and the rear steel ball touch evenly!", "机に置くと左右タイヤと後部ボールの3点が綺麗に水平接地します。"),
            },
        ],
        "structure_lab": {
            "why": T(
                "「前两轮 + 后一万向珠」是经典三点支撑：三个点一定稳稳落在一个平面上（像三脚架一样绝不翘脚），而且万向珠 360° 灵活滚动，转弯几乎没有侧向阻力。",
                "Two drive wheels plus one rear ball caster form a 3-point tripod: it never wobbles on uneven floors and pivots smoothly with low friction.",
                "前2輪＋後部ボールの3点支持は三脚のようにガタつかず、旋回時の横抵抗も最小限になります。",
            ),
            "troubleshoot": [
                T("小车跑起来往一边偏？检查两个车轮是否都留出 1mm 间隙，不要把某一边车轮硬顶到电机外壳上。", "Car curves to one side? Make sure neither wheel is pressed tightly against the motor housing.", "まっすぐ走らない場合、タイヤがモーター本体に擦れていないか1mm隙間を確認しましょう。"),
                T("后万向轮松动？确认蓝色 3L 长销（6558）同时穿过了万向轮、7 孔梁和主控三层。", "Caster feels wobbly? Verify the blue 3L pins pass through all 3 layers (caster + beam + Hub).", "キャスターが緩い場合、青3Lピンが3層すべて貫通しているか確認します。"),
            ],
            "mod_ideas": [
                T("加装载货篮：在主控顶部四角孔搭一个 7×11 开放框架（39794），变成能运文具的快递车。", "Cargo Basket: pin a 7×11 frame (39794) on top of the Hub to carry pencils or bricks.", "荷台カスタム：ハブ上に7×11フレームを載せて小物運搬カーにしよう。"),
                T("高底盘越野改装：用 5×7 框架把主控架高，给车底留出更大离地间隙。", "Off-Road Lift: raise the Hub on a 5×7 frame for extra ground clearance.", "ハイリフト改造：5×7フレームで車高を上げて段差に強くしよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看看：我们想让左右两轮一起正转 400°/s 向前开进绿色停车区，结果小车居然在原地疯狂打转，一步也没往前走！",
                "Run v1 and watch: we told both motors C and D to spin at +400°/s to drive straight — instead, the car spins wildly in place!",
                "v1を実行してみよう：CとDを両方+400度/秒で回したのに、前進せずその場でグルグル回ってしまいます！",
            ),
            v1_why=T(
                "因为左右电机是「镜像面对面」安装的！对着左轮轴看顺时针转（+）是往后倒车，对着右轮轴看顺时针转（+）才是往前开——两个轮子一个往前一个往后，当然原地打转！",
                "Left and right motors are mounted face-to-face as mirrors! Positive (+deg) drives the right wheel forward but reverses the left wheel — causing an instant spin!",
                "左右のモーターは鏡合わせに付いているため、同じプラス回転でも左輪は後退・右輪は前進になり、その場旋回してしまいます。",
            ),
            v1_code="""import runloop
import motor
from hub import light_matrix, port

async def main():
    # {{both_pos}}
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)
    motor.run(port.C, 400)
    motor.run(port.D, 400)
    await runloop.sleep_ms(1800)
    motor.stop(port.C)
    motor.stop(port.D)

runloop.run(main())
""",
            v1_comments={
                "both_pos": T("直接让 C 和 D 同号正转——镜像安装会让小车原地打转！", "Running C and D at the same +400 sign spins mirrored motors in place!", "C と D を同じ +400 で回すと、向かい合わせのモーターでその場回転！"),
            },
            v1_explanations=[
                {
                    "lines": "8-9",
                    "title": T("镜像电机的经典方向陷阱", "The Mirrored-Motor Direction Trap", "向かい合わせモーターの回転方向のわな"),
                    "desc": T("左轮（C）正转向后滚，右轮（D）正转向右前滚，小车像陀螺一样原地自转。", "Port C (+400) rolls backward while Port D (+400) rolls forward — spinning in place.", "ポートC（+400）は後ろへ、ポートD（+400）は前へ転がり、その場でくるくる回ります。"),
                },
            ],
            v1_blocks=B.program(
                B.show_image("SAD"),
                B.motor_start("C", 400),
                B.motor_start("D", 400),
                B.wait(1.8),
                B.motor_stop("C"),
                B.motor_stop("D"),
            ),
            v1_scratch=B.program(
                B.show_image("SAD"),
                B.motor_start("C", 400),
                B.motor_start("D", 400),
                B.wait(1.8),
                B.motor_stop("C"),
                B.motor_stop("D"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "用官方 motor_pair.pair(PAIR_1, port.C, port.D) 把左右轮配成差速对，SPIKE 3 会自动帮左轮反向！转动 720°（整 2 圈 ≈ 35.2cm），笔直停进绿色目标区！",
                "Pair C and D with motor_pair.pair() so SPIKE 3 handles the left-wheel inversion automatically. Driving 720° (2 turns ≈ 35.2 cm) parks dead-center on the green mat!",
                "motor_pair.pair() で左右をペアリングすれば反転は自動処理！720度（2回転≒35.2cm）で緑のゴールへ一直線に駐車します。",
            ),
            v2_code="""import runloop
import motor_pair
from hub import light_matrix, port, sound

async def main():
    # {{pair}}
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)

    # {{drive}}
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, 720, 0, velocity=400)

    # {{parked}}
    motor_pair.stop(motor_pair.PAIR_1)
    light_matrix.show_image(light_matrix.IMAGE_HEART)
    await sound.beep(784, 220, 100)

runloop.run(main())
""",
            v2_comments={
                "pair": T("把 C（左）与 D（右）绑定为差速驱动对 PAIR_1", "Pair Port C (left) and Port D (right) as PAIR_1", "ポートC（左）とポートD（右）を PAIR_1 としてペアにする"),
                "drive": T("steering=0 笔直前进 720°（2 圈 ≈ 35.2 厘米）直达绿色停车垫", "steering=0 drives straight 720° (2 wheel turns ≈ 35.2 cm) onto green pad", "steering=0 で720°（車輪2回転 ≈ 35.2cm）まっすぐ走り、緑のパッドへ"),
                "parked": T("稳稳停车，亮爱心并欢呼一声", "Stop cleanly, show heart & chime", "きれいに止まってハートとチャイム"),
            },
            v2_explanations=[
                {
                    "lines": "7",
                    "title": T("差速配对自动反向", "Differential Pair Auto-Inversion", "差動ペアの自動反転"),
                    "desc": T("配对后，steering=0 就是绝对直线前进，不用再手动算哪边要加负号。", "Once paired, steering=0 drives perfectly straight with automatic left/right sign handling.", "ペアにすると左右の符号を自動で処理し、steering=0 でまっすぐ走ります。"),
                },
                {
                    "lines": "11",
                    "title": T("用轮子周长算精准距离", "Calculate Distance from Wheel Circumference", "車輪の円周から距離を計算"),
                    "desc": T("56mm 轮子 1 圈 17.6cm，绿色停车区在 35.2cm 处，所以正好填 720°。", "One 56 mm wheel turn is 17.6 cm, so 720° (2 turns) lands squarely at 35.2 cm.", "56mm車輪の1回転は17.6cm、720°（2回転）でちょうど35.2cm進みます。"),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.move_for(720, 0, 400),
                B.move_stop(),
                B.show_image("HEART"),
                B.beep(784, 220),
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.move_for(720, 0, 400),
                B.move_stop(),
                B.show_image("HEART"),
                B.beep(784, 220),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("算一算：如果要开到 52.8 厘米远（刚好 3 圈），720 应该改成多少度？", "Math challenge: how many degrees to roll 52.8 cm (3 full wheel turns)?", "計算しよう：52.8cm（タイヤ3回転）進むには何度にすればいい？"),
            T("让小车停进绿区后响一声，再倒车（填 -720）准确退回起跑线！", "After reaching the green zone, reverse (-720°) cleanly back to the start line!", "緑マットで音を鳴らした後、-720度でスタート線へバックしよう！"),
        ],
    }
)


# ==================================================================================================
# Lesson 05: Square Patrol Car
# ==================================================================================================
SQUARE_PATROL = make_lesson(
    {
        "id": "square-patrol",
        "level": "stage2",
        "stars": 2,
        "camera": {"pos": [14.0, 14.0, 11.0], "target": [6.5, 0.5, -8.5]},
        "title": T("正方形巡逻车 (Square Patrol)", "Square Patrol Car", "しかくパトロールカー"),
        "summary": T(
            "给差速小车装上宽幅前保险杠；发现 v1「填 90° 电机角度」根本转不够直角的真相，标定轮距让正方形完美闭合。",
            "Add a wide front bumper; discover why v1's 90° motor angle fails to close a square, then calibrate the exact wheelbase turn angle.",
            "ワイドバンパーを追加し、v1の「モーター90度指定」で四角が閉じない原因をトレッド比の計算で解決します。",
        ),
        "difficulty": T("小学 3-4 年级", "Grades 3-4", "小学3〜4年"),
        "duration": T("15 分钟", "15 min", "15分"),
        "concepts": ["movement", "loop", "variable", "calibration"],
        "ports": DRIVE_PORTS,
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("安装 11 孔黄色前保险杠", "Mount 11L Yellow Front Bumper", "11L黄色フロントバンパーを装着"),
                "instruction": T("用 2 颗黑销把 11 孔黄色梁（32525）横装在主控正前方，为车头提供宽幅防护。", "Pin an 11L yellow beam (32525) across the front of the Hub with 2 black pins.", "ハブ前面に黒ピン2本で11L黄色ビーム（32525）を横向きに取り付けます。"),
                "substeps": [
                    T("在主控正前方中排左右两孔各插 1 颗黑色摩擦销（2780）。", "Insert 2 black pins into the middle-row front holes of the Hub.", "ハブ前面中段の左右2穴に黒ピンを挿します。"),
                    T("把 11 孔黄色梁（32525）居中扣紧在 2 颗黑销上（左右各伸出 3 孔）。", "Center the 11L yellow beam onto both pins so it overhangs evenly left and right.", "11L黄色ビームを左右均等になるよう中央で押し込みます。"),
                ],
                "tip": T("11 孔梁刚好比主控宽出一圈，能挡住车轮前方的轻度刮擦。", "The 11L width shields both front corners ahead of the tires.", "11L幅がタイヤ前方の角をしっかりガードします。"),
            },
            {
                "step": 3,
                "title": T("加装左右洋红防撞护角", "Add Left & Right Bumper Caps", "左右コーナーガードを装着"),
                "instruction": T("在黄色保险杠左右两端各用 2 颗黑销加固一块 3 孔洋红护角梁（32523）。", "Reinforce both ends of the bumper with 3L magenta beams (32523) using 2 pins each.", "バンパー両端に黒ピン2本ずつで3Lマゼンタビーム（32523）を補強します。"),
                "substeps": [
                    T("在黄色保险杠最左侧 2 个孔向前插 2 颗黑销，扣紧 1 根 3 孔梁（32523）。", "Insert 2 black pins at the leftmost 2 holes and press on a 3L beam (32523).", "左端2穴に黒ピン2本で3Lビームを取り付けます。"),
                    T("在最右侧 2 个孔对称装上第 2 根 3 孔梁（32523）。", "Mirror on the rightmost 2 holes with the second 3L beam.", "右端にも対称に2本目の3Lビームを取り付けます。"),
                ],
                "tip": T("每块护角都用 2 颗销固定，碰墙也不会歪斜。", "Two pins per cap keep them locked rigid even after bumps.", "各ガードも2本ピン固定なのでぶつかってもズレません。"),
            },
        ],
        "structure_lab": {
            "why": T(
                "车轮中心距（轮距 ≈ 134mm）比车轮直径（56mm）宽了 2.4 倍！车身原地转 90° 时，车轮走过的圆弧长度需要电机转大约 90° × (134 / 56) ≈ 215°，而不是 90°！",
                "Wheel track width (~134 mm) is 2.4× the wheel diameter (56 mm), so turning the robot body 90° requires ~215° of motor rotation — NOT 90°!",
                "トレッド幅（約134mm）はタイヤ直径（56mm）の約2.4倍あるため、車体を90度回すにはモーターを約215度回す必要があります。",
            ),
            "troubleshoot": [
                T("地毯和木地板转弯角度不一样？不同地面的轮胎抓地力不同，实际桌面实验时可把 turn_deg 在 205~225 之间微调。", "Angle differs on carpet vs wood? Surface friction shifts turning slightly — fine-tune turn_deg between 205 and 225.", "床材で摩擦が違うため、実機では turn_deg を205〜225の間で微調整しましょう。"),
                T("护角挡到轮子？检查 3 孔梁是否装在黄色梁朝前那一面，不要反装到背面。", "Caps touching tires? Mount the 3L caps on the front face of the yellow beam, not the back.", "タイヤに当たる場合、3Lビームが前側に向いているか確認します。"),
            ],
            "mod_ideas": [
                T("扫地推雪铲：把前保险杠往下移 1 排孔，贴近地面就能推走桌上的小积木！", "Mini Bulldozer: lower the bumper by 1 stud to sweep loose bricks out of the way.", "ブルドーザー改造：バンパーを1段下げて机のパーツを押してみよう。"),
                T("窄轮距敏捷版：思考如果把两轮往里挪近一点，转 90° 所需的电机角度会变大还是变小？", "Narrow Track Experiment: predict whether moving wheels closer needs MORE or FEWER degrees to turn 90°!", "トレッド幅実験：左右タイヤの間隔を狭くすると90度旋回に必要な角度は増える？減る？"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看 3D 蓝色轨迹：代码想画地面上那个正方形，直觉填了 turn_deg = 90——结果每个弯只转了不到 38°，小车走出一条大弧线，彻底偏离正方形！",
                "Watch the blue 3D trail: assuming 90° body turn = 90° motor turn only rotates the car ~38° per corner — totally missing the square!",
                "3Dの青い軌跡を見よう：90度旋回のつもりでモーター90度を指定すると、実際は約38度しか曲がらず四角になりません！",
            ),
            v1_why=T(
                "把「车身转弯角度」和「电机轴转动角度」混为一谈，是小车编程中最经典的物理概念误区。",
                "Confusing robot heading degrees with motor shaft degrees is the #1 beginner mistake in wheeled robotics.",
                "「車体の旋回角度」と「モーターの回転角度」を同じものと考えてしまうのが定番の落とし穴です。",
            ),
            v1_code="""import runloop
import motor_pair
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    # {{wrong_turn}}
    side = 600
    turn_deg = 90

    for _ in range(4):
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, side, 0, velocity=420)
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, turn_deg, 100, velocity=260)
        await sound.beep(523, 100, 100)

    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

runloop.run(main())
""",
            v1_comments={
                "wrong_turn": T("误以为转 90° 直角就填 turn_deg = 90——看轨迹有多歪！", "Assuming a 90° corner needs turn_deg = 90 — watch the trail miss!", "90°曲がるには turn_deg = 90 だと思い込む——軌跡がずれるのを見てみよう！"),
            },
            v1_explanations=[
                {
                    "lines": "8-9",
                    "title": T("未标定的转弯度数", "Uncalibrated Turn Angle", "キャリブレーションしていない旋回角"),
                    "desc": T("turn_deg = 90 只是让车轮滚了 1/4 圈，车身远远转不到 90°。", "90 motor degrees rolls each wheel only 1/4 turn — far less than a 90° body turn.", "モーター90°は車輪1/4回転にすぎず、車体の90°旋回にはまったく足りません。"),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.set_var("side", 600),
                B.set_var("turn_deg", 90),
                B.repeat(
                    4,
                    B.move_for(B.var("side"), 0, 420),
                    B.move_for(B.var("turn_deg"), 100, 260),
                    B.beep(523, 100),
                ),
                B.show_image("SAD"),
                variables=["side", "turn_deg"],
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.set_var_named("side", 600),
                B.set_var_named("turn_deg", 90),
                B.repeat(
                    4,
                    B.move_for(B.get_var("side"), 0, 420),
                    B.move_for(B.get_var("turn_deg"), 100, 260),
                    B.beep(523, 100),
                ),
                B.show_image("SAD"),
                variables=["side", "turn_deg"],
            ),
            v1_scratch_vars=["side", "turn_deg"],
            v2_fix=T(
                "按真实几何标定：turn_deg = int(90 * 134 / 56) = 215°！把 turn_deg 改成 215，再跑一次看 3D 蓝色轨迹如何严丝合缝贴着地面正方形回到起点！",
                "Calibrate from exact geometry: turn_deg = 90 × (134 mm track / 56 mm wheel) ≈ 215°! Watch the blue trail trace the square and close right back at start!",
                "実寸比から turn_deg = 90 × 134 ÷ 56 ≒ 215度に補正！3Dの青い軌跡が地面の正方形にぴったり重なって戻ります。",
            ),
            v2_code="""import runloop
import motor_pair
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    # {{calibrated}}
    side = 600
    turn_deg = 215
    tone = 440

    # {{four_sides}}
    for _ in range(4):
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, side, 0, velocity=420)
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, turn_deg, 100, velocity=260)
        await sound.beep(tone, 110, 100)
        tone += 110

    light_matrix.show_image(light_matrix.IMAGE_SQUARE)

runloop.run(main())
""",
            v2_comments={
                "calibrated": T("轮距 134mm ÷ 轮径 56mm × 90° ≈ 215°！标定后的精确直角", "Calibrated: 134 mm track / 56 mm wheel × 90° ≈ 215°!", "キャリブレーション済み：トレッド134mm ÷ 車輪56mm × 90° ≈ 215°！"),
                "four_sides": T("循环走 4 条边，每过一个转角音调升高 110Hz", "Repeat 4 sides, climbing +110 Hz at each corner", "4辺くり返し、角ごとに音を+110Hz上げる"),
            },
            v2_explanations=[
                {
                    "lines": "8-10",
                    "title": T("几何公式标定转角", "Geometry-Calibrated Turn Degrees", "幾何から求めた旋回角"),
                    "desc": T("把 turn_deg 改为 215 后，原地转向精准接近 90°，4 条边稳稳闭合。", "Setting turn_deg = 215 hits a true 90° pivot so all four sides close cleanly.", "turn_deg = 215 で本当に90°回るので、4辺がきれいに閉じます。"),
                },
                {
                    "lines": "13-17",
                    "title": T("循环画正方形 + 渐升提示音", "Square Loop with Rising Corner Chimes", "角ごとに上がるチャイムつきの正方形ループ"),
                    "desc": T("4 次转角依次响 440 / 550 / 660 / 770 Hz，结束亮出 SQUARE 正方形图标。", "Four rising tones announce each corner before displaying the SQUARE icon.", "角ごとに4つの音が上がっていき、最後に SQUARE アイコンを表示します。"),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.set_var("side", 600),
                B.set_var("turn_deg", 215),
                B.set_var("tone", 440),
                B.repeat(
                    4,
                    B.move_for(B.var("side"), 0, 420),
                    B.move_for(B.var("turn_deg"), 100, 260),
                    B.beep(B.var("tone"), 110),
                    B.change_var("tone", 110),
                ),
                B.show_image("SQUARE"),
                variables=["side", "turn_deg", "tone"],
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.set_var_named("side", 600),
                B.set_var_named("turn_deg", 215),
                B.set_var_named("tone", 440),
                B.repeat(
                    4,
                    B.move_for(B.get_var("side"), 0, 420),
                    B.move_for(B.get_var("turn_deg"), 100, 260),
                    B.beep(B.get_var("tone"), 110),
                    B.change_var("tone", 110),
                ),
                B.show_image("SQUARE"),
                variables=["side", "turn_deg", "tone"],
            ),
            v2_scratch_vars=["side", "turn_deg", "tone"],
        ),
        "challenges": [
            T("改成画正三角形（循环 3 次，每个外角转 120°：算算 215 × 120 / 90 ≈ 多少度？）。", "Draw an equilateral triangle: repeat 3 times with 120° exterior turns (≈ 287°).", "正三角形を描こう：3回くり返し、外角120度（約287度）に調整してみよう。"),
            T("改成向左转（steering 设为 -100），看看正方形会画在起点的哪一侧！", "Switch steering to -100 to patrol counter-clockwise on the left side!", "ステアリングを-100にして左回りの正方形を走ってみよう。"),
        ],
    }
)


# ==================================================================================================
# Lesson 06: Gyro Precision Turn
# ==================================================================================================
GYRO_PRECISION = make_lesson(
    {
        "id": "gyro-precision",
        "level": "stage2",
        "stars": 3,
        "camera": {"pos": [14.0, 14.0, 11.0], "target": [6.5, 0.5, -8.5]},
        "title": T("陀螺仪精准转弯 (Gyro Precision)", "Gyro Precision Turn", "ジャイロ精密ターン"),
        "summary": T(
            "给小车装上车头方向罗盘箭头；解决 v1 忘记归零陀螺仪、全速猛转冲过头的问题，用比例减速实现 ±2° 精准闭环转弯。",
            "Add a top compass arrow; fix v1's un-reset gyro & high-speed overshoot with yaw zeroing and proportional slow-down.",
            "方向コンパス矢印を装着。v1のジャイロ未リセット＆高速オーバーシュートを比例減速で±2度精度へ改良します。",
        ),
        "difficulty": T("小学 3-4 年级", "Grades 3-4", "小学3〜4年"),
        "duration": T("18 分钟", "18 min", "18分"),
        "concepts": ["sensor", "feedback", "variable", "loop"],
        "ports": DRIVE_PORTS,
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("在主控前顶加装 7 孔横桥", "Add Top Front 7L Bridge", "ハブ上部に7Lブリッジを装着"),
                "instruction": T("在主控顶面前方左右角孔向上插 2 颗黑销，水平扣上 7 孔灰梁（32524）。", "Insert 2 vertical black pins into the Hub's top-front corners and press on a 7L beam (32524).", "ハブ上面前の左右角穴に黒ピン2本を上向きに挿し、7Lビームを水平固定します。"),
                "substeps": [
                    T("在主控顶面最前端左右两个角孔向上插入黑色摩擦销（2780）。", "Push 2 black pins vertically into the two front-most top Hub holes.", "ハブ上面前端の左右2穴に黒ピンを上向きに挿します。"),
                    T("把 7 孔灰梁（32524）水平横跨在 2 颗销上按紧，完全不遮挡 5×5 灯阵。", "Snap the 7L grey beam across both pins, leaving the 5×5 LED matrix unobstructed.", "7Lビームを水平に押し込み、5×5 LEDが隠れないことを確認します。"),
                ],
                "tip": T("横桥同时能加固车身前部，减少高速转弯时的轻微扭动。", "This bridge also stiffens the front of the chassis.", "車体前部の剛性も上がります。"),
            },
            {
                "step": 3,
                "title": T("装上黄色车头方向罗盘箭头", "Mount Yellow Compass Heading Arrow", "黄色い方向コンパス矢印を装着"),
                "instruction": T("在 7 孔横桥中间两孔向上插 2 颗黑销，扣上黄色 3×3 T 形箭头（60484）指向车头正前方。", "Pin a yellow 3×3 T-beam (60484) onto the center of the bridge pointing straight forward.", "7Lブリッジ中央2穴に黄色いT字ビーム（60484）を前向きに固定します。"),
                "substeps": [
                    T("在 7 孔横桥中心两侧（第 3、第 5 孔）向上各插 1 颗黑销（2780）。", "Insert 2 vertical black pins into holes #3 and #5 of the 7L bridge.", "7Lビームの3番目と5番目の穴に黒ピンを挿します。"),
                    T("将黄色 T 形梁（60484）横边压紧两颗销、尖端笔直指向车头正前方。", "Press the yellow T-beam crossbar onto both pins with its stem pointing straight ahead.", "T字ビームの先端が真正面を向くように押し込みます。"),
                ],
                "tip": T("运行时紧盯这个黄色箭头，就能肉眼检查每次转弯是不是正正 90°！", "Watch this yellow pointer live to see whether each turn hits an exact 90°!", "この黄色い矢印を見ると90度ちょうどで止まったか一目で分かります！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "主控内置 6 轴陀螺仪（motion_sensor），直接测量车身自己转了多少度！即使换了轮子大小、换了地毯或轮胎打滑，只要主控水平固定稳固，陀螺仪反馈就能精准控角。",
                "The Hub's built-in gyro measures actual robot rotation directly — so even if wheels slip or tire sizes change, closed-loop gyro turning stays accurate as long as the Hub is mounted flat.",
                "ハブ内蔵ジャイロは車体そのものの回転角を測るため、タイヤが滑っても正確に90度曲がれます。ハブを水平に固定するのが鍵です。",
            ),
            "troubleshoot": [
                T("陀螺仪读数乱飘？启动程序时先把小车静置 1 秒，不要用手拎着点运行。", "Gyro drifting? Place the robot still on the floor for 1 second before starting.", "値がブレる場合、机に静止させてから実行ボタンを押してください。"),
                T("为什么公式里要除以 10？SPIKE 3 的 tilt_angles()[0] 单位是「十分之一度」（90° = 900）。", "Why divide by 10? SPIKE 3 tilt_angles()[0] returns tenths of a degree (90° = 900).", "10で割る理由は？SPIKE 3 の tilt_angles()[0] は0.1度単位（90度＝900）で返るためです。"),
            ],
            "mod_ideas": [
                T("指南针车：一直保持车头朝北（0°），用手把小车扭歪它就自动转回来！", "Auto-Compass: write a loop that steers back to yaw=0° whenever someone twists the robot!", "自動コンパス：手で向きをずらしても自動で0度へ戻るプログラムに挑戦しよう！"),
                T("大轮子对比实验：换用不同摩擦路面，对比第 5 课开环和第 6 课陀螺仪闭环谁更稳。", "Surface Test: compare Lesson 5 open-loop vs Lesson 6 gyro closed-loop on smooth and rough surfaces.", "床面テスト：レッスン5と6を滑りやすい床で比べてみよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真观察：第 1 个弯还算像样（但因为高速猛刹冲过了 10°），到第 2 个弯由于没调用 reset_yaw(0)，偏航角早已经超过 90°，后 3 个弯直接跳过，小车一路直线冲出场地！",
                "Watch v1: Corner 1 overshoots at full speed, and because yaw is NEVER reset to 0 before Corners 2–4, abs(yaw) is already ≥ 90° so it skips every remaining turn and drives straight off!",
                "v1を観察：1回目の角は高速でオーバーシュートし、さらに reset_yaw(0) を忘れたため2回目以降は既に90度以上と判定され、曲がらず直進してしまいます！",
            ),
            v1_why=T(
                "两个常见工程失误叠加：① 忘记在每次转弯前把相对偏航角归零；② 快到目标角时不减速，靠全速急停会冲过头。",
                "Two classic control bugs combined: (1) forgetting to zero yaw before each turn, and (2) braking from full speed instead of slowing near the target.",
                "①毎回ゼロリセットし忘れ、②目標角の直前で減速しない——この2つが重なると制御が破綻します。",
            ),
            v1_code="""import runloop
import motor_pair
from hub import light_matrix, motion_sensor, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    motion_sensor.reset_yaw(0)

    # {{no_reset}}
    for _ in range(4):
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, 600, 0, velocity=420)
        while abs(motion_sensor.tilt_angles()[0] / 10) < 90:
            motor_pair.move_tank(motor_pair.PAIR_1, 550, -550)
            await runloop.sleep_ms(30)
        motor_pair.stop(motor_pair.PAIR_1)
        await sound.beep(523, 100, 100)

    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

runloop.run(main())
""",
            v1_comments={
                "no_reset": T("只在循环外归零一次 + 550 全速猛转：第 2 弯起直接失效！", "Reset yaw only once outside the loop + 550 full-speed turn — breaks on corner 2!", "yaw のリセットをループの外で1回だけ＋全速550で旋回——2つ目の角で失敗！"),
            },
            v1_explanations=[
                {
                    "lines": "7-14",
                    "title": T("循环外只归零一次的致命 Bug", "Single Reset Outside Loop Bug", "ループ外で1回だけリセットするバグ"),
                    "desc": T("第 1 次转完后 yaw 已经是 -95°，第 2 次进 while 时 95 < 90 为假，根本不转弯！", "After corner 1 yaw is already -95°, so corners 2–4 skip the turn loop completely!", "1つ目の角のあと yaw はすでに -95° なので、2〜4つ目の角では旋回ループが丸ごと飛ばされます！"),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.reset_yaw(),
                B.repeat(
                    4,
                    B.move_for(600, 0, 420),
                    B.repeat_until(
                        B.compare(B.abs_(B.yaw()), ">=", 90),
                        B.move_tank(550, -550),
                    ),
                    B.move_stop(),
                    B.beep(523, 100),
                ),
                B.show_image("SAD"),
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.reset_yaw(),
                B.repeat(
                    4,
                    B.move_for(600, 0, 420),
                    B.repeat_until(
                        B.compare(B.abs_(B.yaw()), ">=", 90),
                        B.move_tank(550, -550),
                    ),
                    B.move_stop(),
                    B.beep(523, 100),
                ),
                B.show_image("SAD"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "每次转弯前先 motion_sensor.reset_yaw(0) 归零；再用剩余角度 remaining = 90 - abs(yaw) 乘以 6 做比例减速（最高 300、最低 80），4 个 90° 弯全部丝滑命中橙色角标并回到绿色起点！",
                "Zero yaw before every corner, then scale turn speed smoothly from remaining angle (speed = clamp(remaining × 6, 80, 300)). Every 90° turn hits all orange markers dead-on!",
                "毎回の旋回前に reset_yaw(0) を行い、残り角度×6で自動減速（下限80・上限300）。4つの角すべてを±2度以内で正確に曲がります。",
            ),
            v2_code="""import runloop
import motor_pair
from hub import light_matrix, motion_sensor, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)

    # {{gyro_square}}
    for _ in range(4):
        await motor_pair.move_for_degrees(motor_pair.PAIR_1, 600, 0, velocity=420)
        motion_sensor.reset_yaw(0)
        await runloop.sleep_ms(60)

        # {{p_turn}}
        while True:
            remaining = 90 - abs(motion_sensor.tilt_angles()[0] / 10)
            if remaining <= 1:
                break
            speed = int(max(80, min(300, remaining * 6)))
            motor_pair.move_tank(motor_pair.PAIR_1, speed, -speed)
            await runloop.sleep_ms(10)

        motor_pair.stop(motor_pair.PAIR_1)
        await sound.beep(660, 100, 100)

    light_matrix.show_image(light_matrix.IMAGE_YES)

runloop.run(main())
""",
            v2_comments={
                "gyro_square": T("每条边直行后立刻归零偏航角，让每次转弯都从 0° 重新算起", "Reset yaw to 0° before every single corner", "角を曲がる前に毎回 yaw を0°にリセット"),
                "p_turn": T("比例减速：离 90° 越近速度越慢（300 → 80），误差压在 ±1° 内！", "Proportional braking: slow from 300 down to 80 as remaining angle shrinks", "比例ブレーキ：残り角度が小さくなるほど 300 から 80 へ減速"),
            },
            v2_explanations=[
                {
                    "lines": "11-12",
                    "title": T("每弯必归零，消灭误差累积", "Zero Yaw Before Each Turn", "旋回のたびに yaw を0に"),
                    "desc": T("把 reset_yaw(0) 放进循环内，4 个直角各自独立清零，互不干扰。", "Putting reset_yaw(0) inside the loop gives every turn a clean 0° baseline.", "reset_yaw(0) をループの中に入れると、毎回の旋回がきれいな0°から始まります。"),
                },
                {
                    "lines": "15-21",
                    "title": T("比例控制（P-Control）优雅刹车", "Proportional Slow-Down", "比例減速"),
                    "desc": T("剩 50° 时以 300 速快转，剩 10° 时降到 80 速轻靠，绝不冲过头。", "Fast at 300 far from target, gently creeping at 80 near 90° for zero overshoot.", "目標から遠いときは 300 で速く、90°付近では 80 でそっと近づくので行き過ぎません。"),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.repeat(
                    4,
                    B.move_for(600, 0, 420),
                    B.reset_yaw(),
                    B.wait(0.06),
                    B.set_var("remaining", 90),
                    B.repeat_until(
                        B.compare(B.var("remaining"), "<=", 1),
                        B.set_var("remaining", B.arith(90, "-", B.abs_(B.yaw()))),
                        B.set_var("speed", B.arith(B.var("remaining"), "*", 6)),
                        B.if_(B.compare(B.var("speed"), "<", 80), B.set_var("speed", 80)),
                        B.if_(B.compare(B.var("speed"), ">", 300), B.set_var("speed", 300)),
                        B.move_tank(B.var("speed"), B.arith(0, "-", B.var("speed"))),
                    ),
                    B.move_stop(),
                    B.beep(660, 100),
                ),
                B.show_image("YES"),
                variables=["remaining", "speed"],
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.repeat(
                    4,
                    B.move_for(600, 0, 420),
                    B.reset_yaw(),
                    B.wait(0.06),
                    B.set_var_named("remaining", 90),
                    B.repeat_until(
                        B.compare(B.get_var("remaining"), "<=", 1),
                        B.set_var_named("remaining", B.arith(90, "-", B.abs_(B.yaw()))),
                        B.set_var_named("speed", B.arith(B.get_var("remaining"), "*", 6)),
                        B.if_(B.compare(B.get_var("speed"), "<", 80), B.set_var_named("speed", 80)),
                        B.if_(B.compare(B.get_var("speed"), ">", 300), B.set_var_named("speed", 300)),
                        B.move_tank(B.get_var("speed"), B.arith(0, "-", B.get_var("speed"))),
                    ),
                    B.move_stop(),
                    B.beep(660, 100),
                ),
                B.show_image("YES"),
                variables=["remaining", "speed"],
            ),
            v2_scratch_vars=["remaining", "speed"],
        ),
        "challenges": [
            T("把 90 改成 72、循环改成 5 次，用陀螺仪精准画出正五边形！", "Change 90° to 72° and repeat 5 times to draw a precision pentagon!", "90度を72度・5回に変えて正確な正五角形を描こう！"),
            T("写一个 turn_right(target_deg) 函数，让主程序一行就能任意转 45° 或 135°。", "Wrap the turn loop into a reusable turn_right(target_deg) helper function.", "turn_right(target_deg) 関数にまとめて好きな角度へ曲がれるようにしよう。"),
        ],
    }
)

STAGE2_LESSONS = [DRIVING_BASE, SQUARE_PATROL, GYRO_PRECISION]
