# -*- coding: utf-8 -*-
"""pkg-B 证据件装配（A-1 口径：本包 evidence/ 与 deviations/ 各件的生成入口）。

与主实现独立成形：函数划分、参数面、拼装顺序均按本包自切节的结果组织，
不引用、不复用另一实现的任何模块。每个函数返回对应交付件的完整 JSON 载荷
（含规范 sha256），由构建流程落盘；本文件不写任何输出路径（落盘是构建流程的事）。

规范 sha：sha256(json.dumps(载荷, sort_keys=True, separators=(",",":"),
ensure_ascii=False).encode("utf-8"))；集合／映射的载荷取裸条目表，标量取裸值，
对账件取 {anchor, measured, self_reported, items} 四键。
"""
from __future__ import annotations

import hashlib
import json

RULE_TEXT = (
    "流式逐行扫描语料：先定位 Methods 节标题行进窗、遇 Discussion 节标题行出窗，"
    "窗内整行以 Step N: 起首者判为步骤标题（按位置取、编号序列校验 1..N 连续）；"
    "禁用标题去重、禁按标题内容判步骤"
)
RULE_SOURCE = "paper_text.txt#L23-L67"


def canonical_sha(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assemble_protocol(step_rows):
    """step_rows: [{pos,label,title,target,evidence_loc,input,output}]，行号由本包实定位。"""
    return {
        "rule": RULE_TEXT,
        "source": RULE_SOURCE,
        "steps": [
            {
                "pos": r["pos"],
                "label": r["label"],
                "title": r["title"],
                "src": "paper_text.txt",
                "kind": "line",
                "target": r["target"],
                "evidence_loc": r["evidence_loc"],
                "input": r["input"],
                "output": r["output"],
            }
            for row in step_rows
            for r in [row]
        ],
    }


def assemble_anchors(anchor_rows):
    return [{"id": r["id"], "value": r["value"], "source": r["source"]} for r in anchor_rows]


def assemble_readings(h2_count, h3_count, tr_total, corpus_digest, ruling_text, row_keys):
    level_items = [{"key": "H2", "value": h2_count}, {"key": "H3", "value": h3_count}]
    row_items = [{"key": k, "ord": i + 1} for i, k in enumerate(row_keys)]
    return [
        {"name": "h2_h3_level_counts", "kind": "map",
         "sha256": canonical_sha(level_items), "items": level_items, "rows": len(level_items)},
        {"name": "table2_tr_total", "kind": "scalar",
         "sha256": canonical_sha(tr_total), "value": tr_total},
        {"name": "corpus_sha", "kind": "scalar",
         "sha256": canonical_sha(corpus_digest), "value": corpus_digest},
        {"name": "k_ruling", "kind": "scalar",
         "sha256": canonical_sha(ruling_text), "value": ruling_text},
        {"name": "table2_rows", "kind": "set",
         "sha256": canonical_sha(row_items), "items": row_items, "rows": len(row_items)},
    ]


def assemble_diff_a01(titles, measured, self_reported_word):
    """自报侧是英文数词（str）、实测侧是整数：两侧不同型，gap／direction 置 null，
    不做跨型算术（记账在 README 机器段 nulls[]）。items＝步骤行清单（逐行给出）。"""
    items = [{"key": t, "ord": i + 1} for i, t in enumerate(titles)]
    core = {"anchor": "A01", "measured": measured,
            "self_reported": self_reported_word, "items": items}
    return {
        "anchor": "A01",
        "measured": measured,
        "self_reported": self_reported_word,
        "items": items,
        "rows": len(items),
        "gap": None,
        "direction": None,
        "sha256": canonical_sha(core),
    }


def assemble_contrast():
    """本单无对照项（三个 peer 清单皆空）：唯一合法形状是空数组。"""
    return []
