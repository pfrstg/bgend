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

# This module contains classes for interfacing with gnubg, which we
# use to validate that we produce the same ending databases.

import base64
import gmpy2
import os
import re
import subprocess
import time

import board
import strategy


def position_id_string_to_board(config, pos_id_str):
    """Convert a Base64 endcoded position ID from gnubg to a Board.

    See 
    https://www.gnu.org/software/gnubg/manual/html_node/A-technical-description-of-the-Position-ID.html
    for a description of their position id encoding.

    Args:
      config: board.GameConfiguration
      pos_id_str: Base64 encoded position ID from gnubg

    Returns:
      board.Board
    """
    pos_id = int.from_bytes(base64.b64decode(pos_id_str + '=='),
                            byteorder='little')

    # pos_id is just like our encoding except they don't explictly
    # have the bits for markers off the board. We'll just count how many
    # markers there are and add those 1s in.
    missing_markers = config.num_markers - gmpy2.popcount(pos_id) 
    modified_pos_id = ( (pos_id << (missing_markers + 1)) |
                        ~(~0 << missing_markers) )

    return board.Board.from_index(config, modified_pos_id)


def parse_gnubg_dump(config, gnubg_str):
    """Parse the output of gnubg's "bearoffdump".
    
    This parses the "Opponent" move distribution from thet "Bearing off" column

    Args:
      config: board.GameConfiguration
      gnubg_str: string to parse

    Returns
      board.Board, strategy.MoveCountDistribution
    """
    pos_id_str = None
    mcd = None
    parsing_mcd = False

    pos_id_re = re.compile(r'GNU Backgammon  Position ID: ([A-Za-z0-9+/]*)')
    start_mcd_re = re.compile(r'^Rolls\s+Player\s+Opponent')
    mcd_line_re = re.compile(
        r'^\s*\d+\s+[\d\.]+\s+([\d\.]+)')
    
    for line in gnubg_str.splitlines():
        if parsing_mcd:
            match = mcd_line_re.search(line)
            if match:
                value = float(match.group(1)) / 100.0
                if not mcd:
                    mcd = strategy.MoveCountDistribution([value])
                else:
                    mcd = mcd.append([value])
            else:
                parsing_mcd = False

        elif start_mcd_re.search(line):
            parsing_mcd = True

        else:
            match = pos_id_re.search(line)
            if match:
                pos_id_str = match.group(1)

    if not pos_id_str:
        raise ValueError('Never found position id line')
    if not mcd:
        raise ValueError('Never found move distribution')
    
    return position_id_string_to_board(config, pos_id_str), mcd


def create_distribution_store_from_gnubg(gnubg_dir):
    """Creates a database in our format from the gnubg database.

    This uses a really dumb and inefficient strategy of calling
    'bearoffdump' many times as separate processes. But it allows us
    to not tweak the gnubg code and not have to deal with the vagaries
    of their format (just some annoying text parsing)

    Args:
      gnubg_dir: source directory of gnubg with everyting compiled 

    Returns:
      strategy.DistributionStore

    """
    progress_interval = 500
    
    config = board.GameConfiguration(15, 6)
    store = strategy.DistributionStore(config)

    start_time = time.time()

    # gnubg uses a 1 based index as an argument to bearoffdump
    for idx in range(1, config.num_valid_boards + 1):
        completed_process = subprocess.run(
            [os.path.join(gnubg_dir, 'bearoffdump'),
             os.path.join(gnubg_dir, 'gnubg_os0.bd'),
             '-n',
             str(idx)],
            universal_newlines=True,
            stdout=subprocess.PIPE,
            check=True)

        try:
            b, mcd = parse_gnubg_dump(config, completed_process.stdout)
        except ValueError as err:
            raise ValueError('For gnubg index {}: {}'.format(idx, err))
        store.distribution_map[b.get_index()] = mcd

        if idx % progress_interval == 0:
            frac_complete = idx / config.num_valid_boards
            this_time = time.time()
            print("%d/%d %.1f%%, %fs elapsed, %fs estimated total" % (
                idx,
                config.num_valid_boards,
                frac_complete * 100,
                this_time - start_time,
                (this_time - start_time) / frac_complete), 
                  flush=True)

        
    return store
