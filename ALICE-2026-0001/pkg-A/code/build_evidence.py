"""ALICE-2026-0001 · pkg-A 证据/偏差件构建器。

从研究夹根的三件输入（bcto.owl／paper_text.txt／fulltext__PMC10427801.xml）重算
evidence/ 与 deviations/ 的全部内容。用法：在包目录下 `python code/build_evidence.py`。
口径：题面 §二／§2.3／§三／§四／§10.2。解析用 xml.etree.ElementTree（pkg-A 允许的读法）。
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ontology_metrics import (
    RDF, OWL, RDFS,
    ontology_about, named_class_iris, local_namespace, _iri_dir, _subclass_edges,
    L1_class_local, L2_subclass_edges, L3_object_properties,
    L4_annotation_properties, L5_max_depth, L6_leaf_classes,
)

HERE = Path(__file__).resolve().parent.parent          # 包目录
RESEARCH = HERE.parent                                  # 研究夹根（输入副本落根）
OWL_F = RESEARCH / "bcto.owl"
TXT_F = RESEARCH / "paper_text.txt"
XML_F = RESEARCH / "fulltext__PMC10427801.xml"


def canon_sha(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def dump(rel: str, obj) -> None:
    p = HERE / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def set_block(keys: list[str]) -> dict:
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def map_block(pairs: list[tuple[str, object]]) -> dict:
    items = [{"key": k, "value": v} for k, v in sorted(pairs, key=lambda kv: kv[0])]
    return {"items": items, "rows": len(items), "sha256": canon_sha(items)}


def anonymous_nodes(root):
    """全件匿名节点（无 rdf:about 的 owl:Class 与 owl:Restriction），按文档序从 1 编号。"""
    out = {}
    n = 0
    for el in root.iter():
        if el.tag in (f"{OWL}Class", f"{OWL}Restriction") and not el.get(RDF + "about"):
            n += 1
            out[id(el)] = n
    return out


def compute(owl_path=OWL_F):
    root = ET.parse(str(owl_path)).getroot()
    rule, host, nsdir, local = local_namespace(root)
    named = named_class_iris(root)
    res_edges, anon_obj_edges = _subclass_edges(root)
    anon_no = anonymous_nodes(root)

    # 匿名宾语的对象节点编号
    parent = {}
    for el in root.iter():
        for ch in list(el):
            parent[ch] = el
    anon_items = []
    for el in root.iter(f"{RDFS}subClassOf"):
        if el.get(RDF + "resource") is not None:
            continue
        p = parent.get(el)
        while p is not None and p.tag != f"{OWL}Class":
            p = parent.get(p)
        subj = p.get(RDF + "about") if p is not None else None
        obj_el = next(iter(list(el)), None)
        no = anon_no.get(id(obj_el), 0) if obj_el is not None else 0
        anon_items.append((subj, f"@anonymous#{no}"))

    t1 = sorted(f"{s}|{o}" for s, o in res_edges if s in local and o in local)
    t2 = sorted(f"{s}|{o}" for s, o in res_edges if s in local and o not in local)
    t3 = sorted(f"{s if s else '@anonymous#0'}|{o}" for s, o in res_edges if s not in local)
    anon_keys = sorted(f"{s}|{o}" for s, o in anon_items)

    ops = sorted({el.get(RDF + "about") for el in root.iter(f"{OWL}ObjectProperty") if el.get(RDF + "about")})
    aps = sorted({el.get(RDF + "about") for el in root.iter(f"{OWL}AnnotationProperty") if el.get(RDF + "about")})
    L3_local = sum(1 for i in ops if _iri_dir(i) == (host, nsdir))
    L4_local = sum(1 for i in aps if _iri_dir(i) == (host, nsdir))

    # L5 家族
    has_parent = {s for s, _ in res_edges if s} | {s for s, _ in anon_obj_edges if s}
    children = {}
    for s, o in res_edges:
        if s:
            children.setdefault(o, set()).add(s)
    roots = named - has_parent
    depth = {}

    def walk(node, d, stack):
        if node in stack:
            return
        if d > depth.get(node, -1):
            depth[node] = d
        stack.add(node)
        for ch in children.get(node, ()):
            walk(ch, d + 1, stack)
        stack.discard(node)

    for r in roots:
        walk(r, 0, set())
    L5 = max((depth.get(c, 0) for c in local), default=0)

    local_parent = {s for s, o in res_edges if s in local and o in local}
    alt_roots = {c for c in local if c not in local_parent}
    lchildren = {}
    for s, o in res_edges:
        if s in local and o in local:
            lchildren.setdefault(o, set()).add(s)
    adepth = {}

    def awalk(node, d, stack):
        if node in stack:
            return
        if d > adepth.get(node, -1):
            adepth[node] = d
        stack.add(node)
        for ch in lchildren.get(node, ()):
            awalk(ch, d + 1, stack)
        stack.discard(node)

    for r in alt_roots:
        awalk(r, 0, set())
    L5_alt = max(adepth.values(), default=0)
    L5_selfcheck = sum(1 for c in local if c not in has_parent)

    lch = {o for s, o in res_edges if s in local and o in local}
    L6 = len({c for c in local if c not in lch})
    ach = {o for s, o in res_edges if o in local and s}
    L6_alt = len({c for c in local if c not in ach})
    anon_class = sum(1 for el in root.iter(f"{OWL}Class") if not el.get(RDF + "about"))

    # 命名空间对照三值（题面 §2.4：只作事后对照，不作判据）
    about = ontology_about(root)
    base_dir = about.rsplit("/", 1)[0] + "/"  # 对照一：rdf:about 去文件名当目录
    c1 = sum(1 for i in named if i.startswith(base_dir))

    def lname(iri):
        i = max(iri.rfind("/"), iri.rfind("#"))
        return iri[i + 1:]

    c2 = sum(1 for i in named if lname(i).startswith("BCIO_"))
    from collections import Counter
    pref = {}
    for i in named:
        m = re.match(r"[A-Za-z]+", lname(i))
        p = m.group(0) if m else ""
        pref[p] = pref.get(p, 0) + 1
    top_prefix = max(sorted(pref), key=lambda k: pref[k])
    c3 = sum(1 for i in named if lname(i).startswith(top_prefix + "_"))

    prefix_iris = sorted(i for i in named if lname(i).startswith("BCIO_"))
    return {
        "rule": rule, "host": host, "dir": nsdir, "local": local, "named": named,
        "prefix_iris": prefix_iris,
        "L1": len(local), "L2": len(res_edges),
        "L3": len(ops), "L4": len(aps), "L5": L5, "L6": L6,
        "L3_local": L3_local, "L4_local": L4_local,
        "L5_alt": L5_alt, "L5_selfcheck": L5_selfcheck, "L6_alt": L6_alt,
        "anonymous_class": anon_class,
        "tier1": t1, "tier2": t2, "tier3": t3, "anon_keys": anon_keys,
        "partition_total": len(res_edges) + len(anon_obj_edges),
        "contrast": [
            ("rdf:about 去文件名当目录（禁用读法①对照；与主口径同值纯属巧合，不是判据）", c1),
            ("类名前缀 BCIO_ 判本地（禁用读法②对照；与主口径同值纯属巧合，不是判据）", c2),
            ("出现最多的前缀判本地（禁用读法③对照；与主口径同值纯属巧合，不是判据）", c3),
        ],
    }


def build_ns(d):
    local, named = d["local"], d["named"]
    in_ns = {i for i in named if i in local}
    sym = sorted(set(d["prefix_iris"]) ^ in_ns)
    return {
        "rule": d["rule"], "host": d["host"], "dir": d["dir"],
        "count": len(in_ns), "prefix_count": len(d["prefix_iris"]),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": [{"iri": i, "in_ns": i in in_ns} for i in sorted(named)],
        "prefix_iris": d["prefix_iris"],
    }


def build_tiers(d):
    return {
        "tier1": set_block(d["tier1"]),
        "tier2": set_block(d["tier2"]),
        "tier3": set_block(d["tier3"]),
        "anon_subclass_objects": set_block(d["anon_keys"]),
        "readings_alt": map_block([("partition_total", d["partition_total"])]),
    }


def build_readings(d, anchors):
    self_un = {a["id"]: a["value"] for a in anchors if a["id"] in ("A02", "A03", "A04", "A05")}
    out = []
    for name, val in (
        ("L3_local", d["L3_local"]), ("L4_local", d["L4_local"]),
        ("L5_alt", d["L5_alt"]), ("L5_selfcheck", d["L5_selfcheck"]),
        ("L6_alt", d["L6_alt"]), ("anonymous_class", d["anonymous_class"]),
    ):
        el = {"name": name, "kind": "scalar", "value": val}
        el["sha256"] = canon_sha({"name": name, "kind": "scalar", "value": val})
        out.append(el)
    el = {"name": "self_report_unmeasured", "kind": "map", "value": self_un}
    el["sha256"] = canon_sha({"name": el["name"], "kind": "map", "value": self_un})
    out.append(el)
    return out


def build_contrast(d):
    return [
        {"rule": rule, "hits": hits,
         "derivation_ref": {"code": "code/build_evidence.py", "entry": "compute", "params": {}}}
        for rule, hits in d["contrast"]
    ]


def build_diff_a01(d, anchors):
    a01 = next(a["value"] for a in anchors if a["id"] == "A01")
    measured = d["L1"]
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(sorted(d["local"]))]
    gap = measured - a01
    return {
        "anchor": "A01", "measured": measured, "self_reported": a01,
        "items": items, "rows": len(items),
        "gap": gap, "direction": "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等"),
        "sha256": canon_sha({"anchor": "A01", "measured": measured, "self_reported": a01, "items": items}),
    }


def build_anchors(txt_path=TXT_F, xml_path=XML_F, owl_path=OWL_F):
    lines = Path(txt_path).read_text(encoding="utf-8").splitlines()
    squashed = [re.sub(r"\s+", " ", ln) for ln in lines]

    def grab(line_no, pattern, group=1):
        m = re.search(pattern, squashed[line_no - 1])
        if not m:
            raise RuntimeError(f"锚定位失败 L{line_no}: {pattern}")
        return m.group(group)

    a01 = int(grab(58, r"The first release of the BCTO consisted of (\d+)"))
    a02 = int(grab(53, r"The revised version of the BCTO following expert review had (\d+)"))
    a34 = re.findall(r"a=(\d+\.\d+)", squashed[54])
    a03, a04 = float(a34[0]), float(a34[1])
    a05 = grab(80, r"(\w+) hierarchical levels")
    a06 = squashed[58]                      # L59 题注整行（含 Table 2. 标签）
    a08 = squashed[10]                      # L11 图题整行（含 Figure 1. 标签）
    a09 = squashed[14]                      # L15 Methods 标题行
    a10 = squashed[19]                      # L20 Step 1 标题行（Methods 内第 1 处）

    xroot = ET.parse(str(xml_path)).getroot()
    am = xroot.find(".//front/article-meta")
    a11 = None
    for c in list(am):
        if c.tag == "article-id" and c.get("pub-id-type") == "doi":
            a11 = (c.text or "").strip()
            break
    # A07：Table 2 表头首格＝该表 thead 首个 th 文本
    a07 = None
    for tw in xroot.iter("table-wrap"):
        label = tw.find("label")
        if label is not None and (label.text or "").strip() == "Table 2.":
            th = tw.find(".//thead//th")
            a07 = "".join(th.itertext()).strip()
            break
    if a07 not in squashed[59]:
        raise RuntimeError("A07 表头首格不在 L60 内")

    oroot = ET.parse(str(owl_path)).getroot()
    ont = oroot.find(f".//{OWL}Ontology")
    a13 = ont.get(RDF + "about")
    a12 = ont.find(f"{OWL}versionIRI").get(RDF + "resource")

    return [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L58"},
        {"id": "A02", "value": a02, "source": "paper_text.txt#L53"},
        {"id": "A03", "value": a03, "source": "paper_text.txt#L55"},
        {"id": "A04", "value": a04, "source": "paper_text.txt#L55"},
        {"id": "A05", "value": a05, "source": "paper_text.txt#L80"},
        {"id": "A06", "value": a06, "source": "paper_text.txt#L59"},
        {"id": "A07", "value": a07, "source": "paper_text.txt#L60"},
        {"id": "A08", "value": a08, "source": "paper_text.txt#L11"},
        {"id": "A09", "value": a09, "source": "paper_text.txt#L15"},
        {"id": "A10", "value": a10, "source": "paper_text.txt#L20"},
        {"id": "A11", "value": a11, "source": "fulltext__PMC10427801.xml#front/article-meta/article-id[@pub-id-type='doi']"},
        {"id": "A12", "value": a12, "source": f"bcto.owl#{a12}"},
        {"id": "A13", "value": a13, "source": f"bcto.owl#{a13}"},
    ]


def build_protocol():
    steps = [
        (1, "S1", "Step 1: Extract and synthesise feedback on the BCTTv1", "L20-L21"),
        (2, "S2", "Step 2: Changes to BCTs: labels and definitions", "L22-L23"),
        (3, "S3", "Step 3: Structuring the BCTO as an ontology", "L24-L25"),
        (4, "S4", "Step 4: Expert stakeholder review", "L26-L29"),
        (5, "S5", "Step 5: Inter-rater reliability of annotations using the BCTO", "L30-L33"),
        (6, "S6", "Step 6: Computer-readable version of the BCTO and publication in online repositories", "L34-L36"),
    ]
    return {
        "rule": "步骤＝Methods 直系 sub-sec 中标题以 `Step N: `（N=1..6 连续）起头的 6 个；"
                "起止行＝该步标题行至下一 title 行前一行（不分层级）；"
                "「按位置取前 N 个」与「标题去重读数」都禁用",
        "source": "paper_text.txt#L15-L36",
        "steps": [
            {"pos": pos, "label": lab, "title": title, "src": "paper_text.txt", "kind": "line",
             "target": f"paper_text.txt#{span}", "evidence_loc": f"paper_text.txt#{span}",
             "input": None, "output": None}
            for pos, lab, title, span in steps
        ],
    }


def main():
    d = compute()
    anchors = build_anchors()
    dump("evidence/ns.json", build_ns(d))
    dump("evidence/anchors.json", anchors)
    dump("evidence/protocol.json", build_protocol())
    dump("deviations/tiers.json", build_tiers(d))
    dump("deviations/overlap.json", {"peers": {}, "unavailable": []})
    dump("deviations/contrast.json", build_contrast(d))
    dump("deviations/readings.json", build_readings(d, anchors))
    dump("deviations/diff_A01.json", build_diff_a01(d, anchors))
    print(json.dumps({k: d[k] for k in
                      ("L1", "L2", "L3", "L4", "L5", "L6", "L3_local", "L4_local",
                       "L5_alt", "L5_selfcheck", "L6_alt", "anonymous_class", "partition_total")},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
