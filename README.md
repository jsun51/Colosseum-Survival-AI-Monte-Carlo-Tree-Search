# Colosseum Survival!

<p align="center">
  <img src="https://cdn.britannica.com/36/162636-050-932C5D49/Colosseum-Rome-Italy.jpg?w=690&h=388&c=crop">
</p>

## The Game 
Colosseum Survival! is a 2-player turn-based strategy game in which two players move in an M x M chessboard and put barriers around them until they are separated in two closed zones. M can have a value between 6 and 12. Each player will try to maximize the number of blocks in its zone to win the game. Our solution can be found in agents/student_agent.py.

## Monte Carlo Tree Search
Monte Carlo tree search (MCTS) is a method for finding the best move
in a game that combines a tree policy that selects promising nodes to be
1
expanded with a default policy that simulates games starting from a node
to help estimate the utility of a move. Each time a simulation is completed,
the value of the node is updated based on whether the agent won or lost the
game, and the updated value is back-propagated to the parent nodes. Each
node tracks the number of games that begin from itself which have been
won, lost, or tied, whether simulated directly from the node itself or from a
child node expanded from it.
The tree policy combines the exploration of nodes with little information
about them and the exploitation of nodes that data from simulations
indicate to be of high utility. The following equation is used in the Upper Confidence Trees (UCT) method to
balance exploration and exploitation:
Q⊕(s, a) = Q(s, a) + c*sqrt[log n(s) / n(s, a)]. This is used to determine the next node to traverse to given the
current node s. Q(s, a) is the currently estimated value of taking an action
a given the state s; n(s, a) is the number of times we have taken the action
a from state s, and n(s) is the number of times we have visited state s,
regardless of the next action taken. The first term represents the value of
exploitation—it captures the currently estimated utility of selecting node a.
The second term represents the value of exploration, and becomes higher
when the number of times a has been visited from s is small compared to
the number of times s has been visited. c is used as a scaling factor: a
higher value increases the importance of exploration. The child node a with
the highest estimated utility after adjustment for exploration Q⊕(s, a) is the
next node to be traversed to.

## Implementation 

### Motivation 
Our agent for the Colosseum Survival game applies Monte Carlo Tree Search
(MCTS) to intelligently find moves. Because of MCTS’s ability to provide
insights into the long-term impacts of a move without exhaustively searching
through all possible moves, our agent provides fairly high performance in
games, beating the random agent nearly 100 percent of the time. The game’s
extensive branching factor, evident in the numerous potential moves on a
12x12 board, combined with our constraints of a 2-second time limit and
a 500 MB RAM cap, prompted us to choose Monte Carlo Tree Search.
Although the game is deterministic and fully observable, making it suitable
for approaches like minimax with alpha-beta pruning, using minimax would
demand a cutoff test or an evaluation function given our constraints and
the branching factor of the game. In contrast, Monte Carlo Tree Search
simulates full games randomly from possible next moves and backpropagates
the result, so we can pick the best move based on the win rate from the
simulations. This allows more focus on subtrees that have more promising
moves, eliminating the problem of the game’s high branching factor.

### Design and structure 
To implement MCTS in our project, we implemented a tree data structure
for the MCTS tree. Each node, representing a game state, has instance
variables that represent:  
**1.** The state of the chess board’s wall positions  
**2.** The positions of the student and adversary agents  
**3.** The node’s parent and children  
**4.** The number of games that have been won, lost, or tied  
**5.** The list of potential actions to be taken from the node that have not
yet been simulated and turned into child nodes  

Upon being launched, the student agent creates a root node using the
game state passed to it by the game engine, and calls the root node’s
find best move function. The find best move function operates in a loop
until a time limit of 1.8 seconds is reached. In each iteration, our tree policy
selects a node to simulate. Then, our default policy simulates the game to
the end by starting from that node and taking random moves on behalf of
both players until the end of the game is reached. The data from the simulation is then back-propagated throughout the tree.
Once the time limit is reached, the child with the highest ratio of wins to total games simulated is returned.
Our tree policy expands the first entry in the list of possible moves if the
node currently being considered has not yet been fully expanded. Otherwise,
it applies the UCT method, using Equation (1) with c = 0.1 to traverse to
the best child until it reaches a leaf node, upon which it returns the leaf
node, or it reaches a node that has not yet been fully expanded, upon which
a move in its list of possible moves is expanded. When a potential move is
expanded, it is taken off of the list of possible moves and a new child node
is created from it. New child nodes are automatically penalized with the
equivalent of 20 lost games if the player character is surrounded by 3 walls,
as such moves are likely to cause the player to lose from becoming trapped.
The generation of the list of possible next actions makes use of a function derived from the check valid step function from world.py, applying
breadth-first search to find all the positions the player can traverse to and
then iterating through all possible wall positions. The list of next possible
actions is generated upon the creation of a node and while games are being
simulated by the default policy.

