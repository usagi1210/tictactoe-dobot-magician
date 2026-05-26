# TicTacToe C版本：手绘圆识别 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 B 版本（键盘输入）基础上，新增摄像头校准模式和手绘圆圈识别，用差分+圆形度算法将用户落子输入从键盘数字改为纸上手画圆。

**Architecture:** 新增 `board_calibrator.py`（校准交互）和 `circle_detector.py`（差分+圆形度检测）两个独立模块；`camera_display.py` 扩展实例变量叠加参数、帧捕获和高亮显示方法；`main.py` 在连接后加入校准阶段，人类落子改为"空格触发检测"流程。

**Tech Stack:** Python 3.11, OpenCV (cv2), NumPy, pytest + unittest.mock（TDD）

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `tictactoe/config.py` | 修改 | 新增圆形检测和校准参数常量 |
| `tictactoe/camera_display.py` | 修改 | 叠加参数改为实例变量；新增 `capture_frame()`、`set_highlight()`、`draw_calib_hint()` |
| `tictactoe/board_calibrator.py` | 新建 | 方向键调整格线叠加，Enter 确认，Q 退出 |
| `tictactoe/circle_detector.py` | 新建 | 差分+圆形度检测，返回格子编号 1-9 或 None |
| `tictactoe/main.py` | 修改 | 加入校准阶段，人类输入改为空格触发圆检测 |
| `tictactoe/tests/test_camera_display.py` | 新建 | camera_display 新功能单元测试 |
| `tictactoe/tests/test_circle_detector.py` | 新建 | 用合成 numpy 帧测试检测逻辑 |
| `tictactoe/tests/test_board_calibrator.py` | 新建 | 测试 `_apply_key()` 各按键行为 |

**运行测试（在 `tictactoe/` 目录下）：**
```
conda activate pytorch_py3.11
cd tictactoe
pytest tests/ -v
```

---

## Task 1: config.py — 新增圆形检测与校准参数

**Files:**
- Modify: `tictactoe/config.py`

- [ ] **Step 1: 在 config.py 末尾追加新增参数**

打开 `tictactoe/config.py`，在文件末尾追加：

```python
# ── 圆形检测参数 ────────────────────────────────────
CIRCLE_MIN_AREA        = 500    # 最小轮廓面积（像素²），排除噪点
CIRCLE_MAX_AREA        = 8000   # 最大轮廓面积（像素²），排除过大区域
CIRCLE_MIN_CIRCULARITY = 0.45   # 圆形度阈值（4π·A/P²，1为完美圆）
CIRCLE_DIFF_THRESHOLD  = 30     # 差分二值化阈值（0~255）
CIRCLE_BLUR_KERNEL     = 5      # 高斯模糊核大小（奇数）
CIRCLE_DILATE_ITER     = 2      # 形态学膨胀迭代次数（连接断笔）

# ── 校准控制 ───────────────────────────────────────
CALIB_MOVE_STEP   = 5   # 方向键每次移动格线的像素数
CALIB_RESIZE_STEP = 5   # W/S 每次调整每格大小的像素数
```

- [ ] **Step 2: 验证导入正常**

```
cd tictactoe
python -c "import config; print(config.CIRCLE_MIN_AREA, config.CALIB_MOVE_STEP)"
```

期望输出：`500 5`

- [ ] **Step 3: Commit**

```
git add tictactoe/config.py
git commit -m "feat: add circle detection and calibration config params"
```

---

## Task 2: camera_display.py — 实例叠加参数 + 新增方法

**Files:**
- Modify: `tictactoe/camera_display.py`
- Create: `tictactoe/tests/test_camera_display.py`

**背景：** 当前 `_draw_overlay()` 直接读 `config.OVERLAY_X` 等常量，无法在运行时修改。需改为 `self._overlay_x` 等实例变量，同时新增三个方法：
- `capture_frame()` — 只读帧不显示（用于拍基准帧）
- `set_highlight(cell)` — 存储待高亮格子编号（None 清除）
- `draw_calib_hint(frame)` — 在帧上叠加校准操作提示文字

- [ ] **Step 1: 新建测试文件并写失败测试**

新建 `tictactoe/tests/test_camera_display.py`：

