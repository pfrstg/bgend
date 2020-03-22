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

import numpy as np
import tempfile
import unittest

import board
import strategy


class MoveCountDistributionTestCase(unittest.TestCase):

    def test_init(self):
        d = strategy.MoveCountDistribution()
        np.testing.assert_allclose(d.dist, [0])
        with self.assertRaises(ValueError):
            strategy.MoveCountDistribution([[0.1], [0.2]])

    def test_add_subtract(self):
        d1 = strategy.MoveCountDistribution([0.75, 0.25])
        d2 = strategy.MoveCountDistribution([0.7, 0.2, 0.1])
        np.testing.assert_allclose((d1 + d2).dist, [1.45, 0.45, 0.1])
        np.testing.assert_allclose((d2 + d1).dist, [1.45, 0.45, 0.1])
        np.testing.assert_allclose((d1 - d2).dist, [0.05, 0.05, -0.1])
        np.testing.assert_allclose((d2 - d1).dist, [-0.05, -0.05, 0.1])

    def test_multiply_divide(self):
        d = strategy.MoveCountDistribution([0.75, 0.25])
        np.testing.assert_allclose((d * 2).dist, [1.5, .5])
        np.testing.assert_allclose((d / 5).dist, [.15, .05])

    def test_increase_counts(self):
        d = strategy.MoveCountDistribution([0.75, 0.25])
        np.testing.assert_allclose(d.increase_counts(2).dist,
                                   [0, 0, 0.75, 0.25])

    def test_is_normalized(self):
        self.assertTrue(
            strategy.MoveCountDistribution([0.75, 0.25]).is_normalized())
        self.assertFalse(
            strategy.MoveCountDistribution([0.1, 0.2]).is_normalized())

    def test_expected_value(self):
        np.testing.assert_approx_equal(
            strategy.MoveCountDistribution([0.75, 0.25]).expected_value(),
            0.25)
        np.testing.assert_approx_equal(
            strategy.MoveCountDistribution([0.0, 0.2, 0.8]).expected_value(),
            1.8)
        np.testing.assert_approx_equal(
            strategy.MoveCountDistribution([0.0, 0.0, 1.0]).expected_value(),
            2)

    def test_append(self):
        d = strategy.MoveCountDistribution([0.1, 0.2])
        np.testing.assert_allclose(d.append([0.3, 0.4]).dist,
                                   [0.1, 0.2, 0.3, 0.4])
        

class DistributionStoreTestCase(unittest.TestCase):

    def test_e2e_6_3(self):
        config = board.GameConfiguration(6, 3)
        store = strategy.DistributionStore(config)
        store.compute()

        def test_move_count_distribution(board_init, expected_move_count):
            print("board_init: %s" % board_init)
            b = board.Board(config, board_init)
            np.testing.assert_allclose(
                store.distribution_map[b.get_index()].dist,
                expected_move_count)

        # This is an end to end test. We'll pull a few specific cases
        # that are relatively easy to understand.

        # The end game state
        test_move_count_distribution([6, 0, 0, 0], [1])
        # Only two pieces left, has to finish on one roll
        test_move_count_distribution([4, 2, 0, 0], [0, 1])
        # Only three pieces left. If doubles, finish in 1 move otherwise, 2.
        test_move_count_distribution([3, 3, 0, 0], [0, 1/6, 5/6])
        # Only two pieces left but on 2nd spot. Any of the 1-2, 1-3,
        # 1-4, 1-5, 1-6 rolls mean you will finish in 2 instead of 1.
        test_move_count_distribution([4, 0, 2, 0], [0, 26/36, 10/36])
        # Only two pieces left but on 1st and 3rd spot. Any roll
        # except 1-2 and you go out in 1 roll
        test_move_count_distribution([4, 1, 0, 1], [0, 34/36, 2/36])

    def test_round_trip_save_load(self):
        config = board.GameConfiguration(3, 2)
        store = strategy.DistributionStore(config)
        store.compute()

        with tempfile.TemporaryFile() as tmp:
            store.save_hdf5(tmp)

            tmp.seek(0)
        
            loaded_store = strategy.DistributionStore.load_hdf5(tmp)

            self.assertEqual(store.config.num_markers,
                             loaded_store.config.num_markers)
            self.assertEqual(store.config.num_spots,
                             loaded_store.config.num_spots)
            self.assertEqual(len(store.distribution_map),
                             len(loaded_store.distribution_map))
            for board_idx, mcd in store.distribution_map.items():
                np.testing.assert_allclose(
                    mcd.dist,
                    loaded_store.distribution_map[board_idx].dist)
        

if __name__ == '__main__':
    unittest.main()
