# 井字棋机器人 · TicTacToe Robot

杭州电子科技大学（HDU）智能机器人课程项目。基于 **Dobot Magician** 机械臂的人机井字棋游戏。机械臂负责在纸上画棋盘和叉（X），用户用摄像头视野内的纸上手画圆（O）落子，程序通过差分+圆形度算法自动识别落子位置。

---

## 功能概览

| 阶段 | 操作者 | 动作 |
|------|--------|------|
| 启动 | 程序 | 连接 Dobot 机械臂 |
| 校准 | 用户 | 用方向键把 OpenCV 画面中的格线叠加层对准实物纸张 |
| 开局 | 机械臂 | 在纸上画 3×3 棋盘格线 |
| 人类落子 | 用户 | 在格内手画圆圈（O），按空格键触发识别 |
| 识别 | 程序 | 差分+圆形度检测，确认格子编号并高亮显示 |
| AI 落子 | 机械臂 | 随机选择空格，在纸上画叉（X） |
| 胜负判断 | 程序 | 三连即获胜，格满平局，结果显示在摄像头画面上 |

---

## 硬件需求

- Dobot Magician 机械臂（含笔夹工具，连接 COM6）
- USB 摄像头（手持正上方俯拍棋盘，CAMERA_INDEX = 1）
- A4 白纸（作为棋盘纸张）

---

## 快速开始

```bash
conda activate pytorch_py3.11
cd tictactoe
python main.py
```

**操作键位一览：**

| 按键 | 时机 | 动作 |
|------|------|------|
| ← → ↑ ↓ | 校准阶段 | 移动格线叠加层（每次 5px） |
| W / S | 校准阶段 | 放大 / 缩小格子尺寸 |
| R | 校准阶段 | 重置叠加层到默认位置 |
| Enter | 校准完成 / 换纸确认 | 确认并继续 |
| 空格 | 落子时 | 拍照触发圆形识别 |
| R | 游戏结束后 | 重开一局（需换纸） |
| Q | 任何时候 | 退出程序 |

---

## 文件结构

```
project1/
├── tictactoe/
│   ├── config.py              # 全局配置参数
│   ├── main.py                # 程序入口，游戏主循环
│   ├── game_logic.py          # 棋局逻辑与 AI
│   ├── dobot_controller.py    # 机械臂控制
│   ├── camera_display.py      # 摄像头显示与叠加层
│   ├── circle_detector.py     # 手绘圆识别
│   ├── board_calibrator.py    # 开局前格线校准
│   └── tests/                 # 单元测试（pytest）
│       ├── test_game_logic.py
│       ├── test_dobot_controller.py
│       ├── test_camera_display.py
│       ├── test_circle_detector.py
│       └── test_board_calibrator.py
├── demo-magician-python-64-master/  # Dobot Python SDK
├── find_camera.py             # 摄像头检测工具
├── verify_coords.py           # 机械臂坐标验证工具
└── README.md
```

---

## 各文件说明

### `config.py` — 全局配置

所有运行时参数的唯一入口，分为六组：

| 参数组 | 关键参数 | 说明 |
|--------|----------|------|
| 机械臂坐标 | `BOARD_CENTER_X/Y`, `BOARD_Z_DRAW/MOVE` | 棋盘在机械臂坐标系的位置，需用示教法实测 |
| 棋盘几何 | `CELL_SIZE`, `CROSS_SIZE` | 格子边长（40mm），X 笔画半长（14mm） |
| 运动参数 | `ARM_VELOCITY`, `ARM_ACCEL` | 速度与加速度比例（1-100） |
| 归位参数 | `ARM_PARK_X/Y/Z` | 画完后机械臂归位坐标，避免遮挡摄像头 |
| 摄像头 | `CAMERA_INDEX`, `OVERLAY_X/Y/CELL_PX` | 摄像头编号及格线叠加层初始位置 |
| 圆形检测 | `CIRCLE_MIN/MAX_AREA`, `CIRCLE_MIN_CIRCULARITY` 等 | 差分+圆形度算法阈值，可调节识别灵敏度 |
| 校准控制 | `CALIB_MOVE_STEP`, `CALIB_RESIZE_STEP` | 方向键每次移动/缩放的像素步长 |

