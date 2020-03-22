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

import array
import base64
import gmpy2

import board

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
    spot_counts = array.array('b', [0] * (config.num_spots + 1))

    pos_id = int.from_bytes(base64.b64decode(pos_id_str + '=='),
                            byteorder='little')

    # pos_id is just like our encoding except they don't explictly
    # have the bits for markers off the board. We'll just count how many
    # markers there are and add those 1s in.
    missing_markers = config.num_markers - gmpy2.popcount(pos_id) 
    modified_pos_id = ( (pos_id << (missing_markers + 1)) |
                        ~(~0 << missing_markers) )

    print(bin(pos_id))
    print(bin(modified_pos_id))
    return board.Board.from_index(config, modified_pos_id)
