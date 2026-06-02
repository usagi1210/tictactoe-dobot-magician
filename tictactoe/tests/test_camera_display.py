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
