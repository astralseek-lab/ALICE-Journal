#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg-A 主实现：Wright 2023《Style of Delivery Ontology》K=6 量与证据件生成。

口径（与题面 §二／§七.3 一致）：
  · XML 解析：xml.etree.ElementTree；遍历：递归；计数：建索引后计数；
    IRI 划界：前缀比较（本地命名空间串前缀匹配）。
  · 本地命名空间＝宿主＋最集中目录：宿主取自 owl:Ontology@rdf:about 的 netloc，
    目录＝命中本地类 IRI 最多的那一层完整 path 前缀（#fragment 与末段不计）。
  · L5 方向：rdfs:subClassOf 的宾语是父类、主语是子类；「下行」＝按宾语反查子节点；
    深度＝边数；环由「同边只走一次」断开。
六个固定入口（判据 19 声明名，不得改）：l1_local_classes／l2_subclass_edges／
l3_object_properties／l4_annotation_properties／l5_max_depth／l6_leaf_classes。
"""
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from urllib.parse import urlsplit

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWLT = "{http://www.w3.org/2002/07/owl#}"
RDFST = "{http://www.w3.org/2000/01/rdf-schema#}"
ABOUT = RDF + "about"
RESOURCE = RDF + "resource"

SECTION_TITLES = (
    "Introduction", "Aim", "Methods", "Ethics", "Design", "Results",
    "Discussion", "Strengths and limitations", "Conclusions",
)


def _parse(path):
    return ET.parse(str(path)).getroot()


def ontology_iri(root):
    el = root.find(OWLT + "Ontology")
    return el.get(ABOUT) if el is not None else ""


def version_iri(root):
    el = root.find(OWLT + "Ontology")
    if el is None:
        return ""
    v = el.find(OWLT + "versionIRI")
    return v.get(RESOURCE) if v is not None else ""


def iri_dir(iri):
    """IRI 的目录层：去 #fragment，再去 path 末段（文件名／标识段）。"""
    nofrag = iri.split("#", 1)[0]
    path = urlsplit(nofrag).path
    if "/" in path:
        return path.rsplit("/", 1)[0] + "/"
    return "/"


def local_namespace(root):
    """主口径：宿主＋最集中目录。返回 (host, dir, namespace)。"""
    ont = ontology_iri(root)
    host = urlsplit(ont).netloc
    scheme = urlsplit(ont).scheme
    named = [el.get(ABOUT) for el in root.iter(OWLT + "Class") if el.get(ABOUT)]
    host_iris = {i for i in named if urlsplit(i).netloc == host}
    counter = counter_dirs(host_iris)
    best_dir = counter_most(counter) if host_iris else "/"
    return host, best_dir, f"{scheme}://{host}{best_dir}"


def counter_dirs(host_iris):
    return Counter(iri_dir(i) for i in host_iris)


def counter_most(counter):
    return counter.most_common(1)[0][0] if counter else "/"


def named_class_iris(root):
    """全件具名 owl:Class（带 rdf:about），文档序，不去重。"""
    return [el.get(ABOUT) for el in root.iter(OWLT + "Class") if el.get(ABOUT)]


def local_class_set(root):
    _h, _d, ns = local_namespace(root)
    return {i for i in set(named_class_iris(root)) if i.startswith(ns)}


def anonymous_numbers(root):
    """匿名节点编号：无 rdf:about 的 owl:Class 与 owl:Restriction，文档序从 1 连续编号。"""
    out = {}
    n = 0
    for el in root.iter():
        if el.tag in (OWLT + "Class", OWLT + "Restriction") and el.get(ABOUT) is None:
            n += 1
            out[id(el)] = n
    return out


def iter_subclass_edges(root):
    """递归遍历，产出每条 rdfs:subClassOf 元素：
    (subject_kind, subject, object)；subject_kind ∈ ('iri', 'anon')；
    object 为 IRI 串（@rdf:resource）或 '@anonymous#n'（匿名宾语）。
    """
    anon = anonymous_numbers(root)
    edges = []

    def walk(el, enclosing):
        if el.tag == OWLT + "Class":
            about = el.get(ABOUT)
            enclosing = ("iri", about) if about else ("anon", f"@anonymous#{anon[id(el)]}")
        if el.tag == RDFST + "subClassOf":
            res = el.get(RESOURCE)
            subj = enclosing if enclosing else ("anon", "@anonymous#0")
            if res:
                edges.append((subj[0], subj[1], res))
            else:
                obj = None
                for ch in list(el):
                    if isinstance(ch.tag, str):
                        obj = ch
                        break
                if obj is not None and obj.get(ABOUT):
                    edges.append((subj[0], subj[1], obj.get(ABOUT)))
                elif obj is not None and id(obj) in anon:
                    edges.append((subj[0], subj[1], f"@anonymous#{anon[id(obj)]}"))
                else:
                    edges.append((subj[0], subj[1], "@anonymous#0"))
        for ch in list(el):
            walk(ch, enclosing)

    for top in list(root):
        walk(top, None)
    return edges