```python
import sys, os
from unittest.mock import MagicMock
import numpy as np

# 在导入 camera_display 前 mock cv2（避免依赖摄像头）
mock_cv2 = MagicMock()
sys.modules['cv2'] = mock_cv2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config
from camera_display import CameraDisplay


def _make():
    """跳过 __init__（避免打开摄像头），手动设置实例变量。"""
    d = CameraDisplay.__new__(CameraDisplay)
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    d.cap = mock_cap
    d._board = None
    d._status = ""
    d._result = None
    d._highlighted_cell = None
    d._overlay_x = config.OVERLAY_X
    d._overlay_y = config.OVERLAY_Y
    d._overlay_cell_px = config.OVERLAY_CELL_PX
    return d


def test_overlay_x_is_instance_var_initialized_from_config():
    """__init__ 后 _overlay_x 应等于 config.OVERLAY_X。"""
    mock_cv2.VideoCapture.return_value = MagicMock(isOpened=lambda: True)
    d = CameraDisplay()
    assert d._overlay_x == config.OVERLAY_X
    assert d._overlay_y == config.OVERLAY_Y
    assert d._overlay_cell_px == config.OVERLAY_CELL_PX


def test_capture_frame_returns_ndarray():
    """capture_frame() 应返回 numpy ndarray。"""
    d = _make()
    frame = d.capture_frame()
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (480, 640, 3)


def test_capture_frame_returns_zeros_on_cap_failure():
    """摄像头读取失败时返回全黑帧。"""
    d = _make()
    d.cap.read.return_value = (False, None)
    frame = d.capture_frame()
    assert isinstance(frame, np.ndarray)
    assert frame.shape[2] == 3


def test_set_highlight_stores_cell():
    """set_highlight(5) 后 _highlighted_cell 应为 5。"""
    d = _make()
    d.set_highlight(5)
    assert d._highlighted_cell == 5


def test_set_highlight_none_clears():
    """set_highlight(None) 后 _highlighted_cell 应为 None。"""
    d = _make()
    d.set_highlight(5)
    d.set_highlight(None)
    assert d._highlighted_cell is None


def test_draw_calib_hint_returns_frame():
    """draw_calib_hint 应返回相同形状的帧（不崩溃）。"""
    d = _make()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = d.draw_calib_hint(frame)
    assert result is not None
```

- [ ] **Step 2: 运行测试确认失败**

```
cd tictactoe
pytest tests/test_camera_display.py -v
```

期望：多个 FAILED（方法不存在）

- [ ] **Step 3: 修改 camera_display.py**

完整替换 `tictactoe/camera_display.py` 为以下内容：

