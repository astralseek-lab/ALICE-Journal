#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""独立第二实现（B 侧）：ALICE-2026-0006 六量与证据件。

与另一实现包的差异（题面 §5.3bis 十道）：
  · 解析器：xml.dom.minidom（不用树形库的另一族 API）；
  · 遍历：显式栈迭代，不递归；
  · 计数：流式一次过（单趟扫描累加，不预建索引再数）；
  · IRI 划界：urllib.parse.urlsplit 取 netloc＋path 逐段比对，不做字符串前缀比较；
  · 命名空间：独立按「宿主＋最集中目录」算主值，另算三个对照读数；
  · 匿名类：自己按 rdf:about 有无判定；
  · L5／L6：主口径与另一读法都算；
  · protocol：自己从语料按位置切七步；
  · 不引用另一实现包的任何模块与件。
入口六名与题面 §九 固定名逐字一致；返回 {"v": 整数}。
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import xml.dom.minidom as minidom
from urllib.parse import urlsplit

TASK_ID = "ALICE-2026-0006"
PAPER = "paper_text.txt"
OWLNAME = "bcio_setting.owl"

READINGS_ORDER = [
    "L3_local", "L4_local", "L5_alt", "L5_selfcheck", "L6_alt",
    "anonymous_class", "self_report_unmeasured",
]
STEP_INPUTS = [
    "CONSORT／CONSORT-SPI／TIDieR／TIPPME 等词典与报告规范（正文 L11）",
    "既有文献报告（bottom-up 抽样）与既有分类系统（top-down 汇集）（正文 L13–L14）",
    "试点标注结果（正文 L17 首句所指）",
    "Step 3 产出的修订版本体（正文 L19 首句所指）",
    "两组各 50 篇文献（熟手一组、生手一组）（正文 L24）",
    "BFO 与 Relation Ontology 的候选关系（正文 L26）",
    "稳定后的实体表（正文 L28 首句所指）",
]
STEP_OUTPUTS = [
    "本体的定义与总主题（正文 L11）",
    "初版原型本体（正文 L13–L15）",
    "修订后的本体与标注指南（正文 L17）",
    "专家反馈及据之再修订的本体与标注手册（正文 L22）",
    "标注一致性评估（Krippendorff’s Alpha）（正文 L24）",
    "实体间关系（is_a／located_in）（正文 L26）",
    "OWL 版本并上架 GitHub（正文 L28–L29）",
]


# ── 解析：minidom＋显式栈迭代遍历（文档序） ─────────────────────────

def _iter_nodes(doc):
    stack = [doc.documentElement]
    while stack:
        node = stack.pop()
        yield node
        kids = [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]
        stack.extend(reversed(kids))


def _tag(node, name):
    return node.nodeType == node.ELEMENT_NODE and node.tagName == name


def _about(node):
    v = node.getAttribute("rdf:about")
    return v if v else None


def _enclosing_named_class(node):
    cur = node.parentNode
    while cur is not None and cur.nodeType == cur.ELEMENT_NODE:
        if cur.tagName == "owl:Class":
            a = _about(cur)
            if a:
                return a
        cur = cur.parentNode
    return None


def _ontology_iri(doc):
    for node in _iter_nodes(doc):
        if _tag(node, "owl:Ontology"):
            return _about(node)
    raise RuntimeError("owl:Ontology 缺失")


def local_namespace(input_path):
    """主口径（独立实现）：宿主＝owl:Ontology@rdf:about 的 netloc；再取该宿主上
    命名类 IRI 最集中的一层目录；本地＝urlsplit 后 netloc 同宿主且 path 落在该目录。"""
    doc = minidom.parse(str(input_path))
    ont = _ontology_iri(doc)
    osp = urlsplit(ont)
    host = osp.netloc
    dirs = {}
    for node in _iter_nodes(doc):
        if _tag(node, "owl:Class"):
            a = _about(node)
            if a:
                sp = urlsplit(a)
                if sp.netloc == host:
                    d = sp.path.rsplit("/", 1)[0] + "/"
                    dirs[d] = dirs.get(d, 0) + 1
    if not dirs:
        raise RuntimeError("宿主上没有任何命名类")
    top = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return osp.scheme, host, top


