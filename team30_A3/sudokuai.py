#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import random
import time
import copy
import math
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
    count += (0 not in board_2d[i, :])  # checking the corresponding row
    count += (0 not in board_2d[:, j])  # checking the corresponding column
    block = board_2d[i // rows_block * rows_block:(i // rows_block + 1) * rows_block, j // cols_block * cols_block:(j // cols_block + 1)
                     * cols_block]  # checking the corresponding block
    count += (0 not in block)
    return score[count]


def find_available_moves(board, taboolist):
    # find the available moves for the board using sinlge possibility rule recursion
    rows_block = board.m
    cols_block = board.n
    board_size = rows_block * cols_block
    board_2d = np.array(board.squares).reshape(
        (board.n * board.m, board.n * board.m))

    # creating the sets of possible values for rows, columns and blocks
    rows = [set(row) - {0} for row in board_2d]
    columns = [set(col) - {0} for col in board_2d.T]
    blocks = [[set(board_2d[i * rows_block:(i + 1) * rows_block, j * cols_block:(j + 1)
                            * cols_block].reshape(-1)) - {0} for j in range(rows_block)] for i in range(cols_block)]

    # finding the possible values for the empty sells by using sets
    all_values = {i + 1 for i in range(board_size)}

    result = np.where(board_2d == 0)
    empty_cells = list(zip(result[0], result[1]))

    # collecting all the moves when there's only one possible value for a cell (one_value)
    one_value = []
    for (i, j) in empty_cells:
        vals = list(all_values.difference(rows[i].union(columns[j]).union(
            blocks[i // rows_block][j // cols_block])))
        if len(vals) == 1:
            one_value.append((i, j, vals[0]))

    # if there are one_value moves, put them on the board and return from the function combined with the moves for the new board
    if len(one_value) != 0:
        newboard = copy.deepcopy(board)
        for move in one_value:
            newboard.put(*move)
        return one_value + find_available_moves(newboard, taboolist)

    # there are no one_value moves, so return all the moves 
    moves = []
    for (i, j) in empty_cells:
        vals = list(all_values.difference(rows[i].union(columns[j]).union(
            blocks[i // rows_block][j // cols_block])))
        for val in vals:
            if (i, j, val) not in taboolist:
                moves.append((i, j, val))
    return moves
    

class treeNode():
    #theeNode class for every state of the game in the MC tree 

    def __init__(self, board, taboo_moves, move=None, score=0, player=1):
        self.board = board
        self.taboo_moves = taboo_moves
        self.move = move
        self.score = score
        self.player = player
        self.q = 0 
        self.n = 0
        self.children = []
    
    def best_move(self):
        # function for returning the best move based on the tree and the corresponding child
        max_move = None 
        max_value = -10000
        for child in self.children:
            if child.n == 0:
                continue
            value = child.q / child.n
            if value > max_value:
                max_value = value
                max_move = child
        return max_move.move, max_move

    def update_node(self, delta):
        #updating the node's n (number of times visited) and q (the "value" of the node)
        self.n += 1
        if delta > 0:
            self.q += -self.player
        return 


    def explore(self):
        #the MC tree search function of the node

        
        if not 0 in self.board.squares:
            #we have reached the end of the game
            self.update_node(self.score)
            return self.score


        if self.children:
            # we have already visited this node, got saved children and calculating where to go next.
            # aka "Leaf selection stage"
            maxValue = -10000
            maxNode = None
            for child in self.children:
                if child.n == 0:
                    maxNode = child
                    break
                curValue = child.q / child.n + 2 * math.sqrt(math.log(self.n) / child.n)
                if curValue > maxValue:
                    maxValue = curValue
                    maxNode = child
            delta = maxNode.explore()
            self.update_node(delta)
            return delta
        else:
            def random_simulate(board, taboo_moves, player, score):
                # function for "simulation" stage
                new_board = copy.deepcopy(board)
                while 0 in new_board.squares:
                    moves = find_available_moves(new_board,taboo_moves)
                    if len(moves) == 0:
                        return 0
                    random_move = random.sample(moves, 1)[0]
                    new_board.put(*random_move)
                    score += player * calculate_score(random_move[0], random_move[1], new_board)
                    player *= -1

                return score

            if self.n == 0:
                #this leaf has never been visited, "simulation" stage starts
                delta = random_simulate(self.board, self.taboo_moves, self.player, self.score)
                self.update_node(delta)
                return delta
            else:
                # this leaf was visited, constructing this node's children
                # aka stage "leaf expansion"
                moves = find_available_moves(self.board, self.taboo_moves)
                for move in moves:
                    new_board = copy.deepcopy(self.board)
                    new_board.put(*move)
                    self.children.append(treeNode(new_board, self.taboo_moves, 
                                        move,
                                        score=self.score + self.player * calculate_score(move[0], move[1], new_board), 
                                        player=-self.player))
                delta = self.children[0].explore()
                self.update_node(delta)
                return delta

    


class SudokuAI(competitive_sudoku.sudokuai.SudokuAI):
    """
    Sudoku AI that computes a move for a given sudoku configuration.
    """

    def __init__(self):
        super().__init__()


    def compute_best_move(self, game_state: GameState) -> None:
        board = copy.deepcopy(game_state.board)
        taboo = [(taboo_move.i, taboo_move.j, taboo_move.value)
                 for taboo_move in game_state.taboo_moves]
        
        #proposing any move 
        satisfy = find_available_moves(board, taboo)
        self.propose_move(
                        Move(satisfy[0][0], satisfy[0][1], satisfy[0][2]))

        # mc_tree = self.load()
        # if mc_tree:
        #     for child in mc_tree.children:
        #         if child.board.squares == game_state.board.squares:
        #             mc_tree = child 
        #             mc_tree.taboo_moves = taboo
        #             break
        #     mc_tree = None
        # if not mc_tree:
        #     mc_tree = treeNode(board, taboo)
        current_score = game_state.scores[self.player_number - 1] - game_state.scores[2 - self.player_number]
        mc_tree = treeNode(board, taboo, score=current_score)
        propose_freq = 100
        mc_runs = 0
        while True:
            mc_tree.explore()
            mc_runs += 1
            if mc_runs % propose_freq == 0:
                move, subtree = mc_tree.best_move()
                # self.save(subtree)
                self.propose_move(Move(*move))