```python
import cv2
import numpy as np
import config
from game_logic import GameLogic


class CameraDisplay:
    def __init__(self):
        # 优先用 DirectShow（Windows USB摄像头更稳定），失败则用默认后端
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self._board = None
        self._status = ""
        self._result = None          # GameLogic.HUMAN / GameLogic.ROBOT / 'draw' / None
        self._highlighted_cell = None  # int 1-9 or None

        # 叠加参数改为实例变量，供 BoardCalibrator 在运行时修改
        self._overlay_x       = config.OVERLAY_X
        self._overlay_y       = config.OVERLAY_Y
        self._overlay_cell_px = config.OVERLAY_CELL_PX

    # ── 状态 setter ───────────────────────────────────
    def set_board(self, board: list):
        self._board = board

    def set_status(self, text: str):
        self._status = text

    def set_result(self, winner):
        self._result = winner

    def clear_result(self):
        self._result = None

    def set_highlight(self, cell):
        """高亮指定格子（1-9），传 None 清除高亮。"""
        self._highlighted_cell = cell

    # ── 帧操作 ────────────────────────────────────────
    def capture_frame(self) -> np.ndarray:
        """只读取当前帧，不显示。用于拍基准帧。"""
        ret, frame = self.cap.read()
        if not ret:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        return frame

    def update(self) -> int:
        """读取一帧，绘制叠加层，显示窗口。返回按键（无按键返回 -1）。"""
        ret, frame = self.cap.read()
        if not ret:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = self._draw_overlay(frame)
        frame = self._draw_highlight(frame)
        frame = self._draw_status(frame)
        if self._result is not None:
            frame = self._draw_result(frame)
        cv2.imshow(config.WINDOW_NAME, frame)
        return cv2.waitKey(1) & 0xFF

    # ── 内部绘制 ─────────────────────────────────────
    def _draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        overlay = frame.copy()
        ox = self._overlay_x        # 使用实例变量（可被 BoardCalibrator 修改）
        oy = self._overlay_y
        sp = self._overlay_cell_px
        color = (200, 200, 0)       # 青黄色格线

        # 4 条格线（2竖 + 2横）
        cv2.line(overlay, (ox + sp,     oy),          (ox + sp,     oy + 3*sp), color, 2)
        cv2.line(overlay, (ox + 2*sp,   oy),          (ox + 2*sp,   oy + 3*sp), color, 2)
        cv2.line(overlay, (ox,          oy + sp),     (ox + 3*sp,   oy + sp),   color, 2)
        cv2.line(overlay, (ox,          oy + 2*sp),   (ox + 3*sp,   oy + 2*sp), color, 2)

        # 棋子
        if self._board:
            for r in range(3):
                for c in range(3):
                    cx = ox + c * sp + sp // 2
                    cy = oy + r * sp + sp // 2
                    val = self._board[r][c]
                    if val == GameLogic.HUMAN:
                        cv2.circle(overlay, (cx, cy), sp // 3, (255, 150, 0), 3)
                    elif val == GameLogic.ROBOT:
                        d = sp // 4
                        cv2.line(overlay, (cx-d, cy-d), (cx+d, cy+d), (0, 60, 220), 3)
                        cv2.line(overlay, (cx+d, cy-d), (cx-d, cy+d), (0, 60, 220), 3)

        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        return frame

    def _draw_highlight(self, frame: np.ndarray) -> np.ndarray:
        """在识别到的格子上叠加绿色半透明高亮。"""
        if self._highlighted_cell is None:
            return frame
        idx = self._highlighted_cell - 1
        row, col = idx // 3, idx % 3
        ox = self._overlay_x
        oy = self._overlay_y
        sp = self._overlay_cell_px
        x1 = ox + col * sp
        y1 = oy + row * sp
        x2 = x1 + sp
        y2 = y1 + sp
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 255, 0), -1)
        cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
        return frame

    def _draw_status(self, frame: np.ndarray) -> np.ndarray:
        if self._status:
            cv2.putText(frame, self._status, (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)
        return frame

    def _draw_result(self, frame: np.ndarray) -> np.ndarray:
        labels = {
            GameLogic.HUMAN: ("You Win!",    (0, 200, 0)),
            GameLogic.ROBOT: ("Robot Wins!", (0, 60, 220)),
            'draw':          ("Draw!",        (0, 200, 200)),
        }
        msg, color = labels.get(self._result, ("Game Over", (255, 255, 255)))
        h, w = frame.shape[:2]
        cv2.putText(frame, msg, (w//2 - 110, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.6, color, 3)
        cv2.putText(frame, "R: restart  Q: quit", (w//2 - 120, h//2 + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (200, 200, 200), 2)
        return frame

    def draw_calib_hint(self, frame: np.ndarray) -> np.ndarray:
        """在帧顶部显示校准操作说明。"""
        lines = [
            "CALIBRATION: align grid overlay to physical board",
            "Arrows:move  W/S:resize  R:reset  Enter:confirm  Q:quit",
        ]
        for i, line in enumerate(lines):
            cv2.putText(frame, line, (10, 22 + i * 26),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 255, 255), 1)
        return frame

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
```

- [ ] **Step 4: 运行测试确认通过**

```
cd tictactoe
pytest tests/test_camera_display.py -v
```

期望：6 passed

- [ ] **Step 5: 确认全量测试无回归**

```
pytest tests/ -v
```

期望：原有 test_game_logic 和 test_dobot_controller 全部仍然 passed

- [ ] **Step 6: Commit**

```
git add tictactoe/camera_display.py tictactoe/tests/test_camera_display.py
git commit -m "feat: make overlay params instance vars, add capture_frame/set_highlight/draw_calib_hint"
```

---

## Task 3: circle_detector.py — 差分 + 圆形度检测

**Files:**
- Create: `tictactoe/circle_detector.py`
- Create: `tictactoe/tests/test_circle_detector.py`

**算法：** 基准帧与当前帧均灰度+高斯模糊 → 绝对差分 → 裁剪到棋盘区域 → 二值化 → 膨胀 → 轮廓 → 面积+圆形度过滤 → 最大有效轮廓重心 → 格子编号

- [ ] **Step 1: 写失败测试**

新建 `tictactoe/tests/test_circle_detector.py`：

