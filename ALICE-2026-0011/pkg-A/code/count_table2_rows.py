# -*- coding: utf-8 -*-
"""M3 入口（pkg-A 主实现）：Table 2 数据行数。

口径（题面 §二.1 写死）：`Table 2` 的 `<tr>` 总数 − 表头行数（表头＝`thead` 里
`<th>` 那一行）；`colspan` 的 `Step N:` 横幅行照计为数据行（colspan 只影响视觉
合并、不影响 `<tr>` 计数）；不数 Table 3。数源只认 XML。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _text(elem):
    return "".join(elem.itertext()).strip()


def count_table2_rows(path):
    root = ET.parse(path).getroot()
    for tw in root.iter():
        if _local(tw.tag) != "table-wrap":
            continue
        label = ""
        for child in tw:
            if _local(child.tag) == "label":
                label = _text(child)
                break
        if label != "Table 2.":
            continue
        all_tr = [e for e in tw.iter() if _local(e.tag) == "tr"]
        thead = next((e for e in tw.iter() if _local(e.tag) == "thead"), None)
        head_rows = len([e for e in thead if _local(e.tag) == "tr"]) if thead is not None else 0
        data = all_tr[head_rows:]
        return {
            "v": len(all_tr) - head_rows,
            "unit": "count",
            "tr_total": len(all_tr),
            "head_rows": head_rows,
            "first_cells": [
                (_text([c for c in tr if _local(c.tag) in ("td", "th")][0]) if [c for c in tr if _local(c.tag) in ("td", "th")] else "")
                for tr in data
            ],
        }
    raise RuntimeError("Table 2. 的 table-wrap 未找到")
