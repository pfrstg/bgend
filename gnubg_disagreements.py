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

import numpy as np
import pandas as pd
import random

import board
import strategy


SAMPLE_EVERY = 0

def find_disagreement():
    print("Reading stores")
    our_store = strategy.DistributionStore.load_hdf5('data/bgend_store_15_6.hdf5')
    their_store = strategy.DistributionStore.load_hdf5('data/gnubg_store_15_6.hdf5')
    config = our_store.config

    print("Starting analysis")

    move_disagreements = []
    boards_examined = 0
    progress_indicator = strategy.ProgressIndicator(config.num_valid_boards, 500)

    for board_id in our_store.distribution_map:
        progress_indicator.complete_one()
        if np.random.randint(0, SAMPLE_EVERY) > 0:
            continue

        boards_examined += 1

        b = board.Board.from_id(config, board_id)
        our_mcd = our_store.distribution_map[board_id]
        their_mcd = their_store.distribution_map[board_id]

        for roll in board.ROLLS:
            our_moves = our_store.compute_best_moves_for_roll(b, roll)
            their_moves = their_store.compute_best_moves_for_roll(b, roll)
            our_board = b.apply_moves(our_moves)
            their_board = b.apply_moves(their_moves)
            if our_board.get_id() == their_board.get_id():
                continue
            our_moves_our_ev = our_store.distribution_map[our_board.get_id()].expected_value()
            our_moves_their_ev = their_store.distribution_map[our_board.get_id()].expected_value()
            their_moves_our_ev = our_store.distribution_map[their_board.get_id()].expected_value()
            their_moves_their_ev = their_store.distribution_map[their_board.get_id()].expected_value()

            move_disagreements.append( (b.get_id(),
                                        roll.dice[0], roll.dice[1],
                                        board.encode_moves_string(our_moves),
                                        our_moves_our_ev,
                                        our_moves_their_ev,
                                        board.encode_moves_string(their_moves),
                                        their_moves_our_ev,
                                        their_moves_their_ev,
            )
            )

    print("Examined {} boards, found {} disagreement".format(boards_examined, len(move_disagreements)))

    df = pd.DataFrame.from_records(data=move_disagreements,
                                   index=None,
                                   columns=["board_idx", "roll0", "roll1",
                                            "our_moves", "our_moves_our_ev", "our_moves_their_ev",
                                            "their_moves", "their_moves_our_ev", "their_moves_their_ev"],
                                   )
    df.to_csv("data/disagreements.csv")



if __name__ == '__main__':
    find_disagreement()
