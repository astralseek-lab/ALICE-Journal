#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pkg-A 六量入口（ALICE-2026-0003）。

唯一入口：parse(input_path, params)，按 params["quantity"] 分派。
实现族：xml.etree.ElementTree iterparse（文档序事件流，显式栈追踪外层类）。

口径（题面 §二，逐字执行）：
  本地命名空间 = owl:Ontology@rdf:about 的 host ＋ 该 host 下类最集中的目录。
  L1 本地类（rdf:about，IRI 去重）；L2 全件 rdfs:subClassOf@rdf:resource 按条计；
  L3/L4 属性按 IRI 去重全件计；L5 全图根起沿 subClassOf 下行、外部父类不计层；
  L6 本地类中无本地子类者。
"""
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

OWL = "http://www.w3.org/2002/07/owl#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

T_CLASS = f"{{{OWL}}}Class"
T_SUB = f"{{{RDFS}}}subClassOf"
T_OP = f"{{{OWL}}}ObjectProperty"
T_AP = f"{{{OWL}}}AnnotationProperty"
T_ONT = f"{{{OWL}}}Ontology"
T_RESTR = f"{{{OWL}}}Restriction"
A_ABOUT = f"{{{RDF}}}about"
A_RES = f"{{{RDF}}}resource"


def _ontology_about(input_path):
    """从 owl:Ontology 元素的 rdf:about 取本体身份 IRI（不读类名、不读文件名）。"""
    for _ev, el in ET.iterparse(input_path, events=("start",)):
        if el.tag == T_ONT:
            about = el.get(A_ABOUT)
            el.clear()
            return about
    raise RuntimeError("无 owl:Ontology@rdf:about")


def _named_class_iris(input_path):
    """全件带 rdf:about 的 owl:Class 的 IRI（文档序）。"""
    iris = []
    for _ev, el in ET.iterparse(input_path, events=("start",)):
        if el.tag == T_CLASS:
            about = el.get(A_ABOUT)
            if about:
                iris.append(about)
            el.clear()
    return iris


def local_namespace(input_path):
    """host＋dir：host 取自 owl:Ontology@rdf:about；dir ＝ 该 host 下类最集中的目录。"""
    about = _ontology_about(input_path)
    host = urlsplit(about).netloc
    scheme = urlsplit(about).scheme
    best_dir, best_n = None, -1
    counts = {}
    for iri in _named_class_iris(input_path):
        u = urlsplit(iri)
        if u.netloc != host:
            continue
        d = u.path.rsplit("/", 1)[0] + "/" if "/" in u.path else "/"
        counts[d] = counts.get(d, 0) + 1
    for d in sorted(counts):
        if counts[d] > best_n:
            best_dir, best_n = d, counts[d]
    if best_dir is None:
        raise RuntimeError("该 host 下无任何具名类")
    return f"{scheme}://{host}{best_dir}", host, best_dir


def scan(input_path):
    """单遍事件流扫描：类／属性／subClassOf 边／匿名节点编号，全部在此累积。"""
    ns, host, ns_dir = local_namespace(input_path)

    def is_local(iri):
        return iri is not None and iri.startswith(ns)

    classes_named = []        # 具名类 IRI（文档序）
    class_set = set()
    anon_no = {}              # id(element) -> n（匿名 owl:Class / owl:Restriction 全局编号）
    anon_counter = 0
    anonymous_class_count = 0
    objprops, annprops = set(), set()
    edges = []                # (subject IRI 或 @anonymous#n, object IRI) —— 仅 rdf:resource 边
    anon_obj_edges = []       # 宾语为匿名 Restriction 的 subClassOf：(主体 key, 宾语 @anonymous#n)
    subclass_subjects = set()  # 作为 subClassOf 主体的具名类
    pending_anon_subj = None  # 上一条无 rdf:resource 的 subClassOf 的主体（待配对其 Restriction 子节点）

    stack = []                # [(tag, about_or_anonkey)]
    for ev, el in ET.iterparse(input_path, events=("start", "end")):
        if ev == "start":
            if el.tag in (T_CLASS, T_RESTR):
                about = el.get(A_ABOUT)
                if about:
                    key = about
                    if el.tag == T_CLASS:
                        classes_named.append(about)
                        class_set.add(about)
                else:
                    anon_counter += 1
                    key = f"@anonymous#{anon_counter}"
                    anon_no[id(el)] = anon_counter
                    if el.tag == T_CLASS:
                        anonymous_class_count += 1
                    elif el.tag == T_RESTR and pending_anon_subj is not None:
                        anon_obj_edges.append((pending_anon_subj, key))
                        pending_anon_subj = None
                stack.append((el.tag, key))
                continue
            if el.tag == T_OP:
                about = el.get(A_ABOUT)
                if about:
                    objprops.add(about)
                stack.append((el.tag, None))
                continue
            if el.tag == T_AP:
                about = el.get(A_ABOUT)
                if about:
                    annprops.add(about)
                stack.append((el.tag, None))
                continue
            if el.tag == T_SUB:
                subj = None
                for t, k in reversed(stack):
                    if t == T_CLASS:
                        subj = k
                        break
                res = el.get(A_RES)
                if res is not None:
                    edges.append((subj, res))
                    if subj is not None and not subj.startswith("@anonymous#"):
                        subclass_subjects.add(subj)
                else:
                    pending_anon_subj = subj
                    if subj is not None and not subj.startswith("@anonymous#"):
                        subclass_subjects.add(subj)
                stack.append((el.tag, None))
                continue
            stack.append((el.tag, None))
        else:  # end
            if stack:
                stack.pop()
            el.clear()

    local_set = {c for c in class_set if is_local(c)}

    # ── L2 三档（同一次累积结果上分档；重复边对在装配层加 @k 后缀） ──
    tier1, tier2, tier3 = [], [], []
    for s, o in edges:
        s_loc = is_local(s)
        o_loc = is_local(o)
        if s_loc and o_loc:
            tier1.append((s, o))
        elif s_loc and not o_loc:
            tier2.append((s, o))
        else:
            tier3.append((s, o))

    # ── L5／L6 用图（具名类节点；子→父 与 父→子 两个方向） ──
    parents = {}   # child -> [parent]
    children = {}  # parent -> [child]
    for s, o in edges:
        if s.startswith("@anonymous#"):
            continue
        parents.setdefault(s, []).append(o)
        children.setdefault(o, []).append(s)

    cycle_breaks = []
    depth_memo = {}

    def local_depth(c, seen_edges):
        """本地类 c 的深度：沿父边上行、父类不在本地即停；边只走一次断环。"""
        if c in depth_memo:
            return depth_memo[c]
        best = 0
        for p in parents.get(c, []):
            if p not in local_set:
                continue  # 外部父类到那里停，不算一层
            e = (c, p)
            if e in seen_edges:
                cycle_breaks.append((c, p))
                continue
            seen_edges.add(e)
            d = 1 + local_depth(p, seen_edges)
            seen_edges.discard(e)
            best = max(best, d)
        depth_memo[c] = best
        return best

    l5 = max((local_depth(c, set()) for c in local_set), default=0)

    # L5_alt：只走两端皆本地的边，起点＝本地类中无本地父类者
    alt_children = {}
    alt_roots = []
    has_local_parent = set()
    for s, o in edges:
        if s in local_set and o in local_set:
            alt_children.setdefault(o, []).append(s)
            has_local_parent.add(s)
    for c in local_set:
        if c not in has_local_parent:
            alt_roots.append(c)

    def alt_walk(roots):
        best = 0
        stack = [(r, 0, set()) for r in roots]
        while stack:
            node, d, seen = stack.pop()
            best = max(best, d)
            for ch in alt_children.get(node, []):
                e = (node, ch)
                if e in seen:
                    continue
                stack.append((ch, d + 1, seen | {e}))
        return best
    l5_alt = alt_walk(alt_roots)

    # L5_selfcheck：本地类中无任何父类者（不作为任何 subClassOf 的主体）
    l5_selfcheck = sum(1 for c in local_set if c not in subclass_subjects)

    # L6：本地类中无本地子类者（只看 本地→本地 的边）
    has_local_child = set()
    for s, o in edges:
        if s in local_set and o in local_set:
            has_local_child.add(o)
    l6 = sum(1 for c in local_set if c not in has_local_child)

    # L6_alt：外部子类也算子类（任何具名子类都不算叶）
    has_any_named_child = set(children.keys())
    l6_alt = sum(1 for c in local_set if c not in has_any_named_child)

    return {
        "ns": ns, "host": host, "dir": ns_dir,
        "classes_named": classes_named, "class_set": class_set, "local_set": local_set,
        "L1": len(local_set),
        "edges": edges, "tier1": tier1, "tier2": tier2, "tier3": tier3,
        "anon_subclass_objects": anon_obj_edges,
        "subclass_total": len(edges) + len(anon_obj_edges),
        "L2": len(edges),
        "objprops": objprops, "annprops": annprops,
        "L3": len(objprops), "L3_local": sum(1 for p in objprops if is_local(p)),
        "L4": len(annprops), "L4_local": sum(1 for p in annprops if is_local(p)),
        "L5": l5, "L5_alt": l5_alt, "L5_selfcheck": l5_selfcheck,
        "L6": l6, "L6_alt": l6_alt,
        "anonymous_class": anonymous_class_count,
        "cycle_breaks": cycle_breaks,
        "is_local": is_local,
    }


_QUANTITIES = {
    "L1_class_local": ("L1", "count"),
    "L2_subclass_edges": ("L2", "count"),
    "L3_object_properties": ("L3", "count"),
    "L4_annotation_properties": ("L4", "count"),
    "L5_max_depth": ("L5", "edges"),
    "L6_leaf_classes": ("L6", "count"),
}


def parse(input_path, params):
    """唯一入口。params["quantity"] 取题面 §二 六个键名之一，返回 {'quantity','v','unit'}。"""
    q = params["quantity"]
    if q not in _QUANTITIES:
        raise ValueError(f"未知 quantity: {q}")
    key, unit = _QUANTITIES[q]
    r = scan(input_path)
    return {"quantity": q, "v": int(r[key]), "unit": unit}


def contrast_hits(input_path, params):
    """三个对照读法的命中数（题面 §二 三条禁法的对照值；不进主值，只供 deviations/contrast.json）。

    rule ∈ {"about_dirname", "prefix_BCIO", "top_prefix"}：
      about_dirname —— owl:Ontology@rdf:about 去文件名当目录；
      prefix_BCIO  —— 类名以 BCIO_ 起头（类名前缀判定，仅在此对照入口出现）；
      top_prefix   —— 本地类名第一个 '_' 之前段里命中数最多者（降序、同数按串升序取首）。
    """
    rule = params["rule"]
    r = scan(input_path)
    allc, local = r["class_set"], r["local_set"]
    if rule == "about_dirname":
        about = _ontology_about(input_path)
        u = urlsplit(about)
        base = f"{u.scheme}://{u.netloc}{u.path.rsplit('/', 1)[0]}/"
        hits = {c for c in allc if c.startswith(base)}
    elif rule == "prefix_BCIO":
        hits = {c for c in allc if c.rsplit("/", 1)[-1].startswith("BCIO_")}
    elif rule == "top_prefix":
        counts = {}
        for c in local:
            counts.setdefault(c.rsplit("/", 1)[-1].split("_", 1)[0], []).append(c)
        top = sorted(counts.items(), key=lambda kv: (-len(kv[1]), kv[0]))[0][0]
        hits = {c for c in local if c.rsplit("/", 1)[-1].split("_", 1)[0] == top}
    else:
        raise ValueError(f"未知 rule: {rule}")
    return {"rule": rule, "v": len(hits), "unit": "count"}


if __name__ == "__main__":
    import json
    q = sys.argv[2] if len(sys.argv) > 2 else "L1_class_local"
    print(json.dumps(parse(sys.argv[1], {"quantity": q}), ensure_ascii=False, sort_keys=True))
