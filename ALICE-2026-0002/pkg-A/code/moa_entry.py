# -*- coding: utf-8 -*-
"""pkg-A 唯一入口：ALICE-2026-0002（Schenk2023MoA）六量自算。

parse(input_path, params)：input_path 是 bcio_moa.owl 的路径（可能是判分器
扰动后的副本），params["quantity"] 选择要算的量，返回 dict，该量的数在键 "v" 上。

实现口径（题面 §二）：
  · 只做 RDF/XML 结构解析（xml.etree.ElementTree），不做 OWL 推理；
  · 本地命名空间前缀 = http://humanbehaviourchange.org/ontology/；
  · L1/L3/L4 为带 rdf:about 的去重 IRI 计数；
  · L2 为去重 (子类 IRI, 父类 IRI) 边：rdfs:subClassOf 所在具名 owl:Class ＝子类，
    rdf:resource ＝父类（可外部）；无 rdf:resource 的内嵌匿名类不计；
  · L5 在「两端皆本地」的 L2 子图上按边数计最大深度，同一 (子,父) 边只走一次断环；
  · L6 为本地类中在全 L2 边集里从未出现在父类位的个数。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

LOCAL_PREFIX = "http://humanbehaviourchange.org/ontology/"
OBO_PREFIX = "http://purl.obolibrary.org/obo/"
ADDICTO_MARK = "addictovocab.org"

_NS_OWL = "http://www.w3.org/2002/07/owl#"
_NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
_NS_RDFS = "http://www.w3.org/2000/01/rdf-schema#"
T_CLASS = "{%s}Class" % _NS_OWL
T_OBJPROP = "{%s}ObjectProperty" % _NS_OWL
T_ANNPROP = "{%s}AnnotationProperty" % _NS_OWL
T_SUBCLASS = "{%s}subClassOf" % _NS_RDFS
A_ABOUT = "{%s}about" % _NS_RDF
A_RESOURCE = "{%s}resource" % _NS_RDF

QUANTITIES = (
    "L1_class_local",
    "L2_subclass_edges",
    "L3_object_props",
    "L4_annotation_props",
    "L5_depth_max",
    "L6_leaf_classes",
    "X_ext_classes",
)


def _named_classes_and_edges(root):
    """返回 (named_class_iris, edges)。edges＝去重 (子类, 父类)，父类须 rdf:resource 非空。"""
    parent = {c: p for p in root.iter() for c in p}
    named = set()
    edges = set()
    for el in root.iter(T_CLASS):
        about = el.get(A_ABOUT)
        if about:
            named.add(about)
    for sub in root.iter(T_SUBCLASS):
        # 向上找最近的 owl:Class 祖先（即“所在的”类），须为具名类
        enc = parent.get(sub)
        while enc is not None and enc.tag != T_CLASS:
            enc = parent.get(enc)
        if enc is None:
            continue
        child = enc.get(A_ABOUT)
        if not child:
            continue
        res = sub.get(A_RESOURCE)
        if not res:
            continue  # 内嵌匿名类（子元素写法）一律不计
        edges.add((child, res))
    return named, edges


def _namespace_family(iri):
    if iri.startswith(OBO_PREFIX):
        return "obo"
    if ADDICTO_MARK in iri:
        return "addicto"
    return "other"


def _max_depth(local_classes, edges):
    """两端皆本地的子图上的最大深度（边数）。同一 (子,父) 边只走一次断环。

    返回 (max_depth, cycle_breaks)。根＝子图里不作子类出现的本地类。
    """
    local_edges = [(a, b) for a, b in edges if a in local_classes and b in local_classes]
    children = {}
    in_subgraph = set()
    is_child = set()
    for a, b in local_edges:
        children.setdefault(b, []).append(a)
        in_subgraph.add(a)
        in_subgraph.add(b)
        is_child.add(a)
    for key in children:
        children[key].sort()
    roots = sorted(c for c in in_subgraph if c not in is_child)
    best = 0
    breaks = []
    for r in roots:
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, seen_edges = stack.pop()
            if depth > best:
                best = depth
            for ch in children.get(node, []):
                edge = (ch, node)
                if edge in seen_edges:
                    breaks.append({"child": ch, "parent": node, "broken_at": edge})
                    continue
                stack.append((ch, depth + 1, seen_edges | {edge}))
    return best, breaks


def parse(input_path, params):
    """唯一入口。params["quantity"] ∈ QUANTITIES；返回 {"quantity","v","unit",...}。"""
    quantity = (params or {}).get("quantity")
    if quantity not in QUANTITIES:
        raise ValueError("unknown quantity: %r" % (quantity,))
    root = ET.parse(str(input_path)).getroot()
    named, edges = _named_classes_and_edges(root)
    local = {iri for iri in named if iri.startswith(LOCAL_PREFIX)}

    if quantity == "L1_class_local":
        return {"quantity": quantity, "v": len(local), "unit": "count"}
    if quantity == "L2_subclass_edges":
        internal = sum(1 for _a, b in edges if b.startswith(LOCAL_PREFIX))
        return {
            "quantity": quantity,
            "v": len(edges),
            "unit": "count",
            "by_namespace": {"internal": internal, "to_external": len(edges) - internal},
        }
    if quantity == "L3_object_props":
        v = len({e.get(A_ABOUT) for e in root.iter(T_OBJPROP) if e.get(A_ABOUT)})
        return {"quantity": quantity, "v": v, "unit": "count"}
    if quantity == "L4_annotation_props":
        v = len({e.get(A_ABOUT) for e in root.iter(T_ANNPROP) if e.get(A_ABOUT)})
        return {"quantity": quantity, "v": v, "unit": "count"}
    if quantity == "L5_depth_max":
        depth, breaks = _max_depth(local, edges)
        out = {"quantity": quantity, "v": depth, "unit": "edges"}
        if breaks:
            out["cycle_breaks"] = breaks
        return out
    if quantity == "L6_leaf_classes":
        parents = {b for _a, b in edges}
        return {"quantity": quantity, "v": sum(1 for c in local if c not in parents), "unit": "count"}
    # X_ext_classes
    ext = [iri for iri in named if not iri.startswith(LOCAL_PREFIX)]
    by_ns = {"obo": 0, "addicto": 0, "other": 0}
    for iri in ext:
        by_ns[_namespace_family(iri)] += 1
    return {"quantity": quantity, "v": len(ext), "unit": "count", "by_namespace": by_ns}


if __name__ == "__main__":
    import json
    import sys

    owl = sys.argv[1] if len(sys.argv) > 1 else "bcio_moa.owl"
    for q in QUANTITIES:
        print(json.dumps(parse(owl, {"quantity": q}), ensure_ascii=False, sort_keys=True))