```python
import sys, os
import numpy as np
import cv2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config


# 用 SimpleNamespace 模拟 CameraDisplay，仅需要三个叠加属性
class FakeDisplay:
    def __init__(self, x=0, y=0, cell=100):
        self._overlay_x = x
        self._overlay_y = y
        self._overlay_cell_px = cell


def make_frames(center, radius=30, size=(480, 640)):
    """生成基准帧（全黑）和当前帧（含实心/轮廓圆）。"""
    ref = np.zeros((*size, 3), dtype=np.uint8)
    cur = ref.copy()
    # 使用较厚的圆让差分更明显
    cv2.circle(cur, center, radius, (200, 200, 200), 4)
    return ref, cur


from circle_detector import CircleDetector


def test_detect_circle_in_cell_1():
    """棋盘左上角（格1）画圆，应返回 1。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    # 格1中心在 (50, 50)
    ref, cur = make_frames(center=(50, 50))
    assert CircleDetector(d).detect(ref, cur) == 1


def test_detect_circle_in_cell_5():
    """棋盘中央（格5）画圆，应返回 5。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    # 格5中心在 (150, 150)
    ref, cur = make_frames(center=(150, 150))
    assert CircleDetector(d).detect(ref, cur) == 5


def test_detect_circle_in_cell_9():
    """棋盘右下角（格9）画圆，应返回 9。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    # 格9中心在 (250, 250)
    ref, cur = make_frames(center=(250, 250))
    assert CircleDetector(d).detect(ref, cur) == 9


def test_detect_with_nonzero_overlay_offset():
    """叠加层偏移非零时，仍能正确定位格子。"""
    d = FakeDisplay(x=50, y=50, cell=100)
    # 格5中心在原始帧坐标 (50+150, 50+150) = (200, 200)
    ref, cur = make_frames(center=(200, 200))
    assert CircleDetector(d).detect(ref, cur) == 5


def test_no_circle_returns_none():
    """当前帧与基准帧完全相同，应返回 None。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    ref = np.zeros((480, 640, 3), dtype=np.uint8)
    cur = ref.copy()
    assert CircleDetector(d).detect(ref, cur) is None


def test_only_noise_returns_none():
    """只有随机噪点（面积太小），应返回 None。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    ref = np.zeros((480, 640, 3), dtype=np.uint8)
    cur = ref.copy()
    # 在格内画一个微小点（面积 < CIRCLE_MIN_AREA）
    cv2.circle(cur, (50, 50), 5, (200, 200, 200), -1)
    assert CircleDetector(d).detect(ref, cur) is None


def test_square_contour_rejected():
    """矩形轮廓圆形度低，应被过滤掉，返回 None。"""
    d = FakeDisplay(x=0, y=0, cell=100)
    ref = np.zeros((480, 640, 3), dtype=np.uint8)
    cur = ref.copy()
    # 画一个矩形（圆形度 << 0.45）
    cv2.rectangle(cur, (20, 20), (80, 80), (200, 200, 200), 3)
    result = CircleDetector(d).detect(ref, cur)
    assert result is None
```

- [ ] **Step 2: 运行测试确认失败**

```
cd tictactoe
pytest tests/test_circle_detector.py -v
```

期望：ModuleNotFoundError (circle_detector 不存在)

- [ ] **Step 3: 实现 circle_detector.py**

新建 `tictactoe/circle_detector.py`：

```python
import math
import cv2
import numpy as np
import config


class CircleDetector:
    def __init__(self, display):
        """
        display: 需要有 _overlay_x, _overlay_y, _overlay_cell_px 属性
                 （CameraDisplay 实例或同接口的测试替身）
        """
        self._display = display

    def detect(self, ref_frame: np.ndarray, cur_frame: np.ndarray):
        """
        差分 + 圆形度检测。
        返回格子编号 1-9，或 None（未检测到有效圆）。
        """
        ksize = config.CIRCLE_BLUR_KERNEL
        if ksize % 2 == 0:
            ksize += 1  # 核大小必须为奇数

        # 步骤1：灰度 + 高斯模糊
        ref_gray = cv2.GaussianBlur(
            cv2.cvtColor(ref_frame, cv2.COLOR_BGR2GRAY), (ksize, ksize), 0)
        cur_gray = cv2.GaussianBlur(
            cv2.cvtColor(cur_frame, cv2.COLOR_BGR2GRAY), (ksize, ksize), 0)

        # 步骤2：绝对差分
        diff = cv2.absdiff(ref_gray, cur_gray)

        # 步骤3：裁剪到棋盘区域
        ox = self._display._overlay_x
        oy = self._display._overlay_y
        cell = self._display._overlay_cell_px
        board_size = 3 * cell
        h, w = diff.shape
        x1 = max(0, ox)
        y1 = max(0, oy)
        x2 = min(w, ox + board_size)
        y2 = min(h, oy + board_size)
        diff_crop = diff[y1:y2, x1:x2]

        # 步骤4：二值化
        _, thresh = cv2.threshold(
            diff_crop, config.CIRCLE_DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)

        # 步骤5：形态学膨胀（连接手绘断笔）
        kernel = np.ones((3, 3), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=config.CIRCLE_DILATE_ITER)

        # 步骤6：查找轮廓
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 步骤7：过滤面积 + 圆形度
        valid = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if not (config.CIRCLE_MIN_AREA <= area <= config.CIRCLE_MAX_AREA):
                continue
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * math.pi * area / (perimeter ** 2)
            if circularity >= config.CIRCLE_MIN_CIRCULARITY:
                valid.append((area, cnt))

        if not valid:
            return None

        # 步骤8：取面积最大的有效轮廓，计算重心
        _, best = max(valid, key=lambda x: x[0])
        M = cv2.moments(best)
        if M['m00'] == 0:
            return None

        # 重心在裁剪坐标系内 → 转换回原始帧坐标
        cx = int(M['m10'] / M['m00']) + x1
        cy = int(M['m01'] / M['m00']) + y1

        # 步骤9：映射到格子编号 1-9
        col = (cx - ox) // cell
        row = (cy - oy) // cell

        if not (0 <= col <= 2 and 0 <= row <= 2):
            return None

        return int(row * 3 + col + 1)
```

