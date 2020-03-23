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

import gnubg_interface

parser = argparse.ArgumentParser()
parser.add_argument("gnubg_dir")
args = parser.parse_args()

store = gnubg_interface.create_distribution_store_from_gnubg(
    args.gnubg_dir)
store.save_hdf5('data/gnubg_store_15_6.hdf5')

