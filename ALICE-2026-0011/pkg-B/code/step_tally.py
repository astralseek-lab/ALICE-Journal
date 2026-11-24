# -*- coding: utf-8 -*-
"""M1 入口（pkg-B 独立实现）：步骤标题数——序列法。

与主实现的分工（题面 §4.1 写死）：主实现按位置做「区间内计数」；本实现做
「编号序列校验」——流式逐行读入（不整篇载入），先定位 Methods 节标题行进入
窗口、遇 Discussion 节标题行出窗口，窗口内收集整行以 `Step N:` 起首的标题行，
校验其编号恰为 1..N 连续不跳号，步数即 N。两法须同值，且与 M1 同值。

步标题逐字取自语料（冒号／连字符差异照留，不归一）。
"""
from __future__ import annotations

import re

STEP_LINE = re.compile(r"^Step ([0-9]+):")


def tally_step_titles(path):
    numbers = []
    titles = []
    in_window = False
    with open(path, encoding="utf-8") as fh:  # 流式：逐行迭代，不整篇载入
        for raw in fh:
            line = raw.rstrip("\r\n")
            if not in_window:
                if line == "Methods":
                    in_window = True
                continue
            if line == "Discussion":
                break
            m = STEP_LINE.match(line)
            if m:
                numbers.append(int(m.group(1)))
                titles.append(line)
    n = len(titles)
    sequence_ok = sorted(numbers) == list(range(1, n + 1)) and n == len(set(numbers))
    return {"v": n, "unit": "count", "sequence_ok": sequence_ok, "titles": titles}
