#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B 侧六量入口（ALICE-2026-0003 旁证包）。

实现族：xml.dom.minidom 建 DOM，之后显式栈迭代、单遍累计；
IRI 划界用 urlsplit 取 scheme+netloc+path 自行比对；
host／dir 由 owl:Ontology@rdf:about 独立解析一次。
不使用基于树状 Element 结构的其它解析库；不使用递归遍历；不为任何量走第二遍 DOM。

入口：parse(input_path, params)，params["quantity"] ∈ 题面 §二 六键名。
另：contrast_hits(input_path, params) 算三个对照读法的命中数（params["rule"]）。
"""
import sys
from xml.dom import minidom
from urllib.parse import urlsplit

NS = {
    "owl": "http://www.w3.org/2002/07/owl#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
}


def _iri_dir(iri):
    u = urlsplit(iri)
    path = u.path
    d = path.rsplit("/", 1)[0] + "/" if "/" in path else "/"
    return u.scheme, u.netloc, d


def walk_collect(input_path):
    """单遍显式栈遍历整棵 DOM，累计：具名类、匿名节点、subClassOf 边、两类属性、本体 IRI。"""
    doc = minidom.parse(str(input_path))
    root = doc.documentElement

    ontology_about = None
    named_classes = []       # 具名 owl:Class 的 IRI（文档序）
    anon_class_count = 0     # 无 rdf:about 的 owl:Class（全树）
    anon_nodes = 0           # 匿名 owl:Class／owl:Restriction 全局编号器
    obj_props = set()
    ann_props = set()
    subj_res_edges = []      # (主体 key, 宾语 IRI)：宾语带 rdf:resource 的 subClassOf，按条计
    anon_obj_edges = []      # 宾语为匿名 Restriction 的 subClassOf：(主体 key, 宾语 @anonymous#n)
    pending_subj = None      # 上一条无 rdf:resource 的 subClassOf 的主体

    class_stack = []         # 外层 owl:Class 的 key 栈（具名 IRI 或 @anonymous#n）
    # 事件栈：("enter", node) ／ ("exit", node)
    stack = [("enter", root)]
    while stack:
        ev, node = stack.pop()
        if ev == "exit":
            if node.nodeType == node.ELEMENT_NODE and node.tagName == "owl:Class":
                class_stack.pop()
            continue
        if node.nodeType != node.ELEMENT_NODE:
            continue
        tag = node.tagName
        if tag == "owl:Ontology" and ontology_about is None:
            ontology_about = node.getAttribute("rdf:about") or None
        if tag == "owl:Class":
            about = node.getAttribute("rdf:about")
            if about:
                named_classes.append(about)
                class_stack.append(about)
            else:
                anon_nodes += 1
                anon_class_count += 1
                class_stack.append("@anonymous#%d" % anon_nodes)
        elif tag == "owl:Restriction":
            if not node.getAttribute("rdf:about"):
                anon_nodes += 1
                if pending_subj is not None:
                    anon_obj_edges.append((pending_subj, "@anonymous#%d" % anon_nodes))
                    pending_subj = None
        elif tag == "owl:ObjectProperty":
            about = node.getAttribute("rdf:about")
            if about:
                obj_props.add(about)
        elif tag == "owl:AnnotationProperty":
            about = node.getAttribute("rdf:about")
            if about:
                ann_props.add(about)
        elif tag == "rdfs:subClassOf":
            subject = class_stack[-1] if class_stack else None
            res = node.getAttribute("rdf:resource")
            if res:
                subj_res_edges.append((subject, res))
            else:
                pending_subj = subject
        # 子节点逆序压栈，保持文档序
        children = []
        ch = node.firstChild
        while ch is not None:
            children.append(ch)
            ch = ch.nextSibling
        stack.append(("exit", node))
        for ch in reversed(children):
            stack.append(("enter", ch))
    doc.unlink()
    return {
        "ontology_about": ontology_about,
        "named_classes": named_classes,
        "anon_class_count": anon_class_count,
        "obj_props": obj_props,
        "ann_props": ann_props,
        "subj_res_edges": subj_res_edges,
        "anon_obj_edges": anon_obj_edges,
    }


def local_namespace(col):
    """host 取自 owl:Ontology@rdf:about；dir ＝ 该 host 下具名类最集中的目录。"""
    about = col["ontology_about"]
    if not about:
        raise RuntimeError("无 owl:Ontology@rdf:about")
    host = urlsplit(about).netloc
    scheme = urlsplit(about).scheme
    counts = {}
    for iri in col["named_classes"]:
        s, h, d = _iri_dir(iri)
        if h == host:
            counts[d] = counts.get(d, 0) + 1
    best = None
    for d in sorted(counts):
        if best is None or counts[d] > counts[best]:
            best = d
    if best is None:
        raise RuntimeError("该 host 下无任何具名类")
    return scheme + "://" + host + best, host, best


def analyze(input_path):
    col = walk_collect(input_path)
    ns, host, ns_dir = local_namespace(col)

    def is_local(iri):
        if not iri or iri.startswith("@anonymous#"):
            return False
        s, h, d = _iri_dir(iri)
        return h == host and (s + "://" + h + d) == ns

    named = col["named_classes"]
    named_set = set(named)
    local_set = set()
    for iri in named_set:
        if is_local(iri):
            local_set.add(iri)

    tier1, tier2, tier3 = [], [], []
    for s, o in col["subj_res_edges"]:
        sl, ol = is_local(s), is_local(o)
        if sl and ol:
            tier1.append((s, o))
        elif sl and not ol:
            tier2.append((s, o))
        else:
            tier3.append((s, o))

    parents = {}
    children = {}
    subject_named = set()
    for s, o in col["subj_res_edges"]:
        if s is not None and not s.startswith("@anonymous#"):
            parents.setdefault(s, []).append(o)
            children.setdefault(o, []).append(s)
            subject_named.add(s)
    for s, _o in col["anon_obj_edges"]:
        if s is not None and not s.startswith("@anonymous#"):
            subject_named.add(s)

    # L5：本地类深度＝沿父边上行的连续本地边数（父非本地即停）；边访问集断环
    depth = {}
    breaks = []
    visiting = set()
    for c0 in sorted(local_set):
        if c0 in depth:
            continue
        stack = [(c0, False)]
        while stack:
            node, done = stack.pop()
            if done:
                best = 0
                for p in parents.get(node, []):
                    if p not in local_set:
                        continue
                    if (node, p) in breaks:
                        continue
                    best = max(best, 1 + depth.get(p, 0))
                depth[node] = best
                visiting.discard(node)
                continue
            if node in depth:
                continue
            if node in visiting:
                continue
            visiting.add(node)
            stack.append((node, True))
            for p in parents.get(node, []):
                if p not in local_set:
                    continue
                if p in visiting:      # 回边：断环并留痕
                    breaks.append((node, p))
                    continue
                if p not in depth:
                    stack.append((p, False))
    l5 = 0
    for c in local_set:
        if depth.get(c, 0) > l5:
            l5 = depth[c]

    # L5_alt：只走两端皆本地的边，起点＝本地无本地父类者
    alt_children = {}
    has_local_parent = set()
    for s, o in col["subj_res_edges"]:
        if s in local_set and o in local_set:
            alt_children.setdefault(o, []).append(s)
            has_local_parent.add(s)
    alt_roots = [c for c in sorted(local_set) if c not in has_local_parent]
    l5_alt = 0
    stack = []
    for r0 in alt_roots:
        stack.append((r0, 0, set()))
    while stack:
        node, d0, seen = stack.pop()
        if d0 > l5_alt:
            l5_alt = d0
        for ch in alt_children.get(node, []):
            e = (node, ch)
            if e in seen:
                continue
            stack.append((ch, d0 + 1, seen | {e}))

    # L5_selfcheck：本地类中无任何父类者
    l5_selfcheck = 0
    for c in local_set:
        if c not in subject_named:
            l5_selfcheck += 1

    # L6：本地类中无本地子类者
    has_local_child = set()
    for s, o in col["subj_res_edges"]:
        if s in local_set and o in local_set:
            has_local_child.add(o)
    l6 = 0
    for c in local_set:
        if c not in has_local_child:
            l6 += 1
    # L6_alt：外部子类也算
    l6_alt = 0
    for c in local_set:
        if c not in children:
            l6_alt += 1

    return {
        "ns": ns, "host": host, "dir": ns_dir,
        "named_set": named_set, "local_set": local_set,
        "L1": len(local_set),
        "L2": len(col["subj_res_edges"]),
        "tier1": tier1, "tier2": tier2, "tier3": tier3,
        "anon_obj": col["anon_obj_edges"],
        "subclass_total": len(col["subj_res_edges"]) + len(col["anon_obj_edges"]),
        "L3": len(col["obj_props"]),
        "L3_local": sum(1 for p in col["obj_props"] if is_local(p)),
        "L4": len(col["ann_props"]),
        "L4_local": sum(1 for p in col["ann_props"] if is_local(p)),
        "L5": l5, "L5_alt": l5_alt, "L5_selfcheck": l5_selfcheck,
        "L6": l6, "L6_alt": l6_alt,
        "anonymous_class": col["anon_class_count"],
        "cycle_breaks": breaks,
    }


_Q = {
    "L1_class_local": ("L1", "count"),
    "L2_subclass_edges": ("L2", "count"),
    "L3_object_properties": ("L3", "count"),
    "L4_annotation_properties": ("L4", "count"),
    "L5_max_depth": ("L5", "edges"),
    "L6_leaf_classes": ("L6", "count"),
}


def parse(input_path, params):
    q = params["quantity"]
    if q not in _Q:
        raise ValueError("未知 quantity: %s" % q)
    key, unit = _Q[q]
    r = analyze(input_path)
    return {"quantity": q, "v": int(r[key]), "unit": unit}


def contrast_hits(input_path, params):
    """三个对照读法（不进主值）：about_dirname／prefix_BCIO／top_prefix。"""
    rule = params["rule"]
    col = walk_collect(input_path)
    named_set = set(col["named_classes"])
    if rule == "about_dirname":
        about = col["ontology_about"]
        u = urlsplit(about)
        d = u.path.rsplit("/", 1)[0] + "/"
        base = u.scheme + "://" + u.netloc + d
        hits = [c for c in named_set if c.startswith(base)]
    elif rule == "prefix_BCIO":
        hits = [c for c in named_set if c.rsplit("/", 1)[-1].startswith("BCIO_")]
    elif rule == "top_prefix":
        ns, host, _d = local_namespace(col)
        local = [c for c in named_set if c.startswith(ns)]
        counts = {}
        for c in local:
            counts.setdefault(c.rsplit("/", 1)[-1].split("_", 1)[0], []).append(c)
        top = sorted(counts.items(), key=lambda kv: (-len(kv[1]), kv[0]))[0][0]
        hits = [c for c in local if c.rsplit("/", 1)[-1].split("_", 1)[0] == top]
    else:
        raise ValueError("未知 rule: %s" % rule)
    return {"rule": rule, "v": len(hits), "unit": "count"}


if __name__ == "__main__":
    import json
    if len(sys.argv) > 2 and sys.argv[2] == "--all":
        r = analyze(sys.argv[1])
        out = {k: r[k] for k in ("ns", "host", "dir", "L1", "L2", "L3", "L3_local", "L4", "L4_local",
                                  "L5", "L5_alt", "L5_selfcheck", "L6", "L6_alt",
                                  "anonymous_class", "subclass_total")}
        out["tiers"] = [len(r["tier1"]), len(r["tier2"]), len(r["tier3"]), len(r["anon_obj"])]
        out["cycle_breaks"] = len(r["cycle_breaks"])
        print(json.dumps(out, ensure_ascii=False, sort_keys=True))
    else:
        q = sys.argv[2] if len(sys.argv) > 2 else "L1_class_local"
        print(json.dumps(parse(sys.argv[1], {"quantity": q}), ensure_ascii=False, sort_keys=True))
