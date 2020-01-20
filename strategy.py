# Copyright 2020 Patrick Riley <patriley@gmail.com>

import numpy as np


class MoveCountDistribution(object):
    """Stores a distribution over number of moves till end of game."""

    __slots__ = ["dist"]
    
    def __init__(self, dist=np.ones([1])):
        self.dist = dist

    def increase_counts(self, amount):
        return MoveCountDistribution(np.insert(self.dist, 0, [0] * amount))
