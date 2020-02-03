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
import unittest
from parameterized import parameterized

import board


class GameConfigurationTestCase(unittest.TestCase):

    def test_initialize_3marker_2spots(self):
        config = board.GameConfiguration(3, 2)
        self.assertEqual(config.num_valid_boards, 10)
        # 5 total bits 00111 is the min
        self.assertEqual(config.min_board_index, 7)
        # 5 total bits 11100 is the max, adding 1 for exclusive
        self.assertEqual(config.max_board_index, 28 + 1)

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_is_valid_counts(self, num_markers, num_spots):
        config = board.GameConfiguration(num_markers, num_spots)
        count_valid = 0
        for idx in range(config.min_board_index, config.max_board_index):
            if config.is_valid_index(idx):
                count_valid += 1
        self.assertEqual(config.num_valid_boards, count_valid)

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_generator(self, num_markers, num_spots):
        config = board.GameConfiguration(num_markers, num_spots)
        self.assertEqual(config.num_valid_boards,
                         sum(1 for _ in config.generate_valid_indices()))
        

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_next_valid_index(self, num_markers, num_spots):
        config = board.GameConfiguration(num_markers, num_spots)
        board_idx = config.min_board_index
        while True:
            try:
                next_board_idx = config.next_valid_index(board_idx)
            except StopIteration:
                next_board_idx = -1
            expected_board_idx = board_idx + 1
            while not(config.is_valid_index(expected_board_idx)):
                expected_board_idx += 1
                if expected_board_idx >= config.max_board_index:
                    expected_board_idx = -1
                    break
            self.assertEqual(next_board_idx, expected_board_idx,
                             "previous board idx: %d" % board_idx)

            if next_board_idx == -1:
                break

            board_idx = next_board_idx
        
    def rolls_sum_to_one(self):
        sum = 0
        for _, prob in board.ROLLS:
            sum += prob
        self.assertEqual(sum, 1.0)

        
