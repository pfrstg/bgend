import numpy as np
import unittest

import strategy


class MoveCountDistributionTestCase(unittest.TestCase):

    def test_init(self):
        d = strategy.MoveCountDistribution()
        np.testing.assert_allclose(d.dist, [1])
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


if __name__ == '__main__':
    unittest.main()
