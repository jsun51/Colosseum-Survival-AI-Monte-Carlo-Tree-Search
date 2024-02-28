# MCTS agent for Colosseum Survival
# Implemented by Justin Sun
from agents.agent import Agent
from store import register_agent
import sys
import numpy as np
from copy import deepcopy
import time
from collections import defaultdict
import math

class MonteCarloTreeSearchNode():
    def __init__(self, chess_board=None, my_pos=None, adv_pos=None, max_step=None, parent=None, parent_action=None):

        self.chess_board = chess_board
        self.my_pos=my_pos
        self.adv_pos=adv_pos
        self.max_step=max_step
        self.parent = parent
        self.parent_action = parent_action
        self.children = []
        self._number_of_visits = 0
        self._results = defaultdict(int)
        self._results[1] = 0
        self._results[0] = 0
        self._results[-1] = 0
        self._untried_actions = None
        self._untried_actions = self.untried_actions(self.chess_board, self.my_pos, self.adv_pos)
        self.board_size = len(chess_board)
        return

    def check_valid_step(self, chess_board, max_step, adv_pos, start_pos, end_pos, barrier_dir):
        # Endpoint already has barrier or is border
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        r, c = end_pos

        if not (0 <= r < len(chess_board) and 0 <= c < len(chess_board)):
            return False
        if chess_board[r, c, barrier_dir]:
            return False
        if np.array_equal(start_pos, end_pos):
            return True

        # BFS
        state_queue = [(start_pos, 0)]
        visited = {tuple(start_pos)}
        is_reached = False
        while state_queue and not is_reached:
            cur_pos, cur_step = state_queue.pop(0)
            r, c = cur_pos
            if cur_step == max_step:
                break
            for dir, move in enumerate(moves):
                if chess_board[r, c, dir]:
                    continue

                next_pos = (cur_pos[0] + move[0], cur_pos[1] + move[1])
                if np.array_equal(next_pos, adv_pos) or tuple(next_pos) in visited:
                    continue
                if np.array_equal(next_pos, end_pos):
                    is_reached = True
                    break

                visited.add(tuple(next_pos))
                state_queue.append((next_pos, cur_step + 1))

        return is_reached
    
    def untried_actions(self, chess_board, my_pos, adv_pos):
        possible_steps = []
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        state_queue = [(my_pos, 0)]
        visited = {tuple(my_pos)}
        while state_queue:
            cur_pos, cur_step = state_queue.pop(0)
            r, c = cur_pos

            for wallDir in range(0, 4):
                if chess_board[r, c, wallDir] == 0:
                    possible_steps.append((cur_pos, wallDir))

            if cur_step == self.max_step:
                break
            for dir, move in enumerate(moves):
                if chess_board[r, c, dir]:
                    continue

                next_pos = (cur_pos[0] + move[0], cur_pos[1] + move[1])
                if np.array_equal(next_pos, adv_pos) or tuple(next_pos) in visited:
                    continue

                visited.add(tuple(next_pos))

                state_queue.append((next_pos, cur_step + 1))
        return possible_steps

    # Expansion function
    # Finds all the possible steps within the max step range given an initial state
    # returns list of possible steps that are tuples ((x,y), dir)
    #def untried_actions(self, chess_board, my_pos, adv_pos, max_step):
        #possible_steps = []
        #for delta_x in range(-max_step, max_step + 1):
            #for delta_y in range(-(max_step - abs(delta_x)), max_step - abs(delta_x) + 1):
                #for dir in range(0, 4):
                    #move = ((my_pos[0] + delta_x, my_pos[1] + delta_y), dir)
                    #if self.check_valid_step(chess_board, max_step, adv_pos, my_pos, move[0], move[1]):
                        #possible_steps.append(move)
                    ##     print(f"Move {move} is valid")
                    ## else:
                    ##     print(f"Move {move} is invalid")
        #return possible_steps
    
    # Number of wins for UCT calculation    
    def q(self):
        return self._results[1] - self._results[-1]
    
    # Number of visits for UCT Calculation
    def n(self):
        return self._number_of_visits
    
    # Copied from world.py, used to make moves in the simulation
    # Modified slightly to work on a copy of the chessboard and returns the modified chessboard for child nodes
    def set_barrier(self, chess_board, r, c, dir):
        # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))

        # Opposite Directions
        opposites = {0: 2, 1: 3, 2: 0, 3: 1}

        # Board copy
        board_copy = deepcopy(chess_board)

        # Set the barrier to True
        board_copy[r, c, dir] = True
        # Set the opposite barrier to True
        move = moves[dir]
        board_copy[r + move[0], c + move[1], opposites[dir]] = True

        return board_copy
    
    def penalize(self, num):
        self._results[-1] += num
    
    # Next board is the result of taking a move/action on the current board
    # The corresponding child node for this next board is contructed, added to the current nodes children list, and returned
    def expand(self):
        move = self._untried_actions.pop()
        next_board = self.set_barrier(self.chess_board, move[0][0], move[0][1], move[1])
        child_node = MonteCarloTreeSearchNode(next_board, move[0], self.adv_pos, self.max_step, parent=self, parent_action=move)

        #Penalize a node heavily if it is surrpunded by three walls
        walls = 0
        for i in range(4):
            if next_board[move[0][0]][move[0][1]][i]:
                walls += 1
        if walls == 3:
            child_node.penalize(20)

        self.children.append(child_node)
        return child_node 

    def check_endgame(self, chess_board, my_pos, adv_pos):
        """
        Check if the game ends and compute the current score of the agents.
        Copied from world.py, modified to return 0, 1, or -1 depending on tie, we win, or adversary wins

        Returns
        -------
        is_endgame : bool
            Whether the game ends.
        utility : int
            0, 1, or -1 depending on tie, we win, adversary wins
        """
         # Moves (Up, Right, Down, Left)
        moves = ((-1, 0), (0, 1), (1, 0), (0, -1))
        # Union-Find
        father = dict()
        for r in range(self.board_size):
            for c in range(self.board_size):
                father[(r, c)] = (r, c)

        def find(pos):
            if father[pos] != pos:
                father[pos] = find(father[pos])
            return father[pos]

        def union(pos1, pos2):
            father[pos1] = pos2

        for r in range(self.board_size):
            for c in range(self.board_size):
                for dir, move in enumerate(
                    moves[1:3]
                ):  # Only check down and right
                    if chess_board[r, c, dir + 1]:
                        continue
                    pos_a = find((r, c))
                    pos_b = find((r + move[0], c + move[1]))
                    if pos_a != pos_b:
                        union(pos_a, pos_b)

        for r in range(self.board_size):
            for c in range(self.board_size):
                find((r, c))
        p0_r = find(tuple(my_pos))
        p1_r = find(tuple(adv_pos))
        p0_score = list(father.values()).count(p0_r)
        p1_score = list(father.values()).count(p1_r)
        if p0_r == p1_r:
            return False, None
        utility = None
        if p0_score > p1_score:
            utility = 1  # we win
        elif p0_score < p1_score:
            utility = -1 # adv wins
        else:
            utility = 0  # Tie
        
        return True, utility
    
    # Check if the game is over, if it is, then we are at a leaf
    def is_leaf_node(self):
        game_over, utility = self.check_endgame(self.chess_board, self.my_pos, self.adv_pos)
        return game_over
    
    # Check if node still have moves it can make or not
    def is_fully_expanded(self):
        return len(self._untried_actions) == 0
    
    # Best child out of a fully expanded nodes children array based on UCT formula
    def best_child(self, c_param=0.1):
        choices_weights = [(c.q() / c.n()) + c_param * np.sqrt((2 * np.log(self.n()) / c.n())) for c in self.children]
        return self.children[np.argmax(choices_weights)]
    
    # Tree policy for selection of a node to simulate, fully expands a node before using UCT to pick the best child
    def tree_policy(self):
        cur_node = self

        while not cur_node.is_leaf_node():
            if not cur_node.is_fully_expanded():
                return cur_node.expand()
            else:
                cur_node = cur_node.best_child()
        
        return cur_node
    
    # Default policy for simulation, randomly select a move from the possible moves
    def default_policy(self, possible_moves):
        return possible_moves[np.random.randint(len(possible_moves))]
    
    def simulate(self):
        cur_chess_board = self.chess_board
        cur_pos = self.my_pos
        cur_adv_pos = self.adv_pos

        game_over, utility = self.check_endgame(cur_chess_board, cur_pos, cur_adv_pos)
        while not game_over:
            my_moves = self.untried_actions(cur_chess_board, cur_pos, cur_adv_pos)
            move = self.default_policy(my_moves)
            cur_chess_board = self.set_barrier(cur_chess_board, move[0][0], move[0][1], move[1])
            cur_pos = move[0]

            game_over, utility = self.check_endgame(cur_chess_board, cur_pos, cur_adv_pos)
            if game_over:
                break
            
            adv_moves = self.untried_actions(cur_chess_board, cur_adv_pos, cur_pos)
            move = self.default_policy(adv_moves)
            cur_chess_board = self.set_barrier(cur_chess_board, move[0][0], move[0][1], move[1])
            cur_adv_pos = move[0]

            game_over, utility = self.check_endgame(cur_chess_board, cur_pos, cur_adv_pos)
            if game_over:
                break

        return utility
    
    # Recursively updates all nodes until root node is reached
    # Results is a dictionary of the utility values [-1,0,1] 
    def backpropagate(self, utility):
        self._number_of_visits += 1.
        self._results[utility] += 1.
        if self.parent:
            self.parent.backpropagate(utility)

    # Getter for the move resulting in the best child
    def get_move(self):
        return self.parent_action
    
    # Find the best move by using the tree policy to select and expand, then simulate, and backpropagate the result
    # Keep simluating for 1.8s to stay under the time limit
    # Fully exploratory (c_param = 0), could play with this more... 
    def find_best_move(self, start_time):
        while (time.time() - start_time) < 1.8:
            selected_node = self.tree_policy()
            utility = selected_node.simulate()
            selected_node.backpropagate(utility)

        return self.best_child(c_param=0).get_move()




