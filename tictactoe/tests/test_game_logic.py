import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from game_logic import GameLogic

# ── cell_to_rowcol ────────────────────────────────────
def test_cell_to_rowcol_1_is_top_left():
    assert GameLogic().cell_to_rowcol(1) == (0, 0)

def test_cell_to_rowcol_5_is_center():
    assert GameLogic().cell_to_rowcol(5) == (1, 1)

def test_cell_to_rowcol_9_is_bottom_right():
    assert GameLogic().cell_to_rowcol(9) == (2, 2)

# ── place_move ────────────────────────────────────────
def test_place_move_returns_true_on_empty():
    assert GameLogic().place_move(5, GameLogic.HUMAN) is True

def test_place_move_updates_board():
    g = GameLogic()
    g.place_move(5, GameLogic.HUMAN)
    assert g.board[1][1] == GameLogic.HUMAN

def test_place_move_returns_false_on_occupied():
    g = GameLogic()
    g.place_move(5, GameLogic.HUMAN)
    assert g.place_move(5, GameLogic.ROBOT) is False

def test_place_move_does_not_overwrite_on_occupied():
    g = GameLogic()
    g.place_move(5, GameLogic.HUMAN)
    g.place_move(5, GameLogic.ROBOT)
    assert g.board[1][1] == GameLogic.HUMAN

# ── check_winner ─────────────────────────────────────
def test_check_winner_returns_none_on_empty():
    assert GameLogic().check_winner() is None

def test_check_winner_detects_row_win():
    g = GameLogic()
    for c in [1, 2, 3]:
        g.place_move(c, GameLogic.HUMAN)
    assert g.check_winner() == GameLogic.HUMAN

def test_check_winner_detects_column_win():
    g = GameLogic()
    for c in [1, 4, 7]:
        g.place_move(c, GameLogic.ROBOT)
    assert g.check_winner() == GameLogic.ROBOT

def test_check_winner_detects_main_diagonal():
    g = GameLogic()
    for c in [1, 5, 9]:
        g.place_move(c, GameLogic.HUMAN)
    assert g.check_winner() == GameLogic.HUMAN

def test_check_winner_detects_anti_diagonal():
    g = GameLogic()
    for c in [3, 5, 7]:
        g.place_move(c, GameLogic.ROBOT)
    assert g.check_winner() == GameLogic.ROBOT

def test_check_winner_detects_draw():
    g = GameLogic()
    # X O X / O X O / O X O （无三连，格满）
    seq = [(1, GameLogic.ROBOT),  (2, GameLogic.HUMAN), (3, GameLogic.ROBOT),
           (4, GameLogic.HUMAN), (5, GameLogic.ROBOT), (6, GameLogic.HUMAN),
           (7, GameLogic.HUMAN), (8, GameLogic.ROBOT), (9, GameLogic.HUMAN)]
    for cell, player in seq:
        g.place_move(cell, player)
    assert g.check_winner() == 'draw'

def test_check_winner_returns_none_mid_game():
    g = GameLogic()
    g.place_move(1, GameLogic.HUMAN)
    g.place_move(5, GameLogic.ROBOT)
    assert g.check_winner() is None

# ── ai_move ───────────────────────────────────────────
def test_ai_move_returns_valid_cell():
    cell = GameLogic().ai_move()
    assert 1 <= cell <= 9

def test_ai_move_returns_empty_cell():
    g = GameLogic()
    cell = g.ai_move()
    r, c = g.cell_to_rowcol(cell)
    assert g.board[r][c] == GameLogic.EMPTY

def test_ai_move_returns_none_when_full():
    g = GameLogic()
    for cell in range(1, 10):
        g.place_move(cell, GameLogic.HUMAN)
    assert g.ai_move() is None

# ── reset ─────────────────────────────────────────────
def test_reset_clears_all_cells():
    g = GameLogic()
    g.place_move(5, GameLogic.HUMAN)
    g.reset()
    assert all(g.board[r][c] == GameLogic.EMPTY for r in range(3) for c in range(3))
