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
        import numpy as np
        while True:
            # 读取原始帧（不经 display.update，以便完全控制显示内容）
            ret, frame = display.cap.read()
            if not ret:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)

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
