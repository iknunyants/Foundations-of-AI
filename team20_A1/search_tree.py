from competitive_sudoku.sudoku import Move, SudokuBoard, TabooMove
from team20_A1.legal_moves import compute_legal_moves
from team20_A1.evaluation import evaluate
import copy


class Node:
    """
    Class Node represents the node of the decision tree for the game.
    It has next properties:

    Used during initialization:
    * depth (int) - the depth of the node. The root (initial state) is the current situation,
    * board (SudokuBoard) - the board before the move done and the initial board of of the situation for the root.
    * move (Move) - the move done to come to the current Node (None for the root)
    * points (float) - the number of points player who's turn it is gets from the move

    Other:
    * score (float) - the score the AI agent gets (calculated from the leaf to the root)
    * children (list of Nodes) - the list of child-nodes, related with next possible moves
    """

    def __init__(self, parent_board: SudokuBoard, depth: int = 0, move: Move = None, points: float = 0):
        self.depth = depth  # depth of the tree, root depth = 0
        self.board = copy.deepcopy(parent_board)
        if move is not None:
            self.board.put(i=move.i, j=move.j, value=move.value)  # board after move
        self.move = move  # move that leads to the state
        self.points = points  # point received after the move 
        self.score = None  # evaluation minimax score （minimax score）
        self.children = None # new Node does not have children after the initialization
 
    def add_children(self, taboo_moves: list):
        """
        The function that adds children to the Node if it is not yet processed
        给树结点加子结点

        @param taboo_moves - the list of taboo moves
        @return None - the function modifies the target node's children property
        """

        # check if Node has not been processed yet
        # check not processed or not
        if self.children is None:

            # add children as all legal moves for the current state of the game (represented as the board)
            # 所有的legal move
            legal_moves = compute_legal_moves(self.board, taboo_moves)
            
            #
            self.children = [Node(parent_board=self.board, 
                                    depth=self.depth + 1, move=x_move,
                                    points=evaluate(move=x_move, current_board=self.board)) 
                                    for x_move in legal_moves]

    def add_level(self, taboo_moves: list, target_depth: int) -> None:

        """
        Function, that calls for all leaf nodes 
        the function that produce children 
        (expanding the tree to one more possible level)
        @param taboo_moves - taboo_moves - the list of taboo moves
        @param target_depth - the target depth of tree expansion 树扩张的目标深度
        @return: None - the function modifies the tree properties
        """

        # check if the Node is a non-processed leaf. If it is a non-processed leaf, try to get children
        # check node have child or not
        if (self.children is None) and (self.depth < target_depth):
            self.add_children(taboo_moves)

        # if it is not a non-processed leaf and not a processed leaf (with zero-children), run the function
        # recursively for the children
        
        if (self.children is not None) and (len(self.children) > 0) and (self.depth < target_depth):
            
            #iteration 
            for child in self.children:
                child.add_level(taboo_moves, target_depth)

    def update_score(self):
        """
        A minimax function for the tree, that upwards from the leaves updates the score 
        (difference between points agent AI gets and the opponent gets). 
        All nodes located on the even levels (except root) represents the moves
        that gives points to the opponent (negative scores, to maximize as for the agent), 
        all nodes on the odd levels represents the moves that gives points to the AI agent 
        (positive scores, to minimize as for the opponent).
        

        minimax function
        odd layer my score positive min
        even layer opponent score negative max

        @return:
        """

        # initial instruction (for leaves)
        # no child or child len=0 -> 
        if (self.children is None) or (len(self.children) == 0):
            self.score = self.points * ((-1) ** (self.depth + 1))

        # recursive part of calculation
        else:

            # opponents turn -> max of the children
            if self.depth % 2 == 0:
                scores = []
                for x in self.children:
                    x.update_score()
                    scores.append(x.score)
                # the new score calculated as the least of the children (positive difference for opponent)
                self.score = max(scores) + self.points * ((-1) ** (self.depth + 1))
            # agent's turn -> min of the children
            else:
                scores = []
                for x in self.children:
                    x.update_score()
                    scores.append(x.score)
                # the new score calculated as the most of the children (positive difference for AI agent)
                self.score = min(scores) + self.points * ((-1) ** (self.depth + 1))

    def best_move(self):
        """
        Function that basically returns the Node related with the best move according to the score
        :@return - best_move, object of class Move (as the property of Node object)
        """
        best_moves = [x for x in self.children if x.score == self.score]
        return best_moves[0].move