def l1_local_classes(path):
    """L1 本地类数：有 rdf:about 且 IRI 落在本地命名空间的 owl:Class，按 IRI 去重。"""
    return len(local_class_set(_parse(path)))


def l2_subclass_edges(path):
    """L2 子类边数：全件 rdfs:subClassOf@rdf:resource 三元组，按条计、不去重。"""
    return sum(1 for _k, _s, o in iter_subclass_edges(_parse(path)) if not o.startswith("@anonymous#"))


def l3_object_properties(path):
    """L3 对象属性数：owl:ObjectProperty 按 IRI 去重，全件计（含外部内联声明）。"""
    return len({el.get(ABOUT) for el in _parse(path).iter(OWLT + "ObjectProperty") if el.get(ABOUT)})


def l4_annotation_properties(path):
    """L4 注释属性数：owl:AnnotationProperty 按 IRI 去重，全件计。"""
    return len({el.get(ABOUT) for el in _parse(path).iter(OWLT + "AnnotationProperty") if el.get(ABOUT)})


def _depth_index(root):
    """建索引：子→父、父→子、具名类集、本地类集。"""
    named = set(named_class_iris(root))
    in_ns = local_class_set(root)
    children, parents = {}, {}
    for kind, s, o in iter_subclass_edges(root):
        if kind != "iri" or o.startswith("@anonymous#"):
            continue
        children.setdefault(o, []).append(s)
        parents.setdefault(s, []).append(o)
    return named, in_ns, children, parents


def l5_max_depth(path):
    """L5 最大层级深度：起点＝全图根（不作任何 subClassOf 主语的具名类，含外部顶层类），
    沿 subClassOf 下行到最远本地类的边数；同边只走一次。"""
    root = _parse(path)
    named, in_ns, children, parents = _depth_index(root)
    roots = sorted(c for c in named if c not in parents)
    sys.setrecursionlimit(100000)
    best = 0

    def dfs(node, depth, used):
        nonlocal best
        if node in in_ns and depth > best:
            best = depth
        for ch in children.get(node, []):
            edge = (ch, node)
            if edge in used:
                continue
            used.add(edge)
            dfs(ch, depth + 1, used)
            used.discard(edge)

    for r in roots:
        dfs(r, 0, set())
    return best


def l6_leaf_classes(path):
    """L6 叶类数：本地类中无本地子类者（只看本地→本地的边）。"""
    root = _parse(path)
    in_ns = local_class_set(root)
    local_children = set()
    for kind, s, o in iter_subclass_edges(root):
        if kind == "iri" and not o.startswith("@anonymous#") and s in in_ns and o in in_ns:
            local_children.add(o)
    return len([c for c in in_ns if c not in local_children])


# ── 另报量（deviations/readings.json 的实测端；非 K）──

