# -*- coding: utf-8 -*-
"""bcio_schedule.owl 核心扫描（pkg-B 独立实现）。

与 pkg-A 的十道独立性差异（题面 §5.3bis）中本模块承担的部分：
- XML 解析用 xml.dom.minidom（禁用 ElementTree）；
- 遍历一律迭代（显式栈），无递归；
- 计数为流式一次过（单趟文档序遍历同时建立全部计数，不另建索引后再数）；
- IRI 划界独立实现：urllib.parse.urlsplit 取 netloc＋path。

口径（题面 §二／§7.3）：本地命名空间＝宿主＋该宿主下具名类 IRI 最集中的目录
（平票按目录串升序取第一）；本地类＝本件声明（有 rdf:about）且 IRI 落在命名空间的
owl:Class，按 IRI 去重；子类边＝rdfs:subClassOf@rdf:resource（匿名 Restriction
宾语不进边集、单列）；三档按声明的本地类集成员资格划分。
"""
from __future__ import annotations

from collections import Counter
from urllib.parse import urlsplit
from xml.dom import minidom

T_CLASS = "owl:Class"
T_RESTR = "owl:Restriction"
T_SCO = "rdfs:subClassOf"
T_OPROP = "owl:ObjectProperty"
T_APROP = "owl:AnnotationProperty"
T_ONT = "owl:Ontology"
T_EQUIV = "owl:equivalentClass"


def _attr(el, name):
    v = el.getAttribute(name)
    return v if v else None


def _host_of(iri):
    p = urlsplit(iri)
    return f"{p.scheme}://{p.netloc}"


def _dir_of(iri):
    """IRI 目录：urlsplit 的 path 去末段（#fragment 与文件名段不计入目录）。"""
    p = urlsplit(iri)
    path = p.path
    if not path.endswith("/"):
        path = path.rsplit("/", 1)[0] + "/"
    return path


def walk_elements(doc, wanted):
    """全文档序迭代遍历（显式栈），产出 tag ∈ wanted 的元素（文档序）。"""
    out = []
    stack = [doc.documentElement]
    while stack:
        node = stack.pop()
        if node.nodeType == node.ELEMENT_NODE and node.tagName in wanted:
            out.append(node)
        # 子节点逆序压栈，弹出即文档序
        stack.extend(reversed([c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]))
    return out


def _enclosing(el):
    cur = el.parentNode
    while cur is not None and cur.nodeType == cur.ELEMENT_NODE:
        if cur.tagName in (T_CLASS, T_RESTR):
            return cur
        cur = cur.parentNode
    return None


def scan(path):
    """单趟迭代扫描＋计数。返回纯数据 dict（确定性：集合一律排序后落 list）。"""
    doc = minidom.parse(str(path))  # minidom 不吃 Path，须 str 包裹
    # 单趟文档序遍历：同时收集类、匿名节点编号、subClassOf 三分、属性、equivalentClass 匿名类
    named_classes = []
    anon_no = {}
    anon_counter = [0]

    def _num(el):
        """按需取匿名节点号：文档序（父元素先于子元素访问，编号一致）。"""
        if id(el) not in anon_no:
            anon_counter[0] += 1
            anon_no[id(el)] = anon_counter[0]
        return anon_no[id(el)]

    edges = []          # (subject_key, object_iri)
    anon_objects = []   # (subject_key, @anonymous#n)
    sco_total = 0
    object_properties = set()
    annotation_properties = set()
    equiv_anon = 0
    ontology_about = None
    for el in walk_elements(doc, {T_CLASS, T_RESTR, T_SCO, T_OPROP, T_APROP, T_ONT, T_EQUIV}):
        if el.tagName == T_ONT:
            if ontology_about is None:
                ontology_about = _attr(el, "rdf:about")
        elif el.tagName == T_CLASS:
            about = _attr(el, "rdf:about")
            if about:
                named_classes.append(about)
            else:
                _num(el)
        elif el.tagName == T_RESTR:
            if _attr(el, "rdf:about") is None:
                _num(el)
        elif el.tagName in (T_OPROP, T_APROP):
            about = _attr(el, "rdf:about")
            if about:
                (object_properties if el.tagName == T_OPROP else annotation_properties).add(about)
        elif el.tagName == T_EQUIV:
            for ch in el.childNodes:
                if ch.nodeType == ch.ELEMENT_NODE and ch.tagName == T_CLASS and _attr(ch, "rdf:about") is None:
                    equiv_anon += 1
        elif el.tagName == T_SCO:
            sco_total += 1
            enc = _enclosing(el)
            if enc is None:
                subj = "@none"
            else:
                subj = _attr(enc, "rdf:about") or f"@anonymous#{_num(enc)}"
            res = _attr(el, "rdf:resource")
            if res is not None:
                edges.append((subj, res))
            else:
                for ch in el.childNodes:
                    if ch.nodeType == ch.ELEMENT_NODE and ch.tagName == T_RESTR:
                        anon_objects.append((subj, f"@anonymous#{_num(ch)}"))
                        break
    doc.unlink()
    n_anon = anon_counter[0]

    # 命名空间判定（独立实现：urlsplit 取 netloc＋path）
    host = _host_of(ontology_about)
    dist = Counter(_dir_of(i) for i in named_classes if _host_of(i) == host)
    ns_dir = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    namespace = host + ns_dir
    named_set = set(named_classes)
    local_set = {i for i in named_set if i.startswith(namespace)}

    # 三档（成员资格语义）
    tier1 = [(s, o) for s, o in edges if s in local_set and o in local_set]
    tier2 = [(s, o) for s, o in edges if s in local_set and o not in local_set]
    tier3 = [(s, o) for s, o in edges if s not in local_set]

    # 全图（具名主语边）与本地子图
    children = {}
    subj_any = set()
    for s, o in edges:
        if s.startswith("@"):
            continue
        children.setdefault(o, []).append(s)
        subj_any.add(s)
    # 「任何 subClassOf 主语」含匿名宾语档：anon_objects 的具名主语也要计入
    for s, _ in anon_objects:
        if not s.startswith("@"):
            subj_any.add(s)
    roots = sorted(c for c in named_set if c not in subj_any)
    local_children = {}
    local_parented = set()
    for s, o in edges:
        if s in local_set and o in local_set:
            local_children.setdefault(o, []).append(s)
            local_parented.add(s)

    return {
        "ontology_about": ontology_about, "host": host, "ns_dir": ns_dir,
        "namespace": namespace, "ns_dir_dist": dict(dist),
        "named_set": named_set, "local_set": local_set,
        "edges": edges, "anon_objects": anon_objects, "sco_total": sco_total,
        "tier1": tier1, "tier2": tier2, "tier3": tier3,
        "object_properties": sorted(object_properties),
        "annotation_properties": sorted(annotation_properties),
        "anon_nodes_total": n_anon, "equiv_anon_classes": equiv_anon,
        "children": children, "subj_any": subj_any, "roots": roots,
        "local_children": local_children,
    }


