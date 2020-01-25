#!/usr/bin/python3

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
