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

import argparse

import board
import strategy

parser = argparse.ArgumentParser()
parser.add_argument("num_markers")
parser.add_argument("num_spots")
args = parser.parse_args()
num_markers = int(args.num_markers)
num_spots = int(args.num_spots)

config = board.GameConfiguration(num_markers, num_spots)
store = strategy.DistributionStore(config)
store.compute()
fn = "data/bgend_store_%d_%d.hdf5" % (num_markers, num_spots)
store.save_hdf5(fn)
