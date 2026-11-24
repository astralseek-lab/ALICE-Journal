# -*- coding: utf-8 -*-
"""M2 入口（pkg-B 独立实现）：Table 1 术语行数——流式 iterparse。

与主实现相互独立：主实现整树解析后按 label 找表；本实现用 iterparse 事件流
顺序扫件，遇到 table-wrap 闭事件就地判定、就地计数、随即 clear，不保留整树。
口径同题面 §二.1：数 `tbody` 内 Term 列（首格）文本非空的 `<tr>`，表头不计；
按单元格文本判、不按视觉合并。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _text(elem):
    return "".join(elem.itertext()).strip()


def _tally(tw):
    tbody = None
    label = ""
    for child in tw:
        if _local(child.tag) == "label":
            label = _text(child)
        if _local(child.tag) == "table":
            tbody = next((e for e in child.iter() if _local(e.tag) == "tbody"), None)
    if tbody is None:
        for e in tw.iter():
            if _local(e.tag) == "tbody":
                tbody = e
                break
    if tbody is None:
        return label, []
    terms = []
    for tr in tbody:
        if _local(tr.tag) != "tr":
            continue
        cells = [c for c in tr if _local(c.tag) in ("td", "th")]
        head_cell = _text(cells[0]) if cells else ""
        if head_cell:
            terms.append(head_cell)
    return label, terms


def tally_table1_term_rows(path):
    found = None
    for _event, elem in ET.iterparse(path, events=("end",)):
        if _local(elem.tag) == "table-wrap":
            label, terms = _tally(elem)
            if label == "Table 1.":
                found = terms
            elem.clear()
    if found is None:
        raise RuntimeError("Table 1. 的 table-wrap 未在事件流中出现")
    return {"v": len(found), "unit": "count", "terms": found}
