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

import heapq


class Node:

    __slots__ = ["entry", "node_len", "pos", "epos", "index", "left_id", "right_id", "cost", "min_cost", "back_pos", "back_index", "skip"]

    @classmethod
    def create_bos(cls):
        return cls(None, 0, 1, 0, -1, 0, 0, 0, -1, -1, False)

    @classmethod
    def create_eos(cls, pos):
        return cls(None, pos, pos + 1, 0, 0, -1, 0, 0x7FFFFFFF, -1, -1, False)

    @classmethod
    def create_by_entry(cls, e):
        original, lc_attr, rc_attr, posid, wcost, feature, skip = e
        return cls(e, 0, 0, posid, lc_attr, rc_attr, wcost, 0x7FFFFFFF, -1, -1, skip)

    def __init__(self, entry, pos, epos, index, left_id, right_id, cost, min_cost, back_pos, back_index, skip):
        self.entry = entry
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
        self.node_len = len(self.entry[0]) if self.entry else 1     # 1: BOS or EOS

    def is_bos(self):
        return self.entry is None and self.pos == 0

    def is_eos(self):
        return self.entry is None and self.pos != 0

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
                bp.path.reverse()
                paths.append(bp.path)
                n -= 1
            else:
                node = bp.path[-1]
                epos = node.epos - node.node_len
                for index in range(len(self.enodes[epos])):
                    node = self.enodes[epos][index]
                    heapq.heappush(pq, BackwardPath(matrix, node, bp))
        return paths


class BackwardPath:
    def __init__(self, matrix, node, right_path=None):
        self.cost_from_bos = node.min_cost
        if right_path is None:
            assert node.is_eos()
            self.cost_from_eos = 0
            self.path = [node]
        else:
            neighbor_node = right_path.path[-1]
            self.cost_from_eos = (
                right_path.cost_from_eos +
                neighbor_node.cost +
                matrix.get_trans_cost(node.right_id, neighbor_node.left_id)
            )
            self.path = right_path.path[:]
            self.path.append(node)

    def __lt__(self, other):
        return self.cost_from_bos + self.cost_from_eos < other.cost_from_bos + other.cost_from_eos

    def is_complete(self):
        return self.path[-1].is_bos()
