#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg-A 主实现：ALICE-2026-0006 六量入口与证据件发射。

技术选型（题面 §5.3bis 允许面）：xml.etree.ElementTree 解析、递归遍历、
建索引后计数、前缀比较划界。六个固定入口 l1_* … l6_* 各返 {"v": <整数>}。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

OWLNS = "{http://www.w3.org/2002/07/owl#}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"

TASK_ID = "ALICE-2026-0006"
PAPER = "paper_text.txt"
OWLNAME = "bcio_setting.owl"

STEP_TITLES = [
    "Step 1 – Defining the scope of the Intervention Setting Ontology",
    "Step 2 – Identifying key entities and developing the preliminary Intervention Setting Ontology",
    "Step 3 – Refinement of the ontology through literature annotation, discussion and revision",
    "Step 4 – Expert stakeholder review",
    "Step 5 – Inter-rater Reliability of Annotations using the Intervention Setting Ontology",
    "Step 6 – Specifying the relationships between Intervention Setting Ontology entities",
    "Step 7 - Making the Intervention Setting Ontology machine-readable and available online",
]
STEP_IO = [
    ("dictionaries and the reporting guidelines of CONSORT, CONSORT-SPI, TIDieR and TIPPME（L11 段）",
     "a definition and overall topic for the ontology（L11 段）"),
    ("100 published reports of BCIs（bottom-up，L13 段）与 existing classification systems（top-down，L14 段）",
     "an initial prototype version of the ontology（L13–L15 段）"),
    ("the results of the pilot annotations（L17 段首句）",
     "the revised Intervention Setting Ontology 与修订后的 annotation guidance manual（L17 段）"),
    ("the Intervention Setting Ontology resulting from Step 3（L19 段）",
     "feedback from the expert consultation，以及据之修订的 ontology 与 annotation guidance（L22 段）"),
    ("50 papers from Cochrane reviews 与另一组 50 randomised controlled trials（L24 段）",
     "inter-rater reliability assessed using Krippendorff’s Alpha（L24 段）"),
    ("common relationships from Basic Formal Ontology and the Relation Ontology（L26 段）",
     "relationships between ontology entities（is_a／located_in，L26 段）"),
    ("a table of entities（stable level of development for initial release，L28 段）",
     "the Web Ontology Language (OWL) format version, stored on the project GitHub repository（L28–L29 段）"),
]
READINGS_NAMES = [
    "L3_local", "L4_local", "L5_alt", "L5_selfcheck", "L6_alt",
    "anonymous_class", "self_report_unmeasured",
]


# ── 解析与遍历（递归） ─────────────────────────────────────────────

def _walk(el):
    """递归深度优先遍历（文档序）。"""
    yield el
    for ch in el:
        yield from _walk(ch)


def _parse(input_path):
    tree = ET.parse(str(input_path))
    root = tree.getroot()
    els = list(_walk(root))
    pmap = {}
    for p in els:
        for c in p:
            pmap[id(c)] = p
    return root, els, pmap


def _enclosing_named_class(el, pmap):
    cur = el
    while cur is not None:
        if cur.tag == OWLNS + "Class":
            about = cur.get(RDF + "about")
            if about:
                return about
        cur = pmap.get(id(cur))
    return None


def _ontology_iri(els):
    for el in els:
        if el.tag == OWLNS + "Ontology":
            return el.get(RDF + "about")
    raise RuntimeError("owl:Ontology 缺失")


def local_namespace(input_path):
    """主口径（§7.3）：宿主＝owl:Ontology@rdf:about 的 netloc；
    本地命名空间＝宿主＋该宿主上命名类 IRI 最集中的那一层目录。"""
    _root, els, _pm = _parse(input_path)
    iri = _ontology_iri(els)
    sp = urlsplit(iri)
    host = sp.netloc
    dirs = Counter()
    for el in els:
        if el.tag == OWLNS + "Class":
            about = el.get(RDF + "about")
            if about and urlsplit(about).netloc == host:
                d = urlsplit(about).path.rsplit("/", 1)[0] + "/"
                dirs[d] += 1
    if not dirs:
        raise RuntimeError("宿主上没有任何命名类，命名空间无从判定")
    top = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return f"{sp.scheme}://{host}{top}"


def _ns_parts(ns):
    sp = urlsplit(ns)
    return sp.netloc, sp.path