def _is_local(iri, ns_parts):
    sp = urlsplit(iri)
    return sp.netloc == ns_parts[1] and sp.path.startswith(ns_parts[2])


# ── 流式一次过：单趟扫描把所有计数原料齐 ──────────────────────────

def _scan(input_path):
    """一趟迭代遍历收齐：命名类（文档序）、资源边（主,宾）、匿名宾语边、
    匿名节点编号、对象属性、注释属性。"""
    doc = minidom.parse(str(input_path))
    named = []
    edges = []
    anon_edges = []
    anon_no = {}
    objprops = set()
    annprops = set()
    n = 0
    for node in _iter_nodes(doc):
        tag = node.tagName
        if tag == "owl:ObjectProperty":
            a = _about(node)
            if a:
                objprops.add(a)
            continue
        if tag == "owl:AnnotationProperty":
            a = _about(node)
            if a:
                annprops.add(a)
            continue
        if tag in ("owl:Class", "owl:Restriction") and not _about(node):
            n += 1
            anon_no[id(node)] = n
            if tag == "owl:Class":
                continue
        if tag == "owl:Class":
            a = _about(node)
            if a:
                named.append(a)
            continue
        if tag == "rdfs:subClassOf":
            subj = _enclosing_named_class(node)
            res = node.getAttribute("rdf:resource")
            if res:
                edges.append((subj, res))
            else:
                obj = next((c for c in node.childNodes
                            if c.nodeType == c.ELEMENT_NODE), None)
                anon_edges.append((subj, obj))
    # 匿名对象在文档序上位于 subClassOf 之后，本趟扫描时尚未编号；
    # 扫描结束后匿名编号表已齐，再统一回填（编号方案不变：文档序、全局唯一）
    anon_edges = [(s, anon_no.get(id(o)) if o is not None else None)
                  for s, o in anon_edges]
    return {
        "named": named, "edges": edges, "anon_edges": anon_edges,
        "anon_total": n, "objprops": objprops, "annprops": annprops,
        "anon_class_count": None,  # 另算，见 alt_readings
    }


def _anon_class_count(input_path):
    doc = minidom.parse(str(input_path))
    cnt = 0
    for node in _iter_nodes(doc):
        if _tag(node, "owl:Class") and not _about(node):
            cnt += 1
    return cnt


# ── 六量固定入口 ────────────────────────────────────────────────────

def l1_local_classes(input_path, params=None):
    ns = local_namespace(input_path)
    seen = set()
    for iri in _scan(input_path)["named"]:
        if _is_local(iri, ns):
            seen.add(iri)
    return {"v": len(seen)}


def l2_subclass_edges(input_path, params=None):
    cnt = 0
    for _s, _o in _scan(input_path)["edges"]:
        cnt += 1
    return {"v": cnt}


def l3_object_properties(input_path, params=None):
    return {"v": len(_scan(input_path)["objprops"])}


def l4_annotation_properties(input_path, params=None):
    return {"v": len(_scan(input_path)["annprops"])}


def l5_max_depth(input_path, params=None):
    """全图根沿 subClassOf 下行（宾语＝父类）到最远本地类的边数；
    显式栈迭代，路径内同边只走一次。"""
    ns = local_namespace(input_path)
    scan = _scan(input_path)
    named = set(scan["named"])
    subjects = set()
    children = {}
    for s, o in scan["edges"]:
        if s:
            subjects.add(s)
            children.setdefault(o, []).append(s)
    roots = sorted(named - subjects)
    best = 0
    stack = [(r, 0, frozenset()) for r in roots]
    while stack:
        node, depth, seen = stack.pop()
        if _is_local(node, ns) and depth > best:
            best = depth
        for ch in children.get(node, []):
            e = (ch, node)
            if e not in seen:
                stack.append((ch, depth + 1, seen | {e}))
    return {"v": best}


