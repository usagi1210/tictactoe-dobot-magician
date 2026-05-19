import random

class GameLogic:
    EMPTY = 0
    HUMAN = 1   # 圈 O
    ROBOT = 2   # 叉 X

    _WIN_LINES = [
        [(0,0),(0,1),(0,2)],
        [(1,0),(1,1),(1,2)],
        [(2,0),(2,1),(2,2)],
        [(0,0),(1,0),(2,0)],
        [(0,1),(1,1),(2,1)],
        [(0,2),(1,2),(2,2)],
        [(0,0),(1,1),(2,2)],
        [(0,2),(1,1),(2,0)],
    ]

    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[self.EMPTY] * 3 for _ in range(3)]

    def cell_to_rowcol(self, cell: int) -> tuple:
        idx = cell - 1
        return idx // 3, idx % 3

    def place_move(self, cell: int, player: int) -> bool:
        row, col = self.cell_to_rowcol(cell)
        if self.board[row][col] != self.EMPTY:
            return False
        self.board[row][col] = player
        return True

    def check_winner(self):
        for line in self._WIN_LINES:
            vals = [self.board[r][c] for r, c in line]
            if vals[0] != self.EMPTY and vals[0] == vals[1] == vals[2]:
                return vals[0]
        if all(self.board[r][c] != self.EMPTY for r in range(3) for c in range(3)):
            return 'draw'
        return None

    def ai_move(self):
        empty = [r*3+c+1 for r in range(3) for c in range(3)
                 if self.board[r][c] == self.EMPTY]
        return random.choice(empty) if empty else None