**首次使用必须调整的参数：**
- `BOARD_CENTER_X/Y`、`BOARD_Z_DRAW`：用 Dobot Studio 示教笔尖到纸中心，读取坐标填入
- `CAMERA_INDEX`：运行 `find_camera.py` 查找正确的摄像头编号
- `DOBOT_PORT`：确认 Dobot 连接的 COM 口

---

### `main.py` — 程序入口

游戏主循环，负责协调所有模块。流程：

```
连接机械臂
  ↓
校准阶段（BoardCalibrator.run）→ Enter 确认
  ↓
每局循环：
  按 Enter → 机械臂画棋盘
  ↓
  人类回合：拍基准帧 → 画圆 → 按空格 → 检测 → 落子
  ↓
  检查胜负
  ↓
  机器人回合：随机选格 → 机械臂画X → 归位
  ↓
  检查胜负 → 循环
```

**关键函数：**
- `_run_game()` — 单局主循环
- `_wait_for_space_or_ctrl()` — 等待空格/Q/R，期间持续刷新摄像头画面
- `_wait_any_key()` — 短暂显示检测结果后自动继续（1.5s 或按任意键跳过）
- `_confirm_restart()` — 提示换纸，等待 Enter 确认

---

### `game_logic.py` — 棋局逻辑

纯逻辑模块，不依赖任何硬件。

- `place_move(cell, player)` — 在指定格子（1-9）落子，格子占用返回 False
- `check_winner()` — 检查 8 条连线，返回 HUMAN / ROBOT / 'draw' / None
- `ai_move()` — 随机从空格中选一个，返回格子编号
- `reset()` — 清空棋盘，准备新一局

格子编号规则（与键盘数字键对应）：
```
1 | 2 | 3
---------
4 | 5 | 6
---------
7 | 8 | 9
```

---

### `dobot_controller.py` — 机械臂控制

封装 Dobot Python SDK，提供高层绘图接口。

**关键实现细节：**
- `__init__`：加载 DLL 时必须先 `os.chdir` 到 SDK 目录（SDK 使用相对路径 `./DobotDll.dll`）
- `_queue_line(x1,y1,x2,y2)` — 排队四步动作：抬笔→移到起点→落笔→划线→抬笔
- `_run_queue(last_idx)` — 启动执行队列，轮询等待到 `last_idx` 完成
- `draw_grid()` — 画 4 条格线，完成后执行 `_queue_park()` 归位
- `draw_cross(cell)` — 画两条斜线组成 X，完成后归位
- `_queue_park()` — 追加归位动作，避免机械臂停在棋盘上方遮挡摄像头

**使用前必须关闭 Dobot Studio**（两者共用 COM6，同时运行会冲突）。

---

### `camera_display.py` — 摄像头显示

管理 OpenCV 窗口，将棋盘状态、格线叠加层、游戏提示实时渲染到摄像头画面上。

**主要方法：**

| 方法 | 说明 |
|------|------|
| `update()` | 读帧→渲染所有叠加层→显示→返回按键（1ms 轮询） |
| `capture_frame()` | 只读取原始帧，不显示（用于拍基准帧） |
| `set_board(board)` | 更新棋盘状态，在叠加层上绘制 O/X 棋子 |
| `set_status(text)` | 设置画面顶部的提示文字 |
| `set_highlight(cell)` | 在识别到的格子上叠加绿色半透明高亮（传 None 清除） |
| `draw_calib_hint(frame)` | 在校准模式下渲染操作说明文字 |
| `set_result(winner)` | 设置游戏结束覆盖层（You Win! / Robot Wins! / Draw!） |

叠加参数 `_overlay_x`、`_overlay_y`、`_overlay_cell_px` 为实例变量，由 `BoardCalibrator` 在运行时修改。

---

### `circle_detector.py` — 手绘圆识别

基于帧差分和圆形度过滤，识别用户新手画的圆圈并返回格子编号。

**算法流程：**

