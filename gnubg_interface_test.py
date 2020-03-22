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

import unittest

import board
import gnubg_interface


class PositionIDTest(unittest.TestCase):
    def test_from_string(self):
        config = board.GameConfiguration(15, 6)
        # index 1
        self.assertEqual(board.Board(config, [14, 1, 0, 0, 0, 0, 0]),
                         gnubg_interface.position_id_string_to_board(
                             config, 'AQAAAAAAAAAAAA'))
        # index 2
        self.assertEqual(board.Board(config, [14, 0, 1, 0, 0, 0, 0]),
                         gnubg_interface.position_id_string_to_board(
                             config, 'AgAAAAAAAAAAAA'))
        # index 99
        self.assertEqual(board.Board(config, [11, 2, 0, 0, 2, 0, 0]),
                         gnubg_interface.position_id_string_to_board(
                             config, 'YwAAAAAAAAAAAA'))
        # index 33333
        self.assertEqual(board.Board(config, [1, 1, 11, 0, 0, 1, 1]),
                         gnubg_interface.position_id_string_to_board(
                             config, '/R8FAAAAAAAAAA'))
        # index 50000 (everything is on the board)
        self.assertEqual(board.Board(config, [0, 1, 0, 3, 8, 3, 0]),
                         gnubg_interface.position_id_string_to_board(
                             config, 'uX8HAAAAAAAAAA'))
        
    

if __name__ == '__main__':
    unittest.main()
