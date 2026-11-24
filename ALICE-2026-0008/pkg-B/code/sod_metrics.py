#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg-B 独立第二实现：Style of Delivery Ontology 六量与证据件（独立重算，不读 pkg-A）。

独立性实现面（与 pkg-A 的十道差异对应）：
  · 解析器：xml.dom.minidom（不用 xml.etree.ElementTree）；
  · 遍历：显式栈迭代（不递归）；
  · 计数：流式一次过（单次遍历同时累计各计数器，不建二次索引）；
  · IRI 划界：urllib.parse.urlsplit 取 netloc＋path 独立推导（不沿用前缀比较路线）；
  · 命名空间：独立按「宿主＋最集中目录」重算主值，三个对照读法各按件实算。
六固定入口名与题面一致（l1_local_classes 等六名），实现自成。
"""
import hashlib
import json
import re
from collections import Counter
from urllib.parse import urlsplit
from xml.dom import minidom

A_ABOUT = "rdf:about"
A_RESOURCE = "rdf:resource"
T_CLASS = "owl:Class"
T_RESTRICTION = "owl:Restriction"
T_SUBCLASS = "rdfs:subClassOf"
T_OBJPROP = "owl:ObjectProperty"
T_ANNPROP = "owl:AnnotationProperty"
T_ONTOLOGY = "owl:Ontology"
T_VERSION = "owl:versionIRI"

SECTION_HEADS = (
    "Introduction", "Aim", "Methods", "Ethics", "Design", "Results",
    "Discussion", "Strengths and limitations", "Conclusions",
)


def _dom(path):
    with open(str(path), "rb") as fh:
        return minidom.parse(fh)


def _child_elems(node):
    return [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]


def _iter_pairs(root):
    """文档序 (element, 最近外层 owl:Class 元素或 None)。"""
    out = []
    stack = [(ch, None) for ch in reversed(_child_elems(root))]
    while stack:
        el, enc = stack.pop()
        if el.tagName == T_CLASS:
            enc = el
        out.append((el, enc))
        for ch in reversed(_child_elems(el)):
            stack.append((ch, enc))
    return out


def _about(el):
    v = el.getAttribute(A_ABOUT)
    return v if v else None


def _ontology_iri(doc):
    for el in doc.getElementsByTagName(T_ONTOLOGY):
        v = _about(el)
        if v:
            return v
    return ""


def _version_iri(doc):
    for el in doc.getElementsByTagName(T_VERSION):
        v = el.getAttribute(A_RESOURCE)
        if v:
            return v
    return ""


def _dir_of(iri):
    """独立划界：urlsplit 取 netloc＋path；目录＝path 去末段（#fragment 先剥）。"""
    parts = urlsplit(iri.split("#", 1)[0])
    p = parts.path
    dirpath = p.rsplit("/", 1)[0] + "/" if "/" in p else "/"
    return parts.netloc, dirpath


def derive_namespace(doc):
    """独立主值推导：宿主＝owl:Ontology@rdf:about 的 netloc；
    目录＝该宿主下具名类 IRI 最集中的完整 path 前缀。"""
    root = doc.documentElement
    ont = _ontology_iri(doc)
    host = urlsplit(ont).netloc
    scheme = urlsplit(ont).scheme
    counter = Counter()
    for el, _enc in _iter_pairs(root):
        if el.tagName != T_CLASS:
            continue
        iri = _about(el)
        if not iri:
            continue
        h, d = _dir_of(iri)
        if h == host:
            counter[d] += 1
    best = counter.most_common(1)[0][0] if counter else "/"
    return host, best, f"{scheme}://{host}{best}"


