# Copyright 2020 Patrick Riley <patriley@gmail.com>

import numpy as np
import time

import board


class MoveCountDistribution(object):
    """Stores a distribution over number of moves till end of game."""

    __slots__ = ["dist"]
    
    def __init__(self, dist=np.zeros([1])):
        self.dist = np.asarray(dist)
        if len(self.dist.shape) != 1:
            raise ValueError("Need 1D shape, got %s", self.dist.shape)

    def __add__(self, other):
        """Only support adding to another MoveCountDistribution."""
        max_len = max(self.dist.shape[0], other.dist.shape[0])
        return MoveCountDistribution(
            np.pad(self.dist, (0, max_len - self.dist.shape[0]),
                   mode="constant",
                   constant_values=0) +
            np.pad(other.dist, (0, max_len - other.dist.shape[0]),
                   mode="constant",
                   constant_values=0))                   
    
    def __sub__(self, other):
        """Only support subtracting to another MoveCountDistribution."""
        max_len = max(self.dist.shape[0], other.dist.shape[0])
        return MoveCountDistribution(
            np.pad(self.dist, (0, max_len - self.dist.shape[0]),
                   mode="constant",
                   constant_values=0) -
            np.pad(other.dist, (0, max_len - other.dist.shape[0]),
                   mode="constant",
                   constant_values=0))
    
    def __mul__(self, other):
        """Only support multiplying with a scalar."""
        return MoveCountDistribution(self.dist * other)
    
    def __truediv__(self, other):
        """Only support multiplying with a scalar."""
        return MoveCountDistribution(self.dist / other)

    def __str__(self):
        return "MCD(%f, %s)" % (self.expected_value(), self.dist)

    def __iter__(self):
        return self.dist.__iter__()
    
    def increase_counts(self, amount):
        return MoveCountDistribution(np.insert(self.dist, 0, [0] * amount))

    def is_normalized(self):
        return np.allclose(np.sum(self.dist), 1)

    def expected_value(self):
        return np.sum(self.dist * range(self.dist.shape[0]))
    

class DistributionStore(object):
    """Stores MoveCountDistributions for board states."""

    def __init__(self, config):
        self.config = config
        self.distribution_map = {}
        
    def compute_best_moves_for_roll(self, this_board, roll):
        """Computes the best moves for the roll.

        "best" means the resulting position with the lowest expected
        value.  "moves" means the move for every die. If there are
        multiple groups of moves that return the same next board, one
        will be chosen arbitrarily.

        Assumes that all next board positions are already computed in
        self.distribution_map.

        Args:
          this_board: board.Board
          roll: board.Roll

        Return
          list of board.Move

        """
        # dict from board index to tuple of (expected_value, moves)
        possible_next_boards = {}
        for moves in this_board.generate_moves(roll):
            next_board = this_board.apply_moves(moves)
            next_board_idx = next_board.get_index()
            if next_board_idx in possible_next_boards:
                continue
            possible_next_boards[next_board_idx] = (
                self.distribution_map[next_board_idx].expected_value(),
                moves)

        best_next_board = min(possible_next_boards.keys(),
                              key=(lambda k: possible_next_boards[k][0]))
        
        return possible_next_boards[best_next_board][1]

    def compute_move_distribution_for_board(self, this_board):
        """Computes the MoveCountDistribution for this_board.

        Assumes that all next board position are already computed in
        self.distribution_map

        Args:
          this_board: board.Board

        Return
          MoveCountDistribution
        """
        out = MoveCountDistribution()
        for roll in board.ROLLS:
            moves = self.compute_best_moves_for_roll(this_board, roll)
            next_board = this_board.apply_moves(moves)
            out += (self.distribution_map[next_board.get_index()]
                    .increase_counts(1) * roll.prob)

        assert out.is_normalized()
            
        return out

    def compute(self, progress_interval=5000, limit=-1):
        """Computes and stores MoveCountDistribution for each board.

        clears an existing data in self.distribution_map

        Args:
          limit: if > 0, only computes this many valid boards
        """
        self.distribution_map.clear()

        if progress_interval:
            print("Starting compute on %d boards" %
                  self.config.num_valid_boards,
                  flush=True)

        start_time = time.time()
        # The minimum board index is the game ended state.
        boards_processed = 1
        self.distribution_map[self.config.min_board_index] = MoveCountDistribution([1])
        
        for board_idx in range(self.config.min_board_index + 1,
                               self.config.max_board_index):
            if not self.config.is_valid_index(board_idx):
                continue

            boards_processed += 1
            if progress_interval and boards_processed % progress_interval == 0:
                frac_complete = boards_processed / self.config.num_valid_boards
                this_time = time.time()
                print("%d/%d %.1f%%, %fs elapsed, %fs estimated total" % (
                      boards_processed,
                      self.config.num_valid_boards,
                      frac_complete * 100,
                      this_time - start_time,
                      (this_time - start_time) / frac_complete), 
                      flush=True)

            this_board = board.Board.from_index(self.config, board_idx)
            dist = self.compute_move_distribution_for_board(this_board)
            self.distribution_map[board_idx] = dist

            if limit > 0 and boards_processed >= limit:
                print("Stopping at %d boards, index %d"
                      % (boards_processed, board_idx))
                break

    def pretty_string(self, limit=-1):
        num_printed = 0
        for board_idx, dist in self.distribution_map.items():
            this_board = board.Board.from_index(self.config, board_idx)
            print("Board %d" % board_idx)
            print(dist)
            print(this_board.pretty_string())

