# Copyright 2019 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import array
import ast
import collections
import copy
import itertools
import gmpy2
import numpy as np
import scipy.special


class GameConfiguration(object):
    """Keeps the overall config of the game and useful computed values.

    Attributes:
    * num_markers: NUmber of markers (playing pieces)
    * num_spots: Number of spots, not including the "off the board" spot
    * num_valid_boards: Total number of valid positions
    * min_board_id: minimum (inclusive) valid board id
    * max_board_id: maximum (exclusive) value board id
    """

    def __init__(self, num_markers, num_spots):
        self.num_markers = num_markers
        self.num_spots = num_spots
        # see Board for a discussion of number of boards and how the board
        # indexing works
        self.num_valid_boards = scipy.special.comb(
            self.num_markers + self.num_spots, self.num_spots, exact=True)
        self.min_board_id = 0
        self.max_board_id = 1  # because max is exclusive
        for i in range(num_markers):
            self.min_board_id |= 1 << i
            self.max_board_id |= 1 << (self.num_markers + self.num_spots - 1 - i)

    def is_valid_id(self, idx):
        return (idx >= self.min_board_id and
                idx < self.max_board_id and
                gmpy2.popcount(idx) == self.num_markers)

    def next_valid_id(self, board_id):
        """Generates the next valid board idx after idx.

        Follows the same algorithm as board.next_valid_board, but done with
        bit manipulations.
        """
        if board_id >= self.max_board_id - 1:
            raise StopIteration

        # Find the bit position of the first 1 and the bit postion of the
        # last 1 in that group of 1s.
        first_one_pos = -1
        one_block_end_pos = -1
        for i in range(0, self.num_markers + self.num_spots):
            if (1 << i) & board_id:
                if first_one_pos < 0:
                    first_one_pos = i
            elif first_one_pos >= 0:
                one_block_end_pos = i - 1
                break

        assert(first_one_pos >= 0)
        assert(one_block_end_pos >= 0)

        # lower mask is everything excpect the last 1 in lowest block of 1s
        # upper mask is everything else
        upper_mask = ~0 << one_block_end_pos
        lower_mask = ~upper_mask

        # the xor swaps a 01 at the end of the group; this puts one 1
        # in the next higher bucket
        upper = (board_id & upper_mask) ^ (3 << one_block_end_pos)
        lower = (board_id & lower_mask) >> first_one_pos

        return upper | lower

    def generate_valid_ids(self):
        board_id = self.min_board_id
        while board_id < self.max_board_id:
            if self.is_valid_id(board_id):
                yield board_id
            board_id += 1

    def save_into_hdf5(self, hdf5_group):
        hdf5_group.create_dataset("num_markers", data=[self.num_markers])
        hdf5_group.create_dataset("num_spots", data=[self.num_spots])

    def load_from_hdf5(hdf5_group):
        return GameConfiguration(hdf5_group["num_markers"][0],
                                 hdf5_group["num_spots"][0])


Move = collections.namedtuple('Move', ['spot', 'count'])

Roll = collections.namedtuple('Roll', ['dice', 'prob'])

def _generate_rolls():
    out = []
    for d1, d2 in itertools.combinations_with_replacement(range(1, 7), 2):
        if (d1 == d2):
            out.append(Roll([d1, d1, d1, d1], 1/36))
        else:
            out.append(Roll([d1, d2], 1/18))
    return out

ROLLS = _generate_rolls()