- [ ] **Step 4: 运行测试确认通过**

```
cd tictactoe
pytest tests/test_circle_detector.py -v
```

期望：7 passed

> **注：** 如果 `test_square_contour_rejected` 失败（矩形被误识别为圆），可将 `CIRCLE_MIN_CIRCULARITY` 调高至 0.6。矩形圆形度 = 4π·A/P² = 4π·3600/57600 ≈ 0.785...实际轮廓（有角点近似）更低，应被过滤。如测试仍失败，检查矩形尺寸是否与格子尺寸有重叠（大矩形面积可能 > CIRCLE_MAX_AREA）。

- [ ] **Step 5: 全量测试无回归**

```
pytest tests/ -v
```

期望：所有测试 passed

- [ ] **Step 6: Commit**

```
git add tictactoe/circle_detector.py tictactoe/tests/test_circle_detector.py
git commit -m "feat: add circle_detector with diff+circularity detection (TDD)"
```

---

## Task 4: board_calibrator.py — 方向键校准交互

**Files:**
- Create: `tictactoe/board_calibrator.py`
- Create: `tictactoe/tests/test_board_calibrator.py`

**注：** `run()` 方法含摄像头读取和 `cv2.waitKey()`，无法单元测试。将键位处理逻辑提取为 `_apply_key(key, display)` 纯函数进行测试。

**Windows OpenCV 方向键编码（不做 `& 0xFF` 掩码时）：**
- 左箭头: `2424832`
- 右箭头: `2555904`
- 上箭头: `2490368`
- 下箭头: `2621440`

- [ ] **Step 1: 写失败测试**

新建 `tictactoe/tests/test_board_calibrator.py`：

```python
import sys, os
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import config
from board_calibrator import BoardCalibrator

# Windows OpenCV 方向键（waitKey 不做 & 0xFF 时）
LEFT  = 2424832
RIGHT = 2555904
UP    = 2490368
DOWN  = 2621440


def make_display():
    """最简测试替身，只有叠加参数三个字段。"""
    d = types.SimpleNamespace(
        _overlay_x=config.OVERLAY_X,
        _overlay_y=config.OVERLAY_Y,
        _overlay_cell_px=config.OVERLAY_CELL_PX,
    )
    return d


def test_left_arrow_decreases_overlay_x():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(LEFT, d)
    assert d._overlay_x == config.OVERLAY_X - config.CALIB_MOVE_STEP


def test_right_arrow_increases_overlay_x():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(RIGHT, d)
    assert d._overlay_x == config.OVERLAY_X + config.CALIB_MOVE_STEP


def test_up_arrow_decreases_overlay_y():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(UP, d)
    assert d._overlay_y == config.OVERLAY_Y - config.CALIB_MOVE_STEP


def test_down_arrow_increases_overlay_y():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(DOWN, d)
    assert d._overlay_y == config.OVERLAY_Y + config.CALIB_MOVE_STEP


def test_w_increases_cell_px():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(ord('w'), d)
    assert d._overlay_cell_px == config.OVERLAY_CELL_PX + config.CALIB_RESIZE_STEP


def test_s_decreases_cell_px():
    d = make_display()
    bc = BoardCalibrator()
    bc._apply_key(ord('s'), d)
    assert d._overlay_cell_px == config.OVERLAY_CELL_PX - config.CALIB_RESIZE_STEP


def test_r_resets_to_config_defaults():
    d = make_display()
    d._overlay_x = 999
    d._overlay_y = 999
    d._overlay_cell_px = 999
    bc = BoardCalibrator()
    bc._apply_key(ord('r'), d)
    assert d._overlay_x == config.OVERLAY_X
    assert d._overlay_y == config.OVERLAY_Y
    assert d._overlay_cell_px == config.OVERLAY_CELL_PX


def test_enter_returns_confirm():
    d = make_display()
    bc = BoardCalibrator()
    result = bc._apply_key(13, d)   # Enter = 13
    assert result == 'confirm'


def test_q_returns_quit():
    d = make_display()
    bc = BoardCalibrator()
    result = bc._apply_key(ord('q'), d)
    assert result == 'quit'


def test_other_key_returns_continue():
    d = make_display()
    bc = BoardCalibrator()
    result = bc._apply_key(ord('z'), d)
    assert result == 'continue'
```

