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

import os
from pathlib import Path


def find_mecabrc():
    for s in ["/usr/local/etc/mecabrc", "/etc/mecabrc"]:
        if Path(s).is_file():
            return s
    return None


def get_mecabrc_map(rc_path=None):
    mecabrc_map = {}
    if not rc_path:
        rc_path = find_mecabrc()

    with open(rc_path, "r") as f:
        for s in f:
            s = s.strip()
            if '=' in s:
                k, v = s.split('=')
                mecabrc_map[k.strip()] = v.strip()
    return mecabrc_map


def get_dic_path(mecabrc_map, filename):
    return os.path.join(mecabrc_map["dicdir"], filename)
