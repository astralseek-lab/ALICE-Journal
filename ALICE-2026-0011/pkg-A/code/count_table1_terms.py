# -*- coding: utf-8 -*-
"""M2 入口（pkg-A 主实现）：Table 1 术语行数。

口径（题面 §二.1 写死）：JATS XML 母件中 `Table 1` 的数据行数——数 `tbody` 内
`Term` 列（首格）非空的 `<tr>`；`thead` 首行（表头）不计；合并单元格按 Term 列
非空行计，不按视觉行高。数源只认 XML 的 `<tr>`，不从抽取件取、不蒸表体。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _text(elem):
    return "".join(elem.itertext()).strip()


def count_table1_terms(path):
    root = ET.parse(path).getroot()
    for tw in root.iter():
        if _local(tw.tag) != "table-wrap":
            continue
        label = ""
        for child in tw:
            if _local(child.tag) == "label":
                label = _text(child)
                break
        if label != "Table 1.":
            continue
        tbody = next((e for e in tw.iter() if _local(e.tag) == "tbody"), None)
        if tbody is None:
            return {"v": 0, "unit": "count", "terms": []}
        terms = []
        for tr in tbody:
            if _local(tr.tag) != "tr":
                continue
            cells = [c for c in tr if _local(c.tag) in ("td", "th")]
            term = _text(cells[0]) if cells else ""
            if term:
                terms.append(term)
        return {"v": len(terms), "unit": "count", "terms": terms}
    raise RuntimeError("Table 1. 的 table-wrap 未找到")
