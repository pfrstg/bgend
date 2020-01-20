# Copyright 2020 Patrick Riley <patriley@gmail.com>

import numpy as np


class MoveCountDistribution(object):
    """Stores a distribution over number of moves till end of game."""

    def __init__(self):
        self.dist = np.ones([1])
