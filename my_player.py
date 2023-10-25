# Authors: Émile Watier (2115718) and Lana Pham (2116078)
import sys

from player_abalone import PlayerAbalone
from seahorse.game.action import Action
from seahorse.game.game_state import GameState
from seahorse.utils.custom_exceptions import MethodNotImplementedError


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

    def compute_action(self, current_state: GameState, **kwargs) -> Action:
        """
        Function to implement the logic of the player.

        Args:
            current_state (GameState): Current game state representation
            **kwargs: Additional keyword arguments

        Returns:
            Action: selected feasible action
        """
        # TODO
        score, action = self.minimax_search(current_state)
        return action

    def minimax_search(self, initial_state: GameState):
        return self.max_value(initial_state, -sys.maxsize - 1, sys.maxsize)

    def max_value(self, state: GameState, alpha: int, beta: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        score = -sys.maxsize - 1
        action = None

        for new_action in state.get_possible_actions():
            new_state = new_action.get_next_game_state()
            new_score, _ = self.min_value(new_state, alpha, beta)

            if new_score > score:
                score = new_score
                action = new_action
                alpha = max(alpha, score)

            if score >= beta:
                return score, action

        return score, action

    def min_value(self, state: GameState, alpha: int, beta: int):
        if state.is_done():
            return state.get_scores().get(state.get_next_player().get_id()), None

        score = sys.maxsize
        action = None

        for new_action in state.get_possible_actions():
            new_state = new_action.get_next_game_state()
            new_score, _ = self.max_value(new_state, alpha, beta)

            if new_score < score:
                score = new_score
                action = new_action
                beta = min(beta, score)

            if score <= alpha:
                return score, action

        return score, action