def _compute_depths(nodes, parents):
    """各节点到根（无父者）的最长路径边数。迭代后序（显式栈），环由「同边只走一次」断开。

    parents: child -> [parent, ...]（沿 subClassOf 下行的逆方向累计深度）。
    """
    memo = {}
    for start in nodes:
        if start in memo:
            continue
        stack = [[start, iter(parents.get(start, [])), frozenset(), 0]]
        while stack:
            frame = stack[-1]
            cur, it, seen = frame[0], frame[1], frame[2]
            descended = False
            for p in it:
                if (p, cur) in seen:
                    continue  # 环：同边只走一次
                if p in memo:
                    frame[3] = max(frame[3], 1 + memo[p])
                    continue
                stack.append([p, iter(parents.get(p, [])), seen | {(p, cur)}, 0])
                descended = True
                break
            if descended:
                continue
            memo[cur] = frame[3]
            stack.pop()
            if stack:
                stack[-1][3] = max(stack[-1][3], 1 + memo[cur])
    return memo


def max_depth_from_roots(data, targets):
    """L5 主口径：全图根（不作任何 subClassOf 主语的具名类）下行到最远本地类的边数。"""
    parents = {}
    for s, o in data["edges"]:
        if not s.startswith("@"):
            parents.setdefault(s, []).append(o)
    memo = _compute_depths(list(targets), parents)
    return max((memo.get(c, 0) for c in targets), default=0)


def max_depth_local_subgraph(data):
    """L5 另一读法：本地子图（只走两端皆本地的边；起点＝无本地父类的本地类）。"""
    local = data["local_set"]
    parents = {}
    for s, o in data["edges"]:
        if s in local and o in local:
            parents.setdefault(s, []).append(o)
    memo = _compute_depths(sorted(local), parents)
    return max(memo.values(), default=0)


def leaf_local(data):
    """L6 主口径：本地类中无本地子类者。"""
    return sum(1 for c in data["local_set"] if not data["local_children"].get(c))


def leaf_with_external(data):
    """L6 另一读法：外部子类也算子类。"""
    return sum(1 for c in data["local_set"] if not data["children"].get(c))


def recount_l2_streaming(path):
    """L2 复核遍历（另一次、独立机制）：xml.dom.pulldom 流式事件逐事件计数。"""
    from xml.dom import pulldom
    total = 0
    with_res = 0
    for event, node in pulldom.parse(str(path)):
        if event == pulldom.START_ELEMENT and node.tagName == T_SCO:
            total += 1
            if node.getAttribute("rdf:resource"):
                with_res += 1
    return total, with_res


def contrast_hits(path, params=None):
    """三个对照读法（题面 §7.4 禁法留痕）：按件实算，独立实现。"""
    data = scan(path)
    ns_strip = data["ontology_about"].rsplit("/", 1)[0] + "/"
    hits_strip = len({i for i in data["named_set"] if i.startswith(ns_strip)})
    hits_bcio = len({
        i for i in data["named_set"]
        if urlsplit(i).path.rsplit("/", 1)[-1].startswith("BCIO_")
    })
    dist = Counter(_host_of(i) + _dir_of(i) for i in data["named_set"])
    top_prefix, hits_top = sorted(dist.items(), key=lambda kv: (-kv[1], kv[0]))[0]
    return {
        "strip_filename": {"namespace": ns_strip, "hits": hits_strip},
        "prefix_BCIO_": {"hits": hits_bcio},
        "most_frequent_prefix": {"prefix": top_prefix, "hits": hits_top},
    }


def overlap_local_sets(this_path, peer_path, params=None):
    """本件与对照件各自按同一主口径判定的本地类集三组差值。"""
    this = scan(this_path)["local_set"]
    peer = scan(peer_path)["local_set"]
    return {
        "both": sorted(this & peer),
        "only_in_this": sorted(this - peer),
        "only_in_peer": sorted(peer - this),
    }
