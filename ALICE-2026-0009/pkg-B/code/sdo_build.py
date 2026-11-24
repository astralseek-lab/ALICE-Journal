# -*- coding: utf-8 -*-
"""pkg-B 派生件生成入口（A-1 口径：evidence 每件产物的生成入口在此各指一行）。

纯函数 gen_* 返回 {"v": <代表整数>, "payload": <件内容>}；写盘由 main() 完成。
本模块与 pkg-A 不共享任何代码（独立写成；路径一律 join 构造）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

import sdo_dom
import sdo_text

TASK_ID = "ALICE-2026-0009"
RUN_ID = "r_8ca461c01376"
A01_SELF_REPORT = 49          # 锚 A01：论文自报终版类数（差额件入账用）
INITIAL_VERSION_CLASSES = 9   # 摘要自报初版类数（readings 名表第 7 行）
READINGS_NAMES = [
    "L3_local", "L4_local", "L5_alt", "L5_selfcheck", "L6_alt",
    "dir_class_counts", "initial_version_class_count", "anonymous_class",
    "self_report_unmeasured",
]

EV = "evidence"
DV = "deviations"


def canon_sha(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def set_block(keys):
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def map_block(pairs):
    items = [{"key": k, "value": v} for k, v in sorted(pairs, key=lambda kv: kv[0])]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def _span_of(src_lines, def_line):
    indent_def = len(src_lines[def_line - 1]) - len(src_lines[def_line - 1].lstrip())
    body_end = def_line
    i = def_line + 1
    while i <= len(src_lines):
        ln = src_lines[i - 1]
        if ln.strip():
            cur = len(ln) - len(ln.lstrip())
            if cur <= indent_def and not ln.lstrip().startswith("#"):
                break
            if not ln.lstrip().startswith("#"):
                body_end = i
        i += 1
    return def_line, body_end


def _find_def(path, name):
    src_lines = Path(str(path)).read_text(encoding="utf-8").splitlines()
    hits = []
    for i, ln in enumerate(src_lines, 1):
        if re.match(rf"\s*def {re.escape(name)}\s*\(", ln):
            hits.append(i)
    if len(hits) != 1:
        raise ValueError(f"{path} 里 def {name}( 出现 {len(hits)} 次")
    return _span_of(src_lines, hits[0])


def _ns_rule():
    src = Path(__file__).parent / "sdo_dom.py"
    a, b = _find_def(src, "scan")
    c, d = _find_def(src, "_host_of")
    e, f = _find_def(src, "_dir_of")
    return (
        "宿主＋最集中目录（独立算一次主值）：code/sdo_dom.py 的 scan "
        f"L{a}-L{b}（宿主取自 owl:Ontology@rdf:about，_host_of L{c}-L{d}（urlsplit 取 netloc）；"
        f"目录按 urlsplit path 段取最集中者，_dir_of L{e}-L{f}；平票按目录串升序取第一）"
    )


def gen_ns_json(schedule_path, params=None):
    """evidence 的 ns 件：命名空间判定八字段（本包独立实现实算）。"""
    data = sdo_dom.scan(schedule_path)
    in_ns = data["local_set"]
    prefix_iris = sorted(
        i for i in data["named_set"]
        if sdo_dom.urlsplit(i).path.rsplit("/", 1)[-1].startswith("BCIO_")
    )
    sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
    payload = {
        "rule": _ns_rule(),
        "host": data["host"],
        "dir": data["ns_dir"],
        "count": len(in_ns),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": [{"iri": iri, "in_ns": iri in in_ns} for iri in sorted(data["named_set"])],
        "prefix_iris": prefix_iris,
    }
    return {"v": len(in_ns), "payload": payload}


def gen_anchors_json(paper_path, schedule_path, params=None):
    """evidence 的 anchors 件：13 锚（id／value／source／locator）。"""
    found = sdo_text.locate_anchors(paper_path, schedule_path)
    payload = [
        {"id": aid, "value": found[aid]["value"], "source": found[aid]["source"], "locator": ""}
        for aid in (f"A{i:02d}" for i in range(1, 14))
    ]
    return {"v": len(payload), "payload": payload}


_STEP_IO = {
    1: ("概念文献语料（top-down scoping review 的对象）", "本体范围定义与初始类清单（文献回顾产出）"),
    2: ("Step 1 抽取的信息（范围与初始清单）", "关键类及其定义的初始结构"),
    3: ("Step 2 的初版类结构", "经文献标注—讨论—修订迭代精炼后的本体版本"),
    4: ("Step 3 精炼后的本体", "专家利益相关者评审意见与相应修订"),
    5: ("Step 4 评审后的本体与标注指南", "标注者间信度（Krippendorff's α）评估结果"),
    6: ("前五步确定的类清单", "类间关系规格（与 BFO 对齐的关系定义）"),
    7: ("Step 6 定稿的类与关系", "机器可读并在线发布的本体（OWL 发布件）"),
}


def gen_protocol_json(paper_path, params=None):
    """evidence 的 protocol 件：B 自己按声明块区间从语料重数七步（不沿用他包切分）。"""
    steps = sdo_text.find_protocol_steps(paper_path)
    payload = {
        "rule": ("paper_text.txt 的 L357–L600 区间内取行首 Step N 标题，编号须 1–7 连续；"
                 "禁用标题去重、句中引用不计（行范围计数路；sop:protocol 声明块 "
                 "sha256=ec2209dfd5c078badf0b9e8b8f5d89cd93ffd41db9f64444bc78202dbe3e530f）"),
        "source": "paper_text.txt#L357-L600",
        "steps": [
            {
                "pos": st["pos"],
                "label": f"S{st['pos']}",
                "title": st["title"],
                "src": "paper_text.txt",
                "kind": "line",
                "target": f"paper_text.txt#L{st['start']}-L{st['end']}",
                "evidence_loc": f"paper_text.txt#L{st['start']}-L{st['start']}",
                "input": _STEP_IO[st["pos"]][0],
                "output": _STEP_IO[st["pos"]][1],
            }
            for st in steps
        ],
    }
    return {"v": len(steps), "payload": payload}


def gen_entries_json(k_code_path, params=None):
    """evidence 的 entries 件：六量入口声明（区间＝def 行至体末，实算本包代码）。"""
    names = {
        "L1": "l1_local_classes", "L2": "l2_subclass_edges", "L3": "l3_object_properties",
        "L4": "l4_annotation_properties", "L5": "l5_max_depth", "L6": "l6_leaf_classes",
    }
    payload = {}
    for key, entry in names.items():
        a, b = _find_def(k_code_path, entry)
        payload[key] = {"file": os.path.join("code", "sdo_k.py").replace(os.sep, "/"),
                        "entry": entry, "lines": [a, b]}
    return {"v": len(payload), "payload": payload}


def gen_independence_json(build_code_path, params=None):
    """evidence 的 independence 件（b_only）：四字段声明。"""
    payload = {
        "entry": "code/sdo_k.py 的六个固定入口（l1_local_classes … l6_leaf_classes）",
        "shared_code_with_a": False,
        "signer_pkg_id": f"pkg-B/{TASK_ID}__{RUN_ID}",
        "source": (
            "独立实现自述：xml.dom.minidom 解析（不用 ElementTree）、显式栈迭代遍历、"
            "流式一次过计数、urlsplit（netloc＋path）独立划界；命名空间主值独立另算一次，"
            "三个对照读法按件实算进 deviations 的 contrast 件；L2 三档由 pulldom 流式复核；"
            "匿名类独立判定；L5／L6 两读法均实算；protocol 按声明块区间从语料重数七步；"
            "未 import／引用另一实现包的任何模块、路径或产物。"
        ),
    }
    return {"v": len(payload), "payload": payload}


def _dup_keys(pairs):
    seen = {}
    out = []
    for s, o in pairs:
        base = f"{s}|{o}"
        seen[base] = seen.get(base, 0) + 1
        out.append(base if seen[base] == 1 else f"{base}@{seen[base]}")
    return out


def gen_tiers_json(schedule_path, params=None):
    """deviations 的 tiers 件：L2 三档另一次遍历（pulldom 流式）复核三档之和＝L2。"""
    data = sdo_dom.scan(schedule_path)
    total2, res2 = sdo_dom.recount_l2_streaming(schedule_path)
    if total2 != data["sco_total"] or res2 != len(data["edges"]):
        raise ValueError(
            f"两次遍历不一致：元素数 {data['sco_total']} vs {total2}、边 {len(data['edges'])} vs {res2}"
        )
    if len(data["tier1"]) + len(data["tier2"]) + len(data["tier3"]) != len(data["edges"]):
        raise ValueError("三档之和 ≠ L2")
    payload = {
        "tier1": set_block(_dup_keys(data["tier1"])),
        "tier2": set_block(_dup_keys(data["tier2"])),
        "tier3": set_block(_dup_keys(data["tier3"])),
        "anon_subclass_objects": set_block(_dup_keys(data["anon_objects"])),
        "readings_alt": map_block([("partition_total", data["sco_total"])]),
    }
    return {"v": len(data["edges"]), "payload": payload}


def gen_overlap_json(this_path, peer_specs, params=None):
    """deviations 的 overlap 件：peers 恰等于持有的两件对照件，逐类 IRI 三组差值。"""
    peers = {}
    for peer_id, peer_path in peer_specs:
        ovl = sdo_dom.overlap_local_sets(this_path, peer_path)
        peers[peer_id] = {
            "both": set_block(ovl["both"]),
            "only_in_this": set_block(ovl["only_in_this"]),
            "only_in_peer": set_block(ovl["only_in_peer"]),
        }
    return {"v": len(peers), "payload": {"peers": peers, "unavailable": []}}


def gen_contrast_json(schedule_path, params=None):
    """deviations 的 contrast 件：三个对照读法各一行（按件实算并附推导）。"""
    data = sdo_dom.scan(schedule_path)
    hits = sdo_dom.contrast_hits(schedule_path)
    main = len(data["local_set"])
    dref = {"code": os.path.join("code", "sdo_dom.py").replace(os.sep, "/"),
            "entry": "contrast_hits", "params": {}}
    r1, r2, r3 = hits["strip_filename"], hits["prefix_BCIO_"], hits["most_frequent_prefix"]
    rows = [
        {
            "rule": (
                "读法①（禁用读法，只留痕）：命名空间＝owl:Ontology@rdf:about 去文件名＝"
                f"{r1['namespace']}；推导：该串是去末段后的目录，本件具名类无一落在其下"
                f"（hits={r1['hits']}）——本件属「带子目录」型，落 0 即实证该读法在本件失效；非判据。"
            ),
            "hits": r1["hits"],
            "derivation_ref": dref,
        },
        {
            "rule": (
                "读法②（禁用读法，只留痕）：本地名以 BCIO_ 起头者计为本地，"
                f"hits={r2['hits']}；推导：BCIO_ 前缀集与主口径 in_ns 集逐 IRI 全等"
                "（对称差为空，见本包 evidence 的 ns 件 coincidence）。与主值同值——巧合，不是判据。"
            ),
            "hits": r2["hits"],
            "derivation_ref": dref,
        },
        {
            "rule": (
                "读法③（禁用读法，只留痕）：全件具名类按 host＋目录分组取出现最多者＝"
                f"{r3['prefix']}（hits={r3['hits']}，外部类群）；与主值 {main} 不同——"
                "本件恰是能反证「出现最多的前缀」读法的件；推导见 derivation_ref 所指入口；非判据。"
            ),
            "hits": r3["hits"],
            "derivation_ref": dref,
        },
    ]
    return {"v": len(rows), "payload": rows}


def gen_readings_json(paper_path, schedule_path, params=None):
    """deviations 的 readings 件：另报名表恰九条（顺序＝题面 §二.3 名表行序）。"""
    data = sdo_dom.scan(schedule_path)
    anchors = sdo_text.locate_anchors(paper_path, schedule_path)
    dir_counts = dict(Counter(
        data["host"] + sdo_dom._dir_of(i) for i in data["local_set"]
    ))

    def scalar(name, value):
        return {"name": name, "kind": "scalar",
                "sha256": canon_sha({"name": name, "kind": "scalar", "value": value}),
                "value": value}

    def mapval(name, value):
        return {"name": name, "kind": "map",
                "sha256": canon_sha({"name": name, "kind": "map", "value": value}),
                "value": value}

    ns = data["namespace"]
    payload = [
        scalar("L3_local", sum(1 for i in data["object_properties"] if i.startswith(ns))),
        scalar("L4_local", sum(1 for i in data["annotation_properties"] if i.startswith(ns))),
        scalar("L5_alt", sdo_dom.max_depth_local_subgraph(data)),
        scalar("L5_selfcheck", sum(1 for c in data["local_set"] if c not in data["subj_any"])),
        scalar("L6_alt", sdo_dom.leaf_with_external(data)),
        mapval("dir_class_counts", dir_counts),
        scalar("initial_version_class_count", INITIAL_VERSION_CLASSES),
        scalar("anonymous_class", data["equiv_anon_classes"]),
        mapval("self_report_unmeasured", {"A02": anchors["A02"]["value"], "A03": anchors["A03"]["value"]}),
    ]
    if [el["name"] for el in payload] != READINGS_NAMES:
        raise ValueError("readings 名表顺序不符")
    return {"v": len(payload), "payload": payload}


def gen_diff_a01_json(schedule_path, params=None):
    """deviations 的 diff_A01 件：A01 ↔ 实测端 L1 的差额（八键；items＝L1 全集不选子集）。"""
    data = sdo_dom.scan(schedule_path)
    measured = len(data["local_set"])
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(sorted(data["local_set"]))]
    gap = measured - A01_SELF_REPORT
    payload = {
        "anchor": "A01",
        "measured": measured,
        "self_reported": A01_SELF_REPORT,
        "items": items,
        "rows": len(items),
        "gap": gap,
        "direction": "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等"),
        "sha256": canon_sha({
            "anchor": "A01", "measured": measured,
            "self_reported": A01_SELF_REPORT, "items": items,
        }),
    }
    return {"v": measured, "payload": payload}


def main(research_root, pkg_dir):
    """按序生成 evidence／deviations 十件（B 多 independence 一件；返回 {相对路径: 件内容}）。"""
    research_root = Path(str(research_root))
    pkg_dir = Path(str(pkg_dir))
    sched = research_root / "bcio_schedule.owl"
    paper = research_root / "paper_text.txt"
    peers = [("0005", research_root / "bcio_upper_level.owl"),
             ("0003", research_root / "bcio_mode_of_delivery.owl")]
    out = {
        os.path.join(EV, "ns.json"): gen_ns_json(sched)["payload"],
        os.path.join(EV, "anchors.json"): gen_anchors_json(paper, sched)["payload"],
        os.path.join(EV, "protocol.json"): gen_protocol_json(paper)["payload"],
        os.path.join(EV, "entries.json"): gen_entries_json(pkg_dir / "code" / "sdo_k.py")["payload"],
        os.path.join(EV, "independence.json"): gen_independence_json(pkg_dir / "code" / "sdo_build.py")["payload"],
        os.path.join(DV, "tiers.json"): gen_tiers_json(sched)["payload"],
        os.path.join(DV, "overlap.json"): gen_overlap_json(sched, peers)["payload"],
        os.path.join(DV, "contrast.json"): gen_contrast_json(sched)["payload"],
        os.path.join(DV, "readings.json"): gen_readings_json(paper, sched)["payload"],
        os.path.join(DV, "diff_A01.json"): gen_diff_a01_json(sched)["payload"],
    }
    for rel, payload in out.items():
        dst = pkg_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
