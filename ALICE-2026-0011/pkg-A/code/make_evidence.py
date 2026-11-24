# -*- coding: utf-8 -*-
"""pkg-A 证据件装配（A-1 口径：evidence/ 与 deviations/ 各件的生成入口）。

每个函数返回对应交付件的完整 JSON 载荷（含规范 sha256），由构建流程落盘：
  make_protocol(step_rows)     -> evidence/protocol.json（rule/source/steps 三键闭集）
  make_anchors(anchor_rows)    -> evidence/anchors.json（A01–A13 三键行）
  make_readings(blocks)        -> deviations/readings.json（名表五条，sha 自洽）
  make_diff_a01(titles, self_reported) -> deviations/diff_A01.json（八键）
  make_contrast()              -> deviations/contrast.json（本单无对照项：[]）

规范 sha 口径：sha256(json.dumps(载荷, sort_keys=True, separators=(",",":"),
ensure_ascii=False).encode("utf-8"))；set/map 的载荷＝裸 items，scalar＝裸 value，
diff 的载荷＝{anchor, measured, self_reported, items}。
"""
from __future__ import annotations

import hashlib
import json

PROTOCOL_RULE = (
    "先列 Methods 这个 H1 下的全部直接子节标题，再按位置取标题以 Step 起首的 H2；"
    "整行逐字匹配、区间内恰 1 次、行号严格递增；禁用标题去重、禁按标题内容判步骤"
)
PROTOCOL_SOURCE = "paper_text.txt#L23-L67"


def canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_protocol(step_rows):
    """step_rows: [{pos,label,title,target,evidence_loc,input,output}]（行号已实定位）。"""
    steps = []
    for row in step_rows:
        steps.append({
            "pos": row["pos"],
            "label": row["label"],
            "title": row["title"],
            "src": "paper_text.txt",
            "kind": "line",
            "target": row["target"],
            "evidence_loc": row["evidence_loc"],
            "input": row["input"],
            "output": row["output"],
        })
    return {"rule": PROTOCOL_RULE, "source": PROTOCOL_SOURCE, "steps": steps}


def make_anchors(anchor_rows):
    """anchor_rows: [{id,value,source}]，A01–A13 顺序。"""
    return [{"id": r["id"], "value": r["value"], "source": r["source"]} for r in anchor_rows]


def make_readings(h2_h3, tr_total, corpus_sha, k_ruling, table2_row_keys):
    """名表五条（顺序＝题面 §二.3）；table2_row_keys 为 ['r1',...,'r<N>']。"""
    items_h = [{"key": "H2", "value": h2_h3["H2"]}, {"key": "H3", "value": h2_h3["H3"]}]
    items_t = [{"key": k, "ord": i + 1} for i, k in enumerate(table2_row_keys)]
    return [
        {"name": "h2_h3_level_counts", "kind": "map", "sha256": canon_sha(items_h),
         "items": items_h, "rows": len(items_h)},
        {"name": "table2_tr_total", "kind": "scalar", "sha256": canon_sha(tr_total),
         "value": tr_total},
        {"name": "corpus_sha", "kind": "scalar", "sha256": canon_sha(corpus_sha),
         "value": corpus_sha},
        {"name": "k_ruling", "kind": "scalar", "sha256": canon_sha(k_ruling),
         "value": k_ruling},
        {"name": "table2_rows", "kind": "set", "sha256": canon_sha(items_t),
         "items": items_t, "rows": len(items_t)},
    ]


def make_diff_a01(titles, measured, self_reported):
    """items＝M1 步骤行清单（key＝标题逐字，ord＝出现序）；self_reported 为 str 英文数词，
    与 int 实测不同型 ⇒ gap／direction 置 null（不对 str 做算术），由 README.nulls[] 记账。"""
    items = [{"key": t, "ord": i + 1} for i, t in enumerate(titles)]
    payload = {"anchor": "A01", "measured": measured, "self_reported": self_reported, "items": items}
    return {
        "anchor": "A01",
        "measured": measured,
        "self_reported": self_reported,
        "items": items,
        "rows": len(items),
        "gap": None,
        "direction": None,
        "sha256": canon_sha(payload),
    }


def make_contrast():
    """本单无对照件（peer_held[]=[]／peer_unheld[]=[]／peer_universe[]=[]）：交 []。"""
    return []