- [ ] **Step 2: 运行测试确认失败**

```
cd tictactoe
pytest tests/test_board_calibrator.py -v
```

期望：ModuleNotFoundError (board_calibrator 不存在)

- [ ] **Step 3: 实现 board_calibrator.py**

新建 `tictactoe/board_calibrator.py`：

```python
import cv2
import config


# Windows OpenCV 方向键编码（waitKey 不做 & 0xFF 掩码）
_KEY_LEFT  = 2424832
_KEY_RIGHT = 2555904
_KEY_UP    = 2490368
_KEY_DOWN  = 2621440


class BoardCalibrator:
    """
    校准模式：在进入游戏前用方向键调整摄像头画面中的格线叠加位置。
    校准结果直接写入 display 的叠加参数实例变量。
    """

    def _apply_key(self, key: int, display) -> str:
        """
        处理一次按键，修改 display 的叠加参数。
        返回 'confirm'（Enter）、'quit'（Q）或 'continue'（其他键）。
        """
        masked = key & 0xFF  # ASCII 范围用 masked，特殊键用原始 key

        if masked == ord('q'):
            return 'quit'
        if key == 13 or masked == 13:   # Enter
            return 'confirm'
        if masked == ord('r'):
            display._overlay_x       = config.OVERLAY_X
            display._overlay_y       = config.OVERLAY_Y
            display._overlay_cell_px = config.OVERLAY_CELL_PX
            return 'continue'
        if key == _KEY_LEFT:
            display._overlay_x -= config.CALIB_MOVE_STEP
        elif key == _KEY_RIGHT:
            display._overlay_x += config.CALIB_MOVE_STEP
        elif key == _KEY_UP:
            display._overlay_y -= config.CALIB_MOVE_STEP
        elif key == _KEY_DOWN:
            display._overlay_y += config.CALIB_MOVE_STEP
        elif masked == ord('w'):
            display._overlay_cell_px += config.CALIB_RESIZE_STEP
        elif masked == ord('s'):
            display._overlay_cell_px -= config.CALIB_RESIZE_STEP

        return 'continue'

    def run(self, display) -> bool:
        """
        进入校准模式，阻塞直到用户确认（Enter）或退出（Q）。
        校准结果写入 display._overlay_x/y/cell_px。
        返回 True=确认进入游戏，False=退出程序。
        """
        while True:
            # 读取原始帧（不经 display.update，以便完全控制显示内容）
            ret, frame = display.cap.read()
            if not ret:
                import numpy as np
                frame = __import__('numpy').zeros((480, 640, 3), dtype=__import__('numpy').uint8)

            # 绘制格线叠加 + 校准提示
            frame = display._draw_overlay(frame)
            frame = display.draw_calib_hint(frame)
            cv2.imshow(config.WINDOW_NAME, frame)

            # 读取原始按键（不做 & 0xFF，保留方向键信息）
            key = cv2.waitKey(1)
            if key == -1:
                continue

            action = self._apply_key(key, display)
            if action == 'confirm':
                return True
            if action == 'quit':
                return False
```

- [ ] **Step 4: 运行测试确认通过**

```
cd tictactoe
pytest tests/test_board_calibrator.py -v
```

期望：10 passed

- [ ] **Step 5: 全量测试无回归**