class Board(object):
    """Board represents a current state of the backgammon end game.

    Let's talk about mapping board states to ids.

    If we have N markers and M spots to place them (excluding the off
    the board state), then the problem of counting the number of board
    states is the classic "Stars and Bars" problem in
    combinatorics. The answer is computed by putting the states of the
    board in correspondance with strings for "stars" (representing the
    pieces) and "bars" representing separating one spot from another.

    The number of valid board states is then C(N+M, M). (If you look
    up the formula and worry I have an off by one error, remember
    that M is the number of *not off the board* states

    This counting comes from the number of distinct sequences of N+M
    characters with M of them are "bars" (our separators). This also
    suggests an encoding: bit strings up to N+M bits. We'll use 1 for
    the "stars" and 0 for the "bars".

    Note that a valid board state must have exactly N bits set to
    1. This is the main reason we have to explcitly test whether an
    id is valid. How efficient is this representation? For a normal
    size backgammon game, N=15, M=6.
    # valid states = C(21, 6) = 54264
    # bit strings of 21 bits = 2**21 = 2097152
    Fraction of bit strings that are valid = 3%.

    An advantage of this encoding is that evey valid move must move
    the bars to the left (make the number lower). So if you want to
    iterate over all board position and ensure that you have processed
    every achievable next board position by the time you get to a
    state, just iterate from min to max.
    """
    __slots__=["config", "spot_counts"]

    def from_id(config, idx):
        if not config.is_valid_id(idx):
            raise ValueError("%d is not a valid board id" % idx)

        spot_counts = array.array('i', [0] * (config.num_spots + 1))
        current_spot = 0
        current_spot_count = 0
        for i in range(config.num_markers + config.num_spots):
            if idx & (1 << i):
                # This is a marker
                current_spot_count += 1
            else:
                # This is a divider
                spot_counts[current_spot] = current_spot_count
                current_spot += 1
                current_spot_count = 0
        spot_counts[current_spot] = current_spot_count

        return Board(config, spot_counts, sanity_check=False)

    def __init__(self, config, spot_counts, sanity_check=True):
        self.config = config
        if not sanity_check:
            self.spot_counts = spot_counts
            return
        if len(spot_counts) != (self.config.num_spots + 1):
            raise ValueError("Bad size for %s, expected %d" %
                             (spot_counts, self.config.num_spots + 1))
        if np.sum(spot_counts) != self.config.num_markers:
            raise ValueError("Total markers %d in %s not expected number %d" %
                             (np.sum(spot_counts),
                              str(spot_counts),
                              self.config.num_markers))
        if isinstance(spot_counts, array.array):
            self.spot_counts = spot_counts
        else:
            self.spot_counts = array.array('i', spot_counts)

    def __str__(self):
        return "Board(%s)" % list(self.spot_counts)

    def __eq__(self, other):
        return self.spot_counts == other.spot_counts

    def get_id(self):
        # This seems like an obviously fairly inefficient way to do this.
        # Batching to set a bunch of bits all at once likely makes more sense
        idx = 0
        bit_idx = 0
        for spot in range(self.config.num_spots + 1):
            for _ in range(self.spot_counts[spot]):
                idx |= 1 << bit_idx
                bit_idx += 1
            bit_idx += 1

        return idx

    def is_finished(self):
        return self.spot_counts[0] == self.config.num_markers

    def total_pips(self):
        return np.sum(np.array(range(self.config.num_spots + 1)) * self.spot_counts)

    def next_valid_board(self):
        """Return a new board which has the next valid id."""
        out = copy.deepcopy(self)
        # Find the first non empty spot. From that spot, move one
        # to the next higher spot and the rest to spot 0.  Note
        # that the range is *not* looking at the last spot. If
        # only the last spot has markers, that's the max valid
        # board.
        for spot_idx in range(0, self.config.num_spots):
            if out.spot_counts[spot_idx] == 0:
                continue
            spots = out.spot_counts[spot_idx]
            out.spot_counts[spot_idx + 1] += 1
            out.spot_counts[spot_idx] = 0
            out.spot_counts[0] = spots - 1
            return out
        raise StopIteration()

    def apply_move(self, move):
        # Check for some error cases first.
        if self.spot_counts[move.spot] < 1:
            raise ValueError("No marker for %s on %s" % (
                move, self))
        if move.spot < 1 or move.spot > self.config.num_spots:
            raise ValueError("Invalid spot on %s on %s" % (
                move, self))
        new_board = Board(self.config, copy.copy(self.spot_counts), sanity_check=False)
        new_board.spot_counts[move.spot] -= 1
        if move.count > move.spot:
            for i in range(move.spot + 1, self.config.num_spots + 1):
                if new_board.spot_counts[i] != 0:
                    raise ValueError(
                        ("Overflow count %s invalid " +
                        "when spot %d still has markers on %s") % (
                            move, i, self))
            new_board.spot_counts[0] += 1
        else:
            new_board.spot_counts[move.spot - move.count] += 1
        return new_board

    def apply_moves(self, moves):
        new_board = self
        for m in moves:
            new_board = new_board.apply_move(m)
        return new_board

    def generate_moves(self, roll):
        """Generates all valid moves given roll.

        All valid moves will be returned and all moves will be valid.
        However, multiple moves may be generated that return exactly
        the same Board after all the moves in the list are applied.

        Args:
          roll: Roll to generate moves for

        Yields:
          list of Move objects. Each list will have the same size as roll.dice
        """
        for move_list in self._generate_moves_recursive(roll, 0, 1, []):
            yield move_list
        if roll.dice[0] != roll.dice[1]:
            for move_list in self._generate_moves_recursive(
                    roll, len(roll.dice) - 1, -1, []):
                yield move_list

    def _generate_moves_recursive(self, roll, roll_idx, roll_idx_step, moves):
        # If you are thinking I shoudl be pythonic and ask for
        # forgiveness not permission, you shoudl remember that -1 is a
        # valid index, but I need to catch that here.
        if roll_idx < 0 or roll_idx >= len(roll.dice) or self.is_finished():
            yield moves
            return
        die = roll.dice[roll_idx]
        found_markers = False
        for spot_idx in range(self.config.num_spots, 0, -1):
            if found_markers and spot_idx < die:
                break
            if self.spot_counts[spot_idx] > 0:
                found_markers = True
                move = Move(spot=spot_idx, count=die)
                new_board = self.apply_move(move)
                for move_list in new_board._generate_moves_recursive(
                        roll, roll_idx + roll_idx_step, roll_idx_step,
                        moves + [move]):
                    yield move_list

    def pretty_string(self, moves=None):
        out = []

        # First, print the markers to a uniform length
        line_format = "%%d %%d %%-%ds" % (max(self.spot_counts) + 1)
        for spot in range(self.config.num_spots + 1):
            out.append(line_format % (spot, self.spot_counts[spot],
                                      'o' * self.spot_counts[spot]))

        # Now, write the moves
        if moves:
            for move_idx, m in enumerate(moves):
                move_end = max(m.spot - m.count, 0)
                for spot_idx in range(self.config.num_spots, -1, -1):
                    if spot_idx > m.spot:
                        this_move_str = '  ';
                    elif spot_idx == m.spot:
                        this_move_str = '%d ' % m.count
                    elif spot_idx > move_end:
                        this_move_str = '| '
                    elif spot_idx == m.spot - m.count:
                        this_move_str = 'x '
                    elif spot_idx == move_end:
                        this_move_str = '+ '
                    else:
                        this_move_str = '  '
                    out[spot_idx] += this_move_str

        return '\n'.join(out) + '\n'


def encode_moves_string(moves):
    out = []
    for m in moves:
        out.append([m.spot, m.count])
    return str(out)


def decode_moves_string(s):
    out = []
    parsed = ast.literal_eval(s)
    for m_arr in parsed:
        if len(m_arr) != 2:
            raise ValueError("Bad element {} in '{}'".format(m_arr, s))
        out.append(Move(m_arr[0], m_arr[1]))
    return out
