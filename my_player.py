# Authors: Émile Watier (2115718) and Lana Pham (2116078)
import math
import random
from typing import List, Union

from game_state_abalone import GameStateAbalone
from player_abalone import PlayerAbalone
from seahorse.game.action import Action

cutoff_depth = 2
infinity = math.inf
center = (8, 4)
max_line_length = 9
nb_piece_colors = 2
coordinates_in_same_row = [((-1, -1), (1, 1)), ((-2, 0), (2, 0)), ((-1, 1), (1, -1))]
overflow_coordinates = {(-1, -1): (-2, -2), (-2, 0): (-4, 0), (-1, 1): (-2, 2), (1, 1): (2, 2), (2, 0): (4, 0),
                        (1, -1): (2, -2)}


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
        self.other_player = 'W' if self.get_piece_type() == 'B' else 'B'
        self.transposition_table = TranspositionTable()

    def compute_action(self, current_state: GameStateAbalone, **kwargs) -> Action:
        """
        Function to implement the logic of the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """

        score, action = self.minimax_search(current_state)

        return action

    def minimax_search(self, initial_state: GameStateAbalone):
        return self.max_value(initial_state, -infinity, infinity, 0)

    def max_value(self, state: GameStateAbalone, alpha: float, beta: float, depth: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        if self.cutoff_depth(depth, state):
            return self.heuristic(state), None

        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table and self.transposition_table.hash_table[hash]['depth'] <= depth:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash][
                'action']

        score = -infinity
        action = None

        actions = state.get_possible_actions() if state.step <= 10 else self.get_sorted_actions(state)

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

    def min_value(self, state: GameStateAbalone, alpha: float, beta: float, depth: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        if self.cutoff_depth(depth, state):
            return self.heuristic(state), None

        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table and self.transposition_table.hash_table[hash]['depth'] <= depth:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash][
                'action']

        score = infinity
        action = None

        actions = state.get_possible_actions() if state.get_step() <= 5 else self.get_sorted_actions(state)

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

    def get_sorted_actions(self, state: GameStateAbalone):
        pieces_difference = self.pieces_alive(state, self.id) - self.pieces_alive(state, self.other_player)

        actions = state.get_possible_actions()

        larger_difference_actions = []
        equal_difference_actions = []
        lesser_difference_actions = []

        for new_action in actions:
            new_state = new_action.current_game_state
            new_pieces_differences = self.pieces_alive(new_state, self.id) - self.pieces_alive(new_state,
                                                                                               self.other_player)
            if new_pieces_differences > pieces_difference:
                larger_difference_actions.append(new_action)
            elif new_pieces_differences == pieces_difference:
                equal_difference_actions.append(new_action)
            else:
                lesser_difference_actions.append(new_action)
        return larger_difference_actions + equal_difference_actions + lesser_difference_actions

    def cutoff_depth(self, current_depth, state: GameStateAbalone):
        # TODO : déterminer un depth
        if 50 - state.step < cutoff_depth:
            return current_depth > 50 - state.step
        return current_depth > cutoff_depth

    def heuristic(self, state):
        score = 0
        score += self.distance_to_center_heuristic(state, self.other_player) - self.distance_to_center_heuristic(state,
                                                                                                                 self.piece_type)
        score += (self.pieces_alive(state, self.piece_type) - self.pieces_alive(state, self.other_player)) * 1000
        score += (self.pieces_together_heuristic(state, self.piece_type) - self.pieces_together_heuristic(state,
                                                                                                  self.other_player))
        return score

    def distance_to_center_heuristic(self, state: GameStateAbalone, piece_type: str):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.piece_type == piece_type:
                score += self.euclidian_distance_to_center(key)
        return score

    def pieces_together_heuristic(self, state: GameStateAbalone, piece_type: str):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.piece_type == piece_type:
                for row_coordinates in coordinates_in_same_row:
                    piece1 = state.get_rep().env.get(tuple(x - y for x, y in zip(key, row_coordinates[0])))
                    piece2 = state.get_rep().env.get(tuple(x - y for x, y in zip(key, row_coordinates[1])))

                    player_is_piece1_owner = piece1 and piece1.piece_type == piece_type
                    player_is_piece2_owner = piece2 and piece2.piece_type == piece_type
                    if player_is_piece1_owner and player_is_piece2_owner:
                        score += 2
                        piece3 = state.get_rep().env.get(tuple(x - y for x, y in zip(key, overflow_coordinates.get(row_coordinates[0]))))
                        piece4 = state.get_rep().env.get(tuple(x - y for x, y in zip(key, overflow_coordinates.get(row_coordinates[1]))))

                        player_is_piece3_owner = piece3 and piece3.piece_type == piece_type
                        player_is_piece4_owner = piece4 and piece4.piece_type == piece_type
                        if player_is_piece3_owner:
                            score -= 1
                        if player_is_piece4_owner:
                            score -= 1

                    elif player_is_piece1_owner or player_is_piece2_owner:
                        score += 1

        return score

    def euclidian_distance_to_center(self, position: tuple[int, int]):
        return self.euclidian_distance(position, center)

    def euclidian_distance(self, position1: tuple[int, int], position2: tuple[int, int]):
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def pieces_alive(self, state, piece_type):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.piece_type == piece_type:
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