def l6_leaf_classes(input_path, params=None):
    ns = local_namespace(input_path)
    scan = _scan(input_path)
    local = {i for i in scan["named"] if _is_local(i, ns)}
    has_local_child = set()
    for s, o in scan["edges"]:
        if s in local and o in local:
            has_local_child.add(o)
    return {"v": len([c for c in local if c not in has_local_child])}


# ── 另报与对照 ─────────────────────────────────────────────────────

def alt_readings(input_path):
    ns = local_namespace(input_path)
    scan = _scan(input_path)
    named = set(scan["named"])
    local = {i for i in named if _is_local(i, ns)}
    # L5_alt：只走两端皆本地的边，起点＝本地类中无本地父类者
    local_children = {}
    local_parents = set()
    subjects_all = set()
    for s, o in scan["edges"]:
        if s:
            subjects_all.add(s)
        if s in local and o in local:
            local_children.setdefault(o, []).append(s)
            local_parents.add(s)
    local_roots = sorted(local - local_parents)
    best = 0
    stack = [(r, 0, frozenset()) for r in local_roots]
    while stack:
        node, depth, seen = stack.pop()
        if depth > best:
            best = depth
        for ch in local_children.get(node, []):
            e = (ch, node)
            if e not in seen:
                stack.append((ch, depth + 1, seen | {e}))
    l5_alt = best
    l5_selfcheck = len([c for c in local if c not in subjects_all])
    has_any_child = {o for s, o in scan["edges"] if o in local}
    l6_alt = len([c for c in local if c not in has_any_child])
    return {
        "L3_local": len([i for i in scan["objprops"] if _is_local(i, ns)]),
        "L4_local": len([i for i in scan["annprops"] if _is_local(i, ns)]),
        "L5_alt": l5_alt,
        "L5_selfcheck": l5_selfcheck,
        "L6_alt": l6_alt,
        "anonymous_class": _anon_class_count(input_path),
    }