@register_agent("mcts_agent")
class MCTSAgent(Agent):
    """
    A dummy class for your implementation. Feel free to use this class to
    add any helper functionalities needed for your agent.
    """

    

    def __init__(self):
        super(StudentAgent, self).__init__()
        self.name = "StudentAgent"
        self.dir_map = {
            "u": 0,
            "r": 1,
            "d": 2,
            "l": 3,
        }

    def step(self, chess_board, my_pos, adv_pos, max_step):
        """
        Implement the step function of your agent here.
        You can use the following variables to access the chess board:
        - chess_board: a numpy array of shape (x_max, y_max, 4)
        - my_pos: a tuple of (x, y)
        - adv_pos: a tuple of (x, y)
        - max_step: an integer

        You should return a tuple of ((x, y), dir),
        where (x, y) is the next position of your agent and dir is the direction of the wall
        you want to put on.

        Please check the sample implementation in agents/random_agent.py or agents/human_agent.py for more details.
        """
        
        # Some simple code to help you with timing. Consider checking 
        # time_taken during your search and breaking with the best answer
        # so far when it nears 2 seconds.
        root = MonteCarloTreeSearchNode(chess_board, my_pos, adv_pos, max_step)
        start_time = time.time()
        move = root.find_best_move(start_time)
        

        # dummy return
        return move[0], move[1]
"""
High level outline:

Expansion function(state at node):
- Loops through all possible steps in max step range
- Calls check_valid_step

Evaluation function:
- Number of possible steps in a state
    - Equal to territory size plus extras from wall placement in endgame

"""