# ── 索引（A 允许建索引后计数） ─────────────────────────────────────

def _named_classes(els):
    return [el.get(RDF + "about") for el in els
            if el.tag == OWLNS + "Class" and el.get(RDF + "about")]


def _edges(els, pmap):
    """全件 rdfs:subClassOf：带 rdf:resource 的边 (主语, 宾语) 按条计；
    宾语匿名（无 rdf:resource）的条另列。"""
    res_edges, anon_obj = [], []
    for el in els:
        if el.tag != RDFS + "subClassOf":
            continue
        subj = _enclosing_named_class(el, pmap)
        res = el.get(RDF + "resource")
        if res:
            res_edges.append((subj, res))
        else:
            anon_obj.append((subj, el))
    return res_edges, anon_obj


def _anon_numbering(els):
    """全件匿名节点（无 rdf:about 的 owl:Class 与 owl:Restriction）
    按文档序从 1 起连续编号；同一节点各处同号。"""
    out = {}
    n = 0
    for el in els:
        if el.tag in (OWLNS + "Class", OWLNS + "Restriction") and not el.get(RDF + "about"):
            n += 1
            out[id(el)] = n
    return out


def _local_set(named, ns):
    return {i for i in named if i.startswith(ns)}


# ── 六量固定入口（题面 §九：名字写死；返回 {"v": 整数}） ────────────

def l1_local_classes(input_path, params=None):
    _root, els, _pm = _parse(input_path)
    ns = local_namespace(input_path)
    return {"v": len(_local_set(_named_classes(els), ns))}


def l2_subclass_edges(input_path, params=None):
    _root, els, pmap = _parse(input_path)
    res_edges, _anon = _edges(els, pmap)
    return {"v": len(res_edges)}


def l3_object_properties(input_path, params=None):
    _root, els, _pm = _parse(input_path)
    iris = {el.get(RDF + "about") for el in els
            if el.tag == OWLNS + "ObjectProperty" and el.get(RDF + "about")}
    return {"v": len(iris)}


def l4_annotation_properties(input_path, params=None):
    _root, els, _pm = _parse(input_path)
    iris = {el.get(RDF + "about") for el in els
            if el.tag == OWLNS + "AnnotationProperty" and el.get(RDF + "about")}
    return {"v": len(iris)}


def l5_max_depth(input_path, params=None):
    """全图根（无任何 subClassOf 主语的命名类，含外部顶层类）沿 subClassOf
    下行（宾语＝父类、主语＝子类）到最远本地类的边数；同边只走一次断开环。"""
    _root, els, pmap = _parse(input_path)
    ns = local_namespace(input_path)
    named = set(_named_classes(els))
    local = _local_set(named, ns)
    res_edges, _anon = _edges(els, pmap)
    subjects = {s for s, _o in res_edges if s}
    children = {}
    for s, o in res_edges:
        if s:
            children.setdefault(o, []).append(s)
    roots = sorted(named - subjects)
    best = 0

    def dfs(node, depth, seen):
        nonlocal best
        if node in local and depth > best:
            best = depth
        for ch in children.get(node, []):
            e = (ch, node)
            if e in seen:
                continue
            dfs(ch, depth + 1, seen | {e})

    for r in roots:
        dfs(r, 0, frozenset())
    return {"v": best}


def l6_leaf_classes(input_path, params=None):
    """本地类中无本地子类者（只看本地→本地的边；子类＝主语、父类＝宾语）。"""
    _root, els, pmap = _parse(input_path)
    ns = local_namespace(input_path)
    named = set(_named_classes(els))
    local = _local_set(named, ns)
    res_edges, _anon = _edges(els, pmap)
    has_local_child = {o for s, o in res_edges if s in local and o in local}
    return {"v": len([c for c in local if c not in has_local_child])}


# ── 另报与对照（不进 K） ──────────────────────────────────────────