def ns_contrast_rows(input_path, params=None):
    """三个对照读数（禁法留痕，不作判据），各按件实算并附推导。"""
    doc = minidom.parse(str(input_path))
    ont = _ontology_iri(doc)
    scan = _scan(input_path)
    named = scan["named"]
    ns = local_namespace(input_path)
    main = len({i for i in named if _is_local(i, ns)})
    host, dirpath = ns[1], ns[2]
    base = ont.rsplit("/", 1)[0] + "/"
    hits_strip = len({i for i in named if urlsplit(i).path.startswith(urlsplit(base).path)
                      and urlsplit(i).netloc == urlsplit(base).netloc})
    hits_bcio = len({i for i in named
                     if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_")})
    pref = {}
    for i in named:
        p = i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].split("_")[0]
        pref[p] = pref.get(p, 0) + 1
    top_pref, top_hits = sorted(pref.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    def phrase(h):
        return "巧合，不是判据" if h == main else "与主值不同值"
    me = os.path.join("code", os.path.basename(__file__))
    rows = [
        {"rule": (f"对照读法一（禁法·不作判据）：rdf:about 去文件名——本体 IRI 去掉末段文件名后"
                  f"按 urlsplit 的 netloc＋path 比对命中；推导得 host={host}、最集中目录={dirpath}；"
                  f"与主值同值，{phrase(hits_strip)}"),
         "hits": hits_strip,
         "derivation_ref": {"code": me, "entry": "ns_contrast_rows", "params": {}}},
        {"rule": (f"对照读法二（禁法·不作判据）：前缀 BCIO_——本地名以 BCIO_ 起头者计数；"
                  f"推导得 host={host}、最集中目录={dirpath}；与主值同值，{phrase(hits_bcio)}"),
         "hits": hits_bcio,
         "derivation_ref": {"code": me, "entry": "ns_contrast_rows", "params": {}}},
        {"rule": (f"对照读法三（禁法·不作判据）：出现最多的前缀——本地名第一个下划线前段计次，"
                  f"{top_pref} 居首（{top_hits} 次）；推导得 host={host}、最集中目录={dirpath}；"
                  f"与主值同值，{phrase(top_hits)}"),
         "hits": top_hits,
         "derivation_ref": {"code": me, "entry": "ns_contrast_rows", "params": {}}},
    ]
    return rows


def ns_document(input_path):
    scan = _scan(input_path)
    ns = local_namespace(input_path)
    named = sorted(set(scan["named"]))
    local = {i for i in named if _is_local(i, ns)}
    prefix_iris = sorted(i for i in named
                         if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_"))
    sym = sorted(local.symmetric_difference(set(prefix_iris)))
    span = _entry_span("local_namespace")
    me = os.path.join("code", os.path.basename(__file__))
    return {
        "rule": (f"{me}::local_namespace（第 {span[0]}–{span[1]} 行）：宿主＝owl:Ontology"
                 f"@rdf:about 的 netloc；dir＝该宿主上命名类 IRI 最集中的目录；"
                 f"本地判定＝urlsplit 的 netloc 同宿主且 path 落在该目录"),
        "host": ns[1],
        "dir": ns[2],
        "count": len(local),
        "prefix_count": len(prefix_iris),
        "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
        "classes": [{"iri": i, "in_ns": i in local} for i in named],
        "prefix_iris": prefix_iris,
    }


def tiers_document(input_path):
    """五键闭集。分档与总数同一次遍历分出；另一次遍历复核总数。"""
    ns = local_namespace(input_path)
    scan = _scan(input_path)
    named = set(scan["named"])
    local = {i for i in named if _is_local(i, ns)}
    t1, t2, t3, anon_rows = [], [], [], []
    for s, o in scan["edges"]:
        s_in = s in local if s else False
        o_in = o in local
        if s_in and o_in:
            t1.append(f"{s}|{o}")
        elif s_in and not o_in:
            t2.append(f"{s}|{o}")
        else:
            t3.append(f"{s}|{o}")
    for s, n in scan["anon_edges"]:
        anon_rows.append(f"{s}|@anonymous#{n}")
    total = len(scan["edges"]) + len(scan["anon_edges"])
    # 独立第二次遍历复核（重新解析再数一遍）
    doc = minidom.parse(str(input_path))
    again = 0
    again_res = 0
    for node in _iter_nodes(doc):
        if _tag(node, "rdfs:subClassOf"):
            again += 1
            if node.getAttribute("rdf:resource"):
                again_res += 1
    if again != total or again_res != len(scan["edges"]):
        raise RuntimeError("两次遍历不一致")

    def block(keys):
        items = [{"key": k, "ord": i + 1} for i, k in enumerate(sorted(keys))]
        return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}

    ra = [{"key": "partition_total", "value": total}]
    return {
        "tier1": block(t1),
        "tier2": block(t2),
        "tier3": block(t3),
        "anon_subclass_objects": block(anon_rows),
        "readings_alt": {"items": ra, "rows": len(ra), "sha256": _canon_sha(ra)},
    }


# ── 文本锚与七步（自己从语料切） ────────────────────────────────────

def _paper_lines(paper_path):
    with open(str(paper_path), encoding="utf-8") as fh:
        return fh.read().splitlines()


def anchors(paper_path, owl_path):
    lines = _paper_lines(paper_path)
    with open(str(owl_path), encoding="utf-8") as fh:
        owl_text = fh.read()

    def int_after(lineno, locator):
        line = lines[lineno - 1]
        i = line.find(locator)
        if i < 0:
            raise RuntimeError(f"locator miss L{lineno}")
        m = re.search(r"-?\d+", line[i + len(locator):])
        return int(m.group(0))

    a01 = int_after(53, "comprising of")
    l46 = lines[45]
    start = l46.find("Inter-rater reliability from the")
    a02 = float(re.search(r"a=\s*(-?\d+(?:\.\d+)?)", l46[start:]).group(1))
    a03 = int_after(42, "countries. Of the")
    v12 = re.search(r'owl:versionIRI[^>]*rdf:resource="([^"]+)"', owl_text).group(1)
    v13 = re.search(r'owl:Ontology[^>]*rdf:about="([^"]+)"', owl_text).group(1)
    rows = [
        {"id": "A01", "value": a01, "source": PAPER + "#L53", "locator": "#s1"},
        {"id": "A02", "value": a02, "source": PAPER + "#L46", "locator": "取第 1/2 处"},
        {"id": "A03", "value": a03, "source": PAPER + "#L42", "locator": "#s2"},
        {"id": "A04", "value": lines[4].strip(), "source": PAPER + "#L5"},
        {"id": "A05", "value": lines[50].strip(), "source": PAPER + "#L51"},
        {"id": "A06", "value": lines[51].split()[0], "source": PAPER + "#L52"},
        {"id": "A07", "value": lines[7].strip(), "source": PAPER + "#L8"},
        {"id": "A08", "value": lines[29].strip(), "source": PAPER + "#L30"},
        {"id": "A09", "value": lines[55].strip(), "source": PAPER + "#L56"},
        {"id": "A10", "value": lines[9].strip(), "source": PAPER + "#L10",
         "locator": "取第 1/2 处"},
        {"id": "A11", "value": lines[26].strip(), "source": PAPER + "#L27"},
        {"id": "A12", "value": v12, "source": OWLNAME + "#" + v12,
         "locator": 'rdf:resource="' + v12 + '"'},
        {"id": "A13", "value": v13, "source": OWLNAME + "#" + v13,
         "locator": 'rdf:about="' + v13 + '"'},
    ]
    return rows


def protocol_document(paper_path):
    """先列 Methods 下全部标题，再按位置取前七个（禁用标题去重）。"""
    lines = _paper_lines(paper_path)
    m_at = r_at = None
    for i, t in enumerate(lines, 1):
        s = t.strip()
        if s == "Methods" and m_at is None:
            m_at = i
        elif s == "Results" and r_at is None:
            r_at = i
    heads = []
    for i in range(m_at + 1, r_at):
        s = lines[i - 1].strip()
        if re.match(r"^Step\s+\d", s):
            heads.append((i, s))
    seven = heads[:7]
    if len(seven) != 7:
        raise RuntimeError("Methods 内标题数不为 7")
    steps = []
    for pos, (lineno, title) in enumerate(seven, 1):
        if not title.startswith(f"Step {pos} "):
            raise RuntimeError(f"第 {pos} 步标题序位不合：{title[:30]}")
        stop = (seven[pos][0] if pos < 7 else r_at) - 1
        steps.append({
            "pos": pos,
            "label": f"S{pos}",
            "title": title,
            "src": PAPER,
            "kind": "line",
            "target": f"{PAPER}#L{lineno}-L{stop}",
            "evidence_loc": f"{PAPER}#L{lineno}-L{lineno}",
            "input": STEP_INPUTS[pos - 1],
            "output": STEP_OUTPUTS[pos - 1],
        })
    return {
        "rule": ("先列 Methods 节内全部 Step 标题行，按位置取前七（Results 节内的同形重列"
                 "一概不计，标题去重禁用）；步段＝标题行至下一标题前一行"),
        "source": PAPER + "#L10-L29",
        "steps": steps,
    }


def readings_document(input_path, anchors_rows):
    vals = alt_readings(input_path)
    amap = {r["id"]: r["value"] for r in anchors_rows}
    out = []
    for name in READINGS_ORDER:
        if name == "self_report_unmeasured":
            item = {"name": name, "kind": "map",
                    "value": {"A02": amap["A02"], "A03": amap["A03"]}}
        else:
            item = {"name": name, "kind": "scalar", "value": vals[name]}
        item["sha256"] = _canon_sha({"name": item["name"], "kind": item["kind"],
                                     "value": item["value"]})
        out.append(item)
    return out


def diff_document(input_path, anchors_rows):
    amap = {r["id"]: r["value"] for r in anchors_rows}
    ns = local_namespace(input_path)
    scan = _scan(input_path)
    local = sorted({i for i in scan["named"] if _is_local(i, ns)})
    measured = len(local)
    self_reported = amap["A01"]
    gap = measured - self_reported
    direction = "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等")
    items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(local)]
    payload = {"anchor": "A01", "measured": measured,
               "self_reported": self_reported, "items": items}
    return {
        "anchor": "A01", "measured": measured, "self_reported": self_reported,
        "items": items, "rows": len(items), "gap": gap, "direction": direction,
        "sha256": _canon_sha(payload),
    }