def stream_scan(path):
    """流式一次过：单趟遍历同时累计全部计数面（六量所需的原始计数与边表）。"""
    doc = _dom(path)
    root = doc.documentElement
    host, best, ns = derive_namespace(doc)
    named_in_order = []
    anon_map = {}          # element -> n（匿名 Class/Restriction 文档序编号）
    edges = []             # (subject_iri_or_anonkey, object_iri_or_anonkey, object_is_iri)
    n_objprop = []
    n_annprop = []
    anon_class_all = 0
    anon_class_top = 0
    for el, enc in _iter_pairs(root):
        tag = el.tagName
        if tag == T_CLASS:
            iri = _about(el)
            if iri:
                named_in_order.append(iri)
            else:
                anon_class_all += 1
                if enc is None:
                    anon_class_top += 1
        if tag in (T_CLASS, T_RESTRICTION) and not _about(el):
            if el not in anon_map:
                anon_map[el] = len(anon_map) + 1
        elif tag == T_OBJPROP:
            v = _about(el)
            if v:
                n_objprop.append(v)
        elif tag == T_ANNPROP:
            v = _about(el)
            if v:
                n_annprop.append(v)
        elif tag == T_SUBCLASS:
            if enc is not None and _about(enc):
                subj = ("iri", _about(enc))
            elif enc is not None:
                subj = ("anon", f"@anonymous#{anon_map[enc]}")
            else:
                subj = ("anon", "@anonymous#0")
            res = el.getAttribute(A_RESOURCE)
            if res:
                edges.append((subj, res, True))
            else:
                kids = _child_elems(el)
                if kids and _about(kids[0]):
                    edges.append((subj, _about(kids[0]), True))
                elif kids:
                    k0 = kids[0]
                    if k0 not in anon_map:
                        anon_map[k0] = len(anon_map) + 1
                    edges.append((subj, f"@anonymous#{anon_map[k0]}", False))
                else:
                    edges.append((subj, "@anonymous#0", False))
    return {
        "ns": (host, best, ns),
        "named": named_in_order,
        "edges": edges,
        "objprops": n_objprop,
        "annprops": n_annprop,
        "anon_class_all": anon_class_all,
        "anon_class_top": anon_class_top,
    }


def _local_set(scan):
    ns = scan["ns"][2]
    return {i for i in set(scan["named"]) if i.startswith(ns)}


def l1_local_classes(path):
    """L1 本地类数（独立实现）：具名 owl:Class 中 IRI 落在本地命名空间者，按 IRI 去重。"""
    return len(_local_set(stream_scan(path)))


def l2_subclass_edges(path):
    """L2 子类边数（独立实现）：subClassOf 且宾语为 IRI 者，按条计、不去重。"""
    return sum(1 for _s, _o, is_iri in stream_scan(path)["edges"] if is_iri)


def l3_object_properties(path):
    """L3 对象属性数（独立实现）：ObjectProperty 具名声明按 IRI 去重、全件计。"""
    return len(set(stream_scan(path)["objprops"]))


def l4_annotation_properties(path):
    """L4 注释属性数（独立实现）：AnnotationProperty 具名声明按 IRI 去重、全件计。"""
    return len(set(stream_scan(path)["annprops"]))


def _graph_views(scan):
    """由一次扫描建两个视图：全图（父→子、子→父）与本地子图。"""
    in_ns = _local_set(scan)
    children, parents = {}, {}
    lch, lpa = {}, {}
    for (skind, s), o, is_iri in scan["edges"]:
        if not is_iri or skind != "iri":
            continue
        children.setdefault(o, []).append(s)
        parents.setdefault(s, []).append(o)
        if s in in_ns and o in in_ns:
            lch.setdefault(o, []).append(s)
            lpa.setdefault(s, []).append(o)
    return in_ns, children, parents, lch, lpa


def l5_max_depth(path):
    """L5（独立实现）：全图根（无父具名类，含外部顶层）沿 subClassOf 下行，
    到最远本地类的边数；迭代 DFS＋同边只走一次。"""
    scan = stream_scan(path)
    in_ns, children, parents, _lch, _lpa = _graph_views(scan)
    named = set(scan["named"])
    best = 0
    for r in sorted(c for c in named if c not in parents):
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, used = stack.pop()
            if node in in_ns and depth > best:
                best = depth
            for ch in children.get(node, []):
                edge = (ch, node)
                if edge in used:
                    continue
                stack.append((ch, depth + 1, used | {edge}))
    return best


def l6_leaf_classes(path):
    """L6（独立实现）：本地类中无本地子类者（仅计两端本地的边）。"""
    scan = stream_scan(path)
    in_ns, _c, _p, lch, _lpa = _graph_views(scan)
    return sum(1 for c in in_ns if c not in lch)


# ── 另报量（独立重算）──

