import cv2
import numpy as np
import config
from game_logic import GameLogic


class CameraDisplay:
    def __init__(self):
        self.cap = cv2.VideoCapture(config.CAMERA_INDEX)
        self._board = None
        self._status = ""
        self._result = None   # GameLogic.HUMAN / GameLogic.ROBOT / 'draw' / None

    def set_board(self, board: list):
        self._board = board

    def set_status(self, text: str):
        self._status = text

    def set_result(self, winner):
        self._result = winner

    def clear_result(self):
        self._result = None

    def update(self) -> int:
        """读取一帧，绘制叠加层，显示窗口。返回按键（无按键返回 -1）。"""
        ret, frame = self.cap.read()
        if not ret:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = self._draw_overlay(frame)
        frame = self._draw_status(frame)
        if self._result is not None:
            frame = self._draw_result(frame)
        cv2.imshow(config.WINDOW_NAME, frame)
        return cv2.waitKey(1) & 0xFF

    def _draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        overlay = frame.copy()
        ox = config.OVERLAY_X
        oy = config.OVERLAY_Y
        sp = config.OVERLAY_CELL_PX
        color = (200, 200, 0)   # 青黄色格线

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

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()