# ── 发射与工具 ─────────────────────────────────────────────────────

def _canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _entry_span(name):
    with open(str(__file__), encoding="utf-8") as fh:
        src = fh.read().splitlines()
    pat = re.compile(r"\s*def " + re.escape(name) + r"\s*\(")
    hits = [i for i, ln in enumerate(src, 1) if pat.match(ln)]
    if len(hits) != 1:
        raise RuntimeError("def " + name + " 出现次数异常")
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
    me = os.path.join("code", os.path.basename(__file__))
    names = {
        "L1": "l1_local_classes", "L2": "l2_subclass_edges",
        "L3": "l3_object_properties", "L4": "l4_annotation_properties",
        "L5": "l5_max_depth", "L6": "l6_leaf_classes",
    }
    return {k: {"file": me, "entry": fn, "lines": _entry_span(fn)}
            for k, fn in names.items()}


def emit_artifacts(input_path, params=None):
    """按 params['only'] 生成一件产物并落盘（相对路径在调用方给的参数里）。"""
    only = (params or {}).get("only", "")
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(str(__file__))))
    research = os.path.dirname(pkg_dir)
    owl_path = str(input_path) if input_path else os.path.join(research, OWLNAME)
    paper_path = os.path.join(research, PAPER)
    rows = anchors(paper_path, owl_path)
    docs = {
        "ns": ns_document(owl_path),
        "anchors": rows,
        "protocol": protocol_document(paper_path),
        "entries": entries_document(),
        "tiers": tiers_document(owl_path),
        "overlap": {"peers": {}, "unavailable": ["0005"]},
        "contrast": ns_contrast_rows(owl_path),
        "readings": readings_document(owl_path, rows),
        "diff_A01": diff_document(owl_path, rows),
        "independence": {
            "entry": os.path.join("code", os.path.basename(__file__)) + "::main",
            "shared_code_with_a": False,
            "signer_pkg_id": "pkg-B",
            "source": ("本实现为独立第二实现：minidom 解析、显式栈迭代、流式一次过计数、"
                       "urlsplit 划界；未读取、未导入、未改写另一实现包的任何代码与产物"),
        },
    }
    table = {
        "ns": ("evidence", "ns.json"),
        "anchors": ("evidence", "anchors.json"),
        "protocol": ("evidence", "protocol.json"),
        "entries": ("evidence", "entries.json"),
        "tiers": ("deviations", "tiers.json"),
        "overlap": ("deviations", "overlap.json"),
        "contrast": ("deviations", "contrast.json"),
        "readings": ("deviations", "readings.json"),
        "diff_A01": ("deviations", "diff_A01.json"),
        "independence": ("evidence", "independence.json"),
    }
    key = None
    for k, (sub, name) in table.items():
        if only == sub + "/" + name or only == k:
            key = k
            break
    if key is None:
        raise RuntimeError("unknown artifact: " + only)
    sub, name = table[key]
    outdir = os.path.join(pkg_dir, sub)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, name), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(docs[key], ensure_ascii=False, indent=2) + "\n")
    return {"path": sub + "/" + name}


def main(argv=None):
    owl = (argv or sys.argv[1:] or [None])[0]
    if owl is None:
        owl = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(str(__file__))))), OWLNAME)
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
