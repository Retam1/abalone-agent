# Authors: Émile Watier (2115718) and Lana Pham (2116078)
import math
import random
from typing import List, Union

from game_state_abalone import GameStateAbalone
from player_abalone import PlayerAbalone
from seahorse.game.action import Action

CUTOFF_DEPTH = 2
INFINITY = math.inf
CENTER = (8, 4)
MAX_LINE_LENGTH = 9
NB_PIECE_COLORS = 2
COORDINATES_IN_SAME_ROW = [((-1, -1), (1, 1)), ((-2, 0), (2, 0)), ((-1, 1), (1, -1))]


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
        return self.max_value(initial_state, -INFINITY, INFINITY, 0)

    def max_value(self, state: GameStateAbalone, alpha: float, beta: float, depth: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        if self.cutoff_depth(depth):
            return self.heuristic(state), None

        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table and self.transposition_table.hash_table[hash]['depth'] <= depth:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash][
                'action']

        score = -INFINITY
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

        if self.cutoff_depth(depth):
            return self.heuristic(state), None

        hash = self.transposition_table.compute_hash(state.get_rep().get_grid())
        if hash in self.transposition_table.hash_table and self.transposition_table.hash_table[hash]['depth'] <= depth:
            return self.transposition_table.hash_table[hash]['score'], self.transposition_table.hash_table[hash][
                'action']

        score = INFINITY
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

    def cutoff_depth(self, current_depth: int):
        # TODO : déterminer un depth
        return current_depth > CUTOFF_DEPTH

    def heuristic(self, state: GameStateAbalone):
        score = 0
        score += self.distance_to_center_heuristic(state, self.other_player) - self.distance_to_center_heuristic(state,
                                                                                                                 self.piece_type)
        score += (self.pieces_alive(state, self.piece_type) - self.pieces_alive(state, self.other_player)) * 1000
        score += (self.pieces_together_heuristic(state, self.piece_type) - self.pieces_together_heuristic(state, self.piece_type))
        score += (self.pieces_in_a_row_heuristic(state, self.piece_type) - self.pieces_in_a_row_heuristic(state,
                                                                                                  self.other_player))
        return score

    def distance_to_center_heuristic(self, state: GameStateAbalone, piece_type: str):
        score = 0
        for coordinate, piece in state.get_rep().env.items():
            if piece.piece_type == piece_type:
                score += self.euclidian_distance_to_center(coordinate)
        return score

    def pieces_together_heuristic(self, state: GameStateAbalone, piece_type: str):
        number_of_pieces_around = 0
        coordinates = {coordinate for coordinate, piece in state.get_rep().env.items() if piece.piece_type == piece_type}

        for coordinate in coordinates:
            for row_coordinates in COORDINATES_IN_SAME_ROW:
                for coordinate_difference in row_coordinates:
                    if (piece := state.get_rep().env.get(self.calculate_neighbor_coordinate(coordinate, coordinate_difference))) and piece.piece_type == piece_type:
                        number_of_pieces_around += 1
        return number_of_pieces_around

    def pieces_in_a_row_heuristic(self, state: GameStateAbalone, piece_type: str):
        score = 0
        coordinates = {coordinate for coordinate, piece in state.get_rep().env.items() if piece.piece_type == piece_type}

        for coordinate in coordinates:
            for coordinate_in_same_row in COORDINATES_IN_SAME_ROW:
                coordinates_to_check = self.calculate_neighbor_coordinate(coordinate, coordinate_in_same_row[0]), \
                                        self.calculate_neighbor_coordinate(coordinate, coordinate_in_same_row[1])

                if coordinates_to_check[0] in coordinates and coordinates_to_check[1] in coordinates:
                    score += 2
                    outer_coordinates_to_check = self.calculate_neighbor_coordinate(coordinates_to_check[0], coordinate_in_same_row[0]), \
                                            self.calculate_neighbor_coordinate(coordinates_to_check[1], coordinate_in_same_row[1])

                    if outer_coordinates_to_check[0] in coordinates or outer_coordinates_to_check[1] in coordinates:
                        score -= 2

                elif coordinates_to_check[0] in coordinates or coordinates_to_check[1] in coordinates:
                    score += 1

        return score

    def calculate_neighbor_coordinate(self, coordinate: tuple[int, int], difference: tuple[int, int]):
        return coordinate[0] + difference[0], coordinate[1] + difference[1]

    def euclidian_distance_to_center(self, position: tuple[int, int]):
        return self.euclidian_distance(position, CENTER)

    def euclidian_distance(self, position1: tuple[int, int], position2: tuple[int, int]):
        return ((position1[0] - position2[0]) ** 2 + (position1[1] - position2[1]) ** 2) ** 0.5

    def pieces_alive(self, state, piece_type):
        score = 0
        for key, value in state.get_rep().env.items():
            if value.piece_type == piece_type:
                score += 10
        return score


class TranspositionTable:
    def __init__(self):
        self.hash_table = {}
        self.zobrist_hash_keys = [
            [
                [random.randint(1, 2 ** (MAX_LINE_LENGTH ** 2) - 1) for _ in range(NB_PIECE_COLORS)]
                for _ in range(MAX_LINE_LENGTH)
            ]
            for _ in range(MAX_LINE_LENGTH)
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

        for i in range(MAX_LINE_LENGTH):
            for j in range(MAX_LINE_LENGTH):
                if type(board[i][j]) == int:
                    continue
                piece = self.indexing(board[i][j])
                hash ^= self.zobrist_hash_keys[i][j][piece]

        return hash

    def record(self, hash: int, score: float, action: Action, depth: int):
        if hash not in self.hash_table:
            self.hash_table[hash] = {}

        self.hash_table[hash]['score'] = score
        self.hash_table[hash]['action'] = action
        self.hash_table[hash]['depth'] = depth

    def to_json(self):
        return {}