def alt_readings(input_path):
    """七个另报量的值（§二.3 名表行序）。"""
    _root, els, pmap = _parse(input_path)
    ns = local_namespace(input_path)
    named = set(_named_classes(els))
    local = _local_set(named, ns)
    res_edges, _anon = _edges(els, pmap)
    objprops = {el.get(RDF + "about") for el in els
                if el.tag == OWLNS + "ObjectProperty" and el.get(RDF + "about")}
    annprops = {el.get(RDF + "about") for el in els
                if el.tag == OWLNS + "AnnotationProperty" and el.get(RDF + "about")}
    # L5_alt：本地子图（只走两端皆本地的边，起点＝本地类中无本地父类者）
    local_children = {}
    local_parents = set()
    for s, o in res_edges:
        if s in local and o in local:
            local_children.setdefault(o, []).append(s)
            local_parents.add(s)
    local_roots = sorted(local - local_parents)
    best = 0

    def dfs(node, depth, seen):
        nonlocal best
        if depth > best:
            best = depth
        for ch in local_children.get(node, []):
            e = (ch, node)
            if e in seen:
                continue
            dfs(ch, depth + 1, seen | {e})

    for r in local_roots:
        dfs(r, 0, frozenset())
    l5_alt = best
    subjects_all = {s for s, _o in res_edges if s}
    l5_selfcheck = len([c for c in local if c not in subjects_all])
    has_any_child = {o for s, o in res_edges if o in local}
    l6_alt = len([c for c in local if c not in has_any_child])
    anonymous_class = sum(1 for el in els
                          if el.tag == OWLNS + "Class" and not el.get(RDF + "about"))
    return {
        "L3_local": len([i for i in objprops if i.startswith(ns)]),
        "L4_local": len([i for i in annprops if i.startswith(ns)]),
        "L5_alt": l5_alt,
        "L5_selfcheck": l5_selfcheck,
        "L6_alt": l6_alt,
        "anonymous_class": anonymous_class,
    }