def readings_scalars(path):
    """另报八条中的七条 scalar（第八条 self_report_unmeasured 由锚侧给值）。"""
    root = _parse(path)
    _h, _d, ns = local_namespace(root)
    named = set(named_class_iris(root))
    in_ns = {i for i in named if i.startswith(ns)}
    obj = {el.get(ABOUT) for el in root.iter(OWLT + "ObjectProperty") if el.get(ABOUT)}
    ann = {el.get(ABOUT) for el in root.iter(OWLT + "AnnotationProperty") if el.get(ABOUT)}
    named_l, in_ns_l, children, parents = _depth_index(root)
    # L5_alt：本地子图（起点＝本地类中无本地父类者，只走两端本地边）
    lch, lpa = {}, {}
    for kind, s, o in iter_subclass_edges(root):
        if kind == "iri" and not o.startswith("@anonymous#") and s in in_ns and o in in_ns:
            lch.setdefault(o, []).append(s)
            lpa.setdefault(s, []).append(o)
    local_roots = [c for c in in_ns if c not in lpa]
    sys.setrecursionlimit(100000)
    best_alt = 0

    def dfs_alt(node, depth, used):
        nonlocal best_alt
        if depth > best_alt:
            best_alt = depth
        for ch in lch.get(node, []):
            edge = (ch, node)
            if edge in used:
                continue
            used.add(edge)
            dfs_alt(node=ch, depth=depth + 1, used=used)
            used.discard(edge)

    for r in local_roots:
        dfs_alt(r, 0, set())
    anon_all = sum(1 for el in root.iter(OWLT + "Class") if el.get(ABOUT) is None)
    anon_direct = sum(1 for el in list(root) if el.tag == OWLT + "Class" and el.get(ABOUT) is None)
    return {
        "L3_local": len([i for i in obj if i.startswith(ns)]),
        "L4_local": len([i for i in ann if i.startswith(ns)]),
        "L5_alt": best_alt,
        "L5_selfcheck": len([c for c in in_ns if c not in parents]),
        "L6_alt": len([c for c in in_ns if c not in children]),
        "anonymous_class": anon_all,
        "anonymous_class_direct": anon_direct,
    }


def build_overlap(this_path, peer_path):
    """与对照件的类 IRI 交叠：全件具名 owl:Class 的 IRI 集三组差。"""
    a = set(named_class_iris(_parse(this_path)))
    peer_root = _parse(peer_path)
    b = {el.get(ABOUT) for el in peer_root.iter(OWLT + "Class") if el.get(ABOUT)}
    return {
        "both": sorted(a & b),
        "only_in_this": sorted(a - b),
        "only_in_peer": sorted(b - a),
    }


# ── 三个对照读法（§7.4 禁法留痕；deviations/contrast.json）──

def contrast_strip_filename(path):
    """对照读法一：rdf:about 去文件名——owl:Ontology@rdf:about 去末段作为命名空间。"""
    root = _parse(path)
    ont = ontology_iri(root)
    ns = ont.rsplit("/", 1)[0] + "/" if "/" in ont else ont
    return len([i for i in set(named_class_iris(root)) if i.startswith(ns)])


def contrast_prefix_bcio(path):
    """对照读法二：前缀 BCIO_——类 IRI 末段以 BCIO_ 开头者。"""
    root = _parse(path)
    return len([
        i for i in set(named_class_iris(root))
        if i.rsplit("/", 1)[-1].split("#")[-1].startswith("BCIO_")
    ])


def contrast_most_common_prefix(path):
    """对照读法三：出现最多的前缀——全件具名类按目录层分组，最集中者。"""
    root = _parse(path)
    counter = Counter(iri_dir(i) for i in set(named_class_iris(root)))
    top = counter.most_common(1)[0][0] if counter else ""
    return len([i for i in set(named_class_iris(root)) if iri_dir(i) == top])


# ── tiers.json 内容（L2 三档＋匿名宾语，同一遍历分出）──

def build_tiers(path):
    """一次遍历分出三档＋匿名宾语清单；key＝主体|宾语，重复条末尾追加 @k。"""
    root = _parse(path)
    in_ns = local_class_set(root)
    edges = iter_subclass_edges(root)
    total = len(edges)
    tier1, tier2, tier3, anon_obj = [], [], [], []
    for kind, s, o in edges:
        if o.startswith("@anonymous#"):
            anon_obj.append((s, o))
        elif kind == "iri" and s in in_ns and o in in_ns:
            tier1.append((s, o))
        elif kind == "iri" and s in in_ns:
            tier2.append((s, o))
        else:
            tier3.append((s, o))
    blocks = {}
    for name, pairs in (("tier1", tier1), ("tier2", tier2), ("tier3", tier3),
                        ("anon_subclass_objects", anon_obj)):
        seen = Counter()
        keys = []
        for s, o in pairs:
            seen[(s, o)] += 1
            k = seen[(s, o)]
            keys.append(f"{s}|{o}" if k == 1 else f"{s}|{o}@{k}")
        keys.sort()
        blocks[name] = [{"key": k2, "ord": i} for i, k2 in enumerate(keys, 1)]
    return {"blocks": blocks, "partition_total": total}


# ── 证据件生成入口（A-1：evidence/ 每件产物的生成入口可指到一行）──