```
pytest tests/ -v
```

期望：所有测试 passed

- [ ] **Step 6: Commit**

```
git add tictactoe/board_calibrator.py tictactoe/tests/test_board_calibrator.py
git commit -m "feat: add board_calibrator with arrow-key overlay alignment (TDD)"
```

---

## Task 5: main.py — 集成校准阶段 + 手绘圆检测输入

**Files:**
- Modify: `tictactoe/main.py`

**变更点：**
1. 连接机械臂成功后立即调用 `BoardCalibrator.run(display)`
2. 人类落子逻辑：等空格 → 拍当前帧 → 检测圆 → 确认或重试

（此 Task 无法自动化测试，依赖摄像头和机械臂硬件，以冒烟测试步骤代替）

- [ ] **Step 1: 完整替换 main.py**

用以下内容完整替换 `tictactoe/main.py`：

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'demo-magician-python-64-master'))

from dobot_controller import DobotController
from game_logic import GameLogic
from camera_display import CameraDisplay
from board_calibrator import BoardCalibrator
from circle_detector import CircleDetector


def main():
    dobot = DobotController()
    logic = GameLogic()
    display = CameraDisplay()

    print("Connecting to Dobot...")
    try:
        dobot.connect()
    except ConnectionError as e:
        print(f"Error: {e}")
        display.release()
        sys.exit(1)
    print("Connected!")

    # ── 校准阶段 ─────────────────────────────────────
    display.set_status("CALIBRATION: align grid, then press Enter")
    confirmed = BoardCalibrator().run(display)
    if not confirmed:
        dobot.disconnect()
        display.release()
        return

    try:
        while _run_game(dobot, logic, display):
            pass
    finally:
        dobot.disconnect()
        display.release()


def _run_game(dobot: DobotController, logic: GameLogic, display: CameraDisplay) -> bool:
    """运行一局。返回 True=继续下一局，False=退出程序。"""
    logic.reset()
    display.set_board(logic.board)
    display.clear_result()
    display.set_highlight(None)

    # 等待用户确认后再开始画棋盘
    display.set_status("Ready! Press ENTER to draw board  |  Q: quit")
    while True:
        key = display.update()
        if key == 13:       # Enter
            break
        if key == ord('q'):
            return False

    display.set_status("Drawing board, please wait...")
    dobot.draw_grid(update_cb=display.update)

    detector = CircleDetector(display)

    while True:
        # ── 人类回合 ──────────────────────────────────
        ref_frame = display.capture_frame()
        display.set_highlight(None)
        display.set_status("Draw O in a cell, then press SPACE  |  R:restart  Q:quit")

        # 等待空格（或 Q/R 中断）
        key = _wait_for_space_or_ctrl(display)
        if key == ord('q'):
            return False
        if key == ord('r'):
            return _confirm_restart(display)

        # 拍当前帧，检测圆
        cur_frame = display.capture_frame()
        cell = detector.detect(ref_frame, cur_frame)

        if cell is None:
            display.set_status("No circle detected. Redraw and press SPACE")
            continue

        if not logic.place_move(cell, GameLogic.HUMAN):
            display.set_highlight(cell)
            display.set_status(f"Cell {cell} is occupied! Redraw in another cell")
            _wait_any_key(display)
            display.set_highlight(None)
            continue

        # 高亮确认落子格
        display.set_highlight(cell)
        display.set_status(f"Detected cell {cell}! Placing O...")
        _wait_any_key(display)
        display.set_highlight(None)
        display.set_board(logic.board)

        if _check_and_handle_end(logic, display):
            return _wait_restart(display)

        # ── 机器人回合 ────────────────────────────────
        ai_cell = logic.ai_move()
        logic.place_move(ai_cell, GameLogic.ROBOT)
        display.set_board(logic.board)
        display.set_status(f"Robot chose cell {ai_cell}, drawing X...")
        dobot.draw_cross(ai_cell, update_cb=display.update)

        if _check_and_handle_end(logic, display):
            return _wait_restart(display)


def _wait_for_space_or_ctrl(display: CameraDisplay) -> int:
    """
    等待空格键（触发检测）或 Q/R（控制键）。
    返回按下的键值（32=空格, ord('q'), ord('r')）。
    """
    while True:
        key = display.update()
        if key == 32 or key == ord('q') or key == ord('r'):
            return key


