"""Stage 3 (Grades 3-5): Sensors, Real-Time Sampling & Proportional Feedback.

Lessons:
  07. obstacle-avoider — Driving Base + Ultrasonic F | -1 out-of-range trap vs 0 < dist < 180 guard
  08. color-traffic    — Driving Base + Color E      | High-speed 450ms blind sleep vs 20ms fast sampling
  09. line-follower    — Driving Base + Color E      | Bang-bang zig-zag vs proportional (P) edge tracking
"""
from __future__ import annotations

from app.cad.assembly import T
from app.data import blocks_dsl as B
from app.data.lessons_stage1 import _ver_pair, make_lesson
from app.data.lessons_stage2 import DRIVE_PORTS, REUSE_BASE_STEP


# ==================================================================================================
# Lesson 07: Ultrasonic Obstacle Avoider
# ==================================================================================================
OBSTACLE_AVOIDER = make_lesson(
    {
        "id": "obstacle-avoider",
        "level": "stage3",
        "stars": 3,
        "camera": {"pos": [12.0, 11.0, 10.5], "target": [2.0, 1.0, -7.5]},
        "title": T("超声波避障车 (Obstacle Avoider)", "Ultrasonic Obstacle Avoider", "超音波障害物よけカー"),
        "summary": T(
            "给差速小车装上前视超声波距离传感器；揭秘 v1 为什么在空旷处也会疯狂倒车（-1 无效值陷阱），实现精准探测与右转绕障。",
            "Mount the ultrasonic distance sensor up front; fix v1's `-1` out-of-range trap that makes it reverse in open air, and dodge 3D walls cleanly.",
            "正面に距離センサーを装着。何もない場所でバックしてしまうv1の「-1問題」を解決し、3Dの壁を確実に回避します。",
        ),
        "difficulty": T("小学 3-4 年级", "Grades 3-4", "小学3〜4年"),
        "duration": T("15 分钟", "15 min", "15分"),
        "concepts": ["sensor", "condition", "forever", "debug"],
        "ports": [
            *DRIVE_PORTS,
            {
                "port": "F",
                "device": T("超声波距离传感器 (45604)", "Distance Sensor (45604)", "距離センサー (45604)"),
                "note": T("朝正前方装在车头横梁上，接入右后端口 F", "Mounted forward on front beam; wired to rear-right Port F", "車体前面に前向き装着、右後ろのポートFへ接続"),
            },
        ],
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("车头上排固定 7 孔支架梁", "Pin Front 7L Mounting Beam", "前面上段に7Lブラケットを固定"),
                "instruction": T("在主控正前方上排左右两孔插 2 颗黑销，水平扣紧 7 孔灰梁（32524）。", "Insert 2 black pins into the Hub's upper-front holes and attach a 7L grey beam (32524).", "ハブ前面上段の左右2穴に黒ピンを挿し、7Lビーム（32524）を固定します。"),
                "substeps": [
                    T("在主控前面顶排左、右两孔各插 1 颗黑色摩擦销（2780）。", "Push 2 black pins (2780) into the top-front left and right Hub holes.", "ハブ前面上段の左右2穴に黒ピン2本を挿します。"),
                    T("把 7 孔灰梁（32524）居中扣紧在 2 颗黑销上。", "Press the 7L beam (32524) centered onto both pins.", "7Lビームを中央合わせでしっかり押し込みます。"),
                ],
                "tip": T("支架装在顶排（高度 y=90 LDU），能让超声波视线避开地面杂波。", "Mounting on the upper row keeps the ultrasonic beam clear of floor reflections.", "上段に付けることで床からの誤反射を防ぎます。"),
            },
            {
                "step": 3,
                "title": T("安装超声波传感器并接端口 F", "Mount Distance Sensor & Wire Port F", "距離センサーを装着しポートFへ配線"),
                "instruction": T("在 7 孔梁最外侧两孔插 2 颗黑销，扣上超声波传感器（45604）双眼朝前，接入端口 F。", "Pin the distance sensor (45604) onto the outer holes of the 7L beam facing forward and plug into Port F.", "7Lビーム両端に黒ピン2本で距離センサー（45604）を前向きに固定し、ポートFへ接続します。"),
                "substeps": [
                    T("在 7 孔梁最左（第 1 孔）和最右（第 7 孔）向前各插 1 颗黑销（2780）。", "Insert 2 black pins into the outermost holes (#1 and #7) of the front 7L beam.", "7Lビームの両端（1番・7番穴）に黒ピン2本を挿します。"),
                    T("将超声波传感器（45604）两只大眼睛朝正前方，背面两孔对准黑销按紧。", "Press the distance sensor onto both pins with its twin eyes facing straight ahead.", "2つの「目」を正面に向けてピンに押し込みます。"),
                    T("将线缆从右侧绕回主控右后【端口 F】。", "Route the cable back into Hub rear-right Port F.", "ケーブルをハブ右後ろの【ポートF】に差し込みます。"),
                ],
                "wiring": [
                    {
                        "port": "F",
                        "device": T("超声波距离传感器 (45604)", "Distance Sensor (45604)", "距離センサー (45604)"),
                        "route": T("从车头传感器背面引出，沿右侧上方插入右后端口 F。", "Route from the sensor rear along the right side into Port F.", "センサー背面から右側を通し右後ろのポートFへ。"),
                        "check": T("两只声波圆眼正前方无电线遮挡。", "Ensure no cable droops in front of the sensor eyes.", "センサーの目の前に線が垂れていないか確認。"),
                    }
                ],
                "tip": T("3D 场地前方放了红、橙两面障碍墙，仿真器会用 3D 射线自动算真实距离！", "The 3D arena has red and orange walls; the simulator raycasts real 3D distance automatically!", "3Dアリーナの壁までの距離をシミュレーターが自動計測します！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "超声波传感器像蝙蝠一样发射声波测回音。安装必须「正对前方 + 离地适当高度」：装太低会把地板当成障碍物，只用 1 颗销则会歪头漏看正前方的墙。",
                "Ultrasonic sensors emit sound cones like bats. Mounting it high and level with 2 pins keeps floor echoes out and aims the beam straight ahead.",
                "超音波は音の跳ね返りで距離を測ります。低すぎると床を検知してしまうため、上段に2本ピンで水平固定します。",
            ),
            "troubleshoot": [
                T("前面明明没东西却一直报警？检查是不是代码没过滤 -1，或者线缆挡在了传感器眼睛前面！", "False alarms in open space? Either a wire is blocking the eyes or your code forgot to filter out -1!", "何もないのに反応する場合、目の前の配線かプログラムの「-1」未除外を確認！"),
                T("斜着撞墙不反弹？声波遇到太斜的光滑墙面会像镜子一样弹走，尽量正对障碍物探测。", "Angled wall missed? Sound waves bounce away off steep angles; approach walls within ~30°.", "斜めの壁は音が逸れやすいため、正面から近づくようにします。"),
            ],
            "mod_ideas": [
                T("机械触须保险杠：在传感器下方再加一根宽横梁，万一盲区擦碰也能物理防撞。", "Whisker Bumper: add a lower wide beam beneath the sensor as a physical backup guard.", "下部バンパー追加：センサー下にワイド梁を足して二重ガードにしよう。"),
                T("转头雷达：把超声波传感器装到中型电机转盘上，停车时左右摇头扫描哪边路更宽！", "Scanning Radar Turret: mount the sensor on a motor rotor to scan left and right before choosing a turn!", "首振りレーダー：モーターの上に距離センサーを載せて左右をスキャンしよう！"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看看：小车刚躲开红墙转向空旷地带，前方明明一望无际没有墙，小车却发疯一样不停倒车、转弯、再倒车！",
                "Run v1 and watch: after dodging the red wall into wide-open space, the robot goes crazy reversing and turning endlessly in empty air!",
                "v1を実行してみよう：赤い壁を避けて広い場所に出た途端、前に何もないのに延々とバックと旋回を繰り返します！",
            ),
            v1_why=T(
                "SPIKE 3 官方传感器铁律：当超过约 2 米测不到回音时，distance_sensor.distance() 会返回 `-1`！如果只写 `dist < 180`，因为 `-1 < 180` 在数学上为真，小车就会把「前方无障碍 (-1)」当成「贴脸撞墙」！",
                "Official SPIKE 3 rule: when no echo returns (>2 m), distance_sensor.distance() returns `-1`! Writing `dist < 180` treats `-1` as `< 180` (True!), triggering phantom collisions in open space!",
                "SPIKE 3 では測定範囲外（壁なし）のとき `-1` を返します！`dist < 180` だけだと `-1 < 180` が真になり、空っぽの空間を壁と勘違いします！",
            ),
            v1_code="""import runloop
import motor_pair
import distance_sensor
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)

    # {{bug_minus_one}}
    while True:
        dist = distance_sensor.distance(port.F)
        if dist < 180:
            motor_pair.stop(motor_pair.PAIR_1)
            light_matrix.show_image(light_matrix.IMAGE_NO)
            await sound.beep(440, 150, 100)
            await motor_pair.move_for_degrees(motor_pair.PAIR_1, -180, 0, velocity=300)
            await motor_pair.move_for_degrees(motor_pair.PAIR_1, 215, 100, velocity=280)
        else:
            motor_pair.move(motor_pair.PAIR_1, 0, velocity=360)
        await runloop.sleep_ms(20)

runloop.run(main())
""",
            v1_comments={
                "bug_minus_one": T("致命陷阱：空旷处 dist 返回 -1，而 -1 < 180 为真，引发无限假避障！", "Classic trap: open air returns -1, and -1 < 180 is True — endless false dodging!"),
            },
            v1_explanations=[
                {
                    "lines": "12-13",
                    "title": T("-1 超量程返回值陷阱", "The -1 Out-of-Range Return Trap"),
                    "desc": T("没检查 dist > 0，导致测不到墙壁（-1）时也进入 if 分支疯狂倒车。", "Without checking dist > 0, an out-of-range -1 reading triggers the obstacle branch."),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.forever(
                    B.if_else(
                        B.compare(B.distance("F"), "<", 180),
                        [
                            B.move_stop(),
                            B.show_image("NO"),
                            B.beep(440, 150),
                            B.move_for(-180, 0, 300),
                            B.move_for(215, 100, 280),
                        ],
                        [B.move_start(0, 360)],
                    ),
                ),
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.forever(
                    B.if_else(
                        B.compare(B.port("spike_distance", "F"), "<", 180),
                        [
                            B.move_stop(),
                            B.show_image("NO"),
                            B.beep(440, 150),
                            B.move_for(-180, 0, 300),
                            B.move_for(215, 100, 280),
                        ],
                        [B.move_start(0, 360)],
                    ),
                ),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "把判断条件写成 `0 < dist < 180`（同时要求大于 0 且小于 180 毫米），彻底过滤掉 `-1` 无效值！现在小车遇到红墙、橙墙都会优雅后退右转，进入开阔地则笔直巡航！",
                "Guard the condition as `0 < dist < 180` so `-1` is rejected! Now the robot cleanly dodges both the red and orange walls and cruises smoothly once clear!",
                "`0 < dist < 180`（0より大きく180未満）に修正して `-1` を除外！赤壁・オレンジ壁を連続で綺麗に回避して直進します。",
            ),
            v2_code="""import runloop
import motor_pair
import distance_sensor
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)

    # {{safe_range}}
    while True:
        dist = distance_sensor.distance(port.F)
        if 0 < dist < 180:
            motor_pair.stop(motor_pair.PAIR_1)
            light_matrix.show_image(light_matrix.IMAGE_NO)
            await sound.beep(523, 140, 100)
            await motor_pair.move_for_degrees(motor_pair.PAIR_1, -180, 0, velocity=300)
            await motor_pair.move_for_degrees(motor_pair.PAIR_1, 215, 100, velocity=280)
            light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
        else:
            motor_pair.move(motor_pair.PAIR_1, 0, velocity=360)
        await runloop.sleep_ms(20)

runloop.run(main())
""",
            v2_comments={
                "safe_range": T("0 < dist < 180：过滤掉 -1，只在真遇到 18cm 内障碍墙时才后退右转！", "0 < dist < 180 filters out -1 and triggers only on real walls within 18 cm!"),
            },
            v2_explanations=[
                {
                    "lines": "12-13",
                    "title": T("双向区间过滤无效值", "Two-Sided Range Guard"),
                    "desc": T("Python 支持连写 0 < dist < 180，一行代码同时完成「有效值校验」和「距离阈值判断」。", "Python's chained `0 < dist < 180` validates the reading and checks the 180 mm threshold in one expression."),
                },
                {
                    "lines": "17-18",
                    "title": T("后退留出转弯空间再右转 90°", "Reverse Before Pivoting 90°"),
                    "desc": T("先退 180° 拉开安全距离，再用第 5 课标定的 215° 原地右转 90°，绝不刮墙角。", "Backing up 180° creates clearance before pivoting 90° (215 motor degrees)."),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.forever(
                    B.if_else(
                        B.logic(
                            B.compare(B.distance("F"), ">", 0),
                            "and",
                            B.compare(B.distance("F"), "<", 180),
                        ),
                        [
                            B.move_stop(),
                            B.show_image("NO"),
                            B.beep(523, 140),
                            B.move_for(-180, 0, 300),
                            B.move_for(215, 100, 280),
                            B.show_image("ARROW_N"),
                        ],
                        [B.move_start(0, 360)],
                    ),
                ),
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.show_image("ARROW_N"),
                B.forever(
                    B.if_else(
                        B.logic(
                            B.compare(B.port("spike_distance", "F"), ">", 0),
                            "and",
                            B.compare(B.port("spike_distance", "F"), "<", 180),
                        ),
                        [
                            B.move_stop(),
                            B.show_image("NO"),
                            B.beep(523, 140),
                            B.move_for(-180, 0, 300),
                            B.move_for(215, 100, 280),
                            B.show_image("ARROW_N"),
                        ],
                        [B.move_start(0, 360)],
                    ),
                ),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("加入「二级减速预警」：当 180 <= dist < 350 时把巡航速度降到 180°/s 慢行靠近。", "Add a warning zone: when 180 <= dist < 350, slow cruising speed to 180°/s.", "180〜350mmのとき速度を180に落とす予告減速を追加しよう。"),
            T("用变量 count 记录避障次数，躲过 2 面墙后自动停车欢呼！", "Count wall dodges in a variable and stop to celebrate after clearing 2 walls!", "壁を避けた回数を変数で数え、2回クリアしたら止まってお祝いしよう！"),
        ],
    }
)


# ==================================================================================================
# Lesson 08: Color Traffic Car
# ==================================================================================================
COLOR_TRAFFIC = make_lesson(
    {
        "id": "color-traffic",
        "level": "stage3",
        "stars": 3,
        "camera": {"pos": [9.5, 8.8, 7.5], "target": [0.0, 0.8, -8.5]},
        "title": T("色彩交通车 (Color Traffic Car)", "Color Traffic Car", "カラー信号カー"),
        "summary": T(
            "车头装上朝下看的颜色传感器，识别地面绿、黄、蓝、红四色交通标线；解决 v1 车速过快 + 采样太慢直接冲过红灯的事故！",
            "Mount a downward-facing color sensor to read green, yellow, blue, and red floor bands; fix v1's slow sampling that blasts right through the red stop line!",
            "下向きカラーセンサーで床の4色ラインを判別。v1の「速すぎ＋確認遅すぎ」による赤信号無視を高速サンプリングで解決します。",
        ),
        "difficulty": T("小学 3-4 年级", "Grades 3-4", "小学3〜4年"),
        "duration": T("15 分钟", "15 min", "15分"),
        "concepts": ["sensor", "condition", "loop", "debug"],
        "ports": [
            *DRIVE_PORTS,
            {
                "port": "E",
                "device": T("颜色传感器 (45605)", "Color Sensor (45605)", "カラーセンサー (45605)"),
                "note": T("镜头朝下悬在车头前方，接入左后端口 E", "Lens facing down ahead of front beam; wired to rear-left Port E", "車体前端にレンズ下向きで装着、左後ろのポートEへ接続"),
            },
        ],
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("车头中排安装 7 孔支架梁", "Pin Front 7L Mounting Beam", "前面中段に7Lブラケットを固定"),
                "instruction": T("在主控正前方中排左右两孔插 2 颗黑销，水平扣上 7 孔灰梁（32524）。", "Insert 2 black pins into the middle-row front Hub holes and attach a 7L beam (32524).", "ハブ前面中段の左右2穴に黒ピンを挿し、7Lビーム（32524）を固定します。"),
                "substeps": [
                    T("在主控前面中排（y=70，与轮轴同高）左右两孔插 2 颗黑销（2780）。", "Insert 2 black pins into the middle-row front holes (axle height).", "ハブ前面中段（車軸と同じ高さ）の左右穴に黒ピン2本を挿します。"),
                    T("把 7 孔灰梁（32524）居中按紧在 2 颗黑销上。", "Snap the 7L beam centered onto both pins.", "7Lビームを中央で押し込みます。"),
                ],
                "tip": T("中排高度能让颜色传感器镜头刚好离地约 8.4 毫米——这是官方颜色识别最准的黄金距离！", "Axle-row height suspends the color lens ~8.4 mm above the floor — the sweet spot for color sensing!", "レンズと床の距離が約8.4mmになり、最も正確に色を読める高さになります！"),
            },
            {
                "step": 3,
                "title": T("装颜色传感器（镜头朝下）并接端口 E", "Mount Color Sensor Downward & Wire Port E", "カラーセンサーを下向き装着・ポートE配線"),
                "instruction": T("在 7 孔梁中间两孔插 2 颗黑销，扣紧颜色传感器（45605）圆形镜头朝向地面，接入端口 E。", "Pin the color sensor (45605) face-down onto the center of the 7L beam and plug into Port E.", "7Lビーム中央2穴にカラーセンサー（45605）をレンズ下向きで固定し、ポートEへ接続します。"),
                "substeps": [
                    T("在 7 孔梁第 3、第 5 孔向前各插 1 颗黑色摩擦销（2780）。", "Insert 2 black pins into holes #3 and #5 of the front 7L beam.", "7Lビームの3番・5番穴に黒ピンを2本挿します。"),
                    T("将颜色传感器（45605）发光镜头垂直朝下，后侧两孔对准黑销按紧。", "Press the color sensor onto both pins with its round lens pointing straight down.", "丸いレンズを真下に向けて2本のピンに押し込みます。"),
                    T("将线缆从左侧绕回主控左后【端口 E】。", "Route the cable back into Hub rear-left Port E.", "ケーブルをハブ左後ろの【ポートE】へ接続します。"),
                ],
                "wiring": [
                    {
                        "port": "E",
                        "device": T("颜色传感器 (45605)", "Color Sensor (45605)", "カラーセンサー (45605)"),
                        "route": T("从车头传感器向后沿左侧接入左后端口 E。", "Route along the left side into rear-left Port E.", "左側面を通して左後ろのポートEへ接続。"),
                        "check": T("镜头与地面平行且无任何遮挡。", "Confirm the bottom lens faces the floor squarely.", "レンズが床と平行で遮るものがないか確認。"),
                    }
                ],
                "tip": T("3D 地面依次铺了绿、黄、蓝、红四条色带，传感器移到色带上方会自动读取真实颜色！", "The 3D floor has GREEN, YELLOW, BLUE, and RED bands that the virtual sensor reads live as it rolls over them!", "3D床の緑・黄・青・赤の帯の上を通るとセンサーが実際に色を読み取ります！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "颜色传感器靠自带环形白光灯照亮地面并接收反射光。离地太远（>2cm）会混入教室环境光导致认错颜色；贴太低又会卡住地板接缝。离地 8~12mm（约 1 孔）最稳定。",
                "The color sensor shines its own white LED ring and reads reflected light. Too high (>2 cm) lets ambient room lightwash out colors; 8–12 mm (~1 stud) is optimal.",
                "カラーセンサーは内蔵ライトの反射光を見ます。高すぎると部屋の光が混ざり、低すぎると床に擦れるため約1ポッチ（8〜12mm）が最適です。",
            ),
            "troubleshoot": [
                T("黄色或绿色认不准？检查传感器有没有装歪斜，镜头必须垂直正对地面。", "Misreading yellow or green? Make sure the sensor is pinned with 2 pins so the lens stays perpendicular to the floor.", "色を読み間違う場合、2本ピンでレンズが床に垂直になっているか確認しましょう。"),
                T("红线停不住？不仅要看传感器高度，更要检查程序里的循环 sleep_ms 是不是写太大了！", "Overshooting the red line? Check your loop's sleep_ms — a long pause makes the robot drive blind!", "赤線で止まれない場合、プログラムの sleep_ms が長すぎて目隠し走行になっていないかチェック！"),
            ],
            "mod_ideas": [
                T("防眩光遮光罩：在传感器左右两侧各挂一块 3×5 L 形黑梁，挡住窗外阳光干扰。", "Light Shield Skirt: hang 3×5 beams on both sides of the sensor to block bright window glare.", "遮光フード：センサーの両脇にビームを添えて外光をカットしよう。"),
                T("双传感器校验车：同时装上颜色传感器（看地标）和超声波传感器（防追尾）。", "Dual-Sensor Cruiser: combine the low color sensor with a high distance sensor for full traffic safety.", "2センサー搭載：下向きカラー＋前向き距離センサーの安全パトカーにしよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看看：小车以 750 高速猛冲，循环里却每 450 毫秒才看一眼颜色传感器——结果小车闭着眼直接飞跃窄窄的红线，一路冲出跑道停不下来！",
                "Watch v1: blasting at 750°/s while checking the sensor only once every 450 ms makes the car leap right over the thin red stop line without ever seeing it!",
                "v1を観察：速度750で爆走しながら450msに1回しかセンサーを見ないため、細い赤ラインを一瞬で飛び越えて止まれません！",
            ),
            v1_why=T(
                "这是机器人感知的「采样率定律」：车速 750°/s 时，450 毫秒小车已经往前冲了 16 厘米，而红色停车线只有 2.2 厘米宽，在两次睁眼之间早就滑过去了！",
                "Sampling theorem in action: at 750°/s the car travels ~16 cm during a 450 ms sleep — easily jumping past a 2.2 cm red tape strip between checks!",
                "サンプリングの基本：450ms眠っている間に車が約16cmも進んでしまい、幅2.2cmの赤テープを「まばたきの間」に通過してしまいます。",
            ),
            v1_code="""import runloop
import motor_pair
import color_sensor
import color
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    motor_pair.move(motor_pair.PAIR_1, 0, velocity=750)

    # {{slow_poll}}
    for _ in range(8):
        c = color_sensor.color(port.E)
        if c == color.RED:
            break
        await runloop.sleep_ms(450)

    motor_pair.stop(motor_pair.PAIR_1)
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

runloop.run(main())
""",
            v1_comments={
                "slow_poll": T("750 极速 + 450ms 才检查一次：红线在闭眼瞬间就被跨过去了！", "750 speed + 450 ms sleep — jumps right over the red line unseen!"),
            },
            v1_explanations=[
                {
                    "lines": "12-16",
                    "title": T("车速过快 + 采样过慢 = 漏检", "Too Fast + Slow Polling = Missed Line"),
                    "desc": T("sleep_ms(450) 让主控每秒只看 2 次地面，窄色带必然漏检。", "sleep_ms(450) checks the floor only ~2 times per second, missing narrow strips."),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.move_start(0, 750),
                B.repeat(
                    8,
                    B.if_(B.color_is("E", "RED"), B.move_stop()),
                    B.wait(0.45),
                ),
                B.move_stop(),
                B.show_image("SAD"),
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.move_start(0, 750),
                B.repeat(
                    8,
                    B.if_(B.color_is("E", "RED"), B.move_stop()),
                    B.wait(0.45),
                ),
                B.move_stop(),
                B.show_image("SAD"),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "把采样间隔缩短到 20 毫秒（每秒看 50 次！），并在压到黄线时主动从 260 减速到 150 慢行预备——绿线欢呼加速、黄线减速慢行、蓝线鸣笛、红线分毫不差稳稳刹停！",
                "Poll every 20 ms (50 Hz!) and use the yellow band as a real caution zone that slows speed from 260 down to 150 — catching the red line with pinpoint accuracy!",
                "確認間隔を20ms（毎秒50回！）に短縮し、黄ラインで速度を260→150へ減速。緑・黄・青すべてに反応して赤ライン上でピタッと止まります！",
            ),
            v2_code="""import runloop
import motor_pair
import color_sensor
import color
from hub import light_matrix, port, sound

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    motor_pair.move(motor_pair.PAIR_1, 0, velocity=260)
    last_c = -1

    # {{fast_traffic}}
    while True:
        c = color_sensor.color(port.E)
        if c == color.RED:
            break
        if c != last_c:
            last_c = c
            if c == color.GREEN:
                light_matrix.show_image(light_matrix.IMAGE_YES)
                await sound.beep(784, 90, 100)
            elif c == color.YELLOW:
                light_matrix.show_image(light_matrix.IMAGE_ARROW_N)
                motor_pair.move(motor_pair.PAIR_1, 0, velocity=150)
                await sound.beep(587, 90, 100)
            elif c == color.BLUE:
                light_matrix.show_image(light_matrix.IMAGE_HEART)
                await sound.beep(659, 90, 100)
        await runloop.sleep_ms(20)

    # {{red_stop}}
    motor_pair.stop(motor_pair.PAIR_1)
    light_matrix.show_image(light_matrix.IMAGE_NO)
    await sound.beep(262, 300, 100)

runloop.run(main())
""",
            v2_comments={
                "fast_traffic": T("每 20ms 高频检测 + last_c 边沿防抖：绿灯通行、黄灯降速、蓝灯鸣笛", "20 ms fast polling + last_c edge trigger: green go, yellow slow down, blue chime"),
                "red_stop": T("因为黄灯已提前降速到 150，遇到红线瞬间稳稳刹停！", "Pre-slowed on yellow, it stops dead on the red line!"),
            },
            v2_explanations=[
                {
                    "lines": "13-17",
                    "title": T("20ms 高频采样 + 状态变化触发", "50 Hz Polling + Edge Detection"),
                    "desc": T("用 last_c 记住上一次颜色，只有进入新色带瞬间才响一声，不会在同一色带上连响十几次。", "Tracking last_c beeps once on entering each color band instead of re-beeping every 20 ms."),
                },
                {
                    "lines": "22-25",
                    "title": T("黄灯预警提前降速", "Yellow Caution Slow-Down"),
                    "desc": T("就像真实交通规则一样，黄线提前把速度降到 150°/s，为前方窄红线精准停车做好准备。", "Slowing to 150°/s on yellow guarantees the sensor catches the narrow red stop strip."),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.move_start(0, 260),
                B.repeat_until(
                    B.color_is("E", "RED"),
                    B.if_(B.color_is("E", "GREEN"), B.show_image("YES"), B.beep(784, 90)),
                    B.if_(
                        B.color_is("E", "YELLOW"),
                        B.show_image("ARROW_N"),
                        B.move_start(0, 150),
                        B.beep(587, 90),
                    ),
                    B.if_(B.color_is("E", "BLUE"), B.show_image("HEART"), B.beep(659, 90)),
                ),
                B.move_stop(),
                B.show_image("NO"),
                B.beep(262, 300),
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.move_start(0, 260),
                B.repeat_until(
                    B.color_is("E", "RED"),
                    B.if_(B.color_is("E", "GREEN"), B.show_image("YES"), B.beep(784, 90)),
                    B.if_(
                        B.color_is("E", "YELLOW"),
                        B.show_image("ARROW_N"),
                        B.move_start(0, 150),
                        B.beep(587, 90),
                    ),
                    B.if_(B.color_is("E", "BLUE"), B.show_image("HEART"), B.beep(659, 90)),
                ),
                B.move_stop(),
                B.show_image("NO"),
                B.beep(262, 300),
            ),
            v2_scratch_vars=[],
        ),
        "challenges": [
            T("在蓝色色带（BLUE）处加入原地右转 90°（215°）动作，做成「蓝色路标自动拐弯」！", "Make the BLUE band a turn sign that pivots 90° right (215 motor degrees)!", "青ラインを踏んだら右へ90度曲がる道路標識プログラムに改造しよう！"),
            T("用变量 score 统计一共压过了几条彩色标线。", "Count how many color bands the car crosses in a score variable.", "通過した色ラインの本数を変数 score で数えよう。"),
        ],
    }
)


# ==================================================================================================
# Lesson 09: Line Follower Challenge
# ==================================================================================================
LINE_FOLLOWER = make_lesson(
    {
        "id": "line-follower",
        "level": "stage3",
        "stars": 4,
        "camera": {"pos": [-2.0, 14.5, 11.5], "target": [-8.5, 0.5, -3.5]},
        "title": T("智能巡线挑战 (Line Follower)", "Line Follower Challenge", "ライントレース挑戦"),
        "summary": T(
            "利用朝下颜色传感器的反射光百分比沿着黑色圆环巡线；对比 v1 非左即右剧烈扭头脱轨，升级为丝滑的 P 比例边缘追踪控制！",
            "Track the black ring using reflected light intensity (%); upgrade from v1's jerky bang-bang wobble that derails to smooth proportional (P) edge control!",
            "反射光（%）で黒いリングを走行。激しく首を振って脱線するv1のオンオフ制御を、滑らかな比例（P）制御へ進化させます。",
        ),
        "difficulty": T("小学 4-5 年级", "Grades 4-5", "小学4〜5年"),
        "duration": T("20 分钟", "20 min", "20分"),
        "concepts": ["sensor", "feedback", "variable", "threshold"],
        "ports": [
            *DRIVE_PORTS,
            {
                "port": "E",
                "device": T("颜色传感器 · 反射光模式 (45605)", "Color Sensor · Reflection Mode (45605)", "カラーセンサー・反射光モード (45605)"),
                "note": T("对准黑线右侧黑白交界边缘（目标反射率 50%）", "Aimed at the right black-white border of the track (target 50% reflection)", "黒ライン右端の境界（反射率50%）を狙って配置"),
            },
        ],
        "steps": [
            REUSE_BASE_STEP,
            {
                "step": 2,
                "title": T("车头中排安装 7 孔支架梁", "Pin Front 7L Mounting Beam", "前面中段に7Lブラケットを固定"),
                "instruction": T("沿用第 8 课结构：在主控正前方中排用 2 颗黑销固定 7 孔灰梁（32524）。", "Same mount as Lesson 8: pin a 7L grey beam (32524) across the Hub's front middle row.", "レッスン8と同じく、ハブ前面中段に黒ピン2本で7Lビーム（32524）を固定します。"),
                "substeps": [
                    T("如果刚做完第 8 课，你的颜色传感器小车已经拼好，可以直接跳到第 3 步检查！", "If you just finished Lesson 8, your car is already built — verify the front beam is snug!", "レッスン8から続けて行う場合はそのままでOKです！"),
                ],
                "tip": T("传感器装在轮轴前方 80 LDU（4 孔）处，相当于给小车留出「提前看路」的预瞄距离。", "Placing the sensor 4 studs ahead of the wheel axle gives the controller vital look-ahead distance.", "車軸より4ポッチ前にセンサーを置くことでカーブを先読みできます。"),
            },
            {
                "step": 3,
                "title": T("确认颜色传感器镜头朝下并接端口 E", "Verify Downward Color Sensor on Port E", "下向きカラーセンサーとポートE配線を確認"),
                "instruction": T("确认颜色传感器（45605）垂直朝下锁在车头正中，线缆接入端口 E。", "Confirm the color sensor (45605) points straight down at the front center and connects to Port E.", "カラーセンサー（45605）が車体前面中央で真下を向き、ポートEに繋がっているか確認します。"),
                "substeps": [
                    T("检查镜头正下方正好落在 3D 黑色圆环跑道的右侧边缘上。", "Notice the sensor starts right over the outer-right edge of the black ring track.", "センサーの真下が黒いリングコースの右端境界に乗っていることを確認します。"),
                    T("确认线缆紧贴主控左侧插入【端口 E】。", "Verify the cable is plugged into rear-left Port E.", "左後ろの【ポートE】への接続を確認します。"),
                ],
                "wiring": [
                    {
                        "port": "E",
                        "device": T("颜色传感器 (45605)", "Color Sensor (45605)", "カラーセンサー (45605)"),
                        "route": T("沿车身左侧接入主控左后端口 E。", "Route along the left side into Hub Port E.", "左側面からポートEへ接続。"),
                        "check": T("不碰左驱动轮。", "Clear of left drive wheel.", "左タイヤに干渉しないこと。"),
                    }
                ],
                "tip": T("巡线秘诀：机器人追的不是「整条黑线正中间」，而是黑白交界那条 50% 灰度的边缘线！", "Pro secret: a single-sensor line follower tracks the 50% grey *edge* between black and white, not the center of the line!", "1センサーライントレースの極意は、黒の真ん中ではなく「黒と白の境目（50%）」を追うことです！"),
            },
        ],
        "structure_lab": {
            "why": T(
                "为什么颜色传感器必须装在车轮轴「前方」？如果装在两轮正中间，车身转弯时镜头几乎不移动，反馈就迟钝；装在车头前方 4 孔处，车身微转 5° 镜头就会横移一截，立即感知灰度变化！",
                "Why mount the sensor AHEAD of the wheel axle? If placed between the wheels, turning barely shifts the lens; 4 studs ahead, a tiny heading change sweeps the lens across the line edge immediately!",
                "センサーを車軸より前に出す理由は、車体が少し向きを変えただけでレンズが左右に大きく動き、すぐに境界のズレを検出できるからです。",
            ),
            "troubleshoot": [
                T("小车往黑圈外侧拐跑了？检查左右轮差速加减号：追黑线右边缘时，看到偏白（>50）应该往左拐回黑线（左轮慢、右轮快）！", "Car steers away from the ring? Check your +/- signs: on the right edge, seeing white (>50) must steer LEFT (left slower, right faster)!", "コースの外へ逃げる場合、左右タイヤの＋／−を確認：白（>50）を見たら左へ戻るため右輪を速くします。"),
                T("小车在直线上也猛晃？比例系数 kp 设太大了，把 kp 从 5 降到 2.5~3 就会平顺。", "Oscillating wildly? Your proportional gain kp is too high — lower kp toward 2.5–3.", "激しく首を振る場合、比例ゲイン kp を2.5〜3に下げると落ち着きます。"),
            ],
            "mod_ideas": [
                T("缩短前伸臂实验：把传感器往后挪近 1 孔，观察过急弯时更容易还是更难。", "Look-Ahead Distance Test: move the sensor 1 stud closer to the axle and see how cornering changes.", "センサー距離実験：1ポッチ手前に寄せるとカーブの追従がどう変わるか試そう。"),
                T("双光传感器竞速车：如果有第二颗颜色传感器，一左一右夹住黑线就能高速飙车！", "Dual-Sensor Racer: two sensors straddling the black line allow much higher straightaway speeds.", "ツインセンサー構想：左右2個のセンサーで黒線を挟む高速マシンを設計してみよう。"),
            ],
        },
        "versions": _ver_pair(
            v1_problem=T(
                "运行仿真看 3D 轨迹：v1 采用「非黑即白」死板转向，还要睡 120ms——小车像喝醉了一样左右大角度猛摆，跑出几步就一头冲出黑环脱轨了！",
                "Watch the 3D trail in v1: harsh bang-bang turns combined with a 120 ms delay make the car zig-zag violently until it flings itself completely off the black ring!",
                "v1の軌跡を見よう：極端な左右交互ターンと120msの遅れで激しくジグザグ蛇行し、すぐ黒リングからコースアウトしてしまいます！",
            ),
            v1_why=T(
                "哪怕只偏离边缘 1%，v1 也用全幅差速（280 vs -80）猛甩车头，加上 120ms 延迟，每次纠偏都会严重矫枉过正。",
                "Even a 1% deviation triggers a full-lock turn (280 vs -80), and sleeping 120 ms guarantees massive over-correction on every swing.",
                "わずか1%のズレでも全力でハンドルを切り、120msの遅れで毎回逆側へ飛び出してしまいます。",
            ),
            v1_code="""import runloop
import motor_pair
import color_sensor
from hub import light_matrix, port

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    light_matrix.show_image(light_matrix.IMAGE_CONFUSED)

    # {{bang_bang}}
    for _ in range(35):
        ref = color_sensor.reflection(port.E)
        if ref < 50:
            motor_pair.move_tank(motor_pair.PAIR_1, 280, -80)
        else:
            motor_pair.move_tank(motor_pair.PAIR_1, -80, 280)
        await runloop.sleep_ms(120)

    motor_pair.stop(motor_pair.PAIR_1)

runloop.run(main())
""",
            v1_comments={
                "bang_bang": T("非左即右猛甩车头 + 120ms 慢反应：跑几步就直接脱轨！", "Harsh bang-bang turns + 120 ms lag — wobbles right off the track!"),
            },
            v1_explanations=[
                {
                    "lines": "13-17",
                    "title": T("二值开关控制（Bang-Bang）的剧烈震荡", "Bang-Bang Oscillation & Derailment"),
                    "desc": T("不管偏了 2% 还是 40% 都用同样大的力猛拐，必然在黑线两侧来回画锯齿直到冲出跑道。", "Applying the same aggressive turn for tiny and huge errors alike causes runaway zig-zags."),
                },
            ],
            v1_blocks=B.program(
                B.move_pair("C", "D"),
                B.show_image("SAD"),
                B.repeat(
                    35,
                    B.if_else(
                        B.compare(B.reflection("E"), "<", 50),
                        [B.move_tank(280, -80)],
                        [B.move_tank(-80, 280)],
                    ),
                    B.wait(0.12),
                ),
                B.move_stop(),
            ),
            v1_scratch=B.program(
                B.move_pair("C", "D"),
                B.show_image("SAD"),
                B.repeat(
                    35,
                    B.if_else(
                        B.compare(B.port("spike_reflection", "E"), "<", 50),
                        [B.move_tank(280, -80)],
                        [B.move_tank(-80, 280)],
                    ),
                    B.wait(0.12),
                ),
                B.move_stop(),
            ),
            v1_scratch_vars=[],
            v2_fix=T(
                "引入工程师王牌「P 比例控制」：`error = reflection - 50`，偏一点点就微调一点点，偏得多才大拐弯（`turn = kp * error`）！看 3D 蓝色轨迹稳稳贴着黑环丝滑巡航！（点「◀ 左键」可随时优雅停车）",
                "Use Proportional (P) control: `error = reflection - 50` and `turn = kp * error`! Small errors get gentle corrections, big errors get strong turns — watch the blue trail hug the ring smoothly!",
                "比例（P）制御を導入：`error = reflection - 50` に応じて修正量を滑らかに変化させます。3Dの青い軌跡がリングに沿って美しく一周します！",
            ),
            v2_code="""import runloop
import motor_pair
import color_sensor
from hub import button, light_matrix, port

async def main():
    motor_pair.pair(motor_pair.PAIR_1, port.C, port.D)
    # {{p_params}}
    target = 50
    kp = 2.6
    base_speed = 220
    light_matrix.show_image(light_matrix.IMAGE_ARROW_N)

    # {{p_loop}}
    while button.pressed(button.LEFT) == 0:
        error = color_sensor.reflection(port.E) - target
        turn = int(kp * error)
        motor_pair.move_tank(motor_pair.PAIR_1, base_speed - turn, base_speed + turn)
        await runloop.sleep_ms(15)

    motor_pair.stop(motor_pair.PAIR_1)
    light_matrix.show_image(light_matrix.IMAGE_HAPPY)

runloop.run(main())
""",
            v2_comments={
                "p_params": T("目标边缘反射率 50%，比例系数 kp=2.6，基础巡航速度 220", "Target edge 50%, proportional gain kp=2.6, base speed 220"),
                "p_loop": T("偏白(error>0)左轮减速向左贴回黑环；偏黑(error<0)向右微调！按左键停止", "White (error>0) steers left toward ring; black (error<0) steers right!"),
            },
            v2_explanations=[
                {
                    "lines": "16-18",
                    "title": T("比例反馈公式 turn = kp × error", "Proportional Feedback Formula"),
                    "desc": T("恰在边缘时 error=0，两轮同速 220 直走；偏白（如 80）时 turn=+78，左轮 142、右轮 298 柔和左拐回线！", "At the edge error=0 (straight at 220); drifting onto white (80) gives turn=+78 so left=142, right=298 curves smoothly left."),
                },
                {
                    "lines": "15",
                    "title": T("随时按左键安全结束", "Press Left Button to Stop Cleanly"),
                    "desc": T("巡线会一直绕圈运行，点击仿真栏的「◀ 左键」即可跳出循环停车。", "The follower laps continuously until you click 'Left' in the simulator bar."),
                },
            ],
            v2_blocks=B.program(
                B.move_pair("C", "D"),
                B.set_var("target", 50),
                B.set_var("kp", 3),
                B.set_var("base_speed", 220),
                B.show_image("ARROW_N"),
                B.repeat_until(
                    B.button_pressed("LEFT"),
                    B.set_var("error", B.arith(B.reflection("E"), "-", B.var("target"))),
                    B.set_var("turn", B.arith(B.var("kp"), "*", B.var("error"))),
                    B.move_tank(
                        B.arith(B.var("base_speed"), "-", B.var("turn")),
                        B.arith(B.var("base_speed"), "+", B.var("turn")),
                    ),
                ),
                B.move_stop(),
                B.show_image("HAPPY"),
                variables=["target", "kp", "base_speed", "error", "turn"],
            ),
            v2_scratch=B.program(
                B.move_pair("C", "D"),
                B.set_var_named("target", 50),
                B.set_var_named("kp", 3),
                B.set_var_named("base_speed", 220),
                B.show_image("ARROW_N"),
                B.repeat_until(
                    B.button_pressed("LEFT"),
                    B.set_var_named("error", B.arith(B.port("spike_reflection", "E"), "-", B.get_var("target"))),
                    B.set_var_named("turn", B.arith(B.get_var("kp"), "*", B.get_var("error"))),
                    B.move_tank(
                        B.arith(B.get_var("base_speed"), "-", B.get_var("turn")),
                        B.arith(B.get_var("base_speed"), "+", B.get_var("turn")),
                    ),
                ),
                B.move_stop(),
                B.show_image("HAPPY"),
                variables=["target", "kp", "base_speed", "error", "turn"],
            ),
            v2_scratch_vars=["target", "kp", "base_speed", "error", "turn"],
        ),
        "challenges": [
            T("尝试把 base_speed 提高到 300，看看 kp 调到多少能既快又不脱轨！", "Raise base_speed to 300 and tune kp so it laps faster without flying off the curve!", "base_speed を300に上げ、脱線しないベストな kp を探してみよう！"),
            T("如果想沿着黑线「内侧边缘」顺时针跑，左轮和右轮的 + turn / - turn 该怎么互换？", "To track the INSIDE edge clockwise, how would you swap +turn and -turn?", "内側エッジを時計回りに走るには＋と−をどう入れ替えればいいか考えよう。"),
        ],
    }
)

STAGE3_LESSONS = [OBSTACLE_AVOIDER, COLOR_TRAFFIC, LINE_FOLLOWER]
