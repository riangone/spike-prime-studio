"""Stage 4 (Grades 4-6): Real Mechanical Transmissions & Capstone Robot.

Lessons:
  10. gear-gate      — 11x19 Baseplate + 12T:36T Geared Gate | Unaccounted 3:1 gear ratio vs calibrated -3x boom drive
  11. rack-pusher    — 11x19 Baseplate + 12T Pinion & 13L Rack | Over-travel stall without return vs color-triggered sort stroke
  12. smart-gripper  — Driving Base + Front Large Motor Claw + Distance F | Closing claw before driving vs autonomous approach-grab-deliver
"""
from __future__ import annotations

from app.cad.assembly import T
from app.data import blocks_dsl as B
from app.data.lessons_stage1 import _ver_pair, make_lesson
from app.data.lessons_stage2 import DRIVE_PORTS, REUSE_BASE_STEP


# ==================================================================================================
# Lesson 10: Geared Parking Gate (12T -> 36T 3:1 Reduction)
# ==================================================================================================
GEAR_GATE = make_lesson(
    {
        "id": "gear-gate",
        "level": "stage4",
        "stars": 4,
        "camera": {"pos": [7.8, 6.2, 7.2], "target": [1.8, 1.8, -2.0]},
        "title": T("齿轮减速道闸 (Geared Parking Gate)", "Geared Parking Gate (3:1)", "ギア減速ゲート (3:1)"),
        "summary": T(
            "在 11×19 大底板上搭建 12 齿啮合 36 齿的 3:1 减速停车场道闸；解决 v1 忽略齿轮比导致栏杆反压、抬起高度只有 1/3 的问题！",
            "Build a real 12T→36T (3:1) geared barrier gate on the 11×19 baseplate; fix v1's wrong direction and 1/3 lift angle by accounting for gear ratio & reversal!",
            "11×19ベースプレート上に12歯×36歯（3:1減速）の遮断機を構築。ギア比と逆回転を計算に入れて正確に90度開閉します。",
        ),
        "difficulty": T("小学 4-5 年级", "Grades 4-5", "小学4〜5年"),
        "duration": T("20 分钟", "20 min", "20分"),
        "concepts": ["motor", "gear", "sensor", "condition"],
        "ports": [
            {
                "port": "A",
                "device": T("中型角度电机 · 12T 主动轮 (45603)", "Medium Motor · 12T Driver (45603)", "Mモーター・12歯駆動ギア (45603)"),
                "note": T("装在主控右侧，通过 12T 小齿轮带动 36T 道闸轴", "Right side of Hub driving the 12T pinion into the 36T gate gear", "ハブ右側で12歯ギアを回し36歯ゲート軸を駆動"),
            },
            {
                "port": "B",
                "device": T("力传感器 · 开闸按钮 (45606)", "Force Sensor · Gate Button (45606)", "フォースセンサー・開門ボタン (45606)"),
                "note": T("装在主控左侧，按下抬杆放行", "Left side of Hub; press to open the barrier gate", "ハブ左側に設置、押すとゲートが開く"),
            },
        ],
        "steps": [
            {
                "step": 1,
                "title": T("铺设 11×19 青蓝大底板并锁紧主控", "Anchor Hub onto 11×19 Baseplate", "11×19ベースプレートにハブを固定"),
                "instruction": T("将 11×19 大底板（39369）平铺桌面，用 4 颗黑销把主控（45601）锁在底板偏左位置，右侧留出搭齿轮塔的空间。", "Lay the 11×19 baseplate (39369) flat and pin the Hub (45601) onto it with 4 black pins, leaving room on the right for the gear tower.", "11×19ベースプレート（39369）に黒ピン4本でハブを固定し、右側にギアタワーのスペースを空けます。"),
                "substeps": [
                    T("在底板对应主控四角孔的位置向上插 4 颗黑色摩擦销（2780）。", "Insert 4 vertical black pins (2780) into the baseplate matching the Hub's 4 bottom corner holes.", "ベースプレートに黒ピン4本を上向きに挿します。"),
                    T("将主控（45601）垂直压紧在底板上，灯阵朝上。", "Press the Hub down firmly onto the 4 pins with LEDs facing up.", "ハブを上からしっかり押し込みます。"),
                ],
                "tip": T("有了大底板把主控和齿轮立柱连成一体，13 孔长栏杆挥舞时底座稳如泰山！", "The 11×19 baseplate ties the Hub and gear tower together so the long boom never tips the base.", "大判プレートでハブと支柱を一体化するため長いバーが動いても倒れません。"),
            },
            {
                "step": 2,
                "title": T("左侧安装力传感器并接端口 B", "Mount Force Sensor on Left (Port B)", "左側にフォースセンサー装着・ポートB配線"),
                "instruction": T("在主控左前侧插 2 颗黑销，扣紧力传感器（45606）作为来车开闸按钮，接入端口 B。", "Pin the force sensor (45606) onto the Hub's front-left side and plug into Port B.", "ハブ左前に黒ピン2本でフォースセンサー（45606）を固定し、ポートBへ接続します。"),
                "substeps": [
                    T("在主控左前侧上下两孔插 2 颗黑销（2780），扣紧力传感器（柱塞朝前）。", "Insert 2 black pins on the front-left side and attach the force sensor facing forward.", "左前の上下2穴に黒ピンを挿し、ボタン前向きで固定します。"),
                    T("线缆绕过上方插入主控右前【端口 B】。", "Plug the sensor cable into Hub front-right Port B.", "ケーブルを【ポートB】に差し込みます。"),
                ],
                "wiring": [
                    {
                        "port": "B",
                        "device": T("力传感器 (45606)", "Force Sensor (45606)", "フォースセンサー (45606)"),
                        "route": T("从左侧传感器上方接入主控端口 B。", "Route cleanly over the front into Port B.", "センサーから上部を通しポートBへ。"),
                        "check": T("插头卡紧，柱塞按压顺畅。", "Plunger presses freely.", "ボタンがスムーズに押せること。"),
                    }
                ],
                "tip": T("仿真时点工具栏「🔘 力传感器」就能模拟司机按取票开闸按钮！", "Click 'Force' in the simulator bar to simulate a driver pressing the ticket button!", "シミュバーの「フォース」ボタンで開門スイッチを押せます！"),
            },
            {
                "step": 3,
                "title": T("右侧安装中型电机并接端口 A", "Mount Medium Motor on Right (Port A)", "右側にMモーター装着・ポートA配線"),
                "instruction": T("在主控右前侧插 2 颗黑销，水平装上中型电机（45603）输出盘朝右，线缆接入端口 A。", "Pin the medium motor (45603) on the Hub's front-right side with its rotor facing right, wired to Port A.", "ハブ右前に黒ピン2本でMモーター（45603）を回転盤右向きに固定し、ポートAへ接続します。"),
                "substeps": [
                    T("在主控右前侧上下两孔插 2 颗黑销（2780），扣上中型电机（输出盘朝右外侧）。", "Insert 2 black pins on the front-right side and press on the medium motor facing right.", "右前上下2穴に黒ピンを挿し、回転盤を外（右）に向けて固定します。"),
                    T("把电机线接入主控左前【端口 A】。", "Route the motor cable into Hub front-left Port A.", "ケーブルを【ポートA】に接続します。"),
                ],
                "wiring": [
                    {
                        "port": "A",
                        "device": T("中型角度电机 (45603)", "Medium Motor (45603)", "Mモーター (45603)"),
                        "route": T("从右电机后方绕至主控端口 A。", "Route neatly to Hub Port A.", "モーター後部からポートAへ接続。"),
                        "check": T("电线远离右侧齿轮啮合区。", "Keep cable clear of the right gear train.", "右側のギア部に線が触れないこと。"),
                    }
                ],
                "tip": T("此时电机输出十字孔中心高度正好在 y=50 LDU。", "The motor output axle center is now at height y = 50 LDU.", "モーター出力軸の高さは y=50 LDU になります。"),
            },
            {
                "step": 4,
                "title": T("在底板右侧立起 7 孔齿轮轴承塔柱", "Erect the 7L Gear Bearing Tower", "ベースプレート右側に7Lギア支柱を立てる"),
                "instruction": T("用 3×3 曲奇连接块（39793）把 7 孔垂直立柱（32524）牢牢铆在电机右侧的底板上。", "Anchor a 3×3 biscuit connector (39793) to the baseplate next to the motor and pin a vertical 7L tower beam (32524) to its outside.", "モーター右隣のプレートに3×3ビスケット（39793）を固定し、外側に7L垂直支柱（32524）を立てます。"),
                "substeps": [
                    T("在电机输出盘外侧的底板孔向上插 2 颗黑销，垂直扣上 3×3 曲奇块（39793）。", "Insert 2 vertical black pins into the baseplate right of the motor and press down the 3×3 biscuit (39793).", "底板に黒ピン2本を上向きに挿し、3×3ビスケットを垂直に固定します。"),
                    T("在曲奇块右侧面插 2 颗黑销，把 7 孔灰梁（32524）笔直竖立扣紧作为齿轮立柱。", "Pin the 7L grey beam (32524) upright onto the outside face of the biscuit with 2 black pins.", "ビスケット外側に黒ピン2本で7Lビームを垂直に固定します。"),
                ],
                "tip": T("立柱不仅托住上方大齿轮，也给下方电机轴提供外侧轴承支撑（双端支撑不歪轴）！", "This upright column supports both the upper 36T shaft and the outer end of the lower 12T motor shaft!", "この支柱が上下2本のギア軸をしっかり支える軸受になります！"),
            },
            {
                "step": 5,
                "title": T("装 12T:36T 啮合齿轮组与 13 孔黄色道闸杆", "Mesh 12T & 36T Gears + 13L Gate Boom", "12歯・36歯ギアを噛み合わせ13Lゲートバーを装着"),
                "instruction": T("下轴装 12 齿小齿轮（32270），上方隔 3 孔（60 LDU）装 36 齿大齿轮（32498）垂直啮合，再用 2×4 L 梁锁紧 13 孔黄色道闸长杆！", "Mount the 12T gear on the motor shaft, mesh the 36T gear 3 studs (60 LDU) above it, and attach the 13L yellow boom via a 2×4 L-beam!", "下軸に12歯ギア、3ポッチ上の軸に36歯ギアを噛み合わせ、2×4 L字ビーム経由で13L黄色ゲートバーを固定します！"),
                "substeps": [
                    T("将 4L 黑十字轴（3705）穿过 12 齿小齿轮（32270）插进电机中心孔，轴尾穿入立柱下孔。", "Slide the 12T gear (32270) onto a 4L axle (3705) into the motor rotor and through the lower tower hole.", "4L十字軸に12歯ギアを通し、モーター中心穴と支柱下穴を貫通させます。"),
                    T("在立柱上方隔 2 个空孔（中心距整 3 孔 = 60 LDU）处穿入第 2 根 4L 轴，内侧装 36 齿大齿轮（32498）与 12 齿完美咬合，中间垫 1 个轴套（3713）。", "Three studs above (y=110), pass a second 4L axle through the 36T gear (32498), a grey bush (3713), and the tower column so the teeth mesh cleanly.", "3ポッチ上の穴に2本目の4L軸を通し、内側に36歯ギアとブッシュを入れて12歯ギアと噛み合わせます。"),
                    T("在上轴外端套上黄色 2×4 L 形梁（32140）的十字孔，再用 2 颗黑销把 13 孔黄色长梁（41239）水平向前锁紧！", "Press the axle hole of a yellow 2×4 L-beam (32140) onto the outer shaft end, then pin the 13L yellow boom (41239) pointing forward with 2 black pins.", "上軸の外端に2×4 L字ビームの十字穴をはめ、黒ピン2本で13L黄色バー（41239）を前向きに固定します。"),
                ],
                "tip": T("为什么 12T 和 36T 必须隔 3 孔？因为齿轮半径和 = (12 + 36) ÷ 16 = 48 ÷ 16 = 整 3.0 孔！", "Why 3 studs apart? Because (12 + 36) / 16 = 48 / 16 = 3.0 studs exact pitch distance!", "なぜ3ポッチ離すの？ (12歯＋36歯)÷16＝3.0ポッチが正確な噛み合い距離だからです！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "13 孔长栏杆伸出去很远，直接装在电机上既转太快又容易抖。用 12 齿小齿轮带动 36 齿大齿轮（传动比 12:36 = 1:3），不仅把转速放慢 3 倍变得稳重优雅，还把抬杆力量（扭矩）放大了整整 3 倍！",
                "A long 13L boom is heavy and fast if driven directly. Stepping down 12T → 36T (1:3 ratio) slows rotation by 3× for smooth motion while multiplying lifting torque by 3×!",
                "12歯から36歯へ3:1減速することで、回転スピードが1/3になって落ち着き、バーを持ち上げる力（トルク）が3倍に増えます！",
            ),
            "troubleshoot": [
                T("两颗齿轮咬不上或卡死？检查上轴是不是插在了下轴正上方第 3 个孔（中间跳过 2 个空孔）。", "Gears slipping or binding? Count holes on the tower: there must be 2 empty holes between the two axles (3-stud center spacing).", "ギアが噛み合わない場合、上下の軸の間に空き穴が2つ（3ポッチ間隔）あるか確認しましょう。"),
                T("道闸杆抬起时自己往下掉？确认 2×4 L 形梁是用末端的「十字孔」套在 4L 十字轴上，圆孔会打滑！", "Boom slips on the shaft? Make sure the 4L axle goes through the cross-shaped AXLE hole of the 2×4 L-beam, not a round pin hole!", "バーが空回りする場合、2×4 L字ビームの「十字穴」に軸が通っているか確認！"),
            ],
            "mod_ideas": [
                T("改成 1:1 等速道闸：如果把上下两颗齿轮都换成 20 齿，它们之间应该隔几孔？（算算 (20+20)÷16 = 2.5 孔！）", "Gear Math Challenge: if you use two 20T gears, what center distance do they need? ((20+20)/16 = 2.5 studs!)", "ギア算数：20歯同士を噛み合わせるなら何ポッチ間隔？（(20+20)÷16＝2.5ポッチ！）"),
                T("加装超声波自动感应开闸：把力传感器换成超声波传感器，小车开近自动抬杆！", "Hands-Free Toll Gate: swap the force button for a distance sensor so approaching toy cars open the gate automatically!", "距離センサーに交換して、ミニカーが近づいたら自動で開くETCゲートにしよう！"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真观察道闸：程序员想让栏杆向上抬起 90° 放行，直接写了 `run_for_degrees(port.A, -90)`——结果栏杆不但没往上抬，反而往下硬压了 30°，差点把栏杆砸断！",
                "Watch the gate in v1: wanting to lift the boom +90° up, the coder wrote `run_for_degrees(port.A, -90)` — and the boom pressed 30° DOWNWARD toward the road instead!",
                "v1を観察：バーを上へ90度開けるつもりでモーターを-90度回したら、逆の下向きへ30度しか動かず地面に押し付けてしまいます！",
            ),
            v1_why=T(
                "忽略了外啮合齿轮的两大铁律：① 相邻两个齿轮旋转方向「相反」（主动轮正转，从动轮反转）；② 12T 带 36T 是 3:1 减速，大齿轮想转 90°，小齿轮必须反方向转 90° × 3 = 270°！",
                "Two gear laws were ignored: (1) meshing gears spin in OPPOSITE directions, and (2) with a 12T:36T (1:3) ratio, the motor must turn 90° × 3 = +270° to lift the boom 90°!",
                "①噛み合うギアは回転方向が逆になる、②12歯→36歯ではモーターを3倍の270度回す必要がある——の2点を忘れています！",
            ),
            v1_code="""import runloop
import motor
from hub import light_matrix, port, sound

async def main():
    # {{wrong_gear}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
    await motor.run_for_degrees(port.A, -90, 360)
    await sound.beep(440, 200, 100)
    await runloop.sleep_ms(1000)
    await motor.run_for_degrees(port.A, 90, 360)
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

runloop.run(main())
""",
            v1_comments={
                "wrong_gear": T("忘了齿轮反向和 3:1 传动比：填 -90° 结果栏杆往下压了 30°！", "Forgot gear reversal & 3:1 ratio: -90° pushes the boom 30° DOWN!"),
            },
            v1_explanations=[
                {
                    "lines": "8",
                    "title": T("未乘传动比且方向搞反", "Unscaled Ratio & Reversed Sign"),
                    "desc": T("电机转 -90° 经过 -12/36 传动后，道闸轴只转了 -30°（向下压），既反了又差了 3 倍。", "Motor -90° × (-12/36) moves the gate shaft only -30° downward."),
                },
            ],
            v1_blocks=B.program(
                B.show_image("ARROW_N"),
                B.motor_run_for("A", -90, 360),
                B.beep(440, 200),
                B.wait(1),
                B.motor_run_for("A", 90, 360),
                B.show_image("SAD"),
            ),
            v1_scratch=B.program(
                B.show_image("ARROW_N"),
                B.motor_run_for("A", -90, 360),
                B.beep(440, 200),
                B.wait(1),
                B.motor_run_for("A", 90, 360),
                B.show_image("SAD"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "按齿轮公式精确计算：`motor_deg = gate_deg × (36 / 12) = 90 × 3 = +270°`！运行 v2，道闸立刻先演示一次标准 90° 竖直抬杆与平稳落杆，随后还可以点「🔘 力传感器」随时按钮开闸！",
                "Apply the exact gear formula: `motor_deg = 90° × (36 / 12) = +270°`! Watch v2 lift the boom straight up 90° to vertical, pause for traffic, and lower level — plus press 'Force' anytime to open again!",
                "ギア比の式 `motor_deg = 90 × (36 ÷ 12) = +270度` を適用！バーが真上へ90度ピシッと開き、通行後に水平へ戻ります。フォースボタンでも開閉可能！",
            ),
            v2_code="""import runloop
import motor
import force_sensor
from hub import light_matrix, port, sound

async def open_and_close_gate():
    # {{lift_270}}
    light_matrix.show_image(light_matrix.IMAGE_YES)
    await sound.beep(784, 150, 100)
    await motor.run_for_degrees(port.A, 270, 450)
    await runloop.sleep_ms(900)
    # {{lower_270}}
    light_matrix.show_image(light_matrix.IMAGE_NO)
    await sound.beep(523, 150, 100)
    await motor.run_for_degrees(port.A, -270, 360)

async def main():
    await motor.run_to_absolute_position(port.A, 0, 360)
    await open_and_close_gate()

    # {{wait_button}}
    for _ in range(40):
        if force_sensor.pressed(port.B):
            await open_and_close_gate()
        await runloop.sleep_ms(30)

runloop.run(main())
""",
            v2_comments={
                "lift_270": T("36T ÷ 12T = 3 倍！电机正转 +270°，道闸正好反向竖直抬起 90°", "36T / 12T = 3x! Motor +270° lifts the 36T gate boom an exact 90° up"),
                "lower_270": T("通行后电机反转 -270°，栏杆慢速平稳落回水平位置", "Motor -270° lowers the boom gently back to horizontal"),
                "wait_button": T("点仿真栏「🔘 力传感器」按钮可再次触发抬杆放行！", "Click 'Force' in the simulator bar to trigger another gate cycle!"),
            },
            v2_explanations=[
                {
                    "lines": "10",
                    "title": T("3:1 减速传动比换算", "3:1 Gear Ratio Calculation"),
                    "desc": T("主动轮 12 齿、从动轮 36 齿，传动比 = 36/12 = 3。想让栏杆抬 90°，电机必须转 90 × 3 = 270°。", "With 12T driving 36T, ratio = 36/12 = 3. Lifting the boom 90° requires 90 × 3 = 270° at the motor."),
                },
                {
                    "lines": "22-25",
                    "title": T("力传感器互动放行", "Interactive Force-Sensor Trigger"),
                    "desc": T("演示完首轮开关闸后，窗口期内按下力传感器会再次调用 open_and_close_gate()。", "Pressing the Force Sensor during the watch loop opens and closes the gate again."),
                },
            ],
            v2_blocks=B.program(
                B.motor_go_to("A", 0, 360),
                B.show_image("YES"),
                B.beep(784, 150),
                B.motor_run_for("A", 270, 450),
                B.wait(0.9),
                B.show_image("NO"),
                B.beep(523, 150),
                B.motor_run_for("A", -270, 360),
                B.repeat(
                    40,
                    B.if_(
                        B.force_pressed("B"),
                        B.show_image("YES"),
                        B.beep(784, 150),
                        B.motor_run_for("A", 270, 450),
                        B.wait(0.9),
                        B.show_image("NO"),
                        B.motor_run_for("A", -270, 360),
                    ),
                    B.wait(0.03),
                ),
            ),
            v2_scratch=B.program(
                B.motor_go_to("A", 0, 360),
                B.show_image("YES"),
                B.beep(784, 150),
                B.motor_run_for("A", 270, 450),
                B.wait(0.9),
                B.show_image("NO"),
                B.beep(523, 150),
                B.motor_run_for("A", -270, 360),
                B.repeat(
                    40,
                    B.if_(
                        B.force_pressed("B"),
                        B.show_image("YES"),
                        B.beep(784, 150),
                        B.motor_run_for("A", 270, 450),
                        B.wait(0.9),
                        B.show_image("NO"),
                        B.motor_run_for("A", -270, 360),
                    ),
                    B.wait(0.03),
                ),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("想让道闸只抬起半高（45°），电机应该转多少度？（提示：45 × 3 = ？）", "If you want the boom to open halfway (45°), how many degrees should Motor A turn?", "ゲートを半分の45度だけ開けたいとき、モーターAは何度回せばいい？"),
            T("落杆前先连续闪烁箭头并响 3 声短促「嘀、嘀、嘀」警示行人！", "Add 3 warning beeps before lowering the gate boom!", "バーを下ろす前に「ピ・ピ・ピ」と3回警告音を鳴らそう！"),
        ],
    }
)


# ==================================================================================================
# Lesson 11: Rack & Pinion Pusher / Sorter
# ==================================================================================================
RACK_PUSHER = make_lesson(
    {
        "id": "rack-pusher",
        "level": "stage4",
        "stars": 4,
        "camera": {"pos": [5.8, 7.5, 7.8], "target": [0.5, 2.2, 0.5]},
        "title": T("齿轮齿条分拣推杆 (Rack & Pinion Pusher)", "Rack & Pinion Pusher Sorter", "ラック＆ピニオン仕分けプッシャー"),
        "summary": T(
            "用大型角度电机驱动 12 齿小齿轮啮合 13 孔齿条，把旋转运动变成直线推杆；修复 v1 行程过大顶死滑轨且不缩回的问题，配合颜色传感器实现智能分拣！",
            "Convert rotary motion into linear stroke with a Large Motor, 12T pinion, and 13L gear rack; fix v1's over-travel jam and build a color-triggered sorter!",
            "Lモーターの12歯ギアと13Lラックで回転を直線運動に変換。v1のストローク超過ロックを直し、色に応じた自動仕分け機を作ります。",
        ),
        "difficulty": T("小学 5-6 年级", "Grades 5-6", "小学5〜6年"),
        "duration": T("22 分钟", "22 min", "22分"),
        "concepts": ["motor", "gear", "sensor", "condition"],
        "ports": [
            {
                "port": "A",
                "device": T("大型角度电机 · 12T 齿轮轴 (45602)", "Large Angular Motor · 12T Pinion (45602)", "Lモーター・12歯ピニオン (45602)"),
                "note": T("竖装在主控右侧，旋转 12T 齿轮推动 13L 齿条横移", "Mounted upright on Hub right; drives the 12T pinion meshing with the 13L rack", "ハブ右側に垂直設置、12歯ギアで13Lラックを左右スライド"),
            },
            {
                "port": "E",
                "device": T("颜色传感器 · 质检口 (45605)", "Color Sensor · Inspection Gate (45605)", "カラーセンサー・検査ゲート (45605)"),
                "note": T("装在主控左侧面，检测货物颜色决定推杆行程", "Mounted on Hub left side to inspect item color", "ハブ左側面に装着し、色を判定して押し出し量を決定"),
            },
        ],
        "steps": [
            {
                "step": 1,
                "title": T("在 11×19 大底板上锁紧主控 Hub", "Mount Hub onto 11×19 Baseplate", "11×19ベースプレートにハブを固定"),
                "instruction": T("将 11×19 大底板（39369）平放桌面，用 4 颗黑销将主控（45601）固定在底板左侧。", "Pin the Hub (45601) onto the left half of the 11×19 baseplate (39369) with 4 black pins.", "11×19ベースプレート（39369）に黒ピン4本でハブを固定します。"),
                "substeps": [
                    T("在底板对应主控四角孔插 4 颗黑销（2780），压紧主控（45601）。", "Insert 4 vertical black pins into the baseplate and press the Hub down flush.", "底板に黒ピン4本を立ててハブをしっかり押し込みます。"),
                ],
                "tip": T("底板右侧留出 5 孔宽度用于垂直安装大型角度电机。", "Leave the right side of the baseplate open for the Large Angular Motor.", "右側にはLモーター用のスペースが空きます。"),
            },
            {
                "step": 2,
                "title": T("主控右侧锁定大型角度电机并接端口 A", "Pin Large Motor on Right & Wire Port A", "右側にLモーター固定・ポートA配線"),
                "instruction": T("用 4 颗黑销把大型角度电机（45602）直立锁在主控右侧面，输出盘朝上与主控顶面齐平，接入端口 A。", "Lock the Large Angular Motor (45602) upright onto the Hub's right side with 4 black pins and plug into Port A.", "ハブ右側面に黒ピン4本でLモーター（45602）を上向き固定し、ポートAへ接続します。"),
                "substeps": [
                    T("在主控右侧面四角孔插满 4 颗黑色摩擦销（2780）。", "Insert 4 black pins into all four corner holes on the Hub's right side.", "ハブ右側面の四隅4穴に黒ピンを挿します。"),
                    T("将大型电机（45602）输出十字孔朝上、左侧面 4 孔对准黑销按紧，线接入【端口 A】。", "Press the Large Motor upright onto the 4 pins so its top output sits flush with the Hub top; wire Port A.", "Lモーターの出力面を上にして押し込み、【ポートA】へ配線します。"),
                ],
                "wiring": [
                    {
                        "port": "A",
                        "device": T("大型角度电机 (45602)", "Large Angular Motor (45602)", "Lアンギュラーモーター (45602)"),
                        "route": T("从大型电机前端引出，跨过侧边插入主控左前端口 A。", "Route from the front of the Large Motor into Hub front-left Port A.", "Lモーター前部から左前のポートAへ接続。"),
                        "check": T("电线不要越过主控后侧的齿条滑轨区。", "Keep cable away from the rear rack guide channel.", "後部のラック走行ラインに線がかからないこと。"),
                    }
                ],
                "tip": T("大型电机（45602）高度正好也是 4 孔（80 LDU），顶面与主控顶面严丝合缝在同一水平面！", "The Large Motor is 4 studs tall (80 LDU), so its top face aligns flush with the Hub top!", "Lモーターの高さはハブと同じ4ポッチ（80 LDU）なので上面がピタッと揃います！"),
            },
            {
                "step": 3,
                "title": T("在主控后顶加装 15 孔齿条导轨梁", "Pin 15L Rear Guide Rail on Hub Top", "ハブ上部に15Lガイドレールを固定"),
                "instruction": T("在主控顶面后排左右两孔插 2 颗黑销，水平扣上 15 孔灰梁（32278）作为齿条直线滑轨靠山。", "Pin a 15L grey beam (32278) flat along the rear top edge of the Hub with 2 black pins to guide the sliding rack.", "ハブ上面後端の左右2穴に黒ピン2本を挿し、15Lビーム（32278）をガイドレールとして固定します。"),
                "substeps": [
                    T("在主控顶面最后排左、右角孔向上各插 1 颗黑销（2780）。", "Insert 2 vertical black pins into the Hub's rear-top corner holes.", "ハブ上面後ろの左右角穴に黒ピンを上向きに挿します。"),
                    T("将 15 孔长梁（32278）贴在两颗销上水平按紧，向右一直延伸到大型电机后方。", "Press the 15L beam flat onto both pins, extending right behind the Large Motor.", "15Lビームを水平に押し込み、Lモーター後ろまで伸ばします。"),
                ],
                "tip": T("这根 15 孔长梁就是齿条的「防退背板」，挡住齿条不往后脱齿！", "This 15L rail backs the gear rack at z=90.5 LDU so the teeth can never push away from the pinion!", "この15Lビームがラックの背面を支え、ギアの歯飛びを防ぎます！"),
            },
            {
                "step": 4,
                "title": T("装 12 齿小齿轮、13 孔齿条与洋红推头", "Install 12T Pinion, 13L Rack & Pusher Head", "12歯ピニオン・13Lラック・プッシャーヘッドを装着"),
                "instruction": T("在大型电机输出孔插 4L 竖轴与 12 齿小齿轮（32270），后方紧贴导轨放上 13 孔齿条（64781）咬合，齿条左端装 2×4 洋红推块！", "Insert a vertical 4L axle and 12T pinion into the Large Motor, mesh the 13L gear rack against the guide rail, and top the left tip with a 2×4 magenta pusher brick!", "Lモーターに4L軸と12歯ギアを立て、ガイドレールとの間に13Lラック（64781）を噛み合わせ、左端に2×4プッシャーブロックを付けます！"),
                "substeps": [
                    T("将 4L 黑十字轴（3705）竖直插进大型电机顶面十字孔，套上 12 齿小齿轮（32270）。", "Push a 4L axle vertically into the Large Motor output and slide on the 12T pinion (32270).", "Lモーター上面穴に4L十字軸を立て、12歯ギアをはめます。"),
                    T("将 13 孔齿条（64781）齿面朝前（-Z）、背面贴紧 15 孔导轨梁，与 12 齿小齿轮正切咬合（法向间距整 20 LDU = 1 孔）。", "Place the 13L rack (64781) between the 12T pinion and the 15L guide rail with teeth facing forward (-Z).", "13Lラックの歯を前に向け、15Lレールと12歯ギアの間にぴったり噛み合わせます。"),
                    T("在齿条左端竖直十字孔插 1 根 2L 红轴（32062），顶上套紧洋红 2×4 科技砖（3701）作为推头。", "Insert a 2L red axle (32062) vertically into the rack's left axle hole and press on the magenta 2×4 Technic brick (3701).", "ラック左端の十字穴に2L赤軸を立て、マゼンタの2×4ブロック（3701）を差し込みます。"),
                ],
                "tip": T("12 齿齿轮分度圆半径 = 15 LDU，加上齿条半厚 5 LDU，中心距正好 20 LDU（1 孔）！", "12T pitch radius (15 LDU) + rack pitch offset (5 LDU) = 20.0 LDU (1 exact stud)!", "12歯ピッチ半径15 LDU＋ラック5 LDU＝20.0 LDU（ぴったり1ポッチ）で噛み合います！"),
            },
            {
                "step": 5,
                "title": T("主控左侧安装颜色传感器并接端口 E", "Mount Side Color Sensor & Wire Port E", "左側にカラーセンサー装着・ポートE配線"),
                "instruction": T("在主控左前侧插 2 颗黑销，把颜色传感器（45605）镜头朝左外侧装好，线缆接入端口 E。", "Pin the color sensor (45605) on the Hub's front-left side with its lens facing left, wired to Port E.", "ハブ左前に黒ピン2本でカラーセンサー（45605）を外向きに固定し、ポートEへ接続します。"),
                "substeps": [
                    T("在主控左前侧上下两孔插 2 颗黑销（2780），扣紧颜色传感器（镜头朝左外侧作质检窗口）。", "Insert 2 black pins on the front-left side and press on the color sensor facing outward.", "ハブ左前の上下2穴に黒ピンを挿し、レンズを左外側に向けて固定します。"),
                    T("线缆向后插入主控左后【端口 E】。", "Plug the cable into Hub rear-left Port E.", "ケーブルを左後ろの【ポートE】へ接続します。"),
                ],
                "wiring": [
                    {
                        "port": "E",
                        "device": T("颜色传感器 (45605)", "Color Sensor (45605)", "カラーセンサー (45605)"),
                        "route": T("从左侧传感器直接连入左后端口 E。", "Route directly along the left side to Port E.", "左側面からポートEへ接続。"),
                        "check": T("电线压低在主控侧边，不挡上方齿条左移行程。", "Keep wire below the top surface so the sliding rack passes freely above.", "上のラックが左へスライドしたとき線に当たらないよう低く配線します。"),
                    }
                ],
                "tip": T("运行时点击仿真栏里的红/绿/蓝圆点按钮，可以实时切换待分拣积木的颜色！", "Click the Red / Green / Blue color dots in the simulator bar to test different sorting strokes!", "シミュバーの赤・緑・青ボタンで仕分け色をリアルタイムに切り替えられます！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "齿轮齿条（Rack & Pinion）是把「旋转角度」变成「精确直线距离」的经典机构（汽车方向盘转向、光驱托盘都用它）！12 齿小齿轮每转 1 圈（360°），正好拨过 12 颗齿 = 移动 12 × 0.75 孔 ≈ 9 孔（72mm），也就是每转 40° 精确平移 1 孔（8mm）！",
                "A rack-and-pinion converts rotation into exact linear travel (used in car steering!). One full 360° turn of the 12T pinion advances 12 teeth ≈ 72 mm — roughly 40° of rotation per 8 mm stud of slide!",
                "ラック＆ピニオンは回転を直線運動に変える機構です。12歯ギア1回転（360度）で約72mm進み、約40度回すごとに1ポッチ（8mm）正確にスライドします！",
            ),
            "troubleshoot": [
                T("齿条推到一半卡住或打滑？检查：① 后方 15 孔导轨梁是否插牢；② 程序旋转度数不能超过齿条总长（最大安全行程约 220°）！", "Rack jams partway? Check (1) the rear 15L guide rail is pinned tight, and (2) motor degrees stay within the rack's 220° safe stroke!", "途中で詰まる場合、後ろの15Lレールが外れていないか、回転角度が上限（約220度）を超えていないか確認！"),
                T("推完第 1 件物品后第 2 次推不动？因为推完忘记反转归零把齿条拉回起点了！", "Works once then stops pushing? You must reverse the motor back to 0° after each push so the rack retracts!", "1回押したあと動かない場合、モーターを逆転させてラックを原点（0度）へ戻し忘れています！"),
            ],
            "mod_ideas": [
                T("双向推拉机械手：在齿条左右两端都装上 L 形爪，往左推A货道、往右拉B货道！", "Two-Way Diverter: add paddles on BOTH ends of the 13L rack to push items left or right.", "両端プッシャー：ラックの両端にパドルを付けて左右2方向へ振り分けよう。"),
                T("加快推杆速度：如果想让电机转更少角度就推出更远，可以把 12 齿换成 20 齿齿轮（记得把导轨往后移半孔）！", "High-Speed Pinion: swap the 12T pinion for a 20T gear to get 1.67× more linear travel per motor degree!", "高速ピニオン：20歯ギアに替えると同じ回転角度で1.67倍遠くまで押し出せます！"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真观察推杆：v1 一口气让电机猛转 500°，远超 13 孔齿条的有效齿数，把齿条硬生生顶到极限卡死，而且推出去后不缩回原点，下一件货物根本没法分拣！",
                "Watch v1: commanding 500° wildly exceeds the 13L rack's tooth length, slamming the rack against its mechanical limit without ever retracting back to 0°!",
                "v1を観察：いきなり500度も回すためラックの可動限界に激突してロックし、さらに原点へ戻らないため次の荷物を処理できません！",
            ),
            v1_why=T(
                "直线机构都有严格的「行程上限（Stroke Limit）」！13 孔齿条有效行程约 60 LDU（对应 12T 齿轮约 220°），不计算行程且不归零复位会让机械结构堵转损坏。",
                "Every linear actuator has a finite stroke limit! On a 13L rack, safe travel is ~220° (≈ 58 LDU). Exceeding it stalls the motor, and skipping retraction leaves the mechanism jammed at the end.",
                "直線機構には必ずストローク上限があります。13Lラックの安全範囲は約220度までで、押し出し後の原点復帰も必須です。",
            ),
            v1_code="""import runloop
import motor
from hub import light_matrix, port, sound

async def main():
    # {{over_travel}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_W)
    await motor.run_for_degrees(port.A, 500, 800)
    await sound.beep(262, 300, 100)
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

runloop.run(main())
""",
            v1_comments={
                "over_travel": T("盲目猛转 500°（远超 220° 安全上限）且不退回原点！", "Blind 500° command exceeds the 220° rack limit and never retracts!"),
            },
            v1_explanations=[
                {
                    "lines": "8",
                    "title": T("超行程堵转与未复位", "Over-Travel Jam & Missing Retract"),
                    "desc": T("500° 相当于要求齿条移动 130 LDU（超过齿条全长），且没有 -deg 退回动作。", "500° demands 130 LDU of travel (more than the entire rack) and leaves the pusher extended."),
                },
            ],
            v1_blocks=B.program(
                B.show_image("ARROW_W"),
                B.motor_run_for("A", 500, 800),
                B.beep(262, 300),
                B.show_image("SAD"),
            ),
            v1_scratch=B.program(
                B.show_image("ARROW_W"),
                B.motor_run_for("A", 500, 800),
                B.beep(262, 300),
                B.show_image("SAD"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "按「每 40° 推 1 孔（20 LDU）」精准限位：检测到红色（默认）推满 5 孔长行程（200°）后自动退回 -200°；检测到其它颜色推 3 孔短行程（120°）后退回 -120°——既有安全边界又每次精准复位！",
                "Calibrate stroke at ~40° per stud: RED triggers a full 5-stud sort stroke (200°) then retracts -200°; other colors trigger a 3-stud stroke (120°) then retract -120° — zero jamming, 100% repeatable!",
                "1ポッチ≒40度で計算：赤なら長ストローク200度押し出して-200度で復帰、他色なら短ストローク120度で仕分け＆原点復帰します！",
            ),
            v2_code="""import runloop
import motor
import color_sensor
import color
from hub import light_matrix, port, sound

async def push_and_retract(deg, tone):
    # {{stroke}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_W)
    await sound.beep(tone, 120, 100)
    await motor.run_for_degrees(port.A, deg, 450)
    await runloop.sleep_ms(300)
    # {{retract}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_E)
    await motor.run_for_degrees(port.A, -deg, 400)

async def main():
    await motor.run_to_absolute_position(port.A, 0, 360)
    # {{sort_logic}}
    c = color_sensor.color(port.E)
    if c == color.RED:
        await push_and_retract(200, 784)
    else:
        await push_and_retract(120, 523)

    light_matrix.show_image(light_matrix.IMAGE_YES)

runloop.run(main())
""",
            v2_comments={
                "stroke": T("在安全上限（220°）内精准推出指定度数 deg", "Push out by exact calibrated degrees within the 220° safe limit"),
                "retract": T("推出去多少度（+deg），就反转多少度（-deg）丝滑缩回原点！", "Reverse by the exact same -deg to retract cleanly to origin!"),
                "sort_logic": T("红色货块推远道（200° ≈ 5 孔），其它颜色推近道（120° ≈ 3 孔）", "RED pushes far lane (200° ≈ 5 studs); others push near lane (120° ≈ 3 studs)"),
            },
            v2_explanations=[
                {
                    "lines": "7-15",
                    "title": T("推出去 + 缩回来闭环封装", "Push & Retract Helper Function"),
                    "desc": T("把 +deg 推出和 -deg 缩回写进同一个函数，保证每次动作结束齿条必回到 0° 起点。", "Pairing +deg and -deg inside one function guarantees the rack always returns home."),
                },
                {
                    "lines": "20-24",
                    "title": T("按颜色智能分级行程", "Color-Graded Stroke Length"),
                    "desc": T("利用仿真栏切换颜色（红 vs 蓝/绿）再点运行，对比 200° 长推杆和 120° 短推杆的区别！", "Click Blue or Green in the sim bar and re-run to compare the 120° short push vs 200° red push!"),
                },
            ],
            v2_blocks=B.program(
                B.motor_go_to("A", 0, 360),
                B.if_else(
                    B.color_is("E", "RED"),
                    [B.set_var("stroke", 200), B.beep(784, 120)],
                    [B.set_var("stroke", 120), B.beep(523, 120)],
                ),
                B.show_image("ARROW_W"),
                B.motor_run_for("A", B.var("stroke"), 450),
                B.wait(0.3),
                B.show_image("ARROW_E"),
                B.motor_run_for("A", B.arith(0, "-", B.var("stroke")), 400),
                B.show_image("YES"),
                variables=["stroke"],
            ),
            v2_scratch=B.program(
                B.motor_go_to("A", 0, 360),
                B.if_else(
                    B.color_is("E", "RED"),
                    [B.set_var_named("stroke", 200), B.beep(784, 120)],
                    [B.set_var_named("stroke", 120), B.beep(523, 120)],
                ),
                B.show_image("ARROW_W"),
                B.motor_run_for("A", B.get_var("stroke"), 450),
                B.wait(0.3),
                B.show_image("ARROW_E"),
                B.motor_run_for("A", B.arith(0, "-", B.get_var("stroke")), 400),
                B.show_image("YES"),
                variables=["stroke"],
            ),
            v2_scratch_vars=["stroke"],
        ),
        "challenges": [
            T("增加第 3 条分拣通道：红色推 210°、黄色推 140°、绿色推 70°！", "Create a 3-lane sorter: RED = 210°, YELLOW = 140°, GREEN = 70°!", "赤＝210度、黄＝140度、緑＝70度の3レーン仕分け機にアップグレードしよう！"),
            T("算出如果要让齿条恰好左移 2 孔（40 LDU = 16mm），电机应该转多少度？（提示：40 ÷ 0.2618 ≈ 153°）", "Calculate exact degrees to slide the rack 2 studs (40 LDU): 40 / 0.2618 ≈ 153°!", "ラックをちょうど2ポッチ（16mm）動かす角度を計算してみよう（約153度）！"),
        ],
    }
)


# ==================================================================================================
# Lesson 12: Smart Gripper Transporter (Capstone)
# ==================================================================================================
SMART_GRIPPER = make_lesson(
    {
        "id": "smart-gripper",
        "level": "stage4",
        "stars": 5,
        "camera": {"pos": [13.5, 11.5, 11.0], "target": [3.5, 1.2, -9.0]},
        "title": T("智能抓取运输车 (Smart Gripper Robot)", "Smart Gripper Transporter", "スマート搬送グリッパーロボ"),
        "summary": T(
            "综合毕业设计：在差速底盘车头集装大型角度电机开合机械爪与前视超声波传感器；修复 v1 还没开到货箱前就提前闭爪撞飞货物的顺序 Bug，全自动完成「探测接近 → 夹紧红箱 → 右转 90° 送达绿区 → 张爪卸货」！",
            "Capstone robot combining the Driving Base, a front Large Motor sweeping gripper claw, and a low-mounted Ultrasonic Sensor; fix v1's premature-clamp bug to autonomously approach, grab, turn 90°, and deliver to the green pad!",
            "総仕上げ：ドライブベース＋前面Lモーター開閉グリッパー＋下段距離センサーを統合。v1の「到着前に爪を閉じて荷物を弾き飛ばすバグ」を直し、接近→把持→90度旋回→緑ゾーン荷下ろしを全自動実行します！",
        ),
        "difficulty": T("小学 5-6 年级（综合毕业课）", "Grades 5-6 (Capstone)", "小学5〜6年（総合課題）"),
        "duration": T("25 分钟", "25 min", "25分"),
        "concepts": ["movement", "motor", "sensor", "state", "feedback"],
        "ports": [
            *DRIVE_PORTS,
            {
                "port": "A",
                "device": T("大型角度电机 · 机械爪驱动 (45602)", "Large Angular Motor · Gripper Claw (45602)", "Lモーター・グリッパー爪駆動 (45602)"),
                "note": T("横装在主控正前方，驱动右侧活动夹臂与黄色 L 形钩指", "Bolted horizontally across Hub front; drives the right sweeping jaw", "ハブ前面に横向き固定、右クランプ爪を開閉駆動"),
            },
            {
                "port": "F",
                "device": T("超声波距离传感器 · 高架货物雷达 (45604)", "Distance Sensor · High Mast Radar (45604)", "距離センサー・高架マストレーダー (45604)"),
                "note": T("通过两根 9 孔竖立桅杆架在车身后上方（高度 y=190），越过夹爪俯视前方高货塔", "Mounted on twin 9L upright masts at y=190 looking forward over the jaws", "2本の9Lマストで後上部（y=190）に設置し、爪の上から前方の荷物タワーを測距"),
            },
        ],
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("用 4 颗黑销在车头横装大型角度电机并接端口 A", "Bolt Large Motor Across Hub Front (Port A)", "車体前面にLモーターを4点固定・ポートA配線"),
                "instruction": T("在主控正前方四角孔插满 4 颗黑销，把大型角度电机（45602）输出盘朝上水平扣紧在车头，线缆接入端口 A。", "Insert 4 black pins into the Hub's 4 front corner holes, press the Large Angular Motor (45602) horizontally onto the nose with its rotor on top, and wire Port A.", "ハブ前面の四隅4穴に黒ピンを挿し、Lモーター（45602）を出力盤を上にして水平固定し、ポートAへ接続します。"),
                "substeps": [
                    T("在主控前面上排左/右、中排左/右共 4 个孔各插 1 颗黑销（2780）。", "Insert 4 black pins (2780) into the Hub front holes at (±40, 50) and (±40, 90).", "ハブ前面の上下左右4か所に黒ピンを挿します。"),
                    T("将大型电机（45602）横放，后侧 4 个孔对准主控前端 4 颗黑销用力按紧，输出圆盘位于右上方。", "Press the Large Motor flush against the Hub front so all 4 pins click in with the output disc at top-right.", "Lモーター背面4穴をピンに合わせ、出力盤が右上になる向きで押し込みます。"),
                    T("将电机线接入主控左前【端口 A】。", "Plug the motor cable into Hub front-left Port A.", "ケーブルを左前の【ポートA】へ接続します。"),
                ],
                "wiring": [
                    {
                        "port": "A",
                        "device": T("大型角度电机 (45602)", "Large Angular Motor (45602)", "Lアンギュラーモーター (45602)"),
                        "route": T("从车头大型电机左侧引出，向上接入主控左前端口 A。", "Loop up from the left end of the front motor into Port A.", "前面Lモーター左端から上へ回しポートAへ接続。"),
                        "check": T("4 颗黑销全部卡紧，搬运重物时车头电机纹丝不动。", "All 4 pins fully seated so the heavy front motor never sags.", "4本すべてのピンが奥まで入りグラつかないこと。"),
                    }
                ],
                "tip": T("4 颗销构成的矩形法兰盘能承受整个大型电机和货物的悬臂重量！", "A 4-pin rectangular flange easily supports the cantilevered mass of the Large Motor and cargo!", "4点フランジ固定により重いLモーターと荷物をしっかり支えます！"),
            },
            {
                "step": 3,
                "title": T("安装左侧固定青蓝导引钳臂", "Attach Fixed Left Cargo Guide Jaw", "左側の固定ガイドアームを装着"),
                "instruction": T("用 1 颗黑销（后）和 1 颗蓝色 3L 长销（前）把 9 孔青蓝梁（40490）水平固定在车头左上方，作为机械爪的左固定钳口。", "Pin a 9L azure beam (40490) horizontally along the top-left side bridging the Hub and Large Motor as the fixed left jaw.", "後ろに黒ピン1本、前に青3Lロングピン1本を使って9L水色ビーム（40490）を左上段に固定し、左側の受け爪にします。"),
                "substeps": [
                    T("在主控顶面左前角孔插 1 颗黑销（2780），在大型电机左前顶孔插 1 颗蓝色 3L 长销（6558）。", "Insert 1 black pin into the Hub top-front-left hole and 1 blue 3L pin (6558) into the motor top-front-left hole.", "ハブ左前上穴に黒ピン、Lモーター左前上穴に青3Lピンを挿します。"),
                    T("把 9 孔青蓝梁（40490）水平扣在两颗销上向前伸出（高度 y=130 LDU）。", "Press the 9L azure beam (40490) across both pins extending straight ahead at height y=130.", "9Lビームを2本のピンに水平に押し込み前へ伸ばします。"),
                ],
                "tip": T("左钳臂跨接主控与大型电机顶面，同时起到「上层拉杆加固车头」的双重作用！", "Bridging the Hub and motor top makes the left jaw double as an upper structural tie-bar!", "ハブとモーターを上から繋ぐ補強ブリッジの役割も兼ねています！"),
            },
            {
                "step": 4,
                "title": T("在输出盘上安装右侧活动夹臂与黄色钩指", "Build Motorized Right Sweeping Jaw & L-Finger", "出力盤に右可動アームと黄色フック指を装着"),
                "instruction": T("在大型电机右上方输出盘插 2 颗黑销，装上 9 孔洋红活动夹臂（40490），最前端再用 2 颗黑销加装向内弯的黄色 2×4 L 形钩指（32140）！", "Pin a 9L magenta clamping arm (40490) onto the Large Motor output disc with 2 black pins, then top its front tip with an inward-pointing yellow 2×4 L-finger (32140)!", "Lモーター出力盤に黒ピン2本で9Lマゼンタ可動アームを固定し、先端に内向きの黄色2×4 L字フック指（32140）を付けます！"),
                "substeps": [
                    T("在大型电机顶面输出圆盘的前、后两个对称孔向上各插 1 颗黑销（2780）。", "Insert 2 vertical black pins into the front and rear holes of the motor output disc.", "出力盤の前後2穴に黒ピンを上向きに挿します。"),
                    T("扣紧 9 孔洋红梁（40490）笔直向前伸出（与左钳臂同高 y=130 LDU，左右间距 6 孔）。", "Snap the 9L magenta beam (40490) straight forward parallel to the left jaw.", "9Lマゼンタビームを左アームと平行に前向き固定します。"),
                    T("在洋红夹臂最前端 2 孔向上插 2 颗黑销，扣上黄色 2×4 L 形梁（32140）短边朝左内侧勾住货物。", "Pin the yellow 2×4 L-beam (32140) onto the front two holes pointing inward (-X) to hook cargo.", "先端2穴に黒ピン2本で黄色2×4 L字ビームを内側向きに固定します。"),
                ],
                "tip": T("电机正转（+deg）右爪向外张开迎货，电机反转（-deg）右爪向内合拢把货箱夹在左右两爪之间！", "Positive motor degrees (+35°) swing the jaw wide open; negative degrees (-35°) clamp inward against the fixed left jaw!", "モーター正転（+）で爪が大きく開き、逆転（-）で内側に閉じて荷物をしっかり挟みます！"),
            },
            {
                "step": 5,
                "title": T("在车身后侧竖起双 9 孔雷达桅杆并安装超声波传感器（端口 F）", "Erect Twin 9L Rear Masts & High Distance Sensor (Port F)", "後部に2本の9Lマストを立て距離センサーを装着（ポートF）"),
                "instruction": T("在主控后侧左右各用 2 颗黑销竖立一根 9 孔灰梁（40490）作高架桅杆，顶部用 4 颗黑销锁紧前视超声波传感器（45604），线缆接入端口 F。", "Pin two upright 9L grey mast beams (40490) to the Hub's rear sides, mount the forward-facing Distance Sensor (45604) across their tops at height y=190, and wire Port F.", "ハブ後ろの左右側面に黒ピン2本ずつで9Lマスト（40490）を垂直に立て、上端（y=190）に距離センサー（45604）を前向き固定してポートFへ接続します。"),
                "substeps": [
                    T("在主控左后、右后侧面上下两孔各插 2 颗黑销（共 4 颗），把 2 根 9 孔灰梁（40490）笔直向上竖立扣紧。", "Insert 2 black pins into each rear side of the Hub and press on two vertical 9L beams (40490) as tall masts.", "ハブ左右の後ろ側上下穴に黒ピンを挿し、9Lビーム2本を垂直に立てます。"),
                    T("在两根桅杆顶端两孔（y=170 和 y=210）向内各插 2 颗黑销，把超声波传感器（45604）双眼朝前卡在两桅杆之间。", "Insert 2 pins near the top of each mast and snap the Distance Sensor (45604) between them facing straight ahead.", "両マスト上端の2穴に黒ピンを挿し、距離センサーを前向きに挟み込んで固定します。"),
                    T("把传感器线向下接入主控右后【端口 F】。", "Plug the sensor cable down into Hub rear-right Port F.", "ケーブルを真下の右後ろ【ポートF】へ接続します。"),
                ],
                "wiring": [
                    {
                        "port": "F",
                        "device": T("超声波距离传感器 (45604)", "Distance Sensor (45604)", "距離センサー (45604)"),
                        "route": T("从高架桅杆传感器直接向下连入主控右后端口 F。", "Route straight down the right mast into Port F.", "右マストに沿って真下のポートFへ接続。"),
                        "check": T("传感器架在 y=190 高处（像轮船驾驶台），车头夹爪（y=130）完全在它视线下方，且车头正面敞开能直接把高货塔抱进怀里！", "Perched at y=190 like a ship's bridge, the sensor looks cleanly over the y=130 jaws while leaving the front bay open for cargo!", "y=190の展望マストから爪（y=130）の頭上越しに前方の荷物タワーを正確に測距できます！"),
                    }
                ],
                "tip": T("为什么不把传感器装在车头正前面？因为车头正面要留给货箱滑进左右两爪之间！高架后桅杆既看得到高货塔，又绝不挡爪口！", "Why a rear mast instead of the front nose? Because cargo must slide right up against the front motor between the jaws! A high mast sees over the claw without blocking the grab bay!", "前にセンサーを置くと荷物が爪の奥まで入れません。後部マストに高く掲げることで視界と把持スペースを両立します！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "这台毕业机器人融合了三大工程巧思：①「高架瞭望塔空间解耦」：超声波架在后方高桅杆（y=190），夹爪在下层（y=130），既让开正面抓货通道，开合又绝不遮挡雷达；②「一静一动非对称夹爪」：左边固定导引、右边单电机扫掠钩紧，省零件且抓得稳；③「4 销法兰承重」保证车头不低头。",
                "Three engineering principles unite here: (1) High rear radar mast (y=190) looks over the jaws (y=130) while leaving the front bay completely open for cargo; (2) Fixed-left + active-right jaw geometry grabs cargo with minimal parts; (3) 4-pin front flange prevents nose droop.",
                "①後部高架マスト（y=190）で正面の把持スペースを空けつつ爪（y=130）の上から測距、②左固定＋右可動の非対称クランプで省パーツ高把持力、③4本ピンフランジで前垂れ防止——の3大設計が詰まっています。",
            ),
            "troubleshoot": [
                T("车头太重导致后万向轮翘起？确认主控电池端在后方压住重心，且起步加速度不要设满 1000。", "Nose feels heavy? The Hub's battery weight over the rear wheels balances the front motor as long as you accelerate smoothly (velocity 280–360).", "前が重い場合、急発進を避けて速度280〜360で滑らかに走らせると安定します。"),
                T("夹爪方向搞反了？记住从车顶往下看：电机 A 正转（+35°）是顺时针向外张开，反转（-35°）是逆时针向内夹紧！", "Jaw direction mixed up? Viewing from above: Motor A positive (+35°) swings CW outward (OPEN); negative (-35°) swings CCW inward (CLAMP)!", "爪の向き：上から見てモーターA正転（+35度）で外へ開き、逆転（-35度）で内へ閉じます！"),
            ],
            "mod_ideas": [
                T("加装地面颜色复核传感器：利用还空着的端口 E 在车底加装颜色传感器，确认绿色卸货区颜色后再松爪！", "Add Floor Color Verification: plug the Color Sensor into free Port E underneath to verify the green delivery zone before releasing!", "空いているポートEに下向きカラーセンサーを追加し、緑ゾーンを検知してから荷物を置こう！"),
                T("双联动齿轮对称爪：在输出轴上加两颗互相啮合的 12 齿小齿轮，让左右两根爪子同时向内合拢！", "Geared Symmetric Jaws: mesh two 12T gears so both left and right jaws close inward simultaneously!", "12歯ギア2枚を噛み合わせて左右の爪が同時に閉じる対称グリッパーに挑戦！"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看看这幕经典翻车：v1 一上来还没开车，就在原地先把机械爪合拢（-40°）关上了大门！接着还不看超声波传感器盲目往前冲，直接把前方的红色货箱撞翻，根本抓不进爪子里！",
                "Watch v1's classic blunder: it closes the gripper jaw (-40°) AT THE START while still far from the cargo, then drives forward blindly without checking the distance sensor — ramming the red crate with a closed claw!",
                "v1の失敗を見よう：出発前にその場で爪を閉じてしまい（-40度）、さらに距離センサーも見ずに直進するため、閉じた爪で赤い荷物に体当たりしてしまいます！",
            ),
            v1_why=T(
                "多机构协同机器人最讲究「状态顺序（State Sequence）」：必须【① 张开爪 → ② 边开边测距接近货物 → ③ 到位停车再合爪 → ④ 转向运送到终点 → ⑤ 松爪后退】，顺序错一步就会撞飞目标。",
                "Multi-actuator robots depend on strict state sequencing: (1) Open claw → (2) Drive until radar sees cargo in the jaws → (3) Stop & clamp → (4) Turn & transport → (5) Release & back away.",
                "複合ロボットでは動作順序（ステート管理）が命です。「①爪を開く→②距離を見ながら接近→③停止して掴む→④旋回搬送→⑤離して後退」の順を守る必要があります。",
            ),
            v1_code="""import runloop
import motor
import motor_pair
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    # {{wrong_order}}
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)
    await motor.run_for_degrees(port.A, -40, 400)
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, 600, 0, velocity=360)
    await sound.beep(262, 300, 100)

runloop.run(main())
""",
            v1_comments={
                "wrong_order": T("顺序全错：在起点就提前把爪关上（-40°），再盲目直冲撞上货箱！", "Wrong sequence: closes claw (-40°) at start, then rams the cargo box blindly!"),
            },
            v1_explanations=[
                {
                    "lines": "10-11",
                    "title": T("未张爪迎货 + 未用雷达测距", "Premature Clamp & Blind Drive"),
                    "desc": T("先把爪子关死再往前开，货箱根本进不了钳口。", "Closing the jaw before driving blocks the cargo from entering the gripper."),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.show_image("SAD"),
                B.motor_run_for("A", -40, 400),
                B.move_for(600, 0, 360),
                B.beep(262, 300),
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.show_image("SAD"),
                B.motor_run_for("A", -40, 400),
                B.move_for(600, 0, 360),
                B.beep(262, 300),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "按 5 步标准状态机执行：① 先转 +35° 张开大爪；② 慢速前进并用 `0 < dist < 100` 测到红箱滑入钳口（雷达在车尾，离爪口还有 8.8 cm，所以读数 < 10 cm 时货物已进入两爪之间）立即停车；③ 转 -70° 稳稳钩紧红箱（夹住货物自动停在接触角）；④ 原地右转 90°（215°）并前进 330° 送达右侧绿色卸货区；⑤ 转 +35° 松开爪子并后退 180° 完美交货！",
                "Execute a 5-stage autonomous mission: (1) Open jaw +35°; (2) Approach until `0 < dist < 100` spots the red crate inside the bay (the rear radar sits 8.8 cm behind the jaw mouth, so < 10 cm means the crate is between the jaws); (3) Stop & clamp -70° (stalling snugly against the crate); (4) Pivot 90° right (215°) and drive 330° onto the green delivery zone; (5) Open jaw +35° and reverse 180°!",
                "5段階の自動シーケンス：①+35度で爪を開く→②`0 < dist < 100`で赤箱が爪に入った瞬間に停止（センサーは爪口の8.8cm後ろなので、10cm未満＝爪の間）→③-70度でしっかり把持→④右へ90度旋回して330度前進し緑ゾーンへ→⑤+35度で爪を開いて180度バックし配送完了！",
            ),
            v2_code="""import runloop
import motor
import motor_pair
import distance_sensor
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    await motor.run_to_absolute_position(port.A, 0, 300)

    # {{step1_open}}
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
    await motor.run_for_degrees(port.A, 35, 300)
    motor_pair.move(motor_pair.PAIR_1, 0, velocity=260)

    # {{step2_approach}}
    while True:
        d = distance_sensor.distance(port.F)
        if 0 < d < 100:
            break
        await runloop.sleep_ms(20)
    motor_pair.stop(motor_pair.PAIR_1)

    # {{step3_grab}}
    await motor.run_for_degrees(port.A, -70, 320)
    await sound.beep(784, 150, 100)

    # {{step4_deliver}}
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, 215, 100, velocity=260)
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, 330, 0, velocity=340)

    # {{step5_release}}
    await motor.run_for_degrees(port.A, 35, 300)
    await motor_pair.move_for_degrees(motor_pair.PAIR_1, -180, 0, velocity=280)
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)
    await sound.beep(988, 250, 100)

runloop.run(main())
""",
            v2_comments={
                "step1_open": T("阶段 1：先正转 +35° 张开右爪，再平稳向前开向红色货箱", "Phase 1: swing jaw +35° wide open, then drive toward the red cargo crate"),
                "step2_approach": T("阶段 2：高架超声波测到读数 < 100mm（减去 88mm 后货箱已进爪口）立即刹停！", "Phase 2: stop as soon as mast radar reads < 100 mm (minus 88 mm = crate inside the jaws)!"),
                "step3_grab": T("阶段 3：反转 -70° 向内合拢把货箱牢牢抱紧！", "Phase 3: swing -70° inward to clamp the cargo crate securely!"),
                "step4_deliver": T("阶段 4：原地右转 90°（215°）对准右侧绿色终点，直行 330° 送达！", "Phase 4: pivot 90° right (215°) and drive 330° onto the green delivery pad!"),
                "step5_release": T("阶段 5：正转 +35° 松开夹爪，倒车退后 180° 留出货物，欢呼通关！", "Phase 5: open jaw +35°, back away 180°, and celebrate mission complete!"),
            },
            v2_explanations=[
                {
                    "lines": "13-22",
                    "title": T("张爪迎货 + 高架雷达精准停靠", "Open-Claw Approach & Mast Radar Docking"),
                    "desc": T("先张开 +35° 再前进，高架雷达位于后方，雷达到爪口有 88mm，当测距 0 < d < 100mm 时红箱正好滑入车头左右两爪之间。", "Opening +35° first lets the crate enter the bay; `0 < d < 100` from the rear mast (88 mm behind the jaw mouth) stops right when the crate sits between the jaws."),
                },
                {
                    "lines": "25-35",
                    "title": T("夹紧实物搬运 → 转向运输 → 卸货后退闭环", "Grab Cargo → Turn & Transport → Release & Retreat"),
                    "desc": T("在 3D 仿真中你会看到红色货箱被真实夹住、跟随机器人一起右转并被放到绿色目标垫上！", "In the 3D simulator, watch the red cargo crate get physically gripped, carried around the 90° turn, and deposited onto the green pad!"),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.motor_go_to("A", 0, 300),
                B.show_image("ARROW_N"),
                B.motor_run_for("A", 35, 300),
                B.move_start(0, 260),
                B.repeat_until(
                    B.logic(
                        B.compare(B.distance("F"), ">", 0),
                        "and",
                        B.compare(B.distance("F"), "<", 100),
                    ),
                    B.wait(0.02),
                ),
                B.move_stop(),
                B.motor_run_for("A", -70, 320),
                B.beep(784, 150),
                B.move_for(215, 100, 260),
                B.move_for(330, 0, 340),
                B.motor_run_for("A", 35, 300),
                B.move_for(-180, 0, 280),
                B.show_image("HAPPY"),
                B.beep(988, 250),
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.motor_go_to("A", 0, 300),
                B.show_image("ARROW_N"),
                B.motor_run_for("A", 35, 300),
                B.move_start(0, 260),
                B.repeat_until(
                    B.logic(
                        B.compare(B.port("spike_distance", "F"), ">", 0),
                        "and",
                        B.compare(B.port("spike_distance", "F"), "<", 100),
                    ),
                    B.wait(0.02),
                ),
                B.move_stop(),
                B.motor_run_for("A", -70, 320),
                B.beep(784, 150),
                B.move_for(215, 100, 260),
                B.move_for(330, 0, 340),
                B.motor_run_for("A", 35, 300),
                B.move_for(-180, 0, 280),
                B.show_image("HAPPY"),
                B.beep(988, 250),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("结合第 6 课陀螺仪：把阶段 4 的 `move_for_degrees(215, 100)` 升级为陀螺仪闭环 90° 精准转弯！", "Upgrade Phase 4's open-loop 215° turn to Lesson 6's closed-loop gyro 90° turn!", "段階4の旋回をレッスン6のジャイロ90度ターンにアップグレードしよう！"),
            T("卸完货后让机器人自动原地掉头（180° = 430° 轮角）开回出发点待命！", "After releasing the cargo, turn 180° around and drive all the way back to the starting base!", "荷下ろし後にUターンしてスタート地点まで自動で帰還させよう！"),
        ],
    }
)

STAGE4_LESSONS = [GEAR_GATE, RACK_PUSHER, SMART_GRIPPER]
