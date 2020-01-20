import array
import unittest
from parameterized import parameterized

import board


class ModuleTestCase(unittest.TestCase):

    def test_initialize_3marker_2spots(self):
        board.initialize(3, 2)
        self.assertEqual(board.num_valid_boards(), 10)
        # 5 total bits 00111 is the min
        self.assertEqual(board.min_board_index(), 7)
        # 5 total bits 11100 is the max, adding 1 for exclusive
        self.assertEqual(board.max_board_index(), 28 + 1)

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_is_valid_counts(self, num_markers, num_spots):
        board.initialize(num_markers, num_spots)
        count_valid = 0
        for idx in range(board.min_board_index(), board.max_board_index()):
            if board.Board.is_valid_index(idx):
                count_valid += 1
        self.assertEqual(board.num_valid_boards(), count_valid)

    def rolls_sum_to_one(self):
        sum = 0
        for _, prob in board.ROLLS:
            sum += prob
        self.assertEqual(sum, 1.0)

        
class BoardTestCase(unittest.TestCase):

    def test_index_init(self):
        board.initialize(6, 2)
        # Board state is 1 off, 2 on 1 spot, 3 on 2 spot
        # 11101101
        b = board.Board.from_index(0xED)
        self.assertListEqual(list(b.spot_counts), [1, 2, 3])

    def test_spot_counts_init(self):
        board.initialize(6, 2)
        b = board.Board([1, 2, 3])
        self.assertListEqual(list(b.spot_counts), [1, 2, 3])

    def test_spot_counts_init_errors(self):
        board.initialize(6, 2)
        with self.assertRaises(ValueError):
            b = board.Board([5, 1])
        with self.assertRaises(ValueError):
            b = board.Board([3, 1, 1, 1])
        with self.assertRaises(ValueError):
            b = board.Board([1, 1, 1])

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_index_round_trip(self, num_markers, num_spots):
        board.initialize(num_markers, num_spots)
        for idx in range(board.min_board_index(), board.max_board_index()):
            if not board.Board.is_valid_index(idx):
                continue
            b = board.Board.from_index(idx)
            self.assertEqual(b.get_index(), idx)

    def test_pretty_print(self):
        board.initialize(6, 2)
        # Board state is 1 off, 2 on 1 spot, 3 on 2 spot
        # 11101101
        b = board.Board.from_index(0xED)
        self.assertEqual(b.pretty_string(),
                         "0 1 o   \n" + 
                         "1 2 oo  \n" + 
                         "2 3 ooo \n")

    def test_pretty_print_with_moves(self):
        board.initialize(6, 4)
        b = board.Board([2, 1, 1, 1, 1])

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
        board.initialize(6, 2)
        b = board.Board([1, 2, 3])

        self.assertEqual(b.apply_move(board.Move(2, 6)),
                         board.Board([2, 2, 2]))
        self.assertEqual(b.apply_move(board.Move(2, 1)),
                         board.Board([1, 3, 2]))
        self.assertEqual(b.apply_move(board.Move(1, 1)),
                         board.Board([2, 1, 3]))

    def test_apply_move_errors(self):
        board.initialize(6, 2)
        
        b = board.Board([1, 2, 3])
        with self.assertRaisesRegex(ValueError, "Invalid spot"):
            b.apply_move(board.Move(0, 6))
        b = board.Board([3, 0, 3])
        with self.assertRaisesRegex(ValueError, "No marker"):
            b.apply_move(board.Move(1, 1))
        b = board.Board([1, 2, 3])
        with self.assertRaisesRegex(ValueError, "Overflow count"):
            b.apply_move(board.Move(1, 6))
        
if __name__ == '__main__':
    unittest.main()
