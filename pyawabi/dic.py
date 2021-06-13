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

import mmap
import struct
from functools import lru_cache
from collections import namedtuple

MAX_GROUPING_SIZE = 24


def utf8_to_ucs2(s, index):
    # utf8 to ucs2(16bit) code and it's array size
    s0 = s[index]
    if (s0 & 0b10000000) == 0b00000000:
        return s0, 1
    elif (s0 & 0b11100000) == 0b11000000:
        return ((s0 & 0x1F) << 6) | (s[index+1] & 0x3F), 2
    elif (s0 & 0b11110000) == 0b11100000:
        return ((s0 & 0x0F) << 12) | ((s[index+1] & 0x3F) << 6) | (s[index+2] & 0x3F), 3
    elif (s0 & 0b11111000) == 0b11110000:
        ch32 = ((s0 & 0x07) << 18) | ((s[index+1] & 0x3F) << 12) | ((s[index+2] & 0x3F) << 6) | (s[index+3] & 0x03F)
        return (((ch32-0x10000) // 0x400 + 0xD800) << 8) + ((ch32-0x10000) % 0x400 + 0xDC00), 4


DicEntry = namedtuple("DicEntry", ["original", "lc_attr", "rc_attr", "posid", "wcost", "feature", "skip"])


class CharProperty:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.category_names = []
            num_categories = int.from_bytes(f.read(4), byteorder='little')
            for i in range(num_categories):
                name = f.read(32)
                self.category_names.append(name[:name.find(b'\x00')])
            self.offset = 4 + num_categories * 32
            self.size = self.offset + 0xFFFF * 4
            self.mmap = mmap.mmap(f.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)

    def get_char_type(self, code_point):
        return struct.unpack_from('I', self.mmap, self.offset + code_point * 4)[0] & 0b111111111111111111

    def get_char_info(self, code_point):
        v = struct.unpack_from('I', self.mmap, self.offset + code_point * 4)[0]
        return (
            (v >> 18) & 0b11111111,     # default_type
            v & 0b111111111111111111,   # char_type
            (v >> 26) & 0b1111,         # char_count
            (v >> 30) & 0b1,            # group
            (v >> 31) & 0b1,            # invoke
        )

    def get_group_length(self, s, default_type):
        i = char_count = 0
        while i < len(s):
            ch16, ln = utf8_to_ucs2(s, i)
            if ((1 << default_type) & self.get_char_type(ch16)) != 0:
                i += ln
                char_count += 1
                if char_count > MAX_GROUPING_SIZE + 1:
                    return -1
            else:
                break

        return i

    def get_count_length(self, s, default_type, count):
        i = j = 0
        while j < count:
            if i >= len(s):
                return -1
            ch16, ln = utf8_to_ucs2(s, i)
            if ((1 << default_type) & self.get_char_type(ch16)) == 0:
                return -1
            i += ln
            j += 1
        return i

    def get_unknown_lengths(self, s):
        # get unknown word bytes length vector
        ln_list = []
        ch16, first_ln = utf8_to_ucs2(s, 0)

        default_type, _, count, group, invoke = self.get_char_info(ch16)
        if group != 0:
            ln = self.get_group_length(s, default_type)
            if ln > 0:
                ln_list.append(ln)
        if count != 0:
            n = 0
            while n < count:
                ln = self.get_count_length(s, default_type, n+1)
                if ln < 0:
                    break
                ln_list.append(ln)
                n += 1

        if len(ln_list) == 0:
            ln_list.append(first_ln)

        return default_type, ln_list, invoke == 1


class MecabDic:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.size = int.from_bytes(f.read(4), byteorder='little') ^ 0xef718f77

            self.version = int.from_bytes(f.read(4), byteorder='little')
            self.dictype = int.from_bytes(f.read(4), byteorder='little')
            self.lexsize = int.from_bytes(f.read(4), byteorder='little')
            self.lsize = int.from_bytes(f.read(4), byteorder='little')
            self.rsize = int.from_bytes(f.read(4), byteorder='little')
            dsize = int.from_bytes(f.read(4), byteorder='little')
            tsize = int.from_bytes(f.read(4), byteorder='little')
            fsize = int.from_bytes(f.read(4), byteorder='little')
            assert int.from_bytes(f.read(4), byteorder='little') == 0   # dummy
            charset = f.read(32)
            self.charset = charset[:charset.find(b'\x00')].decode('ascii')

            self.mmap = mmap.mmap(f.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)
            self.da_offset = 72
            self.token_offset = 72 + dsize
            self.feature_offset = self.token_offset + tsize

    def _get_base_check(self, idx):
        return struct.unpack_from('iI', self.mmap, self.da_offset + idx * 8)

    def exact_match_search(self, s):
        v = -1
        b, _ = self._get_base_check(0)
        for i in range(len(s)):
            p = b + s[i] + 1
            base, check = self._get_base_check(p)
            if b == check:
                b = base
            else:
                return v

        p = b
        n, check = self._get_base_check(p)
        if b == check and n < 0:
            v = -n-1

        return v

    def common_prefix_search(self, s):
        results = []
        b, _ = self._get_base_check(0)
        for i in range(len(s)):
            p = b
            n, check = self._get_base_check(p)
            if b == check and n < 0:
                results.append((-n-1, i))
            p = b + s[i] + 1
            base, check = self._get_base_check(p)
            if b == check:
                b = base
            else:
                return results

        p = b
        n, check = self._get_base_check(p)
        if b == check and n < 0:
            results.append((-n-1, len(s)))
        return results

    @lru_cache(maxsize=1024)
    def _get_entries_by_index(self, idx, count):
        mmap = self.mmap
        feature_offset = self.feature_offset

        results = []
        start = self.token_offset + idx * 16
        for i in range(start, start+count*16, 16):
            lc_attr, rc_attr, posid, wcost, feature = struct.unpack_from('HHHhI', mmap, i)
            k = j = feature_offset + feature
            while mmap[k]:
                k += 1

            results.append((
                lc_attr,
                rc_attr,
                posid,
                wcost,
                mmap[j:k],  # feature
            ))

        return results

    def get_entries_by_index(self, idx, count, s, skip):
        return [
            DicEntry(s, r[0], r[1], r[2], r[3], r[4], skip) for r in self._get_entries_by_index(idx, count)
        ]

    def get_entries(self, result, s, skip):
        return self.get_entries_by_index(result >> 8, result & 0xFF, s, skip)

    def lookup(self, s):
        results = []
        for result, ln in self.common_prefix_search(s):
            results.extend(
                self.get_entries_by_index(result >> 8, result & 0xff, s[:ln], False)
            )
        return results

    def lookup_unknowns(self, s, cp):
        default_type, ln_list, invoke = cp.get_unknown_lengths(s)
        category_name = cp.category_names[default_type]
        result = self.exact_match_search(category_name)
        results = []
        for ln in ln_list:
            results.extend(
                self.get_entries(result, s[:ln], category_name == b"SPACE")
            )
        return results, invoke


class Matrix:
    def __init__(self, path):
        with open(path, 'rb') as f:
            self.mmap = mmap.mmap(f.fileno(), 0, mmap.MAP_PRIVATE, mmap.PROT_READ)
            self.lsize = int.from_bytes(self.mmap[0:2], byteorder='little')
            self.rsize = int.from_bytes(self.mmap[2:4], byteorder='little')

    def get_trans_cost(self, id1, id2):
        return struct.unpack_from('h', self.mmap, (id2 * self.lsize + id1) * 2 + 4)[0]
