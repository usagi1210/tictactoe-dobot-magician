import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'demo-magician-python-64-master'))
import DobotDllType as dType
import config


_SDK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'demo-magician-python-64-master'))


class DobotController:
    def __init__(self):
        # DobotDllType.load() 使用相对路径 "./DobotDll.dll"，
        # 必须切换到 SDK 目录才能找到 DLL 文件
        _orig = os.getcwd()
        os.chdir(_SDK_DIR)
        try:
            self.api = dType.load()
        finally:
            os.chdir(_orig)

    def connect(self):
        state = dType.ConnectDobot(self.api, config.DOBOT_PORT, 115200)[0]
        if state != dType.DobotConnect.DobotConnect_NoError:
            raise ConnectionError(f"Dobot 连接失败，错误码: {state}")
        # 初始化运动参数（队列方式，确认生效）
        dType.SetQueuedCmdClear(self.api)
        dType.SetPTPJointParams(self.api, 200, 200, 200, 200, 200, 200, 200, 200, isQueued=1)
        last = dType.SetPTPCommonParams(self.api, config.ARM_VELOCITY, config.ARM_ACCEL, isQueued=1)[0]
        dType.SetQueuedCmdStartExec(self.api)
        while last > dType.GetQueuedCmdCurrentIndex(self.api)[0]:
            dType.dSleep(100)
        dType.SetQueuedCmdStopExec(self.api)

    def disconnect(self):
        dType.SetQueuedCmdStopExec(self.api)
        dType.DisconnectDobot(self.api)

    def _cell_center(self, cell: int) -> tuple:
        """格子编号 1-9 → (robot_x, robot_y) mm。"""
        idx = cell - 1
        row, col = idx // 3, idx % 3
        x = config.BOARD_CENTER_X + (col - 1) * config.CELL_SIZE
        y = config.BOARD_CENTER_Y + (1 - row) * config.CELL_SIZE
        return x, y

    def _queue_move(self, x: float, y: float, z: float) -> int:
        return dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode,
                               x, y, z, 0, isQueued=1)[0]

    def _queue_line(self, x1: float, y1: float, x2: float, y2: float) -> int:
        """依次队列：抬笔移到起点 → 落笔 → 划到终点 → 抬笔。"""
        self._queue_move(x1, y1, config.BOARD_Z_MOVE)
        self._queue_move(x1, y1, config.BOARD_Z_DRAW)
        self._queue_move(x2, y2, config.BOARD_Z_DRAW)
        return self._queue_move(x2, y2, config.BOARD_Z_MOVE)

    def _run_queue(self, last_idx: int, update_cb=None):
        """执行队列，等待完成。执行期间每 100ms 调用一次 update_cb（用于刷新显示）。"""
        dType.SetQueuedCmdStartExec(self.api)
        while last_idx > dType.GetQueuedCmdCurrentIndex(self.api)[0]:
            if update_cb:
                update_cb()
            dType.dSleep(100)
        dType.SetQueuedCmdStopExec(self.api)

    def _queue_park(self) -> int:
        """队列添加归位动作：抬臂到安全高度并缩回，避免遮挡摄像头。"""
        return self._queue_move(config.ARM_PARK_X, config.ARM_PARK_Y, config.ARM_PARK_Z)

    def draw_grid(self, update_cb=None):
        """机械臂画 3×3 井字格（4 条线），画完后归位。"""
        cx, cy = config.BOARD_CENTER_X, config.BOARD_CENTER_Y
        s = config.CELL_SIZE
        dType.SetQueuedCmdClear(self.api)
        self._queue_line(cx - s/2, cy + 1.5*s, cx - s/2, cy - 1.5*s)   # 竖线1
        self._queue_line(cx + s/2, cy + 1.5*s, cx + s/2, cy - 1.5*s)   # 竖线2
        self._queue_line(cx - 1.5*s, cy + s/2, cx + 1.5*s, cy + s/2)   # 横线1
        self._queue_line(cx - 1.5*s, cy - s/2, cx + 1.5*s, cy - s/2)   # 横线2
        last = self._queue_park()
        self._run_queue(last, update_cb)

    def draw_cross(self, cell: int, update_cb=None):
        """机械臂在指定格子（1-9）画 X，画完后归位。"""
        cx, cy = self._cell_center(cell)
        r = config.CROSS_SIZE
        dType.SetQueuedCmdClear(self.api)
        self._queue_line(cx - r, cy + r, cx + r, cy - r)          # 斜线1
        self._queue_line(cx + r, cy + r, cx - r, cy - r)          # 斜线2
        last = self._queue_park()
        self._run_queue(last, update_cb)
