import array
import unittest
from parameterized import parameterized

import board


class BoardTestCase(unittest.TestCase):

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
        
    def test_init(self):
        board.initialize(6, 2)
        # Board state is 1 off, 2 on 1 spot, 3 on 2 spot
        # 11101101
        b = board.Board(0xED)
        self.assertListEqual(list(b.spot_counts), [1, 2, 3])

    @parameterized.expand([
        (5, 3),
        (10, 5),
    ])
    def test_index_round_trip(self, num_markers, num_spots):
        board.initialize(num_markers, num_spots)
        for idx in range(board.min_board_index(), board.max_board_index()):
            if not board.Board.is_valid_index(idx):
                continue
            b = board.Board(idx)
            self.assertEqual(b.get_index(), idx)
    
        
if __name__ == '__main__':
    unittest.main()
