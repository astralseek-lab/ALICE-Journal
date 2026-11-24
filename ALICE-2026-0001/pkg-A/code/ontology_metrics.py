"""ALICE-2026-0001 · pkg-A 主实现（K 六量入口）。

口径来源：题面 §二（统一口径：只做 XML 结构解析，不做 OWL 推理）。
件型：RDF/XML（bcto.owl）。本模块用 xml.etree.ElementTree 整树解析＋递归遍历＋建索引计数。
命名空间判定：宿主（owl:Ontology@rdf:about 的 netloc）＋该宿主下「类最集中」的目录，
逐条 IRI 走 urlsplit 划界；不用类名前缀、不用 versionIRI 退段、不用 rdf:about 去文件名
（题面 §2.4 禁用三条；三读数只在 deviations/contrast.json 作事后对照）。
六个 K 量各一个入口：`def <entry>(input_path, params)`，input_path 是 bcto.owl 的路径，
返回 {"v": <int>, "unit": <单位>}（判据 12 要求同输入两跑逐字节同，故返回里无时间戳）。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWL = "{http://www.w3.org/2002/07/owl#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"


def _tree(input_path):
    return ET.parse(str(input_path))


def ontology_about(root):
    ont = root.find(f".//{OWL}Ontology")
    return ont.get(RDF + "about") if ont is not None else None


def named_class_iris(root):
    """全件 owl:Class 带 rdf:about 的 IRI，按 IRI 去重（匿名类不计入）。"""
    out = set()
    for el in root.iter(f"{OWL}Class"):
        about = el.get(RDF + "about")
        if about:
            out.add(about)
    return out


def _iri_dir(iri):
    """IRI 的（netloc, 目录）——目录＝path+fragment 截到最后一个 '/' 或 '#'（含）。"""
    p = urlsplit(iri)
    full = p.path + ("#" + p.fragment if p.fragment else "")
    cut = max(full.rfind("/"), full.rfind("#"))
    return (p.netloc, full[: cut + 1])


def local_namespace(root):
    """题面 §2.1 L1 行：宿主＝owl:Ontology@rdf:about 的 netloc；在该 host 下取类最集中的目录。

    返回 (rule, host, dir, local_set)。rule 是判定链的文字留痕（evidence/ns.json 同串）。
    """
    about = ontology_about(root)
    host = urlsplit(about).netloc
    iris = named_class_iris(root)
    counts = {}
    for iri in iris:
        loc, d = _iri_dir(iri)
        if loc == host:
            counts_key = (loc, d)
            counts[counts_key] = counts.get(counts_key, 0) + 1
    best = max(sorted(counts), key=lambda k: counts[k])  # 类最集中的目录（序确定：先排序再取最大）
    local = {iri for iri in iris if _iri_dir(iri) == best}
    rule = (
        "宿主＝owl:Ontology@rdf:about 的 netloc，在该 host 下取类最集中的目录；"
        "IRI 逐条 urlsplit 划界（不用类名前缀／versionIRI 退段／rdf:about 去文件名）"
    )
    return rule, host, best[1], local


def _subclass_edges(root):
    """全件 rdfs:subClassOf 逐元素（不去重）。

    返回 (resource_edges, anon_object_edges)：
      resource_edges: [(subject_iri, object_iri)] —— 带 rdf:resource，主语为外包具名类；
      anon_object_edges: [(subject_iri, None)] —— 宾语为匿名 Restriction/类（另列，不进 L2）。
    主语匿名（owl:Class 无 rdf:about）时 subject 记 None，由调用方另编号。
    """
    parent = {}
    for el in root.iter():
        for ch in list(el):
            parent[ch] = el

    def enclosing(el):
        p = parent.get(el)
        while p is not None:
            if p.tag == f"{OWL}Class":
                return p.get(RDF + "about")  # None ＝匿名主语
            p = parent.get(p)
        return None

    resource_edges, anon_object_edges = [], []
    for el in root.iter(f"{RDFS}subClassOf"):
        subj = enclosing(el)
        res = el.get(RDF + "resource")
        if res is not None:
            resource_edges.append((subj, res))
        else:
            anon_object_edges.append((subj, None))
    return resource_edges, anon_object_edges


def L1_class_local(input_path, params):
    """L1 本地类数：本地命名空间内 owl:Class 按 IRI 去重（匿名类不计入）。"""
    root = _tree(input_path).getroot()
    _rule, _host, _dir, local = local_namespace(root)
    return {"v": len(local), "unit": "classes"}


def L2_subclass_edges(input_path, params):
    """L2 子类边数：全件 rdfs:subClassOf 带 rdf:resource 的三元组，按条计不去重。"""
    root = _tree(input_path).getroot()
    resource_edges, _anon = _subclass_edges(root)
    return {"v": len(resource_edges), "unit": "edges"}


def L3_object_properties(input_path, params):
    """L3 对象属性数：owl:ObjectProperty 按 IRI 去重，全件计（含外部内联声明）。"""
    root = _tree(input_path).getroot()
    iris = {el.get(RDF + "about") for el in root.iter(f"{OWL}ObjectProperty") if el.get(RDF + "about")}
    return {"v": len(iris), "unit": "properties"}


def L4_annotation_properties(input_path, params):
    """L4 注释属性数：owl:AnnotationProperty 按 IRI 去重，全件计。"""
    root = _tree(input_path).getroot()
    iris = {el.get(RDF + "about") for el in root.iter(f"{OWL}AnnotationProperty") if el.get(RDF + "about")}
    return {"v": len(iris), "unit": "properties"}


def _children_map(resource_edges):
    """父 → 子 索引（子＝subClassOf 主语，父＝宾语）；同边只留一条（环由访问集断开）。"""
    children = {}
    for subj, obj in resource_edges:
        if subj is None:
            continue
        children.setdefault(obj, set()).add(subj)
    return children


def L5_max_depth(input_path, params):
    """L5 最大层级深度（边数）：起点＝全图根（owl:Class 中不作任何 subClassOf 主语者，
    含外部顶层类）；沿 subClassOf 下行；深度＝到最远本地类节点的边数。"""
    root = _tree(input_path).getroot()
    _rule, _host, _dir, local = local_namespace(root)
    named = named_class_iris(root)
    resource_edges, anon_object_edges = _subclass_edges(root)
    has_parent = {s for s, _o in resource_edges if s} | {s for s, _o in anon_object_edges if s}
    roots = named - has_parent
    children = _children_map(resource_edges)

    depth = {}

    def walk(node, d, stack):
        if node in stack:  # 环：同边只走一次，回边断开
            return
        if d > depth.get(node, -1):
            depth[node] = d
        stack.add(node)
        for ch in children.get(node, ()):  # 递归遍历（pkg-A 允许）
            walk(ch, d + 1, stack)
        stack.discard(node)

    for r in roots:
        walk(r, 0, set())
    best = max((depth.get(c, 0) for c in local), default=0)
    return {"v": best, "unit": "edges"}


def L6_leaf_classes(input_path, params):
    """L6 叶类数：本地类中无本地子类者（只看本地→本地的边）。"""
    root = _tree(input_path).getroot()
    _rule, _host, _dir, local = local_namespace(root)
    resource_edges, _anon = _subclass_edges(root)
    local_children_of = set()
    for subj, obj in resource_edges:
        if subj in local and obj in local:
            local_children_of.add(obj)
    leaves = {c for c in local if c not in local_children_of}
    return {"v": len(leaves), "unit": "classes"}
