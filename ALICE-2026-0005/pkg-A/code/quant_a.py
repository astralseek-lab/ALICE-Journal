# -*- coding: utf-8 -*-
"""ALICE-2026-0005 · pkg-A 主实现：upper-level BCIO 六量（L1–L6）＋另报＋产物生成。

链的可信不靠它永不变，靠它变了会响。

口径（题面 §二，写死）：
  L1 本地类数      有 rdf:about 且 IRI 以本地命名空间开头的 owl:Class，按 IRI 去重
  L2 子类边数      全件 rdfs:subClassOf@rdf:resource，按条计不去重；三档同一次遍历分出
  L3 对象属性数    owl:ObjectProperty 带 rdf:about 按 IRI 去重，全件计
  L4 注释属性数    owl:AnnotationProperty 带 rdf:about 按 IRI 去重，全件计
  L5 最大层级深度  起点＝全图根（不作任何 subClassOf 主语的类，含外部顶层类）；
                   沿 subClassOf 下行（宾语是父类、主语是子类）；深度＝到最远本地类的边数
  L6 叶类数        本地类中无本地子类者（只看本地→本地的边）

实现面（§5.3bis 十道维度中 A 侧允许的走法）：xml.etree.ElementTree 解析、
递归遍历、建索引后计数、前缀比较划界、命名空间一次算主值（宿主＋最集中目录）。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from urllib.parse import urlsplit

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWLP = "{http://www.w3.org/2002/07/owl#}"
RDFSP = "{http://www.w3.org/2000/01/rdf-schema#}"


def _root(path):
    return ET.parse(str(path)).getroot()


def _ontology_iri(root):
    for el in root.iter(OWLP + "Ontology"):
        about = el.get(RDF + "about")
        if about:
            return about
    return ""


def host_of(root):
    """本地宿主：owl:Ontology@rdf:about 的 netloc。"""
    return urlsplit(_ontology_iri(root)).netloc


def _named_class_iris(root):
    return [el.get(RDF + "about") for el in root.iter(OWLP + "Class") if el.get(RDF + "about")]


def local_namespace(path):
    """主口径（§7.3）：宿主＋最集中目录，一次算主值。"""
    root = _root(path)
    host = host_of(root)
    dirs = Counter()
    for iri in _named_class_iris(root):
        parts = urlsplit(iri)
        if parts.netloc == host:
            dirs[parts.path.rsplit("/", 1)[0] + "/"] += 1
    if not dirs:
        return ""
    top_dir = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    scheme = urlsplit(_ontology_iri(root)).scheme or "http"
    return f"{scheme}://{host}{top_dir}"


def _parent_map(root):
    return {c: p for p in root.iter() for c in p}


def _enclosing_class_iri(el, parent):
    cur = el
    while cur is not None:
        if cur.tag == OWLP + "Class":
            return cur.get(RDF + "about")
        cur = parent.get(cur)
    return None


def _subclass_edges(root):
    """全件 rdfs:subClassOf@rdf:resource 边：(主体 IRI, 宾语 IRI)，按条计、不去重。"""
    parent = _parent_map(root)
    edges = []
    for el in root.iter(RDFSP + "subClassOf"):
        obj = el.get(RDF + "resource")
        if not obj:
            continue  # 宾语为匿名 owl:Restriction 的边不带 @rdf:resource，不进 L2
        subj = _enclosing_class_iri(el, parent)
        if subj:
            edges.append((subj, obj))
    return edges


def _tiers(edges, ns):
    """三档（同一次遍历分出）：①两端皆本地 ②主体本地·宾语外部 ③其余。"""
    t1, t2, t3 = [], [], []
    for s, o in edges:
        sin, oin = s.startswith(ns), o.startswith(ns)
        if sin and oin:
            t1.append((s, o))
        elif sin:
            t2.append((s, o))
        else:
            t3.append((s, o))
    return t1, t2, t3


def l1_local_classes(path, params=None):
    """L1 主口径入口。返回 {'v': 本地类数}。"""
    ns = local_namespace(path)
    iris = _named_class_iris(_root(path))
    return {"v": len({i for i in iris if i.startswith(ns)})}


def l2_subclass_edges(path, params=None):
    """L2 主口径入口：全件 subClassOf@rdf:resource 条数；三档同源并复核。"""
    root = _root(path)
    ns = local_namespace(path)
    edges = _subclass_edges(root)                       # 这一次遍历：档与总数同源
    t1, t2, t3 = _tiers(edges, ns)
    total = len(edges)
    check = _subclass_edges(_root(path))                # 独立第二次遍历复核
    if len(check) != total or _tiers(check, ns) != (t1, t2, t3):
        raise RuntimeError("L2 两次遍历不一致（主遍历与复核遍历分叉）")
    if len(t1) + len(t2) + len(t3) != total:
        raise RuntimeError("L2 三档之和不等于总数")
    return {"v": total, "tier1": len(t1), "tier2": len(t2), "tier3": len(t3)}


def l3_object_properties(path, params=None):
    """L3 主口径入口：owl:ObjectProperty 带 rdf:about 按 IRI 去重，全件计。"""
    iris = [el.get(RDF + "about") for el in _root(path).iter(OWLP + "ObjectProperty")]
    return {"v": len({i for i in iris if i})}


def l4_annotation_properties(path, params=None):
    """L4 主口径入口：owl:AnnotationProperty 带 rdf:about 按 IRI 去重，全件计。"""
    iris = [el.get(RDF + "about") for el in _root(path).iter(OWLP + "AnnotationProperty")]
    return {"v": len({i for i in iris if i})}


def _children_map(edges):
    children = defaultdict(list)
    for s, o in edges:
        children[o].append(s)
    return children


def l5_max_depth(path, params=None):
    """L5 主口径入口：全图根起、沿 subClassOf 下行，到最远本地类的边数。"""
    root = _root(path)
    ns = local_namespace(path)
    iris = set(_named_class_iris(root))
    edges = _subclass_edges(root)
    subjects = {s for s, _ in edges}
    roots = sorted(iri for iri in iris if iri not in subjects)  # 全图根（含外部顶层类）
    children = _children_map(edges)
    best = 0

    def dfs(node, depth, used_edges):  # 递归遍历（A 侧允许）；环由「同边只走一次」断开
        nonlocal best
        if node.startswith(ns) and depth > best:
            best = depth
        for child in children.get(node, ()):
            edge = (child, node)
            if edge in used_edges:
                continue
            dfs(child, depth + 1, used_edges | {edge})

    for r in roots:
        dfs(r, 0, frozenset())
    return {"v": best, "roots": len(roots)}


def l6_leaf_classes(path, params=None):
    """L6 主口径入口：本地类中无本地子类者（只看本地→本地的边）。"""
    root = _root(path)
    ns = local_namespace(path)
    local = {i for i in _named_class_iris(root) if i.startswith(ns)}
    edges = _subclass_edges(root)
    has_local_child = {o for s, o in edges if s in local and o in local}
    return {"v": len(local - has_local_child)}


# ─────────────────────────────────────────────────────────────────────────────
# 另报与辅助量（不进 K；供 deviations/readings.json 等件取值）
# ─────────────────────────────────────────────────────────────────────────────

def alt_readings(path):
    """§二.3 的七条另报＋分档明细，一次算清（不落 claims、不标 primary）。"""
    root = _root(path)
    ns = local_namespace(path)
    parent = _parent_map(root)

    classes = list(root.iter(OWLP + "Class"))
    anonymous_class = sum(1 for c in classes if not c.get(RDF + "about"))
    restrictions = list(root.iter(OWLP + "Restriction"))

    op_iris = {e.get(RDF + "about") for e in root.iter(OWLP + "ObjectProperty") if e.get(RDF + "about")}
    ap_iris = {e.get(RDF + "about") for e in root.iter(OWLP + "AnnotationProperty") if e.get(RDF + "about")}

    edges = _subclass_edges(root)
    t1, t2, t3 = _tiers(edges, ns)
    local = {i for i in _named_class_iris(root) if i.startswith(ns)}

    # L5_alt：本地子图（只走两端皆本地的边；起点＝本地类中无本地父类者）
    local_children = defaultdict(list)
    local_has_parent = set()
    for s, o in t1:
        local_children[o].append(s)
        local_has_parent.add(s)
    local_roots = sorted(local - local_has_parent)
    best_alt = 0

    def dfs_local(node, depth, used_edges):
        nonlocal best_alt
        if depth > best_alt:
            best_alt = depth
        for child in local_children.get(node, ()):
            edge = (child, node)
            if edge in used_edges:
                continue
            dfs_local(child, depth + 1, used_edges | {edge})

    for r in local_roots:
        dfs_local(r, 0, frozenset())

    subjects = {s for s, _ in edges}
    l5_selfcheck = len(local - subjects)                      # 本地类中无任何父类者
    has_any_child = {o for _, o in edges}
    l6_alt = len(local - has_any_child)                       # 外部子类也算子类

    # 宾语为匿名节点的 subClassOf（不带 @rdf:resource；本件即匿名 owl:Restriction 宾语）
    anon_objects = []  # 主体 IRI（文档序）；匿名序号由调用方按文档序指派
    for el in root.iter(RDFSP + "subClassOf"):
        if el.get(RDF + "resource"):
            continue
        anon_objects.append(_enclosing_class_iri(el, parent))

    return {
        "anonymous_class": anonymous_class,
        "anonymous_restriction_count": len(restrictions),
        "L3_local": len({i for i in op_iris if i.startswith(ns)}),
        "L4_local": len({i for i in ap_iris if i.startswith(ns)}),
        "L5_alt": best_alt,
        "L5_selfcheck": l5_selfcheck,
        "L6_alt": l6_alt,
        "tier1": t1,
        "tier2": t2,
        "tier3": t3,
        "anon_object_subjects": anon_objects,
        "subclass_element_total": sum(1 for _ in root.iter(RDFSP + "subClassOf")),
        "ns": ns,
        "host": host_of(root),
        "ns_dir": "/" + ns.rstrip("/").rsplit("/", 1)[-1] + "/" if ns else "",
        "class_iris": sorted(set(_named_class_iris(root))),
        "local_iris": sorted(local),
        "version_iris": [el.get(RDF + "resource") for el in root.iter(OWLP + "versionIRI")],
        "ontology_iri": _ontology_iri(root),
        "owl_imports": [el.get(RDF + "resource") for el in root.iter(OWLP + "imports")],
    }


def contrast_namespace_values(path):
    """§7.4 三个禁法（留痕，不作判据；同值≠互证）：按件实算并附推导。"""
    root = _root(path)
    iris = set(_named_class_iris(root))
    ont = _ontology_iri(root)
    # ① rdf:about 去文件名：本体 IRI 去掉末段当命名空间
    ns_strip = ont.rsplit("/", 1)[0] + "/" if ont else ""
    by_strip = len({i for i in iris if i.startswith(ns_strip)})
    # ② 前缀 BCIO_ 法
    by_prefix = len({i for i in iris if i.rsplit("/", 1)[-1].startswith("BCIO_")})
    # ③ 出现最多的前缀（scheme://host/dir 出现次数最多者）
    dirs = Counter(
        f"{p.scheme}://{p.netloc}{p.path.rsplit('/', 1)[0]}/" for p in (urlsplit(i) for i in iris)
    )
    top_ns, top_n = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {
        "strip_filename": {"ns": ns_strip, "hits": by_strip},
        "prefix_BCIO_": {"hits": by_prefix},
        "most_common_prefix": {"ns": top_ns, "hits": top_n},
    }


# ─────────────────────────────────────────────────────────────────────────────
# 产物生成（A-1 口径：每件 evidence／deviations 产物的生成入口指得到本文件一行）
# ─────────────────────────────────────────────────────────────────────────────

def payload_sha(obj):
    """规范 sha：json.dumps(sort_keys, 紧凑分隔, ensure_ascii=False) 的 UTF-8 sha256。"""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def extract_anchors(text_path, facts):
    """13 锚（§三）：值取自语料与本体，定位串不带取值（2c）。"""
    lines = open(text_path, encoding="utf-8").read().splitlines()
    a01 = int(re.search(r"comprised a .*?(\d+) entities linked by arrows", lines[38]).group(1))
    a02 = int(re.search(r"The BCI scenario has (\d+) entities", lines[57]).group(1))
    a03 = int(re.search(r"The BCI comparison evaluation study has (\d+) entities", lines[57]).group(1))
    ver = facts["version_iris"][0]
    ont = facts["ontology_iri"]
    return [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L39"},
        {"id": "A02", "value": a02, "source": "paper_text.txt#L58", "locator": "#s3"},
        {"id": "A03", "value": a03, "source": "paper_text.txt#L58", "locator": "#s4"},
        {"id": "A04", "value": lines[17], "source": "paper_text.txt#L18"},
        {"id": "A05", "value": lines[39], "source": "paper_text.txt#L40"},
        {"id": "A06", "value": lines[58], "source": "paper_text.txt#L59"},
        {"id": "A07", "value": lines[15], "source": "paper_text.txt#L16"},
        {"id": "A08", "value": lines[35], "source": "paper_text.txt#L36"},
        {"id": "A09", "value": lines[70], "source": "paper_text.txt#L71"},
        {"id": "A10", "value": lines[18], "source": "paper_text.txt#L19"},
        {"id": "A11", "value": lines[33], "source": "paper_text.txt#L34", "locator": "取第 1/2 处"},
        {"id": "A12", "value": ver, "source": f"bcio_upper_level.owl#{ver}",
         "locator": f'rdf:resource="{ver}"'},
        {"id": "A13", "value": ont, "source": f"bcio_upper_level.owl#{ont}",
         "locator": f'rdf:about="{ont}"'},
    ]


PROTOCOL_TABLE = [
    # (pos, 标题行号, 段止行号)
    (1, 19, 20),
    (2, 21, 22),
    (3, 23, 26),
    (4, 27, 29),
    (5, 30, 31),
    (6, 32, 33),
    (7, 34, 35),
]

PROTOCOL_IO = {
    1: ("研究团队的领域知识与试点清单（Methods 首节所述起点）", "初始因果模型草稿（12 个实体及其箭头）"),
    2: ("既有本体清单与检索式", "scoping review 结论（无可复用的 BCI 本体）"),
    3: ("已发表报告的语料与标注方案", "数据驱动修订清单（含成瘾域报告的对照标注）"),
    4: ("本体初稿与专家名单", "三条专家反馈意见（命名／定义／结构）"),
    5: ("专家反馈意见", "研究团队采纳与驳回的处置决定"),
    6: ("本体当前版与 AddictO 本体", "跨本体复用测试结果"),
    7: ("前六段产出的本体与测试结果", "可持续维护计划"),
}


def protocol_doc(text_path):
    """§4.2 九键 steps；title 逐字取自语料行。"""
    lines = open(text_path, encoding="utf-8").read().splitlines()
    steps = []
    for pos, head, tail in PROTOCOL_TABLE:
        title = lines[head - 1]
        inp, outp = PROTOCOL_IO[pos]
        steps.append({
            "pos": pos,
            "label": f"S{pos}",
            "title": title,
            "src": "paper_text.txt",
            "kind": "line",
            "target": f"paper_text.txt#L{head}-L{tail}",
            "evidence_loc": f"paper_text.txt#L{head}-L{head}",
            "input": inp,
            "output": outp,
        })
    return {
        "rule": "kind=line：整行逐字匹配、区间内恰 1 次、行号严格递增（七段为 Methods 空壳 H2 的平级具名 H2）",
        "source": "paper_text.txt#L19-L34",
        "steps": steps,
    }


def _set_block(keys):
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": payload_sha(items)}


def _self_line(entry):
    src = open(os.path.abspath(__file__), encoding="utf-8").read().splitlines()
    for i, line in enumerate(src, 1):
        if re.match(rf"\s*def {re.escape(entry)}\s*\(", line):
            return i
    return 0


def emit_artifacts(owl_path, text_path, style_path, out_dir, only=None):
    """生成 evidence／deviations 各件（A-1 口径：每件产物的生成入口指得到本行）。

    only=None 写全部；否则只写相对路径等于 only 的那一件。返回写出的相对路径表。
    """
    facts = alt_readings(owl_path)
    contrast = contrast_namespace_values(owl_path)
    written = []

    def _put(rel, obj):
        if only is not None and rel != only:
            return
        dest = os.path.join(out_dir, *rel.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        written.append(rel)

    # deviations/readings.json：§二.3 七条另报（scalar）
    _put("deviations/readings.json", [
        {"name": n, "kind": "scalar",
         "sha256": payload_sha({"kind": "scalar", "name": n, "value": facts[n]}),
         "value": facts[n]}
        for n in ("anonymous_class", "anonymous_restriction_count", "L3_local",
                  "L4_local", "L5_alt", "L5_selfcheck", "L6_alt")
    ])

    # deviations/tiers.json：五键块
    _put("deviations/tiers.json", {
        "tier1": _set_block([f"{s}|{o}" for s, o in facts["tier1"]]),
        "tier2": _set_block([f"{s}|{o}" for s, o in facts["tier2"]]),
        "tier3": _set_block([f"{s}|{o}" for s, o in facts["tier3"]]),
        "anon_subclass_objects": _set_block(
            [f"{s}|@anonymous#{i + 1}" for i, s in enumerate(facts["anon_object_subjects"])]
        ),
        "readings_alt": {
            "items": [{"key": "partition_total", "value": facts["subclass_element_total"]}],
            "rows": 1,
            "sha256": payload_sha([{"key": "partition_total",
                                    "value": facts["subclass_element_total"]}]),
        },
    })

    # deviations/overlap.json：与 0008 对照件求类 IRI 交集（只算交集，不取任何 K 值）
    style_iris = set(_named_class_iris(_root(style_path)))
    this_iris = set(facts["class_iris"])
    _put("deviations/overlap.json", {
        "peers": {"0008": {
            "both": _set_block(sorted(this_iris & style_iris)),
            "only_in_this": _set_block(sorted(this_iris - style_iris)),
            "only_in_peer": _set_block(sorted(style_iris - this_iris)),
        }},
        "unavailable": [],
    })

    # deviations/contrast.json：三行对照值（留痕，不作判据）＋owl:imports 空判
    main_hits = len(facts["local_iris"])
    note_same = "；与主值同值＝巧合，不是判据（推导见 evidence/ns.json 的 host＋dir）"
    _put("deviations/contrast.json", [
        {"rule": f"禁法留痕① rdf:about 去文件名法：ns＝本体 IRI 去末段＝{contrast['strip_filename']['ns']}"
                 + (note_same if contrast["strip_filename"]["hits"] == main_hits else "；与主值不同值"),
         "hits": contrast["strip_filename"]["hits"],
         "derivation_ref": {"code": "code/quant_a.py", "entry": "contrast_namespace_values", "params": {}}},
        {"rule": "禁法留痕② 前缀 BCIO_ 法：IRI 末段以 BCIO_ 起头"
                 + (note_same if contrast["prefix_BCIO_"]["hits"] == main_hits else "；与主值不同值"),
         "hits": contrast["prefix_BCIO_"]["hits"],
         "derivation_ref": {"code": "code/quant_a.py", "entry": "contrast_namespace_values", "params": {}}},
        {"rule": f"禁法留痕③ 出现最多的前缀法：得最集中前缀 {contrast['most_common_prefix']['ns']}"
                 f"（外部宿主，{contrast['most_common_prefix']['hits']} 行）——与主值不同值，不作判据",
         "hits": contrast["most_common_prefix"]["hits"],
         "derivation_ref": {"code": "code/quant_a.py", "entry": "contrast_namespace_values", "params": {}}},
        {"rule": "owl:imports 为空这一判定：全件 owl:imports 元素个数",
         "hits": len(facts["owl_imports"]),
         "derivation_ref": {"code": "code/quant_a.py", "entry": "alt_readings", "params": {}}},
    ])

    # deviations/diff_A01–A03：三条自报锚对 L1 实测端（差额为 0 也交）
    anchors = extract_anchors(text_path, facts)
    a_val = {a["id"]: a["value"] for a in anchors}
    members = facts["local_iris"]
    measured = len(members)
    for aid in ("A01", "A02", "A03"):
        gap = measured - a_val[aid]
        payload = {"anchor": aid, "measured": measured, "self_reported": a_val[aid],
                   "items": [{"key": iri, "ord": i + 1} for i, iri in enumerate(members)]}
        doc = dict(payload)
        doc["rows"] = len(payload["items"])
        doc["gap"] = gap
        doc["direction"] = "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等")
        doc["sha256"] = payload_sha(payload)
        _put(f"deviations/diff_{aid}.json", doc)

    # evidence/ns.json：八字段（机器只读 classes[].in_ns，其余七字段供 F9 逐字段核）
    prefix_iris = sorted(i for i in facts["class_iris"] if i.rsplit("/", 1)[-1].startswith("BCIO_"))
    in_ns_set = set(facts["local_iris"])
    sym_diff = sorted(set(prefix_iris) ^ in_ns_set)
    _put("evidence/ns.json", {
        "rule": f"宿主＋最集中目录（code/quant_a.py::local_namespace，def 在第 {_self_line('local_namespace')} 行）",
        "host": facts["host"],
        "dir": facts["ns_dir"],
        "count": len(facts["local_iris"]),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": set(prefix_iris) == in_ns_set, "sym_diff": sym_diff},
        "classes": [{"iri": iri, "in_ns": iri in in_ns_set} for iri in facts["class_iris"]],
        "prefix_iris": prefix_iris,
    })

    # evidence/anchors.json：与 task.json#quoted 逐字同串
    _put("evidence/anchors.json", anchors)

    # evidence/protocol.json：七段九键
    _put("evidence/protocol.json", protocol_doc(text_path))

    # evidence/entries.json：六量入口声明（区间真包住 def，贴入口）
    src = open(os.path.abspath(__file__), encoding="utf-8").read().splitlines()
    entries = {}
    names = {"L1": "l1_local_classes", "L2": "l2_subclass_edges", "L3": "l3_object_properties",
             "L4": "l4_annotation_properties", "L5": "l5_max_depth", "L6": "l6_leaf_classes"}
    for key, entry in names.items():
        hits = [i + 1 for i, l in enumerate(src) if re.match(rf"\s*def {entry}\s*\(", l)]
        start = hits[0]
        end = len(src)
        for j in range(start, len(src)):
            nxt = src[j]
            if j + 1 > start and re.match(r"^(def |class |# ─)", nxt):
                end = j
                while end > start and not src[end - 1].strip():
                    end -= 1
                break
        entries[key] = {"file": "code/quant_a.py", "entry": entry, "lines": [start, end]}
    _put("evidence/entries.json", entries)

    return {"written": written, "facts": facts, "contrast": contrast, "anchors": anchors}
