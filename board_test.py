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

    def test_generate_moves_one_valid(self):
        board.initialize(6, 2)
        b = board.Board([1, 2, 3]) 
        got = list(b.generate_moves(board.Roll(dice=[5, 4], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(2, 5), board.Move(2, 4)], got)
        self.assertIn([board.Move(2, 4), board.Move(2, 5)], got)
            
    def test_generate_moves_second_dependent(self):
        board.initialize(2, 4)
        b = board.Board([0, 0, 1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 4], prob=0)))
        self.assertEqual(1, len(got))
        self.assertIn([board.Move(4, 4), board.Move(2, 4)], got)

    def test_generate_moves_valid_with_holes(self):
        board.initialize(3, 4)
        # Making sure we don't generate the move that is the 1 spot
        # going 4 spaces.`
        b = board.Board([0, 1, 0, 2, 0]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 4], prob=0)))
        self.assertEqual(1, len(got))
        self.assertIn([board.Move(3, 4), board.Move(3, 4)], got)

    def test_generate_moves_opposite_order(self):
        # This is the case where you have to try applying the dice in the
        # opposite order in order to get a different board as outcome.
        board.initialize(2, 4)
        b = board.Board([0, 0, 1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[4, 3], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(4, 3), board.Move(2, 4)], got)
        self.assertIn([board.Move(4, 4), board.Move(2, 3)], got)

    def test_generate_moves_unfinished(self):
        # This is where you don't have to use all the moves to finish
        board.initialize(2, 2)
        b = board.Board([1, 0, 1]) 
        got = list(b.generate_moves(board.Roll(dice=[5, 4], prob=0)))
        self.assertEqual(2, len(got))
        self.assertIn([board.Move(2, 4)], got)
        self.assertIn([board.Move(2, 5)], got)

    def test_generate_moves_four_dice(self):
        board.initialize(9, 4)
        b = board.Board([0, 0, 3, 3, 3])
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
        board.initialize(6, 4)
        b = board.Board([0, 2, 3, 0, 1])
        for moves in b.generate_moves(roll):
            try:
                b.apply_moves(moves)
            except Exception as e:
                print("%s with moves %s" % (roll, moves))
                raise e
        
        
if __name__ == '__main__':
    unittest.main()