def readings_scalars_b(path):
    scan = stream_scan(path)
    ns = scan["ns"][2]
    in_ns = _local_set(scan)
    _ins, children, parents, lch, lpa = _graph_views(scan)
    # L5_alt：本地子图迭代 DFS，起点＝本地类中无本地父类者
    best = 0
    for r in sorted(c for c in in_ns if c not in lpa):
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, used = stack.pop()
            if depth > best:
                best = depth
            for ch in lch.get(node, []):
                edge = (ch, node)
                if edge in used:
                    continue
                stack.append((ch, depth + 1, used | {edge}))
    return {
        "L3_local": sum(1 for i in set(scan["objprops"]) if i.startswith(ns)),
        "L4_local": sum(1 for i in set(scan["annprops"]) if i.startswith(ns)),
        "L5_alt": best,
        "L5_selfcheck": sum(1 for c in in_ns if c not in parents),
        "L6_alt": sum(1 for c in in_ns if c not in children),
        "anonymous_class": scan["anon_class_all"],
        "anonymous_class_direct": scan["anon_class_top"],
    }


# ── 三个对照读法（独立实算）──

def contrast_strip_filename(path):
    doc = _dom(path)
    ont = _ontology_iri(doc)
    ns = ont.rsplit("/", 1)[0] + "/" if "/" in ont else ont
    scan = stream_scan(path)
    return sum(1 for i in set(scan["named"]) if i.startswith(ns))


def contrast_prefix_bcio(path):
    scan = stream_scan(path)
    return sum(
        1 for i in set(scan["named"])
        if i.rsplit("/", 1)[-1].split("#")[-1].startswith("BCIO_")
    )


def contrast_most_common_prefix(path):
    scan = stream_scan(path)
    counter = Counter(_dir_of(i)[1] for i in set(scan["named"]))
    top = counter.most_common(1)[0][0] if counter else ""
    return sum(1 for i in set(scan["named"]) if _dir_of(i)[1] == top)


# ── tiers（独立：另一次遍历分档）──

def build_tiers_b(path):
    scan = stream_scan(path)
    in_ns = _local_set(scan)
    total = len(scan["edges"])
    buckets = {"tier1": [], "tier2": [], "tier3": [], "anon_subclass_objects": []}
    for (skind, s), o, is_iri in scan["edges"]:
        if not is_iri:
            buckets["anon_subclass_objects"].append((s, o))
        elif skind == "iri" and s in in_ns and o in in_ns:
            buckets["tier1"].append((s, o))
        elif skind == "iri" and s in in_ns:
            buckets["tier2"].append((s, o))
        else:
            buckets["tier3"].append((s, o))
    blocks = {}
    for name, pairs in buckets.items():
        seen = Counter()
        keys = []
        for s, o in pairs:
            seen[(s, o)] += 1
            n = seen[(s, o)]
            keys.append(f"{s}|{o}" if n == 1 else f"{s}|{o}@{n}")
        keys.sort()
        blocks[name] = [{"key": k, "ord": i} for i, k in enumerate(keys, 1)]
    return {"blocks": blocks, "partition_total": total}


def build_overlap(this_path, peer_path):
    """与对照件的类 IRI 交叠（独立实现）：全件具名 owl:Class 的 IRI 集三组差。"""
    a = set(stream_scan(this_path)["named"])
    b = set(stream_scan(peer_path)["named"])
    return {
        "both": sorted(a & b),
        "only_in_this": sorted(a - b),
        "only_in_peer": sorted(b - a),
    }


# ── 证据件生成入口（A-1）──

def build_ns_json(path):
    scan = stream_scan(path)
    host, best, ns = scan["ns"]
    named = sorted(set(scan["named"]))
    classes = [{"iri": i, "in_ns": i.startswith(ns)} for i in named]
    in_ns = {c["iri"] for c in classes if c["in_ns"]}
    prefix_iris = sorted(
        i for i in named if i.rsplit("/", 1)[-1].split("#")[-1].startswith("BCIO_")
    )
    sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
    with open(__file__, encoding="utf-8") as fh:
        src_lines = fh.read().splitlines()
    defline = next(i for i, ln in enumerate(src_lines, 1) if ln.startswith("def derive_namespace("))
    payload = {
        "rule": f"code/sod_metrics.py::derive_namespace（def 第 {defline} 行起）："
                "urlsplit 取宿主，目录为命中本地类最多的完整 path 前缀",
        "host": host,
        "dir": best,
        "count": len(in_ns),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": not sym, "sym_diff": sym},
        "classes": classes,
        "prefix_iris": prefix_iris,
    }
    return {"v": len(in_ns), "payload": payload}


