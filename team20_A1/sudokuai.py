#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

from competitive_sudoku.sudoku import GameState, SudokuBoard
import competitive_sudoku.sudokuai
import copy
from team20_A1.search_tree import Node


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()

    def compute_best_move(self, game_state: GameState) -> None:

        # print("Executing A1 implementation")  # to be removed later
        # copy the board just in case

        board_copy = copy.deepcopy(game_state.board)
        taboo_moves = game_state.taboo_moves

        # initialize the minimax tree
        root = Node(board_copy, depth=0)

        # calculates all candidates for the current situation
        # 当前的所有possible move
        root.add_children(taboo_moves)
        if not root.children:
            raise RuntimeError('Could not generate a move for AI player.\n')

        # propose one of legal moves as the initial proposal
        # inialize proposal
        move = root.children[0].move
        self.propose_move(move)

        # propose the best of legal moves for the tree of depth = 1 as the second proposal
        root.update_score()
        self.propose_move(root.best_move())

        # iteratively deepen the tree and propose the best move based on the updated score
        depth = 2
        while True:
            root.add_level(taboo_moves, target_depth = depth)
            root.update_score()
            self.propose_move(root.best_move())
            depth += 1

