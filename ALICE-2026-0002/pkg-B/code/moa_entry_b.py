# -*- coding: utf-8 -*-
"""pkg-B 独立实现：ALICE-2026-0002（Schenk2023MoA）六量重算。

与本研究另一实现包的差异（题面 §四.5）：
  · 解析器：xml.dom.minidom 建 DOM 后显式栈迭代（不用另一套解析器）；
  · 遍历：显式栈，无递归；
  · 计数：单次遍历边扫边累计，不先建元素索引再回头数；
  · IRI 划界：urllib.parse.urlsplit 取 scheme／netloc／path 再比命名空间；
  · 不导入任何另一实现包的模块。

parse(input_path, params)：入口签名按判分器探针约定（第二位置参数名 params），
params["quantity"] 分派，返回 dict，断言值在键 "v" 上。
"""
from __future__ import annotations

from urllib.parse import urlsplit
from xml.dom import minidom
from xml.dom.minidom import Node

LOCAL_NETLOC = "humanbehaviourchange.org"
LOCAL_PATH_HEAD = "/ontology/"
OBO_NETLOC = "purl.obolibrary.org"
OBO_PATH_HEAD = "/obo/"
ADDICTO_NETLOC_MARK = "addictovocab.org"

QUANTITIES = (
    "L1_class_local",
    "L2_subclass_edges",
    "L3_object_props",
    "L4_annotation_props",
    "L5_depth_max",
    "L6_leaf_classes",
    "X_ext_classes",
)

RDF_ABOUT = "rdf:about"
RDF_RESOURCE = "rdf:resource"


def _is_local(iri):
    p = urlsplit(iri)
    return p.scheme in ("http", "https") and p.netloc == LOCAL_NETLOC and p.path.startswith(LOCAL_PATH_HEAD)


def _family(iri):
    p = urlsplit(iri)
    if p.netloc == OBO_NETLOC and p.path.startswith(OBO_PATH_HEAD):
        return "obo"
    if ADDICTO_NETLOC_MARK in p.netloc:
        return "addicto"
    return "other"


def _scan(input_path):
    """单次显式栈遍历，边扫边累计。返回 (local, ext_by_ns, edges, n_obj, n_ann)。"""
    doc = minidom.parse(str(input_path))
    local = set()
    ext = set()
    edges = set()
    obj_props = set()
    ann_props = set()
    # 栈元素：(DOM 节点, 最近的开放 owl:Class 元素或 None)
    stack = [(doc.documentElement, None)]
    while stack:
        node, enclosing = stack.pop()
        if node.nodeType == Node.ELEMENT_NODE:
            tag = node.tagName
            if tag == "owl:Class":
                about = node.getAttribute(RDF_ABOUT) or None
                if about:
                    (local if _is_local(about) else ext).add(about)
                enclosing = node  # 本元素成为子树里最近的开放类
            elif tag == "owl:ObjectProperty":
                about = node.getAttribute(RDF_ABOUT)
                if about:
                    obj_props.add(about)
            elif tag == "owl:AnnotationProperty":
                about = node.getAttribute(RDF_ABOUT)
                if about:
                    ann_props.add(about)
            elif tag == "rdfs:subClassOf":
                res = node.getAttribute(RDF_RESOURCE)
                if res and enclosing is not None:
                    child = enclosing.getAttribute(RDF_ABOUT)
                    if child:
                        edges.add((child, res))
            # 子节点逆序压栈，保持文档顺序弹出（顺序不影响计数，只为确定行为）
            kids = [c for c in node.childNodes if c.nodeType == Node.ELEMENT_NODE]
            for c in reversed(kids):
                stack.append((c, enclosing))
    by_ns = {"obo": 0, "addicto": 0, "other": 0}
    for iri in ext:
        by_ns[_family(iri)] += 1
    return local, ext, by_ns, edges, obj_props, ann_props


def _max_depth(local, edges):
    """两端皆本地的子图最大深度（边数）。显式栈，同一 (子,父) 边只走一次断环。"""
    children = {}
    in_sub = set()
    is_child = set()
    for a, b in edges:
        if a in local and b in local:
            children.setdefault(b, []).append(a)
            in_sub.add(a)
            in_sub.add(b)
            is_child.add(a)
    for key in children:
        children[key].sort()
    roots = sorted(c for c in in_sub if c not in is_child)
    best = 0
    breaks = []
    for r in roots:
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, seen = stack.pop()
            if depth > best:
                best = depth
            for ch in children.get(node, []):
                edge = (ch, node)
                if edge in seen:
                    breaks.append({"child": ch, "parent": node, "broken_at": list(edge)})
                    continue
                stack.append((ch, depth + 1, seen | {edge}))
    return best, breaks


def parse(input_path, params):
    """唯一入口。params["quantity"] ∈ QUANTITIES；返回 {"quantity","v","unit",...}。"""
    quantity = (params or {}).get("quantity")
    if quantity not in QUANTITIES:
        raise ValueError("unknown quantity: %r" % (quantity,))
    local, ext, by_ns, edges, obj_props, ann_props = _scan(input_path)
    if quantity == "L1_class_local":
        return {"quantity": quantity, "v": len(local), "unit": "count"}
    if quantity == "L2_subclass_edges":
        internal = sum(1 for _a, b in edges if _is_local(b))
        return {
            "quantity": quantity,
            "v": len(edges),
            "unit": "count",
            "by_namespace": {"internal": internal, "to_external": len(edges) - internal},
        }
    if quantity == "L3_object_props":
        return {"quantity": quantity, "v": len(obj_props), "unit": "count"}
    if quantity == "L4_annotation_props":
        return {"quantity": quantity, "v": len(ann_props), "unit": "count"}
    if quantity == "L5_depth_max":
        depth, breaks = _max_depth(local, edges)
        out = {"quantity": quantity, "v": depth, "unit": "edges"}
        if breaks:
            out["cycle_breaks"] = breaks
        return out
    if quantity == "L6_leaf_classes":
        parents = {b for _a, b in edges}
        return {"quantity": quantity, "v": sum(1 for c in local if c not in parents), "unit": "count"}
    return {"quantity": quantity, "v": len(ext), "unit": "count", "by_namespace": by_ns}


def all_quantities(input_path):
    """CLI 用：一次扫描出全部量。"""
    local, ext, by_ns, edges, obj_props, ann_props = _scan(input_path)
    internal = sum(1 for _a, b in edges if _is_local(b))
    depth, breaks = _max_depth(local, edges)
    parents = {b for _a, b in edges}
    return {
        "L1_class_local": len(local),
        "L2_subclass_edges": len(edges),
        "L2_split": {"internal": internal, "to_external": len(edges) - internal},
        "L3_object_props": len(obj_props),
        "L4_annotation_props": len(ann_props),
        "L5_depth_max": depth,
        "L5_cycle_breaks": breaks,
        "L6_leaf_classes": sum(1 for c in local if c not in parents),
        "X_ext_classes": {"v": len(ext), "by_namespace": by_ns},
    }


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--owl", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    result = all_quantities(args.owl)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
