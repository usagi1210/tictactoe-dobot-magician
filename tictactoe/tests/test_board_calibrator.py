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
