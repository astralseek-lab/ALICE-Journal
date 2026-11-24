# -*- coding: utf-8 -*-
"""bcio_schedule.owl 的核心扫描（pkg-A 主实现，ElementTree＋递归遍历）。

口径（题面 §二／§7.3，写死）：
- 本地命名空间＝宿主（owl:Ontology@rdf:about 的 scheme://authority）＋该宿主下
  具名类 IRI 最集中的那一层目录（path 段，平票按目录串升序取第一）。
- 「本地类」＝本件内声明（有 rdf:about 的 owl:Class）且 IRI 落在本地命名空间的类，
  按 IRI 去重；匿名类（无 rdf:about）不计。
- 子类边＝rdfs:subClassOf@rdf:resource（宾语为匿名 owl:Restriction 者不进边集，
  单列 anon_subclass_objects）。三档按「声明的本地类集」成员资格划分：
  ①两端皆本地 ②主体本地·宾语外部 ③其余（主体外部或匿名）。
- 匿名节点编号：文档序遍历所有无 rdf:about 的 owl:Class 与 owl:Restriction，
  从 1 起连续编号；同一节点全件同号。
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter

RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
OWL = "{http://www.w3.org/2002/07/owl#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"


def _host_of(iri: str) -> str:
    # 宿主＝scheme://authority（本件一律绝对 IRI，无相对引用）
    scheme, _, rest = iri.partition("://")
    authority = rest.split("/", 1)[0]
    return f"{scheme}://{authority}"


def _dir_of(iri: str) -> str:
    """IRI 的目录：#fragment 与末段（文件名／本地名）不计入目录。"""
    path = iri.split("#", 1)[0]
    path = path.split("://", 1)[1].split("/", 1)[1] if "/" in path.split("://", 1)[1] else ""
    if not path.endswith("/"):
        path = path.rsplit("/", 1)[0] + "/" if "/" in path else ""
    return "/" + path.lstrip("/")


