import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'demo-magician-python-64-master'))

from dobot_controller import DobotController
from game_logic import GameLogic
from camera_display import CameraDisplay


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

    try:
        while _run_game(dobot, logic, display):
            pass
    finally:
        dobot.disconnect()
        display.release()


def _run_game(dobot: DobotController, logic: GameLogic, display: CameraDisplay) -> bool:
    """运行一局。返回 True 继续，False 退出。"""
    logic.reset()
    display.set_board(logic.board)
    display.clear_result()
    # 等待用户确认后再开始画棋盘
    display.set_status("Ready! Press ENTER to draw board  |  Q: quit")
    while True:
        key = display.update()
        if key == 13:    # Enter
            break
        if key == ord('q'):
            return False

    display.set_status("Drawing board, please wait...")
    dobot.draw_grid(update_cb=display.update)

    while True:
        display.set_status("Your turn! Press 1-9  |  R: restart  |  Q: quit")
        key = display.update()

        if key == ord('q'):
            return False

        if key == ord('r'):
            return _confirm_restart(display)

        if ord('1') <= key <= ord('9'):
            cell = key - ord('0')
            if not logic.place_move(cell, GameLogic.HUMAN):
                display.set_status("Cell occupied! Choose again.")
                continue

            if _check_and_handle_end(logic, display):
                return _wait_restart(display)

            ai_cell = logic.ai_move()
            logic.place_move(ai_cell, GameLogic.ROBOT)
            display.set_status(f"Robot chose {ai_cell}, drawing X...")
            dobot.draw_cross(ai_cell, update_cb=display.update)

            if _check_and_handle_end(logic, display):
                return _wait_restart(display)

    return True


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
        if key == 13:    # Enter
            return True
        if key == ord('q'):
            return False


def _wait_restart(display: CameraDisplay) -> bool:
    """游戏结束后等待用户操作。"""
    while True:
        key = display.update()
        if key == ord('r'):
            return _confirm_restart(display)
        if key == ord('q'):
            return False


if __name__ == '__main__':
    main()
