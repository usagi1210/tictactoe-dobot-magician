import sys, os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 恢复真实 cv2：test_camera_display.py 在模块级将 cv2 替换为 MagicMock，
# 这会污染同一 pytest 进程中后续模块的 cv2 导入。
# 解决方案：先临时移除 mock，用 importlib.import_module 强制重新加载真实模块。
import importlib as _il
if 'cv2' in sys.modules:
    del sys.modules['cv2']
_real_cv2 = _il.import_module('cv2')
sys.modules['cv2'] = _real_cv2
import cv2  # 现在指向真实模块

import config

# 若 circle_detector 已被缓存（使用 mock cv2 加载），强制重新加载
if 'circle_detector' in sys.modules:
    del sys.modules['circle_detector']

from circle_detector import CircleDetector


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
    # 画一个细长矩形（90×8），膨胀后圆形度 ≈ 0.43 < CIRCLE_MIN_CIRCULARITY(0.45)
    cv2.rectangle(cur, (5, 40), (95, 48), (200, 200, 200), 3)
    result = CircleDetector(d).detect(ref, cur)
    assert result is None
