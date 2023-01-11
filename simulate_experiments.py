#!/usr/bin/env python3

#  (C) Copyright Wieger Wesselink 2021. Distributed under the GPL-3.0-or-later
#  Software License, (See accompanying file LICENSE or copy at
#  https://www.gnu.org/licenses/gpl-3.0.txt)

import argparse
import importlib
import multiprocessing
import platform
import re
import time
import os
from pathlib import Path
from tqdm import tqdm

from competitive_sudoku.execute import solve_sudoku
from competitive_sudoku.sudoku import GameState, SudokuBoard, Move, TabooMove, load_sudoku_from_text
from competitive_sudoku.sudokuai import SudokuAI


def check_oracle(solve_sudoku_path: str) -> None:
    board_text = '''2 2
       1   2   3   4
       3   4   .   2
       2   1   .   3
       .   .   .   1
    '''
    output = solve_sudoku(solve_sudoku_path, board_text)
    result = 'has a solution' in output
    if result:
        print('The sudoku_solve program works.')
    else:
        print('The sudoku_solve program gives unexpected results.')
        print(output)


def simulate_game(initial_board: SudokuBoard, player1: SudokuAI, player2: SudokuAI, solve_sudoku_path: str, calculation_time: float = 0.5, print_games=False) -> None:
    """
    Simulates a game between two instances of SudokuAI, starting in initial_board. The first move is played by player1.
    @param initial_board: The initial position of the game.
    @param player1: The AI of the first player.
    @param player2: The AI of the second player.
    @param solve_sudoku_path: The location of the oracle executable.
    @param calculation_time: The amount of time in seconds for computing the best move.
    """
    import copy
    N = initial_board.N

    game_state = GameState(initial_board, copy.deepcopy(
        initial_board), [], [], [0, 0])
    move_number = 0
    number_of_moves = initial_board.squares.count(SudokuBoard.empty)
    if print_games:
        print('Initial state')
        print(game_state)

    with multiprocessing.Manager() as manager:
        # use a lock to protect assignments to best_move
        lock = multiprocessing.Lock()
        player1.lock = lock
        player2.lock = lock

        # use shared variables to store the best move
        player1.best_move = manager.list([0, 0, 0])
        player2.best_move = manager.list([0, 0, 0])

        while move_number < number_of_moves:
            player, player_number = (player1, 1) if len(
                game_state.moves) % 2 == 0 else (player2, 2)
            if print_games:
                print(
                    f'-----------------------------\nCalculate a move for player {player_number}')
            player.best_move[0] = 0
            player.best_move[1] = 0
            player.best_move[2] = 0
            try:
                process = multiprocessing.Process(
                    target=player.compute_best_move, args=(game_state,))
                process.start()
                time.sleep(calculation_time)
                lock.acquire()
                process.terminate()
                lock.release()
            except Exception as err:
                print('Error: an exception occurred.\n', err)
            i, j, value = player.best_move
            best_move = Move(i, j, value)
            if print_games:
                print(f'Best move: {best_move}')
            player_score = 0
            if best_move != Move(0, 0, 0):
                if TabooMove(i, j, value) in game_state.taboo_moves:
                    if print_games:
                        print(
                            f'Error: {best_move} is a taboo move. Player {3-player_number} wins the game.')
                    return 2 - player_number
                board_text = str(game_state.board)
                options = f'--move "{game_state.board.rc2f(i, j)} {value}"'
                output = solve_sudoku(solve_sudoku_path, board_text, options)
                if 'Invalid move' in output:
                    if print_games:
                        print(
                            f'Error: {best_move} is not a valid move. Player {3-player_number} wins the game.')
                    return 2 - player_number
                if 'Illegal move' in output:
                    if print_games:
                        print(
                            f'Error: {best_move} is not a legal move. Player {3-player_number} wins the game.')
                    return 2 - player_number
                if 'has no solution' in output:
                    if print_games:
                        print(
                            f'The sudoku has no solution after the move {best_move}.')
                    player_score = 0
                    game_state.moves.append(TabooMove(i, j, value))
                    game_state.taboo_moves.append(TabooMove(i, j, value))
                if 'The score is' in output:
                    match = re.search(r'The score is ([-\d]+)', output)
                    if match:
                        player_score = int(match.group(1))
                        game_state.board.put(i, j, value)
                        game_state.moves.append(best_move)
                        move_number = move_number + 1
                    else:
                        raise RuntimeError(
                            f'Unexpected output of sudoku solver: "{output}".')
            else:
                if print_games:
                    print(
                        f'No move was supplied. Player {3-player_number} wins the game.')
                return 2 - player_number
            game_state.scores[player_number -
                              1] = game_state.scores[player_number-1] + player_score
            if print_games:
                print(f'Reward: {player_score}')
                print(game_state)
        if game_state.scores[0] > game_state.scores[1]:
            return 0
        elif game_state.scores[0] == game_state.scores[1]:
            return 2
        elif game_state.scores[0] < game_state.scores[1]:
            return 1