## Result 
### Quantitative performance

Full quantitatve analysis can be found in "report/report.pdf".

### Other Approaches
In a previous iteration of the project, we attempted to use an agent with
a look-ahead level of only 2: the agent generates the list of possible moves
and evaluates each potential move a using the heuristic of the number of
possible moves starting from a, cutting evaluation short when a runtime of
1.5 seconds is reached. The heuristic has some value because, in the end
game, the size of a player’s territory corresponds to the number of positions
that it can move to if step limits are ignored.
The previous implementation had a low look-ahead and therefore was
unable to account for the long-term effects of moves. It also had a less
performant way of finding possible next moves: instead of running breadth
first search once to find all the possible moves, each position within the
max step radius was checked for validity by calling the breadth-first-search
based check valid step function a separate time, leading to redundancy.
The implementation was better than the random agent, beating it roughly
90% of the time, but performed poorly compared to the current MCTS
implementation.
 

## Potential Improvement 
Potential improvements to our MCTS Agent could be to look at the effect
of the c parameter on win-rate. This parameter dictates how much our
agent explores the game tree, expanding nodes that do not necessarily have
the highest win-rate, but haven’t been simulated as much. Our approach
currently favours exploitation heavily, that is, the c parameter is 0.1. In
the future, we would make a plot of win-rate versus c parameter and try
to find an optimal c parameter that balances exploitation and exploration.
Additionally, since a major weakness of our agent is the random default
policy, we could spend more time understanding the game itself to gather
good heuristics. We could then use these heuristics in our default policy
for move selection. Furthermore, we could also implement Rapid Action Value Estimation (RAVE) which would estimate the value of playing a move
immediately by looking at all the simulations where the move occurs. RAVE
assumes that only the move itself matters, which simplifies the state space
and thereby requiring fewer simulations to get good results. 

## Setup

To setup the game, clone this repository and install the dependencies:

```bash
pip install -r requirements.txt
```

## Playing a game

To start playing a game, we will run the simulator and specify which agents should complete against eachother. To start, several agents are given to you, and you will add your own following the same game interface. For example, to play the game using two copies of the provided random agent (which takes a random action every turn), run the following:

```bash
python simulator.py --player_1 random_agent --player_2 random_agent
```

This will spawn a random game board of size NxN, and run the two agents of class [RandomAgent](agents/random_agent.py). You will be able to see their moves in the console.

## Visualizing a game

To visualize the moves within a game, use the `--display` flag. You can set the delay (in seconds) using `--display_delay` argument to better visualize the steps the agents take to win a game.

```bash
python simulator.py --player_1 random_agent --player_2 random_agent --display
```

## Play on your own!

To take control of one side of the game and compete against the random agent yourself, use a [`human_agent`](agents/human_agent.py) to play the game.

```bash
python simulator.py --player_1 human_agent --player_2 random_agent --display
```

## Autoplaying multiple games

There is some randomness (coming from the initial game setup and potentially agent logic), so go fairly evaluate agents, we will run them against eachother multiple times, alternating their roles as player_1 and player_2, and on boards are drawn randomly (between size 6 and 12). The aggregate win % will determine a fair winner. Use the `--autoplay` flag to run $n$ games sequentially, where $n$ can be set using `--autoplay_runs`.

```bash
python simulator.py --player_1 random_agent --player_2 random_agent --autoplay
```

During autoplay, boards are drawn randomly between size `--board_size_min` and `--board_size_max` for each iteration. You may try various ranges for your own information and development by providing these variables on the command-line. However, the defaults (to be used during grading) are 6 and 12, so ensure the timing limits are satisfied for every board in this size range. 

**Notes**

- Not all agents supports autoplay. The variable `self.autoplay` in [Agent](agents/agent.py) can be set to `True` to allow the agent to be autoplayed. Typically this flag is set to false for a `human_agent`.
- UI display will be disabled in an autoplay.


## Full API

```bash
python simulator.py -h       
usage: simulator.py [-h] [--player_1 PLAYER_1] [--player_2 PLAYER_2]
                    [--board_size BOARD_SIZE] [--display]
                    [--display_delay DISPLAY_DELAY]

optional arguments:
  -h, --help            show this help message and exit
  --player_1 PLAYER_1
  --player_2 PLAYER_2
  --board_size BOARD_SIZE
  --display
  --display_delay DISPLAY_DELAY
  --autoplay
  --autoplay_runs AUTOPLAY_RUNS
```

## About

This is a class project for COMP 424, McGill University, Fall 2023 (it was originally forked with the permission of Jackie Cheung).
Contributors: Jerry Hou-Liu

## License

[MIT](LICENSE)
