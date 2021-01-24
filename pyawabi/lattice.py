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

import heapq


class Node:

    __slots__ = ["original", "feature", "node_len", "pos", "epos", "index", "left_id", "right_id", "cost", "min_cost", "back_pos", "back_index", "skip"]

    @classmethod
    def create_bos(cls):
        return cls(None, None, 0, 1, 0, -1, 0, 0, 0, -1, -1, False)

    @classmethod
    def create_eos(cls, pos):
        return cls(None, None, pos, pos + 1, 0, 0, -1, 0, 0x7FFFFFFF, -1, -1, False)

    @classmethod
    def create_by_entry(cls, e):
        return cls(e.original, e.feature, 0, 0, e.posid, e.lc_attr, e.rc_attr, e.wcost, 0x7FFFFFFF, -1, -1, e.skip)

    def __init__(self, original, feature, pos, epos, index, left_id, right_id, cost, min_cost, back_pos, back_index, skip):
        self.original = original
        self.feature = feature
        self.pos = pos
        self.epos = epos
        self.index = index
        self.left_id = left_id
        self.right_id = right_id
        self.cost = cost
        self.min_cost = min_cost
        self.back_pos = back_pos
        self.back_index = back_index
        self.skip = skip
        self.node_len = len(self.original) if self.original else 1     # 1: BOS or EOS

    def is_bos(self):
        return self.original is None and self.pos == 0

    def is_eos(self):
        return self.original is None and self.pos != 0

    def __repr__(self):
        original = self.original.decode('utf-8') if self.original else ""
        feature = self.feature.decode('utf-8') if self.feature else ""
        return f"{original},{feature},{self.node_len},{self.pos},{self.epos},{self.index},{self.left_id},{self.right_id},{self.cost},{self.min_cost},{self.back_pos},{self.back_index},{self.skip}"


class Lattice:
    def __init__(self, size):
        bos = Node.create_bos()
        self.snodes = [[bos]] + [[] for i in range(0, size + 1)]
        self.enodes = [[], [bos]] + [[] for i in range(0, size + 1)]
        self.p = 1

    def add(self, node, matrix):
        min_cost = node.min_cost
        best_node = self.enodes[self.p][0]

        for enode in self.enodes[self.p]:
            if enode.skip:
                for enode2 in self.enodes[enode.pos]:
                    if (cost := enode2.min_cost + matrix.get_trans_cost(enode2.right_id, node.left_id)) < min_cost:
                        min_cost = cost
                        best_node = enode2
            else:
                if (cost := enode.min_cost + matrix.get_trans_cost(enode.right_id, node.left_id)) < min_cost:
                    min_cost = cost
                    best_node = enode

        node.min_cost = min_cost + node.cost
        node.back_index = best_node.index
        node.back_pos = best_node.pos
        node.pos = self.p
        node.epos = self.p + node.node_len
        node.index = len(self.snodes[self.p])
        self.snodes[node.pos].append(node)
        self.enodes[node.epos].append(node)

    def forward(self):
        old_p = self.p
        self.p += 1
        while len(self.enodes[self.p]) == 0:
            self.p += 1
        return self.p - old_p

    def end(self, matrix):
        self.add(Node.create_eos(self.p), matrix)
        self.snodes = self.snodes[:self.p+1]
        self.enodes = self.enodes[:self.p+2]

    def backward(self):
        shortest_path = []
        pos = len(self.snodes) - 1
        index = 0
        while pos >= 0:
            node = self.snodes[pos][index]
            index = node.back_index
            pos = node.back_pos
            shortest_path.append(node)

        shortest_path.reverse()
        return shortest_path

    def backward_astar(self, n, matrix):
        paths = []
        epos = len(self.enodes) - 1
        node = self.enodes[epos][0]
        assert node.is_eos()
        pq = []
        bp = BackwardPath(matrix, node)
        heapq.heappush(pq, bp)

        while pq and n:
            bp = heapq.heappop(pq)
            if bp.is_complete():
                bp.back_path.reverse()
                paths.append(bp.back_path)
                n -= 1
            else:
                node = bp.back_path[-1]
                epos = node.epos - node.node_len
                for i in range(len(self.enodes[epos])):
                    node = self.enodes[epos][i]
                    heapq.heappush(pq, BackwardPath(matrix, node, bp))
        return paths

    def _dump_nodes_list(self, prompt, nodes_list):
        print("+" * 110)
        print(prompt)
        for nodes in nodes_list:
            print("-" * 110)
            self._dump_nodes(nodes)

    def _dump_nodes(self, nodes):
        print("-" * 110)
        for node in nodes:
            print(node)

    def dump_snodes_list(self):
        # for debug
        self._dump_nodes_list("snodes", self.snodes)

    def dump_enodes_list(self):
        # for debug
        self._dump_nodes_list("enodes", self.enodes)


class BackwardPath:
    def __init__(self, matrix, node, right_path=None):
        self.cost_from_bos = node.min_cost
        self.cost_from_eos = 0
        self.back_path = []

        if right_path is not None:
            neighbor_node = right_path.back_path[-1]
            self.cost_from_eos = (
                right_path.cost_from_eos +
                neighbor_node.cost +
                matrix.get_trans_cost(node.right_id, neighbor_node.left_id)
            )
            self.back_path = right_path.back_path[:]
        else:
            assert node.is_eos()

        self.back_path.append(node)

    def __lt__(self, other):
        return self.cost_from_bos + self.cost_from_eos < other.cost_from_bos + other.cost_from_eos

    def is_complete(self):
        return self.back_path[-1].is_bos()