def ns_contrast_rows(input_path, params=None):
    """三个禁法对照读数（§7.4：留痕，不作判据）。返回 (三行读数, host, dir)。"""
    _root, els, _pm = _parse(input_path)
    ont = _ontology_iri(els)
    named = _named_classes(els)
    ns = local_namespace(input_path)
    host, dirpath = _ns_parts(ns)
    main = len(_local_set(named, ns))
    # 读法一：rdf:about 去文件名
    base = ont.rsplit("/", 1)[0] + "/"
    hits_strip = len({i for i in named if i.startswith(base)})
    # 读法二：前缀 BCIO_
    hits_bcio = len({i for i in named
                     if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_")})
    # 读法三：出现最多的前缀（本地名第一个 _ 前段；同数按串升序取首）
    pref = Counter(i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].split("_")[0] for i in named)
    top_pref, top_hits = sorted(pref.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    note = "巧合，不是判据" if hits_strip == main else "与主值不同值"
    note2 = "巧合，不是判据" if hits_bcio == main else "与主值不同值"
    note3 = "巧合，不是判据" if top_hits == main else "与主值不同值"
    rows = [
        {"rule": (f"对照读法一（禁法·不作判据）：rdf:about 去文件名——以 owl:Ontology@rdf:about "
                  f"去掉末段文件名所得串 {base} 为前缀计数；推导得 host={host}、最集中目录={dirpath}；"
                  f"与主值同值，{note}"),
         "hits": hits_strip,
         "derivation_ref": {"code": "code/quant_a.py", "entry": "ns_contrast_rows", "params": {}}},
        {"rule": (f"对照读法二（禁法·不作判据）：前缀 BCIO_——本地名以 BCIO_ 起头的命名类计数；"
                  f"推导得 host={host}、最集中目录={dirpath}；与主值同值，{note2}"),
         "hits": hits_bcio,
         "derivation_ref": {"code": "code/quant_a.py", "entry": "ns_contrast_rows", "params": {}}},
        {"rule": (f"对照读法三（禁法·不作判据）：出现最多的前缀——本地名第一个下划线前段计次，"
                  f"{top_pref} 居首（{top_hits} 次）；推导得 host={host}、最集中目录={dirpath}；"
                  f"与主值同值，{note3}"),
         "hits": top_hits,
         "derivation_ref": {"code": "code/quant_a.py", "entry": "ns_contrast_rows", "params": {}}},
    ]
    return rows, host, dirpath


def ns_document(input_path):
    """evidence/ns.json 八字段（rule 指到本文件 local_namespace 的行区间）。"""
    _root, els, _pm = _parse(input_path)
    ns = local_namespace(input_path)
    named = sorted(set(_named_classes(els)))
    local = _local_set(named, ns)
    prefix_iris = sorted(i for i in named
                         if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_"))
    classes = [{"iri": i, "in_ns": i in local} for i in named]
    sym = sorted(local.symmetric_difference(set(prefix_iris)))
    span = _entry_span("local_namespace")
    _rows, host, dirpath = ns_contrast_rows(input_path)
    return {
        "rule": (f"code/quant_a.py::local_namespace（第 {span[0]}–{span[1]} 行）：宿主取 "
                 f"owl:Ontology@rdf:about 的 netloc，再取该宿主上命名类 IRI 最集中的目录；"
                 f"本地＝IRI 以 scheme://host+dir 为前缀"),
        "host": host,
        "dir": dirpath,
        "count": len(local),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": classes,
        "prefix_iris": prefix_iris,
    }


def tiers_document(input_path):
    """deviations/tiers.json 五键闭集。分档与总数来自同一次遍历；
    另一次独立遍历复核总数（不一致会抛错，由人读段记差异）。"""
    _root, els, pmap = _parse(input_path)
    ns = local_namespace(input_path)
    named = set(_named_classes(els))
    local = _local_set(named, ns)
    anon_n = _anon_numbering(els)
    # 同一次遍历：分档 + 总数 + 匿名宾语
    tier = {"tier1": [], "tier2": [], "tier3": []}
    anon_rows = []
    total_elements = 0
    with_resource = 0
    for el in els:
        if el.tag != RDFS + "subClassOf":
            continue
        total_elements += 1
        subj = _enclosing_named_class(el, pmap)
        res = el.get(RDF + "resource")
        if res is None:
            kids = [c for c in el]
            obj = kids[0] if kids else None
            n = anon_n.get(id(obj)) if obj is not None else None
            anon_rows.append(f"{subj}|@anonymous#{n}")
            continue
        with_resource += 1
        s_in = subj in local if subj else False
        o_in = res in local
        if s_in and o_in:
            tier["tier1"].append(f"{subj}|{res}")
        elif s_in and not o_in:
            tier["tier2"].append(f"{subj}|{res}")
        else:
            tier["tier3"].append(f"{subj}|{res}")
    # 独立第二次遍历复核（重建索引再数一遍，两边各自数，不做减法）
    _root2, els2, pmap2 = _parse(input_path)
    recheck_elements = sum(1 for el in els2 if el.tag == RDFS + "subClassOf")
    recheck_resource = sum(1 for el in els2
                           if el.tag == RDFS + "subClassOf" and el.get(RDF + "resource"))
    if (recheck_elements, recheck_resource) != (total_elements, with_resource):
        raise RuntimeError(
            f"两次遍历不一致：{total_elements}/{with_resource} vs "
            f"{recheck_elements}/{recheck_resource}")

    def block(keys):
        items = [{"key": k, "ord": i + 1} for i, k in enumerate(sorted(keys))]
        return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}

    ra_items = [{"key": "partition_total", "value": total_elements}]
    return {
        "tier1": block(tier["tier1"]),
        "tier2": block(tier["tier2"]),
        "tier3": block(tier["tier3"]),
        "anon_subclass_objects": block(anon_rows),
        "readings_alt": {"items": ra_items, "rows": len(ra_items),
                         "sha256": _canon_sha(ra_items)},
    }


# ── 文本锚与七步（kind=line） ──────────────────────────────────────

def _paper_lines(paper_path):
    return Path(paper_path).read_text(encoding="utf-8").splitlines()


def anchors(paper_path, owl_path):
    """13 锚（§三）：定位串全部在本件实跑命中后取值。"""
    lines = _paper_lines(paper_path)
    owl_text = Path(owl_path).read_text(encoding="utf-8")

    def after_int(lineno, locator):
        line = lines[lineno - 1]
        i = line.find(locator)
        if i < 0:
            raise RuntimeError(f"定位串未命中 L{lineno}: {locator[:40]}…")
        m = re.search(r"-?\d+", line[i + len(locator):])
        return int(m.group(0))

    a01 = after_int(53, "The final version of the Intervention Setting Ontology "
                        "presents a six-level hierarchical structure comprising of")
    l46 = lines[45]
    i2 = l46.find("Inter-rater reliability from the")
    a02 = float(re.search(r"a=\s*(-?\d+(?:\.\d+)?)", l46[i2:]).group(1))
    a03 = after_int(42, "countries. Of the")
    m12 = re.search(r'owl:versionIRI[^>]*rdf:resource="([^"]+)"', owl_text)
    m13 = re.search(r'owl:Ontology[^>]*rdf:about="([^"]+)"', owl_text)
    v12, v13 = m12.group(1), m13.group(1)
    return [
        {"id": "A01", "value": a01, "source": f"{PAPER}#L53", "locator": "#s1"},
        {"id": "A02", "value": a02, "source": f"{PAPER}#L46", "locator": "取第 1/2 处"},
        {"id": "A03", "value": a03, "source": f"{PAPER}#L42", "locator": "#s2"},
        {"id": "A04", "value": lines[4].strip(), "source": f"{PAPER}#L5"},
        {"id": "A05", "value": lines[50].strip(), "source": f"{PAPER}#L51"},
        {"id": "A06", "value": lines[51].split()[0], "source": f"{PAPER}#L52"},
        {"id": "A07", "value": lines[7].strip(), "source": f"{PAPER}#L8"},
        {"id": "A08", "value": lines[29].strip(), "source": f"{PAPER}#L30"},
        {"id": "A09", "value": lines[55].strip(), "source": f"{PAPER}#L56"},
        {"id": "A10", "value": lines[9].strip(), "source": f"{PAPER}#L10",
         "locator": "取第 1/2 处"},
        {"id": "A11", "value": lines[26].strip(), "source": f"{PAPER}#L27"},
        {"id": "A12", "value": v12, "source": f"{OWLNAME}#{v12}",
         "locator": f'rdf:resource="{v12}"'},
        {"id": "A13", "value": v13, "source": f"{OWLNAME}#{v13}",
         "locator": f'rdf:about="{v13}"'},
    ]


def protocol_document(paper_path):
    """七步（kind=line）：先列 Methods 下全部 Step 标题，再按位置取前七个；
    禁用标题去重（Results 重列不计）。"""
    lines = _paper_lines(paper_path)
    m_line = next(i for i, t in enumerate(lines, 1) if t.strip() == "Methods")
    r_line = next(i for i, t in enumerate(lines, 1) if t.strip() == "Results")
    heads = [(i, t.strip()) for i, t in enumerate(lines, 1)
             if m_line < i < r_line and re.match(r"^Step \d", t.strip())]
    seven = heads[:7]
    if len(seven) != 7:
        raise RuntimeError(f"Methods 内 Step 标题数 {len(seven)} ≠ 7")
    if [t for _ln, t in seven] != STEP_TITLES:
        raise RuntimeError("Methods 内七步标题与题面 §4.1 表不符")
    steps = []
    for pos, (lineno, title) in enumerate(seven, 1):
        nxt = seven[pos][0] if pos < 7 else r_line
        steps.append({
            "pos": pos,
            "label": f"S{pos}",
            "title": title,
            "src": PAPER,
            "kind": "line",
            "target": f"{PAPER}#L{lineno}-L{nxt - 1}",
            "evidence_loc": f"{PAPER}#L{lineno}-L{lineno}",
            "input": STEP_IO[pos - 1][0],
            "output": STEP_IO[pos - 1][1],
        })
    return {
        "rule": ("先列 Methods 下全部 Step 标题行，再按位置取前七个（禁用标题去重；"
                 "Results 重列的同形标题不计），段＝标题行至下一同级标题前一行"),
        "source": f"{PAPER}#L10-L29",
        "steps": steps,
    }


def readings_document(input_path, anchors_rows):
    vals = alt_readings(input_path)
    a = {r["id"]: r["value"] for r in anchors_rows}
    self_un = {"A02": a["A02"], "A03": a["A03"]}
    out = []
    for name in READINGS_NAMES:
        if name == "self_report_unmeasured":
            payload = {"name": name, "kind": "map", "value": self_un}
        else:
            payload = {"name": name, "kind": "scalar", "value": vals[name]}
        payload["sha256"] = _canon_sha(
            {"name": payload["name"], "kind": payload["kind"], "value": payload["value"]})
        out.append(payload)
    return out


def diff_document(input_path, anchors_rows):
    a = {r["id"]: r["value"] for r in anchors_rows}
    _root, els, _pm = _parse(input_path)
    ns = local_namespace(input_path)
    local = sorted(_local_set(set(_named_classes(els)), ns))
    measured = len(local)
    self_reported = a["A01"]
    gap = measured - self_reported
    direction = "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等")
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(local)]
    payload = {"anchor": "A01", "measured": measured,
               "self_reported": self_reported, "items": items}
    return {
        "anchor": "A01",
        "measured": measured,
        "self_reported": self_reported,
        "items": items,
        "rows": len(items),
        "gap": gap,
        "direction": direction,
        "sha256": _canon_sha(payload),
    }


