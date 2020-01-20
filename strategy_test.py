import numpy as np
import unittest

import strategy


class MoveCountDistributionTestCase(unittest.TestCase):

    def test_init(self):
        d = strategy.MoveCountDistribution()
        np.testing.assert_allclose(d.dist, [1])

    def test_operators(self):
        d = strategy.MoveCountDistribution([0.75, 0.25])
        np.testing.assert_allclose((d + 1).dist, [1.75, 1.25])
        np.testing.assert_allclose((d - .05).dist, [.7, .2])
        np.testing.assert_allclose((d * 2).dist, [1.5, .5])
        np.testing.assert_allclose((d / 5).dist, [.15, .05])
        
    def test_increase_counts(self):
        d = strategy.MoveCountDistribution([0.75, 0.25])
        np.testing.assert_allclose(d.increase_counts(2).dist,
                                   [0, 0, 0.75, 0.25])
        
        
if __name__ == '__main__':
    unittest.main()
