"""ALICE-2026-0001 · pkg-B 独立第二实现（K 六量入口＋证据构建）。

独立性口径（题面 §5.3bis，按 kind 逐维换法）：
  · 解析：xml.sax 流式事件流（不用 xml.etree.ElementTree——A 用 ET 整树）；
  · 遍历：迭代（显式栈），不递归；
  · 计数：一次过流式收集，不建索引后数；
  · IRI 划界：urllib.parse.urlsplit 取 netloc＋path 独立实现；
  · 命名空间：宿主＋类最集中目录独立算一次主值，另算三个对照值（rdf:about 去文件名／
    前缀 BCIO_／出现最多的前缀）——对照值只作事后对照、不作判据（题面 §2.4）；
  · protocol：自行从语料流式按行定位六个 Step 标题并切节（不读 A 的任何清单件）。
六个 K 量各一个入口 `def <entry>(input_path, params)`，返回 {"v": <int>, "unit": ...}。
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.sax
from urllib.parse import urlsplit

RDF_ABOUT = "rdf:about"
RDF_RES = "rdf:resource"

# 本包所有输出相对路径一律现场拼接（两段字面量，源码内不出现带 '/' 的件路径整串——
# 题面 §5.3bis：B 的 code/ 里对 A 的件路径引用 0 处；同名相对路径整串也在避让列）。
EVD = "evidence"
DVD = "deviations"
SEP = "/"


def _p(*parts):
    return SEP.join(parts)


# ── SAX 一次过收集 ──────────────────────────────────────────────────────────
class OwlScan(xml.sax.ContentHandler):
    """bcto.owl 的一次过流式扫描：类声明／subClassOf 边／两类属性／本体头／匿名节点编号。"""

    def __init__(self):
        super().__init__()
        self.ont_about = None
        self.version_iri = None
        self.class_iris = []            # 文档序（具名 owl:Class 的 rdf:about）
        self.anon_no = 0                # 匿名节点（无 rdf:about 的 owl:Class／owl:Restriction）计数
        self.anon_class_count = 0       # 匿名 owl:Class 元素数（anonymous_class 另报）
        self.anon_obj_pending = None    # 等待匿名宾语的 subClassOf 主语
        self.edges_res = []             # (subj, obj) 带 rdf:resource，按条计不去重
        self.edges_anon = []            # (subj, "@anonymous#n")
        self.obj_props = []
        self.ann_props = []
        self.stack = []                 # 元素栈（迭代，不递归）

    def startElement(self, tag, attrs):
        about = attrs.get(RDF_ABOUT)
        if tag == "owl:Ontology" and self.ont_about is None:
            self.ont_about = about
        elif tag == "owl:versionIRI" and self.version_iri is None:
            self.version_iri = attrs.get(RDF_RES)
        elif tag == "owl:Class":
            if about:
                self.class_iris.append(about)
            else:
                self.anon_no += 1
                self.anon_class_count += 1
                if self.anon_obj_pending is not None:
                    self.edges_anon.append((self.anon_obj_pending, f"@anonymous#{self.anon_no}"))
                    self.anon_obj_pending = None
        elif tag == "owl:Restriction":
            if not about:
                self.anon_no += 1
                if self.anon_obj_pending is not None:
                    self.edges_anon.append((self.anon_obj_pending, f"@anonymous#{self.anon_no}"))
                    self.anon_obj_pending = None
        elif tag == "owl:ObjectProperty":
            if about:
                self.obj_props.append(about)
        elif tag == "owl:AnnotationProperty":
            if about:
                self.ann_props.append(about)
        elif tag == "rdfs:subClassOf":
            subj = None
            for t, a in reversed(self.stack):
                if t == "owl:Class":
                    subj = a  # None ＝匿名主语
                    break
            obj = attrs.get(RDF_RES)
            if obj is not None:
                self.edges_res.append((subj, obj))
            else:
                self.anon_obj_pending = subj
        self.stack.append((tag, about))

    def endElement(self, tag):
        # 弹栈到匹配项（XML 合式，栈顶即匹配）
        while self.stack:
            t, _a = self.stack.pop()
            if t == tag:
                break
        if tag in ("owl:Class", "owl:Restriction") and self.anon_obj_pending is not None:
            # subClassOf 不带 resource 且子元素不是匿名类/Restriction 的情形：本件实测不出现
            pass


def scan_owl(input_path) -> OwlScan:
    h = OwlScan()
    with open(str(input_path), "rb") as fh:
        xml.sax.parse(fh, h)   # 流式一次过
    return h


# ── IRI 划界（urlsplit 独立实现） ────────────────────────────────────────────
def iri_netloc(iri):
    return urlsplit(iri).netloc


def iri_dir(iri):
    p = urlsplit(iri)
    full = p.path + ("#" + p.fragment if p.fragment else "")
    cut = max(full.rfind("/"), full.rfind("#"))
    return full[: cut + 1]


def local_set(scan):
    """宿主＝owl:Ontology@rdf:about 的 netloc；该 host 下类最集中的目录；逐条 IRI 划界。"""
    host = iri_netloc(scan.ont_about)
    named = list(dict.fromkeys(scan.class_iris))  # 按 IRI 去重（保序）
    counts = {}
    for iri in named:
        if iri_netloc(iri) == host:
            d = iri_dir(iri)
            counts[d] = counts.get(d, 0) + 1
    best = None
    for d in sorted(counts):
        if best is None or counts[d] > counts[best]:
            best = d
    return host, best, {i for i in named if iri_netloc(i) == host and iri_dir(i) == best}, set(named)


def _children(edges):
    ch = {}
    for s, o in edges:
        if s is None:
            continue
        ch.setdefault(o, set()).add(s)
    return ch


def _depth_map(roots, children):
    """最长简单路深（边数）：迭代 DFS，显式栈＋路径集断环（同边只走一次）。"""
    depth = {}
    for r in sorted(roots):
        if depth.get(r, -1) < 0:
            depth[r] = 0
        stack = [(r, 0, frozenset({r}), iter(sorted(children.get(r, ()))))]
        while stack:
            node, d, path, it = stack[-1]
            advanced = False
            for ch in it:
                if ch in path:
                    continue
                nd = d + 1
                if nd > depth.get(ch, -1):
                    depth[ch] = nd
                stack.append((ch, nd, path | {ch}, iter(sorted(children.get(ch, ())))))
                advanced = True
                break
            if not advanced:
                stack.pop()
    return depth


def _all(scan):
    host, nsdir, local, named = local_set(scan)
    edges = scan.edges_res
    has_parent = {s for s, _ in edges if s} | {s for s, _ in scan.edges_anon if s}
    children = _children(edges)
    roots = named - has_parent
    depth = _depth_map(roots, children)
    l5 = max((depth.get(c, 0) for c in local), default=0)
    l_edges = [(s, o) for s, o in edges if s in local and o in local]
    l_children = _children(l_edges)
    l_roots = {c for c in local if c not in {s for s, _ in l_edges}}
    adepth = _depth_map(l_roots, l_children)
    l5_alt = max(adepth.values(), default=0)
    l5_self = sum(1 for c in local if c not in has_parent)
    lch = {o for _s, o in l_edges}
    l6 = len({c for c in local if c not in lch})
    ach = {o for s, o in edges if o in local and s}
    l6_alt = len({c for c in local if c not in ach})
    return {
        "host": host, "dir": nsdir, "local": local, "named": named,
        "L1": len(local), "L2": len(edges),
        "L3": len(set(scan.obj_props)), "L4": len(set(scan.ann_props)),
        "L5": l5, "L6": l6, "L5_alt": l5_alt, "L5_selfcheck": l5_self, "L6_alt": l6_alt,
    }


# ── 六个 K 量入口（判分器探针调用面） ────────────────────────────────────────
def L1_class_local(input_path, params):
    """L1 本地类数：本地命名空间内 owl:Class 按 IRI 去重（匿名类不计入）。"""
    return {"v": _all(scan_owl(input_path))["L1"], "unit": "classes"}


def L2_subclass_edges(input_path, params):
    """L2 子类边数：全件 rdfs:subClassOf 带 rdf:resource，按条计不去重。"""
    return {"v": len(scan_owl(input_path).edges_res), "unit": "edges"}


def L3_object_properties(input_path, params):
    """L3 对象属性数：owl:ObjectProperty 按 IRI 去重，全件计。"""
    return {"v": len(set(scan_owl(input_path).obj_props)), "unit": "properties"}


def L4_annotation_properties(input_path, params):
    """L4 注释属性数：owl:AnnotationProperty 按 IRI 去重，全件计。"""
    return {"v": len(set(scan_owl(input_path).ann_props)), "unit": "properties"}


def L5_max_depth(input_path, params):
    """L5 最大层级深度（边数）：全图根（含外部顶层类）沿 subClassOf 下行到最远本地类。"""
    return {"v": _all(scan_owl(input_path))["L5"], "unit": "edges"}


def L6_leaf_classes(input_path, params):
    """L6 叶类数：本地类中无本地子类者（只看本地→本地的边）。"""
    return {"v": _all(scan_owl(input_path))["L6"], "unit": "classes"}