# ── 发射（A-1：每件 evidence/deviations 产物都能指到本文件一行） ────

def _canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _entry_span(name):
    """本文件里 `def name(` 的行区间 [def 行, 函数体末行]（供 entries.json）。"""
    src = Path(__file__).read_text(encoding="utf-8").splitlines()
    pat = re.compile(rf"\s*def {re.escape(name)}\s*\(")
    hits = [i for i, ln in enumerate(src, 1) if pat.match(ln)]
    if len(hits) != 1:
        raise RuntimeError(f"def {name}( 出现 {len(hits)} 次")
    d = hits[0]
    indent = len(src[d - 1]) - len(src[d - 1].lstrip())
    body_end = d
    for i in range(d + 1, len(src) + 1):
        ln = src[i - 1]
        if not ln.strip():
            continue
        cur = len(ln) - len(ln.lstrip())
        if cur <= indent and not ln.lstrip().startswith("#"):
            break
        if not ln.lstrip().startswith("#"):
            body_end = i
    return [d, body_end]


def entries_document():
    names = {
        "L1": "l1_local_classes", "L2": "l2_subclass_edges",
        "L3": "l3_object_properties", "L4": "l4_annotation_properties",
        "L5": "l5_max_depth", "L6": "l6_leaf_classes",
    }
    rel = f"code/{Path(__file__).name}"
    return {k: {"file": rel, "entry": fn, "lines": _entry_span(fn)}
            for k, fn in names.items()}


