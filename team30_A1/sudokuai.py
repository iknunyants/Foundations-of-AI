#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


def check_finish(board):
    m = board.m
    n = board.n
    for i in range(m * n):
        for j in range(m * n):
            if board.get(i, j) == 0:
                return False
    return True


def calculate_score(i, j, board):
    score = [0, 1, 3, 7]
    m = board.m
    n = board.n
    count = 0
    flag = True
    for x in range((i // m) * m, (i // m) * m + m):
        for y in range((j // n) * n, (j // n) * n + n):
            if board.get(x, y) == 0:
                flag = False
                break
        if flag == False:
            break
    if flag:
        count += 1
    flag = True
    for x in range(m * n):
        if board.get(x, j) == 0:
            flag = False
            break
    if flag:
        count += 1
    flag = True
    for x in range(m * n):
        if board.get(i, x) == 0:
            flag = False
            break
    if flag:
        count += 1
    return score[count]


def check_valid(i, j, value, board):
    m = board.m
    n = board.n

    if board.get(i, j) != 0:
        return False
    for x in range(m * n):
        if board.get(x, j) == value:
            return False
    for x in range(m * n):
        if board.get(i, x) == value:
            return False
    for x in range((i // m) * m, (i // m) * m + m):
        for y in range((j // n) * n, (j // n) * n + n):
            if board.get(x, y) == value:
                return False
    return True


def minimax(depth, board, is_max, taboo, score1=0, score2=0):
    if check_finish(board) or depth == 0:
        return score1 - score2
    available_list = []
    for i in range(board.m * board.n):
        for j in range(board.m * board.n):
            for v in range(1, board.m * board.n + 1):
                if check_valid(i, j, v, board):
                    available_list.append((i, j, v))
    available_list = list(set(available_list) - set(taboo))
    if is_max:
        value = -100000
        for i in available_list:
            newboard = copy.deepcopy(board)
            newboard.put(i[0], i[1], i[2])
            score = calculate_score(i[0], i[1], newboard)
            value = max(value, minimax(depth - 1, newboard,
                        False, taboo, score1 + score, score2))
        return value
    else:
        value = 100000
        for i in available_list:
            newboard = copy.deepcopy(board)
            newboard.put(i[0], i[1], i[2])
            score = calculate_score(i[0], i[1], newboard)
            value = min(value, minimax(depth - 1, newboard,
                        True, taboo, score1, score2 + score))
        return value


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()
        self.solve_sudoku_path = None  # N.B. this path is set from outside

    # Uses solve_sudoku to compute a random move.
    def compute_best_move(self, game_state: GameState) -> None:
        board = copy.copy(game_state.board)
        satisfy = []
        for i in range(board.m * board.n):
            for j in range(board.m * board.n):
                for v in range(1, board.m * board.n + 1):
                    if check_valid(i, j, v, board):
                        satisfy.append((i, j, v))
        max_score = -1000
        taboo = [(taboo_move.i, taboo_move.j, taboo_move.value)
                 for taboo_move in game_state.taboo_moves]
        for i in range(len(satisfy)):
            if (satisfy[i][0], satisfy[i][1], satisfy[i][2]) in taboo:
                continue
            depth = 2
            newboard = copy.deepcopy(board)
            newboard.put(satisfy[i][0], satisfy[i][1], satisfy[i][2])
            score = calculate_score(satisfy[i][0], satisfy[i][1], newboard)
            current_score = minimax(
                depth - 1, newboard, False, taboo, score, 0)
            if max_score < current_score:
                max_score = current_score
                current_max = [satisfy[i][0], satisfy[i][1], satisfy[i][2]]
                self.propose_move(
                    Move(current_max[0], current_max[1], current_max[2]))