class OntologyScan:
    """一件 RDF/XML 本体发布件的完整扫描结果（按文档序一次性建立）。"""

    def __init__(self, path):
        root = ET.parse(str(path)).getroot()
        self.root = root
        self.parent = {ch: p for p in root.iter() for ch in p}
        # 具名类（文档序；iri 可能重复声明，集合语义在调用方）
        self.class_iris = [el.get(RDF + "about") for el in root.iter(OWL + "Class")]
        self.named_classes = [i for i in self.class_iris if i]
        # 匿名节点编号（文档序，无 rdf:about 的 owl:Class／owl:Restriction）
        self.anon_no = {}
        n = 0
        for el in root.iter():
            if el.tag in (OWL + "Class", OWL + "Restriction") and el.get(RDF + "about") is None:
                n += 1
                self.anon_no[id(el)] = n
        self.anon_nodes_total = n
        # 命名空间
        self.ontology_about = self._ontology_about(root)
        self.host = _host_of(self.ontology_about)
        dist = Counter(
            _dir_of(i) for i in self.named_classes if _host_of(i) == self.host
        )
        self.ns_dir_dist = dict(dist)
        best_dir = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        self.ns_dir = best_dir
        self.namespace = self.host + best_dir
        # 本地类集（声明且落在命名空间）
        self.local_classes = sorted({i for i in self.named_classes if i.startswith(self.namespace)})
        self.local_set = set(self.local_classes)
        # subClassOf 全件元素：rdf:resource 边 与 匿名 Restriction 宾语
        self.edges = []        # (subject_key, object_iri)，subject_key 为 IRI 或 @anonymous#n
        self.anon_objects = []  # (subject_key, @anonymous#n)
        self.sco_total = 0
        for el in root.iter(RDFS + "subClassOf"):
            self.sco_total += 1
            subj = self._subject_key(el)
            res = el.get(RDF + "resource")
            if res is not None:
                self.edges.append((subj, res))
            else:
                restr = [ch for ch in el if ch.tag == OWL + "Restriction"]
                if restr:
                    self.anon_objects.append((subj, f"@anonymous#{self.anon_no[id(restr[0])]}"))
        # 三档（成员资格语义）
        self.tier1 = [(s, o) for s, o in self.edges if s in self.local_set and o in self.local_set]
        self.tier2 = [(s, o) for s, o in self.edges if s in self.local_set and o not in self.local_set]
        self.tier3 = [(s, o) for s, o in self.edges if s not in self.local_set]
        # 属性
        self.object_properties = sorted(
            {el.get(RDF + "about") for el in root.iter(OWL + "ObjectProperty") if el.get(RDF + "about")}
        )
        self.annotation_properties = sorted(
            {el.get(RDF + "about") for el in root.iter(OWL + "AnnotationProperty") if el.get(RDF + "about")}
        )
        # 全图（具名主语边）：children[parent] = [child...]
        self.children = {}
        self.subj_any = set()   # 作过任何 subClassOf 主语的具名类
        for s, o in self.edges:
            if s.startswith("@"):  # 匿名主语不入全图节点
                continue
            self.children.setdefault(o, []).append(s)
            self.subj_any.add(s)
        for el in root.iter(RDFS + "subClassOf"):
            enc = self._enclosing(el)
            siri = enc.get(RDF + "about") if enc is not None else None
            if siri:
                self.subj_any.add(siri)
        self.named_set = set(self.named_classes)
        self.roots = sorted(c for c in self.named_set if c not in self.subj_any)
        # 本地子图
        self.local_children = {}
        local_parented = set()
        for s, o in self.edges:
            if s in self.local_set and o in self.local_set:
                self.local_children.setdefault(o, []).append(s)
                local_parented.add(s)
        self.local_roots = sorted(c for c in self.local_set if c not in local_parented)
        # equivalentClass 内联匿名类
        self.equiv_anon_classes = 0
        for el in root.iter(OWL + "equivalentClass"):
            for ch in el:
                if ch.tag == OWL + "Class" and ch.get(RDF + "about") is None:
                    self.equiv_anon_classes += 1

    @staticmethod
    def _ontology_about(root):
        for el in root.iter(OWL + "Ontology"):
            return el.get(RDF + "about")
        raise ValueError("无 owl:Ontology 元素")

    def _enclosing(self, el):
        cur = self.parent.get(el)
        while cur is not None:
            if cur.tag in (OWL + "Class", OWL + "Restriction"):
                return cur
            cur = self.parent.get(cur)
        return None

    def _subject_key(self, el):
        enc = self._enclosing(el)
        if enc is None:
            return "@none"
        about = enc.get(RDF + "about")
        return about if about else f"@anonymous#{self.anon_no[id(enc)]}"

    # ── 深度（递归遍历；环由「同边只走一次」断开）────────────────
    def depth_from_roots(self, node, _stack=()):
        """node 到全图根的最长路径边数（沿 subClassOf 下行＝按宾语反查子节点的逆方向）。"""
        best = getattr(self, "_dmemo", {}).get(node)
        if best is not None:
            return best
        parents = [o for s, o in self.edges if s == node and not o.startswith("@")]
        if node in self.roots or not parents:
            best = 0
        else:
            best = 0
            seen_edges = set(_stack)
            for p in parents:
                if (p, node) in seen_edges:
                    continue  # 环：同边只走一次
                best = max(best, 1 + self.depth_from_roots(p, tuple(seen_edges | {(p, node)})))
        if not hasattr(self, "_dmemo"):
            self._dmemo = {}
        self._dmemo[node] = best
        return best

    def local_depth(self, node, _stack=()):
        """本地子图内：本地类到本地根的最长路径边数（只走两端皆本地的边）。"""
        parents = [o for s, o in self.edges if s == node and o in self.local_set]
        if not parents:
            return 0
        seen_edges = set(_stack)
        best = 0
        for p in parents:
            if (p, node) in seen_edges:
                continue
            best = max(best, 1 + self.local_depth(p, tuple(seen_edges | {(p, node)})))
        return best

    def max_depth_local(self):
        """L5 主口径：全图根下行到最远本地类的边数。"""
        return max((self.depth_from_roots(c) for c in self.local_set), default=0)

    def max_depth_local_subgraph(self):
        """L5 另一读法：本地子图（起点＝本地类中无本地父类者）。"""
        return max((self.local_depth(c) for c in self.local_set), default=0)

    def leaf_local(self):
        """L6 主口径：本地类中无本地子类者。"""
        return sum(1 for c in self.local_set if not self.local_children.get(c))

    def leaf_with_external(self):
        """L6 另一读法：外部子类也算子类。"""
        return sum(1 for c in self.local_set if not self.children.get(c))


def contrast_hits(path, params=None):
    """三个对照读法（题面 §7.4 禁法，只留痕不作判据）：按件实算 hits。"""
    scan = OntologyScan(path)
    ns_strip = scan.ontology_about.rsplit("/", 1)[0] + "/"          # ① rdf:about 去文件名
    hits_strip = len({i for i in scan.named_set if i.startswith(ns_strip)})
    hits_bcio = len({                                                 # ② 前缀 BCIO_
        i for i in scan.named_set
        if i.rsplit("/", 1)[-1].rsplit("#", 1)[-1].startswith("BCIO_")
    })
    dist = Counter(_host_of(i) + _dir_of(i) for i in scan.named_set)  # ③ 出现最多的前缀
    top_prefix, hits_top = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {
        "strip_filename": {"namespace": ns_strip, "hits": hits_strip},
        "prefix_BCIO_": {"hits": hits_bcio},
        "most_frequent_prefix": {"prefix": top_prefix, "hits": hits_top},
    }


def overlap_sets(this_path, peer_path, params=None):
    """本件本地类集与对照件本地类集（各自按同一主口径判定）的三组差值。"""
    this = OntologyScan(this_path).local_set
    peer = OntologyScan(peer_path).local_set
    return {
        "both": sorted(this & peer),
        "only_in_this": sorted(this - peer),
        "only_in_peer": sorted(peer - this),
    }