def build_ns_json(path):
    """生成 evidence/ns.json 的载荷（八字段）；v＝本地类数（与 L1 同值）。"""
    root = _parse(path)
    host, best_dir, ns = local_namespace(root)
    named = sorted(set(named_class_iris(root)))
    classes = [{"iri": i, "in_ns": i.startswith(ns)} for i in named]
    in_ns = {c["iri"] for c in classes if c["in_ns"]}
    prefix_iris = sorted(
        i for i in named if i.rsplit("/", 1)[-1].split("#")[-1].startswith("BCIO_")
    )
    sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
    with open(__file__, encoding="utf-8") as fh:
        src_lines = fh.read().splitlines()
    defline = next(i for i, ln in enumerate(src_lines, 1) if ln.startswith("def local_namespace("))
    payload = {
        "rule": f"code/style_metrics.py::local_namespace（def 第 {defline} 行起）：宿主取自 "
                "owl:Ontology@rdf:about，目录取命中本地类 IRI 最多的完整 path 前缀（#fragment 与末段不计）",
        "host": host,
        "dir": best_dir,
        "count": len(in_ns),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": not sym, "sym_diff": sym},
        "classes": classes,
        "prefix_iris": prefix_iris,
    }
    return {"v": len(in_ns), "payload": payload}


def build_anchors(corpus_path, owl_path):
    """从语料与本体件抽出 13 条锚（A01–A13）；v＝锚条数。"""
    lines = open(str(corpus_path), encoding="utf-8").read().splitlines()
    owl_text = open(str(owl_path), encoding="utf-8").read()
    m = re.search(r"consisted of (\d+) entities relevant to style of delivery", lines[37])
    a01 = int(m.group(1))
    m = re.search(r"α = ([0-9.]+)", lines[35])
    a02 = float(m.group(1))
    m = re.search(r"annotated (\d+) intervention reports", lines[17])
    a03 = int(m.group(1))
    root = _parse(owl_path)
    a12 = version_iri(root)
    a13 = ontology_iri(root)
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
    """按位置取 Methods 下七个 Step 标题（先列全部标题、禁用去重）；v＝步数。"""
    lines = open(str(corpus_path), encoding="utf-8").read().splitlines()
    methods_pos = lines.index("Methods") + 1     # L40
    results_pos = lines.index("Results") + 1     # L50
    heads = [
        (i + 1, ln) for i, ln in enumerate(lines)
        if methods_pos <= i + 1 < results_pos and (
            ln in SECTION_TITLES or re.match(r"^Step \d+ – ", ln))
    ]
    steps = [(pos, t) for pos, t in heads if t.startswith("Step")][:7]
    return {"v": len(steps), "steps": [{"pos": i + 1, "line": ln0, "title": t}
                                       for i, (ln0, t) in enumerate(steps)]}


def build_entries(owl_path):
    """六量入口声明自检：本文件恰含六个固定入口各一处 def；v＝入口数。"""
    src = open(__file__, encoding="utf-8").read().splitlines()
    names = ("l1_local_classes", "l2_subclass_edges", "l3_object_properties",
             "l4_annotation_properties", "l5_max_depth", "l6_leaf_classes")
    found = {}
    for i, ln in enumerate(src, 1):
        for nm in names:
            if re.match(rf"def {re.escape(nm)}\(", ln):
                found[nm] = found.get(nm, 0) + 1
    assert all(found.get(nm) == 1 for nm in names), found
    return {"v": len(names), "entries": list(names)}


def para_lines_from_corpus(corpus_path):
    """按 §5.2 归行规则回推：内容行 − 节标题 − 表题 − 表头＝主文 <p> 起行数。"""
    lines = open(str(corpus_path), encoding="utf-8").read().splitlines()
    titles = sum(
        1 for ln in lines
        if ln in SECTION_TITLES or re.match(r"^Step \d+ – ", ln)
    )
    captions = sum(1 for ln in lines if re.match(r"^(Table|Figure) \d+\. ", ln))
    headers = {"Term Definition Source", "Label [URI] Parent class Definition"}
    header_lines = sum(1 for ln in lines if ln in headers)
    return len(lines) - titles - captions - header_lines


def canonical_sha(payload):
    """载荷规范 sha：json.dumps(sort_keys, 紧凑分隔, ensure_ascii=False) 的 UTF-8 sha256。"""
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
