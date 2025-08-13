"""
Some example classes for people who want to create a homemade bot.

With these classes, bot makers will not have to implement the UCI or XBoard interfaces themselves.
"""

import chess
from chess.engine import PlayResult, Limit
import random
from lib.engine_wrapper import MinimalEngine
from lib.types import MOVE, HOMEMADE_ARGS_TYPE
import logging
from collections import deque


# Use this logger variable to print messages to the console or log files.
# logger.info("message") will always print "message" to the console or log file.
# logger.debug("message") will only print "message" if verbose logging is enabled.
logger = logging.getLogger(__name__)


class ExampleEngine(MinimalEngine):
    """An example engine that all homemade engines inherit."""

    pass


# Bot names and ideas from tom7's excellent eloWorld video


class Sciasa(ExampleEngine):
    def evaluate_board(self, board: chess.Board) -> int:
        """
        Simple evaluation function based on material balance.
        Positive score favors white; negative favors black.
        """
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
        }
        score = 0
        for piece_type in piece_values:
            score += (
                len(board.pieces(piece_type, chess.WHITE))
                * piece_values[piece_type]
            )
            score -= (
                len(board.pieces(piece_type, chess.BLACK))
                * piece_values[piece_type]
            )
        return score

    def search(
        self, board: chess.Board, *args: "HOMEMADE_ARGS_TYPE"
    ) -> "PlayResult":
        """
        Breadth-First Search (BFS) implementation for chess move evaluation.
        """
        # Default depth to 1 if no depth argument is provided
        depth = 2
        if args and isinstance(args[0], int):
            depth = args[0]

        # BFS queue: (board, depth, move leading to this state)
        queue = deque(
            [(board.copy(), 0, None)]
        )  # (current board, current depth, leading move)
        best_move = None
        best_evaluation = (
            float('-inf') if board.turn else float('inf')
        )  # Maximize for white, minimize for black

        while queue:
            current_board, current_depth, leading_move = queue.popleft()

            # Stop exploring beyond the target depth
            if current_depth >= depth:
                # Evaluate the current position
                evaluation = self.evaluate_board(current_board)

                # Update the best move based on evaluation
                if board.turn:  # Maximizing for white
                    if evaluation > best_evaluation:
                        best_evaluation = evaluation
                        best_move = leading_move
                else:  # Minimizing for black
                    if evaluation < best_evaluation:
                        best_evaluation = evaluation
                        best_move = leading_move
                continue

            # Add all legal moves to the queue
            for move in current_board.legal_moves:
                current_board.push(move)
                queue.append((current_board.copy(), current_depth + 1, move))
                current_board.pop()

        return PlayResult(best_move, None)


class RandomMove(ExampleEngine):
    """Get a random move."""

    def search(
        self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE
    ) -> PlayResult:
        """Choose a random move."""
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    """Get the first move when sorted by san representation."""

    def search(
        self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE
    ) -> PlayResult:
        """Choose the first move alphabetically."""
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Get the first move when sorted by uci representation."""

    def search(
        self, board: chess.Board, *args: HOMEMADE_ARGS_TYPE
    ) -> PlayResult:
        """Choose the first move alphabetically in uci representation."""
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return PlayResult(moves[0], None)


class ComboEngine(ExampleEngine):
    """
    Get a move using multiple different methods.

    This engine demonstrates how one can use `time_limit`, `draw_offered`, and `root_moves`.
    """

    def search(
        self,
        board: chess.Board,
        time_limit: Limit,
        ponder: bool,
        draw_offered: bool,
        root_moves: MOVE,
    ) -> PlayResult:
        """
        Choose a move using multiple different methods.

        :param board: The current position.
        :param time_limit: Conditions for how long the engine can search (e.g. we have 10 seconds and search up to depth 10).
        :param ponder: Whether the engine can ponder after playing a move.
        :param draw_offered: Whether the bot was offered a draw.
        :param root_moves: If it is a list, the engine should only play a move that is in `root_moves`.
        :return: The move to play.
        """
        if isinstance(time_limit.time, int):
            my_time = time_limit.time
            my_inc = 0
        elif board.turn == chess.WHITE:
            my_time = (
                time_limit.white_clock
                if isinstance(time_limit.white_clock, int)
                else 0
            )
            my_inc = (
                time_limit.white_inc
                if isinstance(time_limit.white_inc, int)
                else 0
            )
        else:
            my_time = (
                time_limit.black_clock
                if isinstance(time_limit.black_clock, int)
                else 0
            )
            my_inc = (
                time_limit.black_inc
                if isinstance(time_limit.black_inc, int)
                else 0
            )

        possible_moves = (
            root_moves
            if isinstance(root_moves, list)
            else list(board.legal_moves)
        )

        if my_time / 60 + my_inc > 10:
            # Choose a random move.
            move = random.choice(possible_moves)
        else:
            # Choose the first move alphabetically in uci representation.
            possible_moves.sort(key=str)
            move = possible_moves[0]
        return PlayResult(move, None, draw_offered=draw_offered)