def emit_artifacts(input_path, params=None):
    """按 params['only'] 生成一件 evidence/ 或 deviations/ 产物并落盘。"""
    only = (params or {}).get("only")
    pkg_dir = Path(__file__).resolve().parents[1]
    research = pkg_dir.parent
    owl_path = Path(str(input_path)) if input_path else research / OWLNAME
    paper_path = research / PAPER
    anchors_rows = anchors(paper_path, owl_path)
    docs = {
        "ns": ns_document(owl_path),
        "anchors": anchors_rows,
        "protocol": protocol_document(paper_path),
        "entries": entries_document(),
        "tiers": tiers_document(owl_path),
        "overlap": {"peers": {}, "unavailable": ["0005"]},
        "contrast": ns_contrast_rows(owl_path)[0],
        "readings": readings_document(owl_path, anchors_rows),
        "diff_A01": diff_document(owl_path, anchors_rows),
    }
    paths = {
        "ns": ("evidence", "ns.json"),
        "anchors": ("evidence", "anchors.json"),
        "protocol": ("evidence", "protocol.json"),
        "entries": ("evidence", "entries.json"),
        "tiers": ("deviations", "tiers.json"),
        "overlap": ("deviations", "overlap.json"),
        "contrast": ("deviations", "contrast.json"),
        "readings": ("deviations", "readings.json"),
        "diff_A01": ("deviations", "diff_A01.json"),
    }
    if only not in paths:
        for k, (sub, name) in paths.items():
            if only == f"{sub}/{name}":
                only = k
                break
    if only not in paths:
        raise RuntimeError(f"unknown artifact: {only}")
    sub, name = paths[only]
    out = pkg_dir / sub / name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(docs[only], ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return {"path": f"{sub}/{name}"}


def main(argv=None):
    owl = (argv or sys.argv[1:] or [None])[0]
    if owl is None:
        owl = str(Path(__file__).resolve().parents[2] / OWLNAME)
    vals = {
        "L1": l1_local_classes(owl)["v"],
        "L2": l2_subclass_edges(owl)["v"],
        "L3": l3_object_properties(owl)["v"],
        "L4": l4_annotation_properties(owl)["v"],
        "L5": l5_max_depth(owl)["v"],
        "L6": l6_leaf_classes(owl)["v"],
    }
    print(json.dumps(vals, sort_keys=True))
    return vals


if __name__ == "__main__":
    main()