def run_game(first_player_name, second_player_name, time_param, board_name, print_games=False):
    solve_sudoku_path = 'bin\\solve_sudoku.exe' if platform.system(
    ) == 'Windows' else 'bin/solve_sudoku'

    if board_name:
        board_text = Path(board_name).read_text()
    board = load_sudoku_from_text(board_text)

    module1 = importlib.import_module(first_player_name + '.sudokuai')
    module2 = importlib.import_module(second_player_name + '.sudokuai')
    player1 = module1.SudokuAI()
    player2 = module2.SudokuAI()
    player1.player_number = 1
    player2.player_number = 2
    if first_player_name in ('random_player', 'greedy_player', 'random_save_player'):
        player1.solve_sudoku_path = solve_sudoku_path
    if second_player_name in ('random_player', 'greedy_player', 'random_save_player'):
        player2.solve_sudoku_path = solve_sudoku_path

    # clean up files
    # Check if there actually is something
    if os.path.isfile(os.path.join(os.getcwd(), '-1.pkl')):
        os.remove(os.path.join(os.getcwd(), '-1.pkl'))
    # Check if there actually is something
    if os.path.isfile(os.path.join(os.getcwd(), '1.pkl')):
        os.remove(os.path.join(os.getcwd(), '1.pkl'))
    # Check if there actually is something
    if os.path.isfile(os.path.join(os.getcwd(), '2.pkl')):
        os.remove(os.path.join(os.getcwd(), '2.pkl'))

    return simulate_game(board, player1, player2, solve_sudoku_path=solve_sudoku_path, calculation_time=time_param, print_games=print_games)


def run_experiment(first_player_name, second_player_name, time_param, board_name, run_experiment_times, out_file, print_games=False):

    stats = [0, 0, 0]
    for i in tqdm(range(run_experiment_times)):
    # for i in range(run_experiment_times):
        if i < (run_experiment_times // 2): 
            stats[run_game(first_player_name, second_player_name,
                        time_param, board_name, print_games)] += 1
        else:
            result = run_game(second_player_name, first_player_name,
                        time_param, board_name, print_games)
            if result == 0:
                stats[1] += 1
            elif result == 1:
                stats[0] += 1
            else:
                stats[2] += 1
        print(first_player_name, 'against_player', second_player_name, 'time:',
          time_param, 'board_name:', board_name)
        print('wins:', stats[0] / (i + 1), 'losses:', stats[1] /
        (i + 1), 'draws:', stats[2] / (i + 1))
    print(first_player_name, 'against_player', second_player_name, 'time:',
          time_param, 'board_name:', board_name, file=out_file)
    print('wins:', stats[0] / run_experiment_times, 'losses:', stats[1] /
          run_experiment_times, 'draws:', stats[2] / run_experiment_times, file=out_file)
    print(file=out_file)

    return


if __name__ == '__main__':

    first_player_name = 'team30_A3'

    # f = open("output3b.txt", "w")
    
    # board_names = ['boards/empty-3x3.txt']
    
    # second_players  = ['team30_A1']
    
    # times = [0.1, 0.5, 1.0]

    # print_games = False

    # run_experiment_times = 10

    # for second_player_name in second_players:
    #     for time_param in times:
    #         for board_name in board_names:
    #             run_experiment(first_player_name, second_player_name,
    #                            time_param, board_name, run_experiment_times, f, print_games)


    # board_names = ['boards/empty-3x3.txt', 'boards/random-3x4.txt', 'boards/random-4x4.txt']
    
    # second_players  = ['team30_A1']
    
    # times = [5.0]

    # print_games = False

    # run_experiment_times = 10

    # for second_player_name in second_players:
    #     for time_param in times:
    #         for board_name in board_names:
    #             run_experiment(first_player_name, second_player_name,
    #                            time_param, board_name, run_experiment_times, f, print_games)

    # f.close()
    


    f = open("output.txt", "w")

    second_players  = ['greedy_player', 'team30_A2']

    times = [0.1, 0.5, 1.0, 5.0]

    board_names = ['boards/empty-3x3.txt', 'boards/easy-2x2.txt', 'boards/easy-3x3.txt', 
    'boards/hard-3x3.txt', 'boards/random-2x3.txt', 'boards/random-3x3.txt', 'boards/random-3x4.txt', 'boards/random-4x4.txt']

    print_games = False

    run_experiment_times = 10

    for time_param in times:
        for second_player_name in second_players:
            for board_name in board_names:
                run_experiment(first_player_name, second_player_name,
                               time_param, board_name, run_experiment_times, f, print_games)
                f.flush()

    f.close()

    # f = open("output1.txt", "w")

    # second_players  = ['greedy_player']

    # times = [1000.0]

    # board_names = ['boards/easy-2x2.txt', 'boards/easy-3x3.txt', 
    # 'boards/hard-3x3.txt', 'boards/random-2x3.txt', 'boards/random-3x3.txt', 'boards/random-3x4.txt', 'boards/random-4x4.txt']

    # print_games = False

    # run_experiment_times = 10

    # for time_param in times:
    #     for second_player_name in second_players:
    #         for board_name in board_names:
    #             run_experiment(first_player_name, second_player_name,
    #                            time_param, board_name, run_experiment_times, f, print_games)

    # f.close()
