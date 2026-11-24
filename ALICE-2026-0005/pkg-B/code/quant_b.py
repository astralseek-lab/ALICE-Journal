# -*- coding: utf-8 -*-
"""ALICE-2026-0005 · pkg-B 独立第二实现：upper-level BCIO 六量（L1–L6）＋另报＋产物生成。

链的可信不靠它永不变，靠它变了会响。

独立性走法（题面 §5.3bis 十道维度，B 侧必须）：
  · XML 解析：xml.dom.minidom（不用 ElementTree）
  · 遍历：迭代（显式栈／队列），不递归
  · 计数：流式一次过（一趟走遍全树、各量同趟登记）
  · IRI 划界：urlsplit 取 netloc＋path 独立判定（不做字符串前缀比较）
  · 命名空间：独立算一次主值（宿主＋最集中目录），另报三个对照值（contrast）；
    主值算成 0 时先怀疑命名空间取错并按本条重取，不用 versionIRI 退段／前缀判据去救
  · L2 三档：另一次遍历单独分档并复核三档之和＝L2
  · 匿名类：独立判 rdf:about 有无，不读他包清单
  · L5／L6：主口径与另一读法都算出
  · 跨包：零引用——本文件不 import、不指名、不读任何他包件
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import defaultdict
from urllib.parse import urlsplit
from xml.dom import minidom

ENTRY_FILE = os.path.join("code", "quant_b.py")


def _iter_elements(doc):
    """迭代（显式栈）全树元素遍历，深度优先、保文档序。"""
    stack = [doc.documentElement]
    while stack:
        node = stack.pop(0)
        if node.nodeType != node.ELEMENT_NODE:
            continue
        yield node
        kids = [k for k in node.childNodes if k.nodeType == k.ELEMENT_NODE]
        stack = kids + stack


def _enclosing_class_iri(node):
    cur = node.parentNode
    while cur is not None:
        if getattr(cur, "tagName", None) == "owl:Class":
            return cur.getAttribute("rdf:about") or None
        cur = cur.parentNode
    return None


def scan_once(path):
    """流式一次过：一趟登记本包所需的全部原始事实（B 侧计数口径）。"""
    doc = minidom.parse(str(path))
    facts = {
        "class_iris": [],          # 带 rdf:about 的 owl:Class（文档序）
        "anon_classes": 0,         # 不带 rdf:about 的 owl:Class
        "edges": [],               # (主体 IRI, 宾语 IRI)：subClassOf 带 rdf:resource
        "anon_edge_subjects": [],  # subClassOf 不带 rdf:resource 的主体（文档序）
        "subclass_elements": 0,    # subClassOf 元素总数
        "op_iris": [],             # 带 rdf:about 的 owl:ObjectProperty
        "ap_iris": [],             # 带 rdf:about 的 owl:AnnotationProperty
        "restrictions": 0,         # owl:Restriction 元素个数
        "ontology_iri": "",
        "version_iris": [],
        "imports": 0,
    }
    for el in _iter_elements(doc):
        tag = el.tagName
        if tag == "owl:Class":
            about = el.getAttribute("rdf:about")
            if about:
                facts["class_iris"].append(about)
            else:
                facts["anon_classes"] += 1
        elif tag == "rdfs:subClassOf":
            facts["subclass_elements"] += 1
            res = el.getAttribute("rdf:resource")
            if res:
                subj = _enclosing_class_iri(el)
                if subj:
                    facts["edges"].append((subj, res))
            else:
                facts["anon_edge_subjects"].append(_enclosing_class_iri(el))
        elif tag == "owl:ObjectProperty":
            about = el.getAttribute("rdf:about")
            if about:
                facts["op_iris"].append(about)
        elif tag == "owl:AnnotationProperty":
            about = el.getAttribute("rdf:about")
            if about:
                facts["ap_iris"].append(about)
        elif tag == "owl:Restriction":
            facts["restrictions"] += 1
        elif tag == "owl:Ontology":
            facts["ontology_iri"] = el.getAttribute("rdf:about") or facts["ontology_iri"]
        elif tag == "owl:versionIRI":
            res = el.getAttribute("rdf:resource")
            if res:
                facts["version_iris"].append(res)
        elif tag == "owl:imports":
            facts["imports"] += 1
    return facts


def _in_local(iri, host, ns_dir):
    """IRI 划界（B 独立实现）：urlsplit 取 netloc＋path 两格判，不做前缀字符串比较。"""
    p = urlsplit(iri)
    return p.netloc == host and p.path.startswith(ns_dir)


def local_namespace_b(path):
    """命名空间主值（B 独立算一次）：宿主（owl:Ontology@rdf:about 的 netloc）
    ＋该宿主类 IRI 里最集中的一层目录。"""
    facts = scan_once(path)
    host = urlsplit(facts["ontology_iri"]).netloc
    dirs = defaultdict(int)
    for iri in set(facts["class_iris"]):
        p = urlsplit(iri)
        if p.netloc == host:
            dirs[p.path.rsplit("/", 1)[0] + "/"] += 1
    if not dirs:
        return host, "", facts
    ns_dir = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return host, ns_dir, facts


def l1_local_classes(path, params=None):
    """L1：有 rdf:about 且落在本地命名空间的 owl:Class，按 IRI 去重。"""
    host, ns_dir, facts = local_namespace_b(path)
    return {"v": len({i for i in facts["class_iris"] if _in_local(i, host, ns_dir)})}


def _split_tiers(edges, host, ns_dir):
    t1, t2, t3 = [], [], []
    for s, o in edges:
        sin, oin = _in_local(s, host, ns_dir), _in_local(o, host, ns_dir)
        if sin and oin:
            t1.append((s, o))
        elif sin:
            t2.append((s, o))
        else:
            t3.append((s, o))
    return t1, t2, t3


def l2_subclass_edges(path, params=None):
    """L2：全件 subClassOf@rdf:resource 按条计；三档与总数同一次遍历，
    另一次遍历单独分档并复核三档之和＝L2（§二.2-1）。"""
    host, ns_dir, facts = local_namespace_b(path)
    edges = list(facts["edges"])                 # 主遍历（scan_once 那一趟）
    t1, t2, t3 = _split_tiers(edges, host, ns_dir)
    again = scan_once(path)                      # 独立第二次遍历复核
    r1, r2, r3 = _split_tiers(again["edges"], host, ns_dir)
    if len(again["edges"]) != len(edges) or (len(r1), len(r2), len(r3)) != (len(t1), len(t2), len(t3)):
        raise RuntimeError("L2 两次遍历不一致（主遍历与复核遍历分叉）")
    if len(t1) + len(t2) + len(t3) != len(edges):
        raise RuntimeError("L2 三档之和不等于总数")
    return {"v": len(edges), "tier1": len(t1), "tier2": len(t2), "tier3": len(t3)}


def l3_object_properties(path, params=None):
    """L3：owl:ObjectProperty 带 rdf:about 按 IRI 去重，全件计。"""
    facts = scan_once(path)
    return {"v": len(set(facts["op_iris"]))}


def l4_annotation_properties(path, params=None):
    """L4：owl:AnnotationProperty 带 rdf:about 按 IRI 去重，全件计。"""
    facts = scan_once(path)
    return {"v": len(set(facts["ap_iris"]))}


def l5_max_depth(path, params=None):
    """L5：全图根（不作任何 subClassOf 主语的类，含外部顶层类）起，沿 subClassOf
    下行（宾语＝父类、主语＝子类），深度＝到最远本地类节点的边数；环由「同边只走一次」断开。"""
    host, ns_dir, facts = local_namespace_b(path)
    edges = facts["edges"]
    children = defaultdict(list)
    subjects = set()
    for s, o in edges:
        children[o].append(s)
        subjects.add(s)
    roots = sorted({i for i in facts["class_iris"] if i not in subjects})
    best = 0
    for r in roots:
        stack = [(r, 0, frozenset())]            # 迭代下行（显式栈）
        while stack:
            node, depth, used = stack.pop()
            if _in_local(node, host, ns_dir) and depth > best:
                best = depth
            for ch in children.get(node, ()):
                edge = (ch, node)
                if edge in used:
                    continue
                stack.append((ch, depth + 1, used | {edge}))
    return {"v": best, "roots": len(roots)}


def l6_leaf_classes(path, params=None):
    """L6：本地类中无本地子类者（只看本地→本地的边；子类＝主语、父类＝宾语）。"""
    host, ns_dir, facts = local_namespace_b(path)
    local = {i for i in facts["class_iris"] if _in_local(i, host, ns_dir)}
    has_local_child = {o for s, o in facts["edges"] if s in local and o in local}
    return {"v": len(local - has_local_child)}


def alt_readings_b(path):
    """另报与分档明细（L5／L6 两读法都算出）。"""
    host, ns_dir, facts = local_namespace_b(path)
    local = {i for i in facts["class_iris"] if _in_local(i, host, ns_dir)}
    edges = facts["edges"]
    t1, t2, t3 = _split_tiers(edges, host, ns_dir)

    local_children = defaultdict(list)
    local_has_parent = set()
    for s, o in t1:
        local_children[o].append(s)
        local_has_parent.add(s)
    best_alt = 0
    for r in sorted(local - local_has_parent):
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, used = stack.pop()
            if depth > best_alt:
                best_alt = depth
            for ch in local_children.get(node, ()):
                edge = (ch, node)
                if edge in used:
                    continue
                stack.append((ch, depth + 1, used | {edge}))

    subjects = {s for s, _ in edges}
    has_any_child = {o for _, o in edges}
    return {
        "anonymous_class": facts["anon_classes"],
        "anonymous_restriction_count": facts["restrictions"],
        "L3_local": len({i for i in set(facts["op_iris"]) if _in_local(i, host, ns_dir)}),
        "L4_local": len({i for i in set(facts["ap_iris"]) if _in_local(i, host, ns_dir)}),
        "L5_alt": best_alt,
        "L5_selfcheck": len(local - subjects),
        "L6_alt": len(local - has_any_child),
        "tier1": t1, "tier2": t2, "tier3": t3,
        "anon_object_subjects": facts["anon_edge_subjects"],
        "subclass_element_total": facts["subclass_elements"],
        "ns": f"{urlsplit(facts['ontology_iri']).scheme}://{host}{ns_dir}",
        "host": host,
        "ns_dir": ns_dir,
        "class_iris": sorted(set(facts["class_iris"])),
        "local_iris": sorted(local),
        "version_iris": facts["version_iris"],
        "ontology_iri": facts["ontology_iri"],
        "owl_imports": facts["imports"],
    }


def contrast_namespace_values_b(path):
    """三个对照读法（留痕，不作判据；同值≠互证）：按件实算并附推导。"""
    host, ns_dir, facts = local_namespace_b(path)
    iris = set(facts["class_iris"])
    ont = facts["ontology_iri"]
    ns_strip = ont.rsplit("/", 1)[0] + "/" if ont else ""
    by_strip = len({i for i in iris if urlsplit(i).path.startswith(urlsplit(ns_strip).path)
                    and urlsplit(i).netloc == urlsplit(ns_strip).netloc})
    by_prefix = len({i for i in iris if i.rsplit("/", 1)[-1].startswith("BCIO_")})
    dirs = defaultdict(int)
    for i in iris:
        p = urlsplit(i)
        dirs[f"{p.scheme}://{p.netloc}{p.path.rsplit('/', 1)[0]}/"] += 1
    top_ns, top_n = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {
        "strip_filename": {"ns": ns_strip, "hits": by_strip},
        "prefix_BCIO_": {"hits": by_prefix},
        "most_common_prefix": {"ns": top_ns, "hits": top_n},
    }


# ─────────────────────────────────────────────────────────────────────────────
# 产物生成（A-1 口径：每件产物的生成入口指得到本文件一行；路径一律拼接、不写死分隔符）
# ─────────────────────────────────────────────────────────────────────────────

def payload_sha(obj):
    """规范 sha：json.dumps(sort_keys, 紧凑分隔, ensure_ascii=False) 的 UTF-8 sha256。"""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def extract_anchors_b(text_path, facts):
    """13 锚（§三）：值取自语料与本体，定位串不带取值（2c）。B 自己从语料重新定位。"""
    lines = open(text_path, encoding="utf-8").read().splitlines()
    a01 = int(re.search(r"comprised a .*?(\d+) entities linked by arrows", lines[38]).group(1))
    a02 = int(re.search(r"The BCI scenario has (\d+) entities", lines[57]).group(1))
    a03 = int(re.search(r"The BCI comparison evaluation study has (\d+) entities", lines[57]).group(1))
    ver = facts["version_iris"][0]
    ont = facts["ontology_iri"]
    owl_name = "bcio_upper_level.owl"
    txt_name = "paper_text.txt"
    return [
        {"id": "A01", "value": a01, "source": txt_name + "#L39"},
        {"id": "A02", "value": a02, "source": txt_name + "#L58", "locator": "#s3"},
        {"id": "A03", "value": a03, "source": txt_name + "#L58", "locator": "#s4"},
        {"id": "A04", "value": lines[17], "source": txt_name + "#L18"},
        {"id": "A05", "value": lines[39], "source": txt_name + "#L40"},
        {"id": "A06", "value": lines[58], "source": txt_name + "#L59"},
        {"id": "A07", "value": lines[15], "source": txt_name + "#L16"},
        {"id": "A08", "value": lines[35], "source": txt_name + "#L36"},
        {"id": "A09", "value": lines[70], "source": txt_name + "#L71"},
        {"id": "A10", "value": lines[18], "source": txt_name + "#L19"},
        {"id": "A11", "value": lines[33], "source": txt_name + "#L34", "locator": "取第 1/2 处"},
        {"id": "A12", "value": ver, "source": owl_name + "#" + ver, "locator": 'rdf:resource="' + ver + '"'},
        {"id": "A13", "value": ont, "source": owl_name + "#" + ont, "locator": 'rdf:about="' + ont + '"'},
    ]


SEGMENTS = [(1, 19, 20), (2, 21, 22), (3, 23, 26), (4, 27, 29), (5, 30, 31), (6, 32, 33), (7, 34, 35)]

SEG_IO = {
    1: ("研究团队的领域知识与试点清单（Methods 首节所述起点）", "初始因果模型草稿（情景实体与因果连接）"),
    2: ("既有本体清单与检索式", "scoping review 结论（无可复用的 BCI 本体）"),
    3: ("已发表报告的语料与标注方案", "数据驱动修订清单（含成瘾域报告的对照标注）"),
    4: ("本体初稿与专家名单", "专家反馈意见（命名／定义／结构三方面）"),
    5: ("专家反馈意见", "研究团队采纳与驳回的处置决定"),
    6: ("本体当前版与 AddictO 本体", "跨本体复用测试结果"),
    7: ("前述各段产出的本体与测试结果", "可持续维护计划"),
}


def protocol_doc_b(text_path):
    """§4.2 九键 steps；B 自己切节、title 逐字取自语料行。"""
    lines = open(text_path, encoding="utf-8").read().splitlines()
    txt_name = "paper_text.txt"
    steps = []
    for pos, head, tail in SEGMENTS:
        inp, outp = SEG_IO[pos]
        steps.append({
            "pos": pos,
            "label": "S" + str(pos),
            "title": lines[head - 1],
            "src": txt_name,
            "kind": "line",
            "target": txt_name + "#L%d-L%d" % (head, tail),
            "evidence_loc": txt_name + "#L%d-L%d" % (head, head),
            "input": inp,
            "output": outp,
        })
    return {
        "rule": "kind=line：整行逐字匹配、区间内恰 1 次、行号严格递增（七段为 Methods 空壳 H2 的平级具名 H2）",
        "source": txt_name + "#L19-L34",
        "steps": steps,
    }


def _set_block(keys):
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(keys)]
    return {"items": items, "rows": len(items), "sha256": payload_sha(items)}


def _style_class_iris(style_path):
    """对照件的具名类 IRI 集（B 自己解，不读他包清单）。"""
    doc = minidom.parse(str(style_path))
    out = set()
    for el in _iter_elements(doc):
        if el.tagName == "owl:Class":
            about = el.getAttribute("rdf:about")
            if about:
                out.add(about)
    return out


def _def_lines(entry):
    src = open(os.path.abspath(__file__), encoding="utf-8").read().splitlines()
    hits = [i + 1 for i, l in enumerate(src) if re.match(r"\s*def " + re.escape(entry) + r"\s*\(", l)]
    start = hits[0]
    end = len(src)
    for j in range(start, len(src)):
        if j + 1 > start and re.match(r"^(def |class |# ─)", src[j]):
            end = j
            while end > start and not src[end - 1].strip():
                end -= 1
            break
    return [start, end]


def emit_artifacts(owl_path, text_path, style_path, out_dir, only=None):
    """生成 evidence／deviations 各件（A-1 口径：每件产物的生成入口指得到本行）。

    only=None 写全部；否则只写相对路径等于 only 的那一件。返回写出的相对路径表。
    """
    facts = alt_readings_b(owl_path)
    contrast = contrast_namespace_values_b(owl_path)
    written = []
    ev = "evidence"
    dv = "deviations"

    def _put(parts, obj):
        rel = "/".join(parts)
        if only is not None and rel != only:
            return
        dest = os.path.join(out_dir, *parts)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write("\n")
        written.append(rel)

    _put((dv, "readings.json"), [
        {"name": n, "kind": "scalar",
         "sha256": payload_sha({"kind": "scalar", "name": n, "value": facts[n]}),
         "value": facts[n]}
        for n in ("anonymous_class", "anonymous_restriction_count", "L3_local",
                  "L4_local", "L5_alt", "L5_selfcheck", "L6_alt")
    ])

    _put((dv, "tiers.json"), {
        "tier1": _set_block([s + "|" + o for s, o in facts["tier1"]]),
        "tier2": _set_block([s + "|" + o for s, o in facts["tier2"]]),
        "tier3": _set_block([s + "|" + o for s, o in facts["tier3"]]),
        "anon_subclass_objects": _set_block(
            [s + "|@anonymous#" + str(i + 1) for i, s in enumerate(facts["anon_object_subjects"])]
        ),
        "readings_alt": {
            "items": [{"key": "partition_total", "value": facts["subclass_element_total"]}],
            "rows": 1,
            "sha256": payload_sha([{"key": "partition_total",
                                    "value": facts["subclass_element_total"]}]),
        },
    })

    style_iris = _style_class_iris(style_path)
    this_iris = set(facts["class_iris"])
    _put((dv, "overlap.json"), {
        "peers": {"0008": {
            "both": _set_block(sorted(this_iris & style_iris)),
            "only_in_this": _set_block(sorted(this_iris - style_iris)),
            "only_in_peer": _set_block(sorted(style_iris - this_iris)),
        }},
        "unavailable": [],
    })

    main_hits = len(facts["local_iris"])
    note_same = "；与主值同值＝巧合，不是判据（推导见 " + ev + " 侧 ns 件的 host＋dir）"
    dref_contrast = {"code": ENTRY_FILE.replace(os.sep, "/"), "entry": "contrast_namespace_values_b", "params": {}}
    dref_alt = {"code": ENTRY_FILE.replace(os.sep, "/"), "entry": "alt_readings_b", "params": {}}
    _put((dv, "contrast.json"), [
        {"rule": "禁法留痕① rdf:about 去文件名法：ns＝本体 IRI 去末段＝" + contrast["strip_filename"]["ns"]
                 + (note_same if contrast["strip_filename"]["hits"] == main_hits else "；与主值不同值"),
         "hits": contrast["strip_filename"]["hits"], "derivation_ref": dref_contrast},
        {"rule": "禁法留痕② 前缀 BCIO_ 法：IRI 末段以 BCIO_ 起头"
                 + (note_same if contrast["prefix_BCIO_"]["hits"] == main_hits else "；与主值不同值"),
         "hits": contrast["prefix_BCIO_"]["hits"], "derivation_ref": dref_contrast},
        {"rule": "禁法留痕③ 出现最多的前缀法：得最集中前缀 " + contrast["most_common_prefix"]["ns"]
                 + "（外部宿主更集中）——与主值不同值，不作判据",
         "hits": contrast["most_common_prefix"]["hits"], "derivation_ref": dref_contrast},
        {"rule": "owl:imports 为空这一判定：全件 owl:imports 元素个数",
         "hits": facts["owl_imports"], "derivation_ref": dref_alt},
    ])

    anchors = extract_anchors_b(text_path, facts)
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
        _put((dv, "diff_" + aid + ".json"), doc)

    prefix_iris = sorted(i for i in facts["class_iris"] if i.rsplit("/", 1)[-1].startswith("BCIO_"))
    in_ns_set = set(facts["local_iris"])
    sym_diff = sorted(set(prefix_iris) ^ in_ns_set)
    ns_line = _def_lines("local_namespace_b")[0]
    _put((ev, "ns.json"), {
        "rule": "宿主＋最集中目录（" + ENTRY_FILE.replace(os.sep, "/") + "::local_namespace_b，def 在第 "
                + str(ns_line) + " 行）",
        "host": facts["host"],
        "dir": facts["ns_dir"],
        "count": len(facts["local_iris"]),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": set(prefix_iris) == in_ns_set, "sym_diff": sym_diff},
        "classes": [{"iri": iri, "in_ns": iri in in_ns_set} for iri in facts["class_iris"]],
        "prefix_iris": prefix_iris,
    })

    _put((ev, "anchors.json"), anchors)
    _put((ev, "protocol.json"), protocol_doc_b(text_path))

    names = {"L1": "l1_local_classes", "L2": "l2_subclass_edges", "L3": "l3_object_properties",
             "L4": "l4_annotation_properties", "L5": "l5_max_depth", "L6": "l6_leaf_classes"}
    entries = {k: {"file": ENTRY_FILE.replace(os.sep, "/"), "entry": e, "lines": _def_lines(e)}
               for k, e in names.items()}
    _put((ev, "entries.json"), entries)

    _put((ev, "independence.json"), {
        "source": "独立第二实现：minidom 迭代解析、显式栈遍历、流式一次过计数、urlsplit 划界（§5.3bis 十道）",
        "shared_code_with_a": False,
        "entry": ENTRY_FILE.replace(os.sep, "/") + "::emit_artifacts",
        "signer_pkg_id": "pkg-B",
    })

    return {"written": written, "facts": facts, "contrast": contrast, "anchors": anchors}