class BoardTestCase(unittest.TestCase):

    def test_index_init(self):
        config = board.GameConfiguration(6, 2)
        # Board state is 1 off, 2 on 1 spot, 3 on 2 spot
        # 11101101
        b = board.Board.from_index(config, 0xED)
        self.assertListEqual(list(b.spot_counts), [1, 2, 3])

    def test_spot_counts_init(self):
        config = board.GameConfiguration(6, 2)
        b = board.Board(config, [1, 2, 3])
        self.assertListEqual(list(b.spot_counts), [1, 2, 3])

    def test_spot_counts_init_errors(self):
        config = board.GameConfiguration(6, 2)
        with self.assertRaises(ValueError):
            b = board.Board(config, [5, 1])
        with self.assertRaises(ValueError):
            b = board.Board(config, [3, 1, 1, 1])
        with self.assertRaises(ValueError):
            b = board.Board(config, [1, 1, 1])

    def test_total_pips(self):
        config = board.GameConfiguration(6, 3)
        self.assertEqual(0, board.Board(config, [6, 0, 0, 0]).total_pips())
        self.assertEqual(5, board.Board(config, [1, 5, 0, 0]).total_pips())
        self.assertEqual(14, board.Board(config, [0, 1, 2, 3]).total_pips())
        
    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_index_round_trip(self, num_markers, num_spots):
        config = board.GameConfiguration(num_markers, num_spots)
        for idx in range(config.min_board_index, config.max_board_index):
            if not config.is_valid_index(idx):
                continue
            b = board.Board.from_index(config, idx)
            self.assertEqual(b.get_index(), idx)

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_next_valid_board(self, num_markers, num_spots):
        config = board.GameConfiguration(num_markers, num_spots)
        b = board.Board.from_index(config, config.min_board_index)
        index_gen = config.generate_valid_indices()
        next(index_gen)
        while True:
            msg = "old b: %s; " % str(b)
            try:
                next_b = b.next_valid_board()
                msg += "next b: %s; " % str(next_b)
            except StopIteration:
                try: 
                    next_idx = next(index_gen)
                    self.fail(
                        "Generator not finished with next_valid_board was %s" % msg)
                except StopIteration:
                    break
            try:
                next_idx = next(index_gen)
                msg += "next idx: %d; " % next_idx
            except StopIteration:
                self.fail("Generator ran out before board; %s" % msg)
            self.assertEqual(next_b.get_index(), next_idx, msg)
            b = next_b
        
    def test_pretty_print(self):
        config = board.GameConfiguration(6, 2)
        # Board state is 1 off, 2 on 1 spot, 3 on 2 spot
        # 11101101
        b = board.Board.from_index(config, 0xED)
        self.assertEqual(b.pretty_string(),
                         "0 1 o   \n" + 
                         "1 2 oo  \n" + 
                         "2 3 ooo \n")

    def test_pretty_print_with_moves(self):
        config = board.GameConfiguration(6, 4)
        b = board.Board(config, [2, 1, 1, 1, 1])

        m1 = board.Move(spot=3, count=2)
        m2 = board.Move(spot=3, count=3)
        m3 = board.Move(spot=3, count=6)
        m4 = board.Move(spot=4, count=1)
        self.assertEqual(b.pretty_string([m1, m2, m3, m4]),
                         "0 2 oo   x +   \n" +
                         "1 1 o  x | |   \n" +
                         "2 1 o  | | |   \n" +
                         "3 1 o  2 3 6 x \n" +
                         "4 1 o        1 \n")

    def test_apply_move(self):
        config = board.GameConfiguration(6, 2)
        b = board.Board(config, [1, 2, 3])

        self.assertEqual(b.apply_move(board.Move(2, 6)),
                         board.Board(config, [2, 2, 2]))
        self.assertEqual(b.apply_move(board.Move(2, 1)),
                         board.Board(config, [1, 3, 2]))
        self.assertEqual(b.apply_move(board.Move(1, 1)),
                         board.Board(config, [2, 1, 3]))

    def test_apply_move_errors(self):
        config = board.GameConfiguration(6, 2)
        
        b = board.Board(config, [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "Invalid spot"):
            b.apply_move(board.Move(0, 6))
        b = board.Board(config, [3, 0, 3])
        with self.assertRaisesRegex(ValueError, "No marker"):
            b.apply_move(board.Move(1, 1))
        b = board.Board(config, [1, 2, 3])
        with self.assertRaisesRegex(ValueError, "Overflow count"):
            b.apply_move(board.Move(1, 6))

    def test_generate_moves_one_valid(self):
        config = board.GameConfiguration(6, 2)
        b = board.Board(config, [1, 2, 3]) 
        got = list(b.generate_moves(board.Roll(dice=[5, 4], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(2, 5), board.Move(2, 4)], got)
        self.assertIn([board.Move(2, 4), board.Move(2, 5)], got)
            
    def test_generate_moves_second_dependent(self):
        config = board.GameConfiguration(2, 4)
        b = board.Board(config, [0, 0, 1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 4], prob=0)))
        self.assertEqual(1, len(got))
        self.assertIn([board.Move(4, 4), board.Move(2, 4)], got)

    def test_generate_moves_valid_with_holes(self):
        config = board.GameConfiguration(3, 4)
        # Making sure we don't generate the move that is the 1 spot
        # going 4 spaces.`
        b = board.Board(config, [0, 1, 0, 2, 0]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 4], prob=0)))
        self.assertEqual(1, len(got))
        self.assertIn([board.Move(3, 4), board.Move(3, 4)], got)

    def test_generate_moves_opposite_order(self):
        # This is the case where you have to try applying the dice in the
        # opposite order in order to get a different board as outcome.
        config = board.GameConfiguration(2, 4)
        b = board.Board(config, [0, 0, 1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 3], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(4, 3), board.Move(2, 4)], got)
        self.assertIn([board.Move(4, 4), board.Move(2, 3)], got)

    def test_generate_moves_unfinished(self):
        # This is where you don't have to use all the moves to finish
        config = board.GameConfiguration(2, 2)
        b = board.Board(config, [1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[5, 4], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(2, 4)], got)
        self.assertIn([board.Move(2, 5)], got)

    def test_generate_moves_four_dice(self):
        config = board.GameConfiguration(9, 4)
        b = board.Board(config, [0, 0, 3, 3, 3])
        got = list(b.generate_moves(board.Roll(dice=[2, 2, 2, 2], prob=0)))
        self.assertEqual(78, len(got))
        # Since this generates an annoying large number of moves,
        # we're not going to test all of them, just a couple.
        self.assertIn([board.Move(3, 2), board.Move(2, 2),
                       board.Move(2, 2), board.Move(2, 2)], got)
        self.assertIn([board.Move(3, 2), board.Move(3, 2),
                       board.Move(3, 2), board.Move(2, 2)], got)

    @parameterized.expand([
        (board.Roll(dice=(5, 4), prob=0),),
        (board.Roll(dice=(3, 3, 3, 3), prob=0),),
        (board.Roll(dice=(3, 1), prob=0),),
    ])
    def test_generate_moves_valid(self, roll):
        # For a random board position, we'll just check that all
        # generated moves are valid.
        config = board.GameConfiguration(6, 4)
        b = board.Board(config, [0, 2, 3, 0, 1])
        for moves in b.generate_moves(roll):
            try:
                b.apply_moves(moves)
            except Exception as e:
                print("%s with moves %s" % (roll, moves))
                raise e
        
        
if __name__ == '__main__':
    unittest.main()
