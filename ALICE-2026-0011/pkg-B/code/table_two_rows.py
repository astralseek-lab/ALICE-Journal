# -*- coding: utf-8 -*-
"""M3 入口（pkg-B 独立实现）：Table 2 数据行数——按 tbody 归属直接数。

与主实现走不同的数法：主实现取「全表 `<tr>` 总数 − thead 行数」；本实现按
行与 thead/tbody 的**归属关系**直接数 tbody 内的 `<tr>`（表头行天然不计；
`colspan` 横幅行是 tbody 内的真 `<tr>`，照计为数据行）。两法须同值。
流式 iterparse，不整树驻留。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _text(elem):
    return "".join(elem.itertext()).strip()


def _tally(tw):
    label = ""
    tbody = None
    thead = None
    for child in tw:
        if _local(child.tag) == "label":
            label = _text(child)
        if _local(child.tag) == "table":
            thead = next((e for e in child.iter() if _local(e.tag) == "thead"), None)
            tbody = next((e for e in child.iter() if _local(e.tag) == "tbody"), None)
    if tbody is None:
        for e in tw.iter():
            if _local(e.tag) == "tbody":
                tbody = e
                break
    head_rows = len([e for e in thead if _local(e.tag) == "tr"]) if thead is not None else 0
    tr_total = len([e for e in tw.iter() if _local(e.tag) == "tr"])
    if tbody is None:
        return label, head_rows, tr_total, []
    rows = []
    for tr in tbody:
        if _local(tr.tag) != "tr":
            continue
        cells = [c for c in tr if _local(c.tag) in ("td", "th")]
        rows.append(_text(cells[0]) if cells else "")
    return label, head_rows, tr_total, rows


def tally_table2_data_rows(path):
    found = None
    for _event, elem in ET.iterparse(path, events=("end",)):
        if _local(elem.tag) == "table-wrap":
            label, head_rows, tr_total, rows = _tally(elem)
            if label == "Table 2.":
                found = (head_rows, tr_total, rows)
            elem.clear()
    if found is None:
        raise RuntimeError("Table 2. 的 table-wrap 未在事件流中出现")
    head_rows, tr_total, rows = found
    return {
        "v": len(rows),
        "unit": "count",
        "tr_total": tr_total,
        "head_rows": head_rows,
        "first_cells": rows,
    }
