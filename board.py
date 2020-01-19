# Copyright 2020 Patrick Riley <patriley@gmail.com>

import array
import collections
import itertools
import gmpy2
import numpy as np
import scipy.misc

# We keep module level global variables for the size of the
# board. This allows each indivodual board to be smaller because it
# doesn't even have to keep a reference to this at the cost of some
# loss of flexibility. But really, we'll only muck the board size for
# testing, so it's fine

_num_markers = -1
_num_spots = -1
_num_valid_boards = -1
# minimum (inclusive) valid board index
_min_board_index = -1
# maximum (exclusive) value board index
_max_board_index = -1


def initialize(num_markers, num_spots):
    global _num_markers, _num_spots
    global _num_valid_boards, _min_board_index, _max_board_index
    _num_markers = num_markers
    _num_spots = num_spots
    # see Board for a discussion of number of boards and how the board
    # indexing works
    _num_valid_boards = scipy.misc.comb(_num_markers + _num_spots, _num_spots, exact=True)
    _min_board_index = 0
    _max_board_index = 1  # because max is exclusive
    for i in range(num_markers):
        _min_board_index |= 1 << i
        _max_board_index |= 1 << (_num_markers + _num_spots - 1 - i)


def num_valid_boards():
    return _num_valid_boards


def min_board_index():
    return _min_board_index


def max_board_index():
    return _max_board_index


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

    Let's talk about mapping board states to indexes.

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
    index is valid. How efficient is this representation? For a normal
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

    def is_valid_index(idx):
        return (idx >= _min_board_index and
                idx < _max_board_index and
                gmpy2.popcount(idx) == _num_markers)

    def from_index(idx):
        if not Board.is_valid_index(idx):
            raise ValueError("%d is not a valid board index" % idx)
        
        spot_counts = array.array('i', [0] * (_num_spots + 1))
        current_spot = 0
        current_spot_count = 0
        for i in range(_num_markers + _num_spots):
            if idx & (1 << i):
                # This is a marker
                current_spot_count += 1
            else:
                # This is a divider
                spot_counts[current_spot] = current_spot_count
                current_spot += 1
                current_spot_count = 0
        spot_counts[current_spot] = current_spot_count

        return Board(spot_counts)

    def __init__(self, spot_counts):
        if len(spot_counts) != (_num_spots + 1):
            raise ValueError("Bad size for %s, expected %d" %
                             (spot_counts, _num_spots + 1))
        if np.sum(spot_counts) != _num_markers:
            raise ValueError("Total markers %d in %s not expected number %d" %
                             (np.sum(spot_counts),
                              str(spot_counts),
                              _num_markers))
        if isinstance(spot_counts, array.array):
            self.spot_counts = spot_counts
        else:
            self.spot_counts = array.array('i', spot_counts)
        
    def get_index(self):
        # This seems like an obviously fairly inefficient way to do this.
        # Batching to set a bunch of bits all at once likely makes more sense
        idx = 0
        bit_idx = 0
        for spot in range(_num_spots + 1):
            for _ in range(self.spot_counts[spot]):
                idx |= 1 << bit_idx
                bit_idx += 1
            bit_idx += 1

        return idx

    def pretty_string(self, moves=None):
        out = []

        # First, print the markers to a uniform length
        line_format = "%%d %%d %%-%ds" % (max(self.spot_counts) + 1)
        for spot in range(_num_spots + 1):
            out.append(line_format % (spot, self.spot_counts[spot],
                                      'o' * self.spot_counts[spot]))

        # Now, write the moves
        if moves:
            for move_idx, m in enumerate(moves):
                move_end = max(m.spot - m.count, 0)
                for spot_idx in range(_num_spots, -1, -1):
                    if spot_idx > m.spot:
                        this_move_str == '  ';
                    elif spot_idx == m.spot:
                        this_move_str = '%d ' % m.count
                    elif spot_idx > move_end:
                        this_move_str = '| '
                    elif spot_idx == move_end:
                        this_move_str = '+ '
                    else:
                        this_move_str = '  '
                    out[spot_idx] += this_move_str
            
        return '\n'.join(out) + '\n'
            
            
initialize(15, 6)
