from competitive_sudoku.sudoku import Move, SudokuBoard, TabooMove


def compute_legal_moves(current_board: SudokuBoard, taboo_moves: list):
    """
    Calculates all legal moves for the current state of the game as all possible values for empty cells that do not
    violate the rules of the game. Legal values are checked as the values from possible range that does not appear in
    the same column or the same row or the same block.

    @param current_board - object of class SudokuBoard, the representation of the board before the move
    @param taboo_moves - list of TabooMoves, recorded through the previous turns of the game

    @return list of the Moves, that are possible in the current game situation
    """
    # get the board cells as tuples (i, j, value)
    board_cells = [(current_board.f2rc(i)[0], current_board.f2rc(i)[1], j) for i, j in
                   enumerate(current_board.squares, 0)]
    # get the list of empty cells (candidates)
    empty_cells = [cell for cell in board_cells if cell[2] == 0]

    # save auxiliary variables representing the information about the board
    legal_moves = []
    m = current_board.m
    n = current_board.n
    N = current_board.N

    # for each candidate cell get all possible moves
    for target_cell in empty_cells:
        # extract all already used values in related columns/rows/block
        rows = set(x[2] for x in board_cells if (x[0] == target_cell[0]) and (x[2] > 0))
        columns = set(x[2] for x in board_cells if (x[1] == target_cell[1]) and (x[2] > 0))
        blocks = set(x[2] for x in board_cells if
                     ((x[0] // m == target_cell[0] // m) and (x[1] // n == target_cell[1] // n)) and (x[2] > 0))
        # add possible moves for candidate cell to the list of all possible legal moves
        legal_moves.extend([Move(i=target_cell[0], j=target_cell[1], value=x) for x in
                            set(i for i in range(1, N + 1, 1)) - (rows | columns | blocks)])
    # filter the moves that are in taboo list
    legal_moves = [move for move in legal_moves if move not in taboo_moves]

    return legal_moves