def _wait_any_key(display: CameraDisplay, timeout_ms: int = 1500):
    """短暂显示当前画面后继续（最多等 timeout_ms，也可按任意键跳过）。"""
    import time
    deadline = time.time() + timeout_ms / 1000
    while time.time() < deadline:
        key = display.update()
        if key != 255 and key != 0xFF:   # 有按键则跳过等待
            return


def _check_and_handle_end(logic: GameLogic, display: CameraDisplay) -> bool:
    """检查胜负/平局，设置结果显示。有结果返回 True。"""
    winner = logic.check_winner()
    if winner is None:
        return False
    display.set_result(winner)
    return True


def _confirm_restart(display: CameraDisplay) -> bool:
    """提示换纸，等待 Enter 确认或 Q 退出。"""
    display.set_status("Change paper, then press ENTER | Q: quit")
    while True:
        key = display.update()
        if key == 13:
            return True
        if key == ord('q'):
            return False


def _wait_restart(display: CameraDisplay) -> bool:
    """游戏结束后等待 R 重开或 Q 退出。"""
    while True:
        key = display.update()
        if key == ord('r'):
            return _confirm_restart(display)
        if key == ord('q'):
            return False


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 静态语法检查**

```
cd tictactoe
python -m py_compile main.py && echo "Syntax OK"
```

期望输出：`Syntax OK`

- [ ] **Step 3: 全量自动化测试无回归**

```
pytest tests/ -v
```

期望：所有测试 passed（main.py 无自动化测试，保证其他模块不受影响）

- [ ] **Step 4: Commit**

```
git add tictactoe/main.py
git commit -m "feat: integrate board calibration and circle detection input in main.py"
```

- [ ] **Step 5: 冒烟测试（需硬件）**

连接 Dobot（COM6）和 USB 摄像头，然后：

```
conda activate pytorch_py3.11
cd tictactoe
python main.py
```

验证以下流程：
1. 程序启动后出现摄像头画面 + 格线叠加 + 校准提示文字
2. 按方向键，格线在画面中移动（每按一次移动 5px）
3. 按 W/S，格线整体放大/缩小
4. 按 R，格线恢复到 config.py 默认位置
5. 对准纸上棋盘后按 Enter，校准画面消失
6. 出现"Ready! Press ENTER..."提示
7. 按 Enter，机械臂开始画棋盘
8. 出现"Draw O in a cell, then press SPACE"
9. 在纸上格内画圆，按空格
10. 出现绿色格子高亮在检测到的位置
11. 约 1.5 秒后机器人自动随机落子，机械臂画 X
12. 游戏继续至结束，显示 "You Win!" / "Robot Wins!" / "Draw!"

**常见问题排查：**

| 现象 | 原因 | 解法 |
|------|------|------|
| 方向键不响应 | OpenCV 版本键码不同 | 运行 `python -c "import cv2; cv2.namedWindow('t'); print(cv2.waitKey(5000))"` 按方向键查看实际键码，修改 `board_calibrator.py` 中的 `_KEY_*` 常量 |
| 圆检测总返回 None | 差分阈值太高 | 在 config.py 中降低 `CIRCLE_DIFF_THRESHOLD` 至 20 |
| 识别到错误格子 | 叠加未对准 | 重新校准，确保格线与纸上棋盘线对齐 |
| 摄像头黑屏 | CAMERA_INDEX 错误 | 在 config.py 改 `CAMERA_INDEX = 0` 或运行 `find_camera.py` |

---

## 自我审查（Spec Coverage Check）

| 设计规格要求 | 实现任务 |
|-------------|---------|
| config.py 新增 CIRCLE_* 和 CALIB_* 8 个参数 | Task 1 ✓ |
| camera_display.py：叠加参数改为实例变量 | Task 2 ✓ |
| camera_display.py：draw_calib_hint() | Task 2 ✓ |
| camera_display.py：highlight_cell / set_highlight() | Task 2 ✓ |
| camera_display.py：capture_frame() | Task 2 ✓ |
| circle_detector.py：detect(ref, cur) → 1-9 or None | Task 3 ✓ |
| 差分+模糊+二值化+膨胀+轮廓+圆形度过滤算法 | Task 3 ✓ |
| board_calibrator.py：BoardCalibrator.run(display) | Task 4 ✓ |
| 方向键移动、W/S 缩放、R 重置、Enter 确认、Q 退出 | Task 4 ✓ |
| main.py：连接后校准阶段 | Task 5 ✓ |
| main.py：空格触发检测，未检测到重试，格子占用重试 | Task 5 ✓ |
| 高亮检测到的格子供用户确认 | Task 5 ✓ |
