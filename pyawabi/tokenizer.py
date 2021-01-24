################################################################################
# MIT License
#
# Copyright (c) 2020-2021 Hajime Nakagami
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

from . import mecabrc
from .dic import CharProperty, MecabDic, Matrix
from .lattice import Lattice, Node


class Tokenizer:
    def __init__(self, path=None):
        mecabrc_map = mecabrc.get_mecabrc_map(path)
        self.sys_dic = MecabDic(mecabrc.get_dic_path(mecabrc_map, "sys.dic"))
        if "userdic" in mecabrc_map:
            self.user_dic = MecabDic(mecabrc_map["userdic"])
        else:
            self.user_dic = None
        self.cp = CharProperty(mecabrc.get_dic_path(mecabrc_map, "char.bin"))
        self.unk_dic = MecabDic(mecabrc.get_dic_path(mecabrc_map, "unk.dic"))
        self.matrix = Matrix(mecabrc.get_dic_path(mecabrc_map, "matrix.bin"))

    def build_lattice(self, s):
        lat = Lattice(len(s))
        pos = 0
        while pos < len(s):
            matched = False

            # user_dic
            if self.user_dic:
                user_entries = self.user_dic.lookup(s[pos:])
                if user_entries:
                    for entry in user_entries:
                        lat.add(Node.create_by_entry(entry), self.matrix)
                    matched = True

            # sys_dic
            sys_entries = self.sys_dic.lookup(s[pos:])
            if sys_entries:
                for entry in sys_entries:
                    lat.add(Node.create_by_entry(entry), self.matrix)
                matched = True

            # unknown
            unk_entries, invoke = self.unk_dic.lookup_unknowns(s[pos:], self.cp)
            if invoke or matched is False:
                for entry in unk_entries:
                    lat.add(Node.create_by_entry(entry), self.matrix)

            pos += lat.forward()

        lat.end(self.matrix)

        # lat.dump_snodes_list()
        # lat.dump_enodes_list()

        return lat

    def tokenize(self, s):
        lat = self.build_lattice(s.encode('utf-8'))
        nodes = lat.backward()

        morphemes = []
        for node in nodes[1:-1]:
            morphemes.append(
                (node.original.decode('utf-8'), node.feature.decode('utf-8'))
            )
        return morphemes

    def tokenize_n_best(self, s, n):
        lat = self.build_lattice(s.encode('utf-8'))
        morphemes_list = []
        for nodes in lat.backward_astar(n, self.matrix):
            morphemes = []
            for node in nodes[1:-1]:
                morphemes.append(
                    (node.original.decode('utf-8'), node.feature.decode('utf-8'))
                )
            morphemes_list.append(morphemes)

        return morphemes_list
