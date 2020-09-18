################################################################################
# MIT License
#
# Copyright (c) 2020 Hajime Nakagami
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
################################################################################

import unittest
from pyawabi import mecabrc
from pyawabi.dic import CharProperty, MecabDic, Matrix


class TestDic(unittest.TestCase):
    def setUp(self):
        self.mecabrc_map = mecabrc.get_mecabrc_map()

    def test_matrix(self):
        matrix = Matrix(mecabrc.get_dic_path(self.mecabrc_map, "matrix.bin"))
        self.assertEqual(matrix.get_trans_cost(555, 1283), 340)
        self.assertEqual(matrix.get_trans_cost(10, 1293), -1376)

    def test_char_propery(self):
        cp = CharProperty(mecabrc.get_dic_path(self.mecabrc_map, "char.bin"))
        self.assertEqual(cp.category_names, [
            b"DEFAULT", b"SPACE", b"KANJI", b"SYMBOL", b"NUMERIC", b"ALPHA",
            b"HIRAGANA", b"KATAKANA", b"KANJINUMERIC", b"GREEK", b"CYRILLIC"
        ])
        self.assertEqual(cp.get_char_info(0), (0, 1, 0, 1, 0))          # DEFAULT
        self.assertEqual(cp.get_char_info(0x20), (1, 2, 0, 1, 0))       # SPACE
        self.assertEqual(cp.get_char_info(0x09), (1, 2, 0, 1, 0))       # SPACE
        self.assertEqual(cp.get_char_info(0x6f22), (2, 4, 2, 0, 0))     # KANJI 漢
        self.assertEqual(cp.get_char_info(0x3007), (3, 264, 0, 1, 1))   # SYMBOL
        self.assertEqual(cp.get_char_info(0x31), (4, 16, 0, 1, 1))      # NUMERIC 1
        self.assertEqual(cp.get_char_info(0x3042), (6, 64, 2, 1, 0))    # HIRAGANA あ
        self.assertEqual(cp.get_char_info(0x4e00), (8, 260, 0, 1, 1))   # KANJINUMERIC 一

    def test_lookup(self):
        sys_dic = MecabDic(mecabrc.get_dic_path(self.mecabrc_map, "sys.dic"))
        s = "すもももももももものうち".encode('utf-8')
        self.assertEqual(len(sys_dic.common_prefix_search(s)), 3)
        self.assertEqual(len(sys_dic.lookup(s)), 9)
        s = "もももももも".encode('utf-8')
        self.assertEqual(len(sys_dic.common_prefix_search(s)), 2)
        self.assertEqual(len(sys_dic.lookup(s)), 4)

    def test_lookup_unknowns(self):
        unk_dic = MecabDic(mecabrc.get_dic_path(self.mecabrc_map, "unk.dic"))
        cp = CharProperty(mecabrc.get_dic_path(self.mecabrc_map, "char.bin"))
        self.assertEqual(unk_dic.exact_match_search(b'SPACE'), 9729)
        entries, invoke = unk_dic.lookup_unknowns("１９６７年".encode("utf-8"), cp)
        self.assertEqual(entries[0][0], "１９６７".encode("utf-8"))


if __name__ == "__main__":
    unittest.main()
