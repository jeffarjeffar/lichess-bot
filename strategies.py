"""
Some example strategies for people who want to create a custom, homemade bot.
And some handy classes to extend
"""

import chess
from chess.engine import PlayResult
import random
from engine_wrapper import EngineWrapper


import os


class FillerEngine:
    """
    Not meant to be an actual engine.

    This is only used to provide the property "self.engine"
    in "MinimalEngine" which extends "EngineWrapper"
    """

    def __init__(self, main_engine, name=None):
        self.id = {
            "name": name
        }
        self.name = name
        self.main_engine = main_engine

    def __getattr__(self, method_name):
        main_engine = self.main_engine

        def method(*args, **kwargs):
            nonlocal main_engine
            nonlocal method_name
            return main_engine.notify(method_name, *args, **kwargs)

        return method


class MinimalEngine(EngineWrapper):
    """
    Subclass this to prevent a few random errors

    Even though MinimalEngine extends EngineWrapper,
    you don't have to actually wrap an engine.

    At minimum, just implement `search`,
    however you can also change other methods like
    `notify`, `first_search`, `get_time_control`, etc.
    """

    def __init__(self, commands, options, stderr, draw_or_resign, name=None, **popen_args):
        super().__init__(options, draw_or_resign)

        self.engine_name = self.__class__.__name__ if name is None else name

        self.engine = FillerEngine(self, name=self.name)
        self.engine.id = {
            "name": self.engine_name
        }

    def search(self, board, time_limit, ponder, draw_offered):
        """
        The method to be implemented in your homemade engine

        NOTE: This method must return an instance of "chess.engine.PlayResult"
        """
        raise NotImplementedError("The search method is not implemented")

    def notify(self, method_name, *args, **kwargs):
        """
        The EngineWrapper class sometimes calls methods on "self.engine".
        "self.engine" is a filler property that notifies <self>
        whenever an attribute is called.

        Nothing happens unless the main engine does something.

        Simply put, the following code is equivalent
        self.engine.<method_name>(<*args>, <**kwargs>)
        self.notify(<method_name>, <*args>, <**kwargs>)
        """
        pass


class ExampleEngine(MinimalEngine):
    pass


# Strategy names and ideas from tom7's excellent eloWorld video

class RandomMove(ExampleEngine):
    def search(self, board, *args):
        return PlayResult(random.choice(list(board.legal_moves)), None)


class Alphabetical(ExampleEngine):
    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=board.san)
        return PlayResult(moves[0], None)


class FirstMove(ExampleEngine):
    """Gets the first move when sorted by uci representation"""

    def search(self, board, *args):
        moves = list(board.legal_moves)
        moves.sort(key=str)
        return PlayResult(moves[0], None)


class Engine(ExampleEngine):
    def __init__(self, commands, options, stderr, draw_or_resign, name=None, **popen_args):
        super().__init__(commands, options, stderr, draw_or_resign, name, **popen_args)
        self.move = 0

    def search(self, board, time_limit, ponder, draw_offered):
        os.makedirs('temp', exist_ok=True)
        file_in = os.path.join('temp', f'input-{self.move}.txt')
        file_out = os.path.join('temp', f'output-{self.move}.txt')
        self.move += 1

        time_control = None
        try:
            time_control = time_limit.time * 1000
        except Exception:
            if board.turn == chess.WHITE:
                time_control = max(int(time_limit.white_clock * 10) +
                                   int(time_limit.white_inc) * 1000 - 300, 96)
            else:
                time_control = max(int(time_limit.black_clock * 10) +
                                   int(time_limit.black_inc) * 1000 - 300, 96)

        with open(file_in, 'w') as f:
            f.write(
                f'setoption time_limit {time_control}\n'
                'setoption table_size 69696983\n'
                f'go {board.fen(en_passant="fen")}\nquit')
        os.system(f'~/bin/engine < {file_in} > {file_out}')

        with open(file_out) as f:
            out = f.readlines()

        move = next((out[i][16:].strip() for i in range(
            len(out) - 1, 0, -1) if out[i].startswith('COMPUTER PLAYED')), None)

        if move == 'RESIGN':
            return PlayResult(None, None, resigned=True)
        try:
            return PlayResult(board.push_san(move), None)
        except ValueError:
            return PlayResult(board.push_uci(move), None)
