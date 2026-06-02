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
