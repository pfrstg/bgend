import numpy as np
import unittest

import strategy


class MoveCountDistributionTestCase(unittest.TestCase):

    def test_init(self):
        d = strategy.MoveCountDistribution()
        np.testing.assert_allclose(d.dist, [1])
        
        
if __name__ == '__main__':
    unittest.main()
