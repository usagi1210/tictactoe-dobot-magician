import sys, os
from unittest.mock import MagicMock

# 在导入 dobot_controller 前 mock DobotDllType（避免 DLL 依赖）
mock_dType = MagicMock()
mock_dType.DobotConnect.DobotConnect_NoError = 0
sys.modules['DobotDllType'] = mock_dType
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import config
from dobot_controller import DobotController

def _make():
    """不调用 __init__（跳过 dType.load()）直接创建实例。"""
    return DobotController.__new__(DobotController)

def test_cell_center_5_is_board_center():
    dc = _make()
    x, y = dc._cell_center(5)
    assert x == config.BOARD_CENTER_X
    assert y == config.BOARD_CENTER_Y

def test_cell_center_1_is_top_left():
    dc = _make()
    x, y = dc._cell_center(1)
    assert x == config.BOARD_CENTER_X - config.CELL_SIZE
    assert y == config.BOARD_CENTER_Y + config.CELL_SIZE

def test_cell_center_3_is_top_right():
    dc = _make()
    x, y = dc._cell_center(3)
    assert x == config.BOARD_CENTER_X + config.CELL_SIZE
    assert y == config.BOARD_CENTER_Y + config.CELL_SIZE

def test_cell_center_7_is_bottom_left():
    dc = _make()
    x, y = dc._cell_center(7)
    assert x == config.BOARD_CENTER_X - config.CELL_SIZE
    assert y == config.BOARD_CENTER_Y - config.CELL_SIZE

def test_cell_center_9_is_bottom_right():
    dc = _make()
    x, y = dc._cell_center(9)
    assert x == config.BOARD_CENTER_X + config.CELL_SIZE
    assert y == config.BOARD_CENTER_Y - config.CELL_SIZE

def test_connect_raises_on_failure():
    mock_dType.load.return_value = MagicMock()
    mock_dType.ConnectDobot.return_value = [1]   # 1 = error
    dc = DobotController()
    try:
        dc.connect()
        assert False, "应抛出 ConnectionError"
    except ConnectionError:
        pass
