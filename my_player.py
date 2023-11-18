# Authors: Émile Watier (2115718) and Lana Pham (2116078)
import math
import random
from typing import List, Union

from player_abalone import PlayerAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState

infinity = math.inf
center = (8, 4)
max_line_length = 9
nb_piece_colors = 2
coordinates_in_same_row = [((-1, -1), (1, 1)), ((-2, 0), (2, 0)), ((-1, 1), (1, -1))]


class MyPlayer(PlayerAbalone):
    """
    Player class for Abalone game.

    Attributes:
        piece_type (str): piece type of the player
    """

    def __init__(self, piece_type: str, name: str = "bob", time_limit: float = 60 * 15, *args) -> None:
        """
        Initialize the PlayerAbalone instance.

        Args:
            piece_type (str): Type of the player's game piece
            name (str, optional): Name of the player (default is "bob")
            time_limit (float, optional): the time limit in (s)
        """
        super().__init__(piece_type, name, time_limit, *args)
        self.number_of_actions = 0
        self.other_player = None
        self.transposition_table = TranspositionTable()

    def compute_action(self, current_state: GameState, **kwargs) -> Action:
        """
        Function to implement the logic of the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """

        self.other_player = next(player for player in current_state.players if player.get_id() != self.id).get_id()
        score, action = self.minimax_search(current_state)
        self.number_of_actions += 1
        return action

    def minimax_search(self, initial_state: GameState):
        return self.max_value(initial_state, -infinity, infinity, 0)

    def max_value(self, state: GameState, alpha: float, beta: float, depth: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        if self.cutoff_depth(depth):
            return self.heuristic(state), None

        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash]['action']

        score = -infinity
        action = None

        actions = state.get_possible_actions() if self.number_of_actions <= 5 else self.get_sorted_actions(state)

        for new_action in actions:
            new_state = new_action.get_next_game_state()
            new_score, _ = self.min_value(new_state, alpha, beta, depth + 1)

            if new_score > score:
                score = new_score
                action = new_action
                alpha = max(alpha, score)

            if score >= beta:
                break

        self.transposition_table.record(hash, score, action, depth)
        return score, action

    def min_value(self, state: GameState, alpha: float, beta: float, depth: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        if self.cutoff_depth(depth):
            return self.heuristic(state), None


        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash]['action']

        score = infinity
        action = None

        actions = state.get_possible_actions() if self.number_of_actions <= 5 else self.get_sorted_actions(state)

        for new_action in actions:
            new_state = new_action.get_next_game_state()
            new_score, _ = self.max_value(new_state, alpha, beta, depth + 1)

            if new_score < score:
                score = new_score
                action = new_action
                beta = min(beta, score)

            if score <= alpha:
                break
            
        self.transposition_table.record(hash, score, action, depth)
        return score, action

    def get_sorted_actions(self, state: GameState):
        pieces_difference = self.pieces_alive(state, self.id) - self.pieces_alive(state, self.other_player)

        actions = state.get_possible_actions()

        larger_difference_actions = []
        equal_difference_actions = []
        lesser_difference_actions = []

        for new_action in actions:
            new_pieces_differences = self.pieces_alive(state, self.id) - self.pieces_alive(state, self.other_player)
            if new_pieces_differences > pieces_difference:
                larger_difference_actions.append(new_action)
            elif new_pieces_differences == pieces_difference:
                equal_difference_actions.append(new_action)
            else:
                lesser_difference_actions.append(new_action)
        return larger_difference_actions + equal_difference_actions + lesser_difference_actions

    def cutoff_depth(self, depth):
        # TODO : déterminer un depth
        return depth > 2

    def heuristic(self, state):
        score = 0
        score += self.distance_to_center_heuristic(state, self.other_player) - self.distance_to_center_heuristic(state,
                                                                                                                 self.id)
        score += self.pieces_alive(state, self.id) - self.pieces_alive(state, self.other_player)
        return score

    def distance_to_center_heuristic(self, state: GameState, player_id: int):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.owner_id == player_id:
                score += self.euclidian_distance_to_center(key)
        return score

    def euclidian_distance_to_center(self, position: tuple[int, int]):
        return ((position[0] - center[0]) ** 2 + (position[1] - center[1]) ** 2) ** 0.5

    def pieces_alive(self, state, player_id):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.owner_id == player_id:
                score += 10
        return score

    def other_player_has_more_pieces(self, state):
        return self.pieces_alive(state, self.other_player) > self.pieces_alive(state, self.id)

    def other_player_has_as_much_pieces(self, state):
        return self.pieces_alive(state, self.other_player) == self.pieces_alive(state, self.id)


class TranspositionTable:
    def __init__(self):
        self.hash_table = {}
        self.zobrist_hash_keys = [
            [
                [random.randint(1, 2 ** (max_line_length ** 2) - 1) for _ in range(nb_piece_colors)]
                for _ in range(max_line_length)
            ]
            for _ in range(max_line_length)
        ]

    def indexing(self, piece: Union[int, str]):
        if piece == 'W':
            return 0
        elif piece == 'B':
            return 1
        else:
            return -1

    def compute_hash(self, board: List[List[Union[int, str]]]):
        hash = 0

        for i in range(max_line_length):
            for j in range(max_line_length):
                if type(board[i][j]) == int:
                    continue
                piece = self.indexing(board[i][j])
                hash ^= self.zobrist_hash_keys[i][j][piece]

        return hash

    def record(self, hash, score, action, depth):
        if hash not in self.hash_table:
            self.hash_table[hash] = {}

        self.hash_table[hash]['score'] = score
        self.hash_table[hash]['action'] = action
        self.hash_table[hash]['depth'] = depth

    def to_json(self):
        return {}
