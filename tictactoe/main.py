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
            display.clear_result()   # 清掉 "You Win!" 覆盖层，让 _confirm_restart 提示可见
            return _confirm_restart(display)
        if key == ord('q'):
            return False


if __name__ == '__main__':
    main()
