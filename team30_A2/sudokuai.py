#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import copy
import time
import numpy as np
from competitive_sudoku.sudoku import GameState, Move, SudokuBoard, TabooMove
import competitive_sudoku.sudokuai


def calculate_score(i, j, board):
    # checks the completed regions after the move
    score = [0, 1, 3, 7]
    rows_block = board.m
    cols_block = board.n
    board_size = rows_block * cols_block
    board_2d = np.array(board.squares).reshape(
        (board.n * board.m, board.n * board.m))
    count = 0
    count += (0 not in board_2d[i, :]) #checking the corresponding row
    count += (0 not in board_2d[:, j]) #checking the corresponding column
    block = board_2d[i // rows_block * rows_block:(i // rows_block + 1) * rows_block, j // cols_block * cols_block:(j // cols_block + 1)
                             * cols_block] #checking the corresponding block
    count += (0 not in block)
    return score[count]


# def find_available_moves(board, taboolist):
#     # find the available moves for the board
#     rows_block = board.m
#     cols_block = board.n
#     board_size = rows_block * cols_block
#     board_2d = np.array(board.squares).reshape(
#         (board.n * board.m, board.n * board.m))
    
#     #creating the sets of possible values for rows, columns and blocks
#     rows = [set(row) - {0} for row in board_2d]
#     columns = [set(col) - {0} for col in board_2d.T]
#     blocks = [[set(board_2d[i * rows_block:(i + 1) * rows_block, j * cols_block:(j + 1)
#                             * cols_block].reshape(-1)) - {0} for j in range(rows_block)] for i in range(cols_block)]

#     # finding the possible values for the empty sells by using sets 
#     all_values = {i + 1 for i in range(board_size)}

#     result = np.where(board_2d == 0)
#     empty_cells = list(zip(result[0], result[1]))

#     one_value = []
#     for (i, j) in empty_cells:
#         vals = list(all_values.difference(rows[i].union(columns[j]).union(
#             blocks[i // rows_block][j // cols_block])))
#         # moves.append((i, j, vals)) can be sets of possible values for the cell
#         if len(vals) == 1:
#             one_value.append((i, j, vals[0]))
#     if len(one_value) != 0:
#         for move in one_value:
#             board.put(*move)
#         return one_value + find_available_moves(board, taboolist)
#     else:
#         moves = []
#         for (i, j) in empty_cells:
#             vals = list(all_values.difference(rows[i].union(columns[j]).union(
#                 blocks[i // rows_block][j // cols_block])))
#             # moves.append((i, j, vals)) can be sets of possible values for the cell
#             for val in vals:
#                 if (i, j, val) not in taboolist:
#                     moves.append((i, j, val))
#         return moves
    

def find_available_moves(board, taboolist):
    # find the available moves for the board
    rows_block = board.m
    cols_block = board.n
    board_size = rows_block * cols_block
    board = np.array(board.squares).reshape(
        (board.n * board.m, board.n * board.m))
    
    #creating the sets of possible values for rows, columns and blocks
    lines = [set(line) - {0} for line in board]
    rows = [set(row) - {0} for row in board.T]
    blocks = [[set(board[i * rows_block:(i + 1) * rows_block, j * cols_block:(j + 1)
                            * cols_block].reshape(-1)) - {0} for j in range(rows_block)] for i in range(cols_block)]

    # finding the possible values for the empty sells by using sets 
    all_values = {i + 1 for i in range(board_size)}
    moves = []
    result = np.where(board == 0)
    empty_cells = list(zip(result[0], result[1]))
    for (i, j) in empty_cells:
        vals = all_values.difference(lines[i].union(rows[j]).union(
            blocks[i // rows_block][j // cols_block]))
        for val in vals:
            if (i, j, val) not in taboolist:
                moves.append((i, j, val))
    return moves


def minimax_alphabeta(depth, board, is_max, taboo, alpha, beta, score1=0, score2=0):
    if 0 not in board.squares or depth == 0:
        return score1 - score2
    available_list = find_available_moves(board, taboo)
    if is_max:
        value = -100000
        for i in available_list:
            newboard = copy.deepcopy(board)
            newboard.put(i[0], i[1], i[2])
            score = calculate_score(i[0], i[1], newboard)
            value = max(value, minimax_alphabeta(depth - 1, newboard,
                        False, taboo, alpha, beta, score1 + score, score2))
            if value >= beta:
                break
            alpha = max(alpha, value)
        return value
    else:
        value = 100000
        for i in available_list:
            newboard = copy.deepcopy(board)
            newboard.put(i[0], i[1], i[2])
            score = calculate_score(i[0], i[1], newboard)
            value = min(value, minimax_alphabeta(depth - 1, newboard,
                        True, taboo, alpha, beta, score1, score2 + score))
            if value <= alpha:
                break
            beta = min(beta, value)
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
        board = copy.deepcopy(game_state.board)
        taboo = [(taboo_move.i, taboo_move.j, taboo_move.value)
                 for taboo_move in game_state.taboo_moves]
        satisfy = find_available_moves(board, taboo)
        max_score = -1000
        depth = 2
        while True:
            for i in range(len(satisfy)):
                newboard = copy.deepcopy(board)
                newboard.put(satisfy[i][0], satisfy[i][1], satisfy[i][2])
                score = calculate_score(satisfy[i][0], satisfy[i][1], newboard)
                current_score = minimax_alphabeta(
                    depth - 1, newboard, False, taboo, -10000, 10000, score, 0)
                if max_score < current_score:
                    max_score = current_score
                    current_max = [satisfy[i][0], satisfy[i][1], satisfy[i][2]]
                    self.propose_move(
                        Move(current_max[0], current_max[1], current_max[2]))
            depth += 1
