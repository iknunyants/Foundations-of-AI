from competitive_sudoku.sudoku import SudokuBoard, Move, TabooMove


# evaluate the score of the move in the state
def evaluate(move: Move, current_board: SudokuBoard) -> float:
    """
    A function, that evaluates the score for a child.
    It computes number of points the player gets from the move. The points are evaluated as
    the number of points he gets by the rules of the game (0, 1, 3 or 7 points respectively)
    It also computes a penalty for a move that could win the opponent points.
    It also computes a reward for a move that could win the player points in the future.

    @param move - object of Move class, the move that is done by player
    @param current_board - object of SudokuBoard class, the board before the move done.

    @return: the score for the move done.
    """
    # score variables
    score = 0
    # bonus score from the resulting game situation (score from board situation)
    score_b = 0
    # penalty score from the resulting game situation (score for opponent)
    score_o = 0

    # getting the board values as the tuples (i, j, value)
    board_cells = [(current_board.f2rc(i)[0], current_board.f2rc(i)[1], j) for i, j in
                   enumerate(current_board.squares, 0)]

    target_cell = [move.i, move.j]

    # save the parameters of the board to the auxiliary variables
    m = current_board.m
    n = current_board.n
    total_board_size = m * n

    # extracting the values that are already in the row/column/block related with target cell (move)
    rows = set(x[2] for x in board_cells if (x[0] == target_cell[0]) and (x[2] > 0))
    columns = set(x[2] for x in board_cells if (x[1] == target_cell[1]) and (x[2] > 0))
    blocks = set(x[2] for x in board_cells if
                 ((x[0] // m == target_cell[0] // m) and (x[1] // n == target_cell[1] // n)) and (x[2] > 0))

    # calculating the number of points player gets from the move by the rules

    if len(rows) == total_board_size - 1:
        score += 1
    if len(columns) == total_board_size - 1:
        score += 1
    if len(blocks) == n * m - 1:
        score += 1

    score_table = [0, 1, 3, 7]
    score = score_table[score]


    # calculating the extra penalties and bonuses from the resulting game situation ("naive" analysis)
    scale_b = 0
    scale_o = 0
    
    # for the row
    remaining_empty_in_row = total_board_size - len(rows)
    if remaining_empty_in_row > 0:
        if remaining_empty_in_row % 2 == 0:
            score_o += 1
            scale_o = 1 / remaining_empty_in_row
        else:
            score_b += 1
            scale_b = 1 / remaining_empty_in_row

    # for the column
    remaining_empty_in_column = total_board_size - len(columns)
    if remaining_empty_in_column > 0:
        if remaining_empty_in_column % 2 == 0:
            score_o += 1
            scale_o = max(scale_o, 1 / remaining_empty_in_column)
        else:
            score_b += 1
            scale_b = max(scale_b, 1 / remaining_empty_in_column)

    # for the block
    remaining_empty_in_block = (n * m) - len(blocks)
    if remaining_empty_in_block > 0:
        if remaining_empty_in_block % 2 == 0:
            score_o += 1
            scale_o = max(scale_o, 1 / remaining_empty_in_block)
        else:
            score_b += 1
            scale_b = max(scale_b, 1 / remaining_empty_in_block)

    score_b = score_table[score_b]
    score_o = score_table[score_o]
    score_b = score_b * scale_b
    scale_o = score_o * scale_o

    # calculating the final result
    points = score + score_b - scale_o
    return points
