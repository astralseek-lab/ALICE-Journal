# -*- coding: utf-8 -*-
"""M1 入口（pkg-A 主实现）：步骤标题数。

口径（题面 §二.1 写死）：行式语料 paper_text.txt 中，`Methods` 这个 H1 节标题行
至 `Discussion` 节标题行（不含）之间，整行以 `Step N:` 起首的标题行按位置计数；
H1＝Methods 本身不数；Discussion 下的 H2 不是步骤；禁用标题去重、禁按内容判步骤。
实现法＝区间内计数法（两实现之一；另一实现序列法在独立包内）。

链的可信不靠它永不变，靠它变了会响。
"""
from __future__ import annotations

import re

STEP_HEAD = re.compile(r"^Step [0-9]+:")


def count_steps(path):
    """数窗口内 Step 起首行；窗口锚缺失时退到全文扫描（扰动下仍确定性地返值）。"""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    try:
        start = lines.index("Methods")
    except ValueError:
        start = 0
    try:
        stop = lines.index("Discussion", start + 1)
    except ValueError:
        stop = len(lines)
    titles = [ln for ln in lines[start:stop] if STEP_HEAD.match(ln)]
    return {"v": len(titles), "unit": "count", "titles": titles}
