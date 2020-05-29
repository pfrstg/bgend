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

import random

import board
import strategy

SAMPLING_FRACTION = .005

store = strategy.DistributionStore.load_hdf5('data/bgend_store_15_6.hdf5')

print("Read store")

count = 0
for board_id in store.distribution_map.keys():
    if random.random() > SAMPLING_FRACTION:
        continue

    this_board = board.Board.from_id(store.config, board_id)
    dist = store.compute_move_distribution_for_board(this_board)

    count += 1
    if count % 100 == 0:
        print("Boards processed: {} at id {}".format(count, board_id))


print("Total boards processed: {}".format(count))
