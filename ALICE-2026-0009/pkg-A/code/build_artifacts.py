# -*- coding: utf-8 -*-
"""pkg-A 派生件生成入口（A-1 口径：evidence/ 每件产物的生成入口在此各指一行）。

所有 gen_* 入口为纯函数：返回 {"v": <代表整数>, "payload": <件内容>}，不写盘；
写盘由 main() 完成。判分器探针重跑它们时返回同值（确定性）。
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import owl_scan
import paper_scan

TASK_ID = "ALICE-2026-0009"
A01_SELF_REPORT = 49          # 锚 A01：论文自报终版类数（值不预填进定位串，此处仅为差额件入账）
INITIAL_VERSION_CLASSES = 9   # 摘要「The initial version comprised 9 classes」（readings 名表第 7 行）
READINGS_NAMES = [
    "L3_local", "L4_local", "L5_alt", "L5_selfcheck", "L6_alt",
    "dir_class_counts", "initial_version_class_count", "anonymous_class",
    "self_report_unmeasured",
]


def canon_sha(payload):
    """载荷规范 sha：sort_keys＋紧凑分隔＋ensure_ascii=False 的 UTF-8 字节。"""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def set_block(keys):
    """set 型装载：items[{key,ord}]（ord 1..n 升序）＋rows＋sha256（载荷＝裸 items）。"""
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def map_block(pairs):
    """map 型装载：items[{key,value}] 按 key 升序＋rows＋sha256（载荷＝裸 items）。"""
    items = [{"key": k, "value": v} for k, v in sorted(pairs, key=lambda kv: kv[0])]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def _span_of(src_lines, def_line):
    """与判分器同式的函数体跨度：def 行至最后一个非空非注释体行。"""
    indent_def = len(src_lines[def_line - 1]) - len(src_lines[def_line - 1].lstrip())
    body_end = def_line
    for i in range(def_line + 1, len(src_lines) + 1):
        ln = src_lines[i - 1]
        if not ln.strip():
            continue
        cur = len(ln) - len(ln.lstrip())
        if cur <= indent_def and not ln.lstrip().startswith("#"):
            break
        if not ln.lstrip().startswith("#"):
            body_end = i
    return def_line, body_end


def _find_def(path, name):
    src_lines = Path(str(path)).read_text(encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(src_lines, 1) if re.match(rf"\s*def {re.escape(name)}\s*\(", ln)]
    if len(hits) != 1:
        raise ValueError(f"{path} 里 def {name}( 出现 {len(hits)} 次")
    return _span_of(src_lines, hits[0])


def _ns_rule():
    """ns.json 的 rule：指到 code/owl_scan.py 的函数与行（实算行号）。"""
    src = Path(__file__).parent / "owl_scan.py"
    a, b = _find_def(src, "__init__")
    c, d = _find_def(src, "_host_of")
    e, f = _find_def(src, "_dir_of")
    return (
        "宿主＋最集中目录（一次算主值）：code/owl_scan.py 的 OntologyScan.__init__ "
        f"L{a}-L{b}（宿主取自 owl:Ontology@rdf:about，_host_of L{c}-L{d}；目录按 path 段取"
        f"类 IRI 最集中者，_dir_of L{e}-L{f}；平票按目录串升序取第一）"
    )


def gen_ns_json(schedule_path, params=None):
    """evidence/ns.json：命名空间判定八字段。"""
    scan = owl_scan.OntologyScan(schedule_path)
    in_ns = scan.local_set
    prefix_iris = sorted(
        i for i in scan.named_set
        if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_")
    )
    sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
    classes = [
        {"iri": iri, "in_ns": iri in in_ns}
        for iri in sorted(scan.named_set)
    ]
    payload = {
        "rule": _ns_rule(),
        "host": scan.host,
        "dir": scan.ns_dir,
        "count": len(in_ns),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": classes,
        "prefix_iris": prefix_iris,
    }
    return {"v": len(in_ns), "payload": payload}


def gen_anchors_json(paper_path, schedule_path, params=None):
    """evidence/anchors.json：13 锚（id／value／source／locator）。"""
    found = paper_scan.locate_anchors(paper_path, schedule_path)
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
    """evidence/protocol.json：行范围计数路的七步（九键闭集）。"""
    steps = paper_scan.find_protocol_steps(paper_path)
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
    """evidence/entries.json：六量入口声明（区间＝def 行至体末，实算）。"""
    names = {
        "L1": "l1_local_classes", "L2": "l2_subclass_edges", "L3": "l3_object_properties",
        "L4": "l4_annotation_properties", "L5": "l5_max_depth", "L6": "l6_leaf_classes",
    }
    payload = {}
    for key, entry in names.items():
        a, b = _find_def(k_code_path, entry)
        payload[key] = {"file": "code/schedule_k.py", "entry": entry, "lines": [a, b]}
    return {"v": len(payload), "payload": payload}


def _dup_keys(pairs):
    """(主体,宾语) 条 → key 清单：第 1 条裸 key，第 k 条（k≥2）末尾追加 @k。"""
    seen = {}
    out = []
    for s, o in pairs:
        base = f"{s}|{o}"
        seen[base] = seen.get(base, 0) + 1
        out.append(base if seen[base] == 1 else f"{base}@{seen[base]}")
    return out


def gen_tiers_json(schedule_path, params=None):
    """deviations/tiers.json：L2 三档＋匿名宾语档＋partition_total（恰五键）。"""
    scan = owl_scan.OntologyScan(schedule_path)
    # 复核遍历（第二次、独立机制）：文本级计数（注释／CDATA 遮罩后扫元素起止）
    text = Path(str(schedule_path)).read_text(encoding="utf-8")
    masked = re.sub(r"<!--.*?-->|<!\[CDATA\[.*?\]\]>", lambda m: " " * len(m.group(0)), text, flags=re.S)
    total2 = len(re.findall(r"<rdfs:subClassOf(?:\s[^>]*?)?/?>", masked))
    res2 = len(re.findall(r"<rdfs:subClassOf\s[^>]*?rdf:resource", masked))
    if total2 != scan.sco_total or res2 != len(scan.edges):
        raise ValueError(
            f"两次遍历不一致：元素数 {scan.sco_total} vs {total2}、rdf:resource 边 {len(scan.edges)} vs {res2}"
        )
    payload = {
        "tier1": set_block(_dup_keys(scan.tier1)),
        "tier2": set_block(_dup_keys(scan.tier2)),
        "tier3": set_block(_dup_keys(scan.tier3)),
        "anon_subclass_objects": set_block(_dup_keys(scan.anon_objects)),
        "readings_alt": map_block([("partition_total", scan.sco_total)]),
    }
    return {"v": len(scan.edges), "payload": payload}


def gen_overlap_json(this_path, peer_specs, params=None):
    """deviations/overlap.json：peers 恰等于持有的对照件；逐类 IRI 三组差值。"""
    this = owl_scan.OntologyScan(this_path).local_set
    peers = {}
    for peer_id, peer_path in peer_specs:
        ovl = owl_scan.overlap_sets(this_path, peer_path)
        peers[peer_id] = {
            "both": set_block(ovl["both"]),
            "only_in_this": set_block(ovl["only_in_this"]),
            "only_in_peer": set_block(ovl["only_in_peer"]),
        }
    return {"v": len(peers), "payload": {"peers": peers, "unavailable": []}}


def gen_contrast_json(schedule_path, params=None):
    """deviations/contrast.json：三个对照读法（禁法留痕，同值写「巧合，不是判据」）。"""
    scan = owl_scan.OntologyScan(schedule_path)
    hits = owl_scan.contrast_hits(schedule_path)
    main = len(scan.local_set)
    dref = {"code": "code/owl_scan.py", "entry": "contrast_hits", "params": {}}
    r1 = hits["strip_filename"]
    r2 = hits["prefix_BCIO_"]
    r3 = hits["most_frequent_prefix"]
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
                "（对称差为空，见 evidence/ns.json 的 coincidence）。与主值同值——巧合，不是判据。"
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
    """deviations/readings.json：另报名表恰九条（顺序＝题面 §二.3 名表行序）。"""
    scan = owl_scan.OntologyScan(schedule_path)
    anchors = paper_scan.locate_anchors(paper_path, schedule_path)
    from collections import Counter
    # 本地类 IRI 按目录（IRI 去掉末段）分列：key＝目录串（host＋dir），value＝该类数
    dir_counts = dict(Counter(scan.host + owl_scan._dir_of(i) for i in scan.local_classes))

    def scalar(name, value):
        return {"name": name, "kind": "scalar",
                "sha256": canon_sha({"name": name, "kind": "scalar", "value": value}),
                "value": value}

    def mapval(name, value):
        return {"name": name, "kind": "map",
                "sha256": canon_sha({"name": name, "kind": "map", "value": value}),
                "value": value}

    l3_local = sum(1 for i in scan.object_properties if i in scan.local_set or i.startswith(scan.namespace))
    l4_local = sum(1 for i in scan.annotation_properties if i.startswith(scan.namespace))
    payload = [
        scalar("L3_local", l3_local),
        scalar("L4_local", l4_local),
        scalar("L5_alt", scan.max_depth_local_subgraph()),
        scalar("L5_selfcheck", sum(1 for c in scan.local_set if c not in scan.subj_any)),
        scalar("L6_alt", scan.leaf_with_external()),
        mapval("dir_class_counts", dir_counts),
        scalar("initial_version_class_count", INITIAL_VERSION_CLASSES),
        scalar("anonymous_class", scan.equiv_anon_classes),
        mapval("self_report_unmeasured", {"A02": anchors["A02"]["value"], "A03": anchors["A03"]["value"]}),
    ]
    if [el["name"] for el in payload] != READINGS_NAMES:
        raise ValueError("readings 名表顺序不符")
    return {"v": len(payload), "payload": payload}


def gen_diff_a01_json(schedule_path, params=None):
    """deviations/diff_A01.json：A01（终版自报类数）↔ 实测端 L1 的差额（八键）。"""
    scan = owl_scan.OntologyScan(schedule_path)
    measured = len(scan.local_set)
    iris = sorted(scan.local_set)   # ord＝IRI 升序序位；不选子集
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(iris)]
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
    """按序生成 evidence／deviations 九件（返回 {相对路径: 件内容}）。"""
    research_root = Path(str(research_root))
    pkg_dir = Path(str(pkg_dir))
    sched = research_root / "bcio_schedule.owl"
    paper = research_root / "paper_text.txt"
    peers = [("0005", research_root / "bcio_upper_level.owl"),
             ("0003", research_root / "bcio_mode_of_delivery.owl")]
    out = {
        "evidence/ns.json": gen_ns_json(sched)["payload"],
        "evidence/anchors.json": gen_anchors_json(research_root / "paper_text.txt", sched)["payload"],
        "evidence/protocol.json": gen_protocol_json(research_root / "paper_text.txt")["payload"],
        "evidence/entries.json": gen_entries_json(pkg_dir / "code" / "schedule_k.py")["payload"],
        "deviations/tiers.json": gen_tiers_json(sched)["payload"],
        "deviations/overlap.json": gen_overlap_json(sched, peers)["payload"],
        "deviations/contrast.json": gen_contrast_json(sched)["payload"],
        "deviations/readings.json": gen_readings_json(research_root / "paper_text.txt", sched)["payload"],
        "deviations/diff_A01.json": gen_diff_a01_json(sched)["payload"],
    }
    for rel, payload in out.items():
        dst = pkg_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