def build_anchors(corpus_path, owl_path):
    with open(str(corpus_path), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    with open(str(owl_path), encoding="utf-8") as fh:
        owl_text = fh.read()
    a01 = int(re.search(r"consisted of (\d+) entities relevant to style of delivery", lines[37]).group(1))
    a02 = float(re.search(r"α = ([0-9.]+)", lines[35]).group(1))
    a03 = int(re.search(r"annotated (\d+) intervention reports", lines[17]).group(1))
    doc = _dom(owl_path)
    a12 = _version_iri(doc)
    a13 = _ontology_iri(doc)
    anchors = [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L38", "locator": "#s1"},
        {"id": "A02", "value": a02, "source": "paper_text.txt#L36", "locator": "#s1"},
        {"id": "A03", "value": a03, "source": "paper_text.txt#L18", "locator": "#s2"},
        {"id": "A04", "value": lines[7], "source": "paper_text.txt#L8"},
        {"id": "A05", "value": lines[57], "source": "paper_text.txt#L58"},
        {"id": "A06", "value": lines[10], "source": "paper_text.txt#L11"},
        {"id": "A07", "value": lines[39], "source": "paper_text.txt#L40"},
        {"id": "A08", "value": lines[49], "source": "paper_text.txt#L50"},
        {"id": "A09", "value": lines[70], "source": "paper_text.txt#L71"},
        {"id": "A10", "value": lines[42], "source": "paper_text.txt#L43", "locator": "取第 1/2 处"},
        {"id": "A11", "value": lines[48], "source": "paper_text.txt#L49", "locator": "取第 1/2 处"},
        {"id": "A12", "value": a12, "source": f"bcio_style.owl#{a12}"},
        {"id": "A13", "value": a13, "source": f"bcio_style.owl#{a13}"},
    ]
    assert f'rdf:resource="{a12}"' in owl_text
    assert f'rdf:about="{a13}"' in owl_text
    return {"v": len(anchors), "anchors": anchors}


def build_protocol(corpus_path):
    """B 自己切节：从 paper_text.txt 重新定位 Methods 区间，取其中以 Step 开头的七个标题。"""
    with open(str(corpus_path), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    mpos = [i + 1 for i, ln in enumerate(lines) if ln == "Methods"]
    rpos = [i + 1 for i, ln in enumerate(lines) if ln == "Results"]
    lo, hi = mpos[0], rpos[0]
    heads = [
        (i + 1, ln) for i, ln in enumerate(lines)
        if lo <= i + 1 < hi and (ln in SECTION_HEADS or ln.startswith("Step "))
    ]
    steps = [(ln0, t) for ln0, t in heads if t.startswith("Step ")][:7]
    return {"v": len(steps), "steps": [{"pos": i + 1, "line": ln0, "title": t}
                                       for i, (ln0, t) in enumerate(steps)]}


def build_entries(owl_path):
    with open(__file__, encoding="utf-8") as fh:
        src = fh.read().splitlines()
    names = ("l1_local_classes", "l2_subclass_edges", "l3_object_properties",
             "l4_annotation_properties", "l5_max_depth", "l6_leaf_classes")
    found = Counter()
    for ln in src:
        for nm in names:
            if re.match(rf"def {re.escape(nm)}\(", ln):
                found[nm] += 1
    assert all(found[nm] == 1 for nm in names), dict(found)
    return {"v": len(names), "entries": list(names)}


def build_independence(owl_path):
    """独立性声明（四字段）：本实现自证不读 pkg-A。"""
    return {
        "v": 4,
        "payload": {
            "entry": "code/sod_metrics.py",
            "shared_code_with_a": False,
            "signer_pkg_id": "pkg-B",
            "source": "独立第二实现：xml.dom.minidom 解析＋显式栈迭代＋流式一次过计数＋urlsplit 划界；"
                      "未 import／未读取 pkg-A 的任何文件",
        },
    }


def para_lines_from_corpus(corpus_path):
    with open(str(corpus_path), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    titles = sum(1 for ln in lines if ln in SECTION_HEADS or ln.startswith("Step "))
    captions = sum(1 for ln in lines if re.match(r"^(Table|Figure) \d+\. ", ln))
    header_lines = sum(1 for ln in lines if ln in (
        "Term Definition Source", "Label [URI] Parent class Definition"))
    return len(lines) - titles - captions - header_lines


def canonical_sha(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
