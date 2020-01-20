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
        """Only support adding to another MoveCountDistribution."""
        max_len = max(self.dist.shape[0], other.dist.shape[0])
        return MoveCountDistribution(
            np.pad(self.dist, (0, max_len - self.dist.shape[0]),
                   mode="constant",
                   constant_values=0) +
            np.pad(other.dist, (0, max_len - other.dist.shape[0]),
                   mode="constant",
                   constant_values=0))                   
    
    def __sub__(self, other):
        """Only support subtracting to another MoveCountDistribution."""
        max_len = max(self.dist.shape[0], other.dist.shape[0])
        return MoveCountDistribution(
            np.pad(self.dist, (0, max_len - self.dist.shape[0]),
                   mode="constant",
                   constant_values=0) -
            np.pad(other.dist, (0, max_len - other.dist.shape[0]),
                   mode="constant",
                   constant_values=0))
    
    def __mul__(self, other):
        """Only support multiplying with a scalar."""
        return MoveCountDistribution(self.dist * other)
    
    def __truediv__(self, other):
        """Only support multiplying with a scalar."""
        return MoveCountDistribution(self.dist / other)
    
    def increase_counts(self, amount):
        return MoveCountDistribution(np.insert(self.dist, 0, [0] * amount))

    def is_normalized(self):
        return np.allclose(np.sum(self.dist), 1)

    def expected_value(self):
        return np.sum(self.dist * range(self.dist.shape[0]))
    
