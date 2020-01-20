# Copyright 2020 Patrick Riley <patriley@gmail.com>

import numpy as np


class MoveCountDistribution(object):
    """Stores a distribution over number of moves till end of game."""

    __slots__ = ["dist"]
    
    def __init__(self, dist=np.ones([1])):
        self.dist = np.asarray(dist)
        if len(self.dist.shape) != 1:
            raise ValueError("Need 1D shape, got %s", self.dist.shape)

    def __add__(self, other):
        return MoveCountDistribution(self.dist + other)
    
    def __sub__(self, other):
        return MoveCountDistribution(self.dist - other)
    
    def __mul__(self, other):
        return MoveCountDistribution(self.dist * other)
    
    def __truediv__(self, other):
        return MoveCountDistribution(self.dist / other)
    
    def increase_counts(self, amount):
        return MoveCountDistribution(np.insert(self.dist, 0, [0] * amount))

    
