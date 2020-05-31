#!/usr/bin/python3

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

import timeit

import board
import strategy

def setup():
    global store
    store = strategy.DistributionStore.load_hdf5('data/bgend_store_15_6.hdf5')

BOARD_LIST = [1046905,
              1376236,
              1567095,
              1769255,
              1897213,
              1963925,
              2026203,
              2076269,
              487420,
              860127]

def test_compute_move_distribution():
    for board_id in BOARD_LIST:
        this_board = board.Board.from_id(store.config, board_id)
        dist = store.compute_move_distribution_for_board(this_board)

if __name__ == '__main__':
    num_iterations = 5
    time_taken = timeit.timeit("test_compute_move_distribution()",
                               setup="from __main__ import setup, test_compute_move_distribution; setup()",
                               number=num_iterations)
    print("test_compute_move_distribution: {:.6f}".format(time_taken / len(BOARD_LIST) / num_iterations))