```
基准帧 & 当前帧
  → 转灰度 + 高斯模糊（降噪，kernel=5）
  → 绝对差分（提取新增笔迹）
  → 裁剪到棋盘区域（基于校准参数）
  → 二值化（阈值=30）
  → 形态学膨胀（连接断笔，迭代2次）
  → 查找外轮廓
  → 过滤：面积 ∈ [500, 8000] px²
          圆形度 = 4π·A/P² ≥ 0.45
  → 取最大符合轮廓，计算重心 (cx, cy)
  → 映射到格子编号：col=(cx-ox)//cell, row=(cy-oy)//cell
  → 返回 row*3+col+1（1-9），未检测到返回 None
```

**调参建议：**
- 识别不到圆 → 降低 `CIRCLE_DIFF_THRESHOLD`（至 20）或降低 `CIRCLE_MIN_CIRCULARITY`（至 0.35）
- 误识别噪点 → 提高 `CIRCLE_MIN_AREA` 或提高 `CIRCLE_DIFF_THRESHOLD`

---

### `board_calibrator.py` — 开局格线校准

游戏开始前的一次性校准步骤，让用户将 OpenCV 画面中的格线叠加层对准纸上的实物棋盘。

**键盘操作（校准模式）：**

| 按键 | 动作 |
|------|------|
| ← → ↑ ↓ | 移动整个格线叠加层（每次 5px） |
| W / S | 放大 / 缩小格子（每次 5px/格） |
| R | 重置为 config.py 默认值 |
| Enter | 确认校准，进入游戏 |
| Q | 退出程序 |

校准结果直接写入 `CameraDisplay._overlay_x/y/cell_px`，后续 `CircleDetector` 以此划定检测区域。

**注意：** 方向键在 Windows OpenCV 中的原始键码（不做 `& 0xFF` 掩码）为 2424832/2555904/2490368/2621440。如果方向键不响应，在终端运行：
```python
import cv2; cv2.namedWindow('t'); print(cv2.waitKey(5000))
```
按方向键查看实际键码，修改 `board_calibrator.py` 中的 `_KEY_LEFT/RIGHT/UP/DOWN` 常量。

---

### `tests/` — 单元测试

使用 **pytest + unittest.mock** 编写，所有测试无需连接任何硬件。

```bash
cd tictactoe
pytest tests/ -v       # 运行全部 47 个测试
```

| 测试文件 | 测试内容 |
|----------|----------|
| `test_game_logic.py` | 落子、胜负判断、AI、重置，18 个用例 |
| `test_dobot_controller.py` | 格子坐标映射、连接失败异常，6 个用例 |
| `test_camera_display.py` | 实例叠加参数、capture_frame、高亮，6 个用例 |
| `test_circle_detector.py` | 合成帧检测格1/5/9、空帧、噪点、矩形过滤，7 个用例 |
| `test_board_calibrator.py` | 方向键/W/S/R/Enter/Q 键位逻辑，10 个用例 |

---

## 常见问题排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `FileNotFoundError: DobotDll.dll` | SDK 需要从其所在目录加载 DLL | 已在代码中通过 `os.chdir` 修复，无需操作 |
| 摄像头画面全黑 | `CAMERA_INDEX` 错误 | 运行 `find_camera.py` 找到正确编号，修改 `config.py` |
| 机械臂连接失败 | Dobot Studio 占用 COM6 | 关闭 Dobot Studio 后重试 |
| 方向键不响应 | OpenCV 版本键码差异 | 运行键码检测脚本，修改 `_KEY_*` 常量 |
| 圆识别总返回 None | 光线不足 / 阈值过高 | 降低 `CIRCLE_DIFF_THRESHOLD`（20）或 `CIRCLE_MIN_CIRCULARITY`（0.35） |
| 游戏结束后 R/Q 无反应 | 需要点击 OpenCV 窗口使其获得焦点 | 点击摄像头画面窗口后再按键 |
| 归位后仍挡摄像头 | 归位坐标不合适 | 用 Dobot Studio 示教合适位置，将坐标填入 `config.py` 的 `ARM_PARK_*` |
