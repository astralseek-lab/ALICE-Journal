"""ALICE-2026-0007 第二实现包 · 六量独立实现。

技术选型（与主实现包不同源）：xml.dom.minidom 解析；遍历用显式栈迭代，不用递归；
计数流式一次过；IRI 划界用 urlsplit 拆 netloc＋path 独立判定；命名空间主口径按本包
自己的判定函数独立算一次，三个对照读法另算留痕（不作判据）。

链的可信不靠它永不变，靠它变了会响。

六个固定入口（题面 §九 给定名）：
    l1_local_classes / l2_subclass_edges / l3_object_properties /
    l4_annotation_properties / l5_max_depth / l6_leaf_classes
每个入口收一个 OWL 文件路径，返回 {"v": <整数>}。
"""

import re
from collections import Counter, defaultdict
from urllib.parse import urlsplit
from xml.dom import minidom

CLASS_TAG = "owl:Class"
RESTRICTION_TAG = "owl:Restriction"
SUBCLASS_TAG = "rdfs:subClassOf"
OBJPROP_TAG = "owl:ObjectProperty"
ANNPROP_TAG = "owl:AnnotationProperty"
ONTOLOGY_TAG = "owl:Ontology"
ABOUT_ATTR = "rdf:about"
RESOURCE_ATTR = "rdf:resource"


def _iter_elems(root_elem):
    """显式栈的先序迭代（文档序）；不用递归。"""
    stack = [root_elem]
    while stack:
        node = stack.pop()
        yield node
        kids = [k for k in node.childNodes if k.nodeType == k.ELEMENT_NODE]
        stack.extend(reversed(kids))


def _enclosing_class_iri(node):
    """沿 parentNode 链向上找最近的带 rdf:about 的 owl:Class。"""
    cur = node.parentNode
    while cur is not None and getattr(cur, "nodeType", None) == cur.ELEMENT_NODE:
        if cur.tagName == CLASS_TAG and cur.hasAttribute(ABOUT_ATTR):
            return cur.getAttribute(ABOUT_ATTR)
        cur = cur.parentNode
    return None


def scan_ontology(input_path):
    """流式一次过扫描：单趟走完 DOM，同时落下全部原始计数与记录。

    返回 dict：
      ontology_iri      本体自述 IRI
      named_classes     具名类 IRI（文档序列表，含重复声明）
      anon_nodes        匿名节点（无 rdf:about 的 owl:Class／owl:Restriction，文档序）
      anon_classes      其中的匿名 owl:Class（含其父元素标签）
      edges             subClassOf 记录 (主体 IRI, 宾语 IRI 或 None, 匿名子节点或 None)
      obj_props         ObjectProperty 的 rdf:about 列表
      ann_props         AnnotationProperty 的 rdf:about 列表
    """
    dom = minidom.parse(str(input_path))
    out = {
        "ontology_iri": None, "named_classes": [], "anon_nodes": [],
        "anon_classes": [], "edges": [], "obj_props": [], "ann_props": [],
    }
    for el in _iter_elems(dom.documentElement):
        tag = el.tagName
        if tag == ONTOLOGY_TAG and out["ontology_iri"] is None:
            out["ontology_iri"] = el.getAttribute(ABOUT_ATTR)
        elif tag == CLASS_TAG:
            if el.hasAttribute(ABOUT_ATTR):
                out["named_classes"].append(el.getAttribute(ABOUT_ATTR))
            else:
                out["anon_nodes"].append(el)
                out["anon_classes"].append(el)
        elif tag == RESTRICTION_TAG:
            if not el.hasAttribute(ABOUT_ATTR):
                out["anon_nodes"].append(el)
        elif tag == SUBCLASS_TAG:
            subj = _enclosing_class_iri(el)
            if subj is None:
                continue
            obj = el.getAttribute(RESOURCE_ATTR) or None
            anon = None
            if obj is None:
                for kid in el.childNodes:
                    if kid.nodeType == kid.ELEMENT_NODE and kid.tagName in (RESTRICTION_TAG, CLASS_TAG):
                        anon = kid
                        break
            out["edges"].append((subj, obj, anon))
        elif tag == OBJPROP_TAG:
            if el.hasAttribute(ABOUT_ATTR):
                out["obj_props"].append(el.getAttribute(ABOUT_ATTR))
        elif tag == ANNPROP_TAG:
            if el.hasAttribute(ABOUT_ATTR):
                out["ann_props"].append(el.getAttribute(ABOUT_ATTR))
    return out


def determine_local_namespace(scan):
    """主口径（本包独立实现）：宿主＝本体 IRI 的 netloc；在 netloc 相同的类 IRI 里，
    按 urlsplit 的 path 目录取计数最集中者作本地命名空间。一次算主值。"""
    host = urlsplit(scan["ontology_iri"]).netloc
    iris = set(scan["named_classes"])
    dirs = Counter()
    for iri in iris:
        parts = urlsplit(iri)
        if parts.netloc == host:
            dirs[parts.path.rsplit("/", 1)[0] + "/"] += 1
    if not dirs:
        return host, "", set()
    ns = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    ns_full = "%s://%s%s" % (urlsplit(scan["ontology_iri"]).scheme, host, ns)
    return host, ns_full, {i for i in iris if i.startswith(ns_full)}


def _named_edges(scan):
    return [(a, b) for a, b, _anon in scan["edges"] if b]


def l1_local_classes(input_path):
    """L1：本地命名空间内的具名 owl:Class 数（按 IRI 去重）。"""
    scan = scan_ontology(input_path)
    _host, _ns, local = determine_local_namespace(scan)
    return {"v": len(local)}


def l2_subclass_edges(input_path):
    """L2：全件 rdfs:subClassOf@rdf:resource 三元组数（按条计、不去重）。"""
    scan = scan_ontology(input_path)
    return {"v": len(_named_edges(scan))}


def l3_object_properties(input_path):
    """L3：owl:ObjectProperty 按 IRI 去重、全件计。"""
    scan = scan_ontology(input_path)
    return {"v": len(set(scan["obj_props"]))}


def l4_annotation_properties(input_path):
    """L4：owl:AnnotationProperty 按 IRI 去重、全件计。"""
    scan = scan_ontology(input_path)
    return {"v": len(set(scan["ann_props"]))}


def _depth_map(children, roots):
    """显式栈求各节点自根起的最长边数；环由「同边只走一次」断开。"""
    best = {}
    for r in roots:
        stack = [(r, 0, frozenset())]
        while stack:
            node, depth, seen = stack.pop()
            if depth > best.get(node, -1):
                best[node] = depth
            for ch in children.get(node, []):
                edge = (ch, node)
                if edge in seen:
                    continue
                stack.append((ch, depth + 1, seen | {edge}))
    return best


def l5_max_depth(input_path):
    """L5：全图根（不作任何 subClassOf 主语的具名类）沿 subClassOf 下行
    到最远本地类的边数。"""
    scan = scan_ontology(input_path)
    named = set(scan["named_classes"])
    _host, _ns, local = determine_local_namespace(scan)
    subjects_any = {a for a, _b, _an in scan["edges"]}
    children = defaultdict(list)
    for a, b in _named_edges(scan):
        children[b].append(a)
    roots = sorted(named - subjects_any)
    best = _depth_map(children, roots)
    return {"v": max((best.get(i, 0) for i in local), default=0)}


def l6_leaf_classes(input_path):
    """L6：本地类中无本地子类者（只看「本地→本地」的边）。"""
    scan = scan_ontology(input_path)
    _host, _ns, local = determine_local_namespace(scan)
    has_local_child = {b for a, b in _named_edges(scan) if a in local and b in local}
    return {"v": len([i for i in local if i not in has_local_child])}


# ── 另报与对照（非 K 量；供产物生成层调用）─────────────────────────────


def alt_readings(scan):
    """七条另报中由 OWL 件算出的读数（本包独立口径实现）。"""
    _host, ns, local = determine_local_namespace(scan)
    res_edges = _named_edges(scan)

    lchildren = defaultdict(list)
    lparents = defaultdict(list)
    for a, b in res_edges:
        if a in local and b in local:
            lchildren[b].append(a)
            lparents[a].append(b)
    lroots = sorted(i for i in local if not lparents.get(i))
    l5_alt = max(_depth_map(lchildren, lroots).values(), default=0)

    subjects_any = {a for a, _b, _an in scan["edges"]}
    l5_selfcheck = len([i for i in local if i not in subjects_any])

    has_any_named_child = {b for a, b in res_edges}
    l6_alt = len([i for i in local if i not in has_any_named_child])

    anon_direct = 0
    for el in scan["anon_classes"]:
        p = el.parentNode
        if p is not None and getattr(p, "nodeType", None) == p.ELEMENT_NODE and p.tagName == CLASS_TAG:
            anon_direct += 1

    return {
        "L3_local": len([i for i in set(scan["obj_props"]) if i.startswith(ns)]),
        "L4_local": len([i for i in set(scan["ann_props"]) if i.startswith(ns)]),
        "L5_alt": l5_alt,
        "L5_selfcheck": l5_selfcheck,
        "L6_alt": l6_alt,
        "anonymous_class": len(scan["anon_classes"]),
        "anonymous_class_direct": anon_direct,
    }


def tier_partition(scan):
    """L2 三档＋匿名宾语档（单趟扫描后分档）。"""
    _host, _ns, local = determine_local_namespace(scan)
    tier1, tier2, tier3, anon_objects = [], [], [], []
    for subj, obj, anon in scan["edges"]:
        if obj is not None:
            if subj in local and obj in local:
                tier1.append((subj, obj))
            elif subj in local:
                tier2.append((subj, obj))
            else:
                tier3.append((subj, obj))
        else:
            anon_objects.append((subj, anon))
    return tier1, tier2, tier3, anon_objects, len(scan["edges"])


def anonymous_numbers(scan):
    """匿名节点编号：文档序统一从 1 起连续编号（扫描后统一回填，规避
    先序遍历父先于子导致子节点尚未编号的问题）。返回 {id(node): n}。"""
    return {id(el): i + 1 for i, el in enumerate(scan["anon_nodes"])}


def deepest_local_chain(scan):
    """L5 最深链（并列最深取链节点 IRI 字典序最小者）。返回 (深度, [节点链])。"""
    named = set(scan["named_classes"])
    _host, _ns, local = determine_local_namespace(scan)
    subjects_any = {a for a, _b, _an in scan["edges"]}
    children = defaultdict(list)
    for a, b in _named_edges(scan):
        children[b].append(a)
    roots = sorted(named - subjects_any)
    best = {}
    for r in roots:
        stack = [(r, 0, (r,), frozenset())]
        while stack:
            node, depth, path, seen = stack.pop()
            cur = best.get(node)
            if cur is None or depth > cur[0] or (depth == cur[0] and path < cur[1]):
                best[node] = (depth, path)
            for ch in sorted(children.get(node, [])):
                edge = (ch, node)
                if edge in seen:
                    continue
                stack.append((ch, depth + 1, path + (ch,), seen | {edge}))
    reachable = [i for i in local if i in best]
    if not reachable:
        return 0, []
    maxdepth = max(best[i][0] for i in reachable)
    deepest = min((i for i in reachable if best[i][0] == maxdepth), key=lambda i: best[i][1])
    return best[deepest][0], list(best[deepest][1])


def contrast_reading(input_path, params):
    """三个对照读法之一（§7.4 留痕，不作判据）：
    reading ∈ {strip_filename, prefix_BCIO, most_frequent_prefix}。"""
    scan = scan_ontology(input_path)
    iris = set(scan["named_classes"])
    reading = (params or {}).get("reading", "")
    if reading == "strip_filename":
        base = urlsplit(scan["ontology_iri"])
        ns = "%s://%s%s/" % (base.scheme, base.netloc, base.path.rsplit("/", 1)[0].lstrip("/"))
        return {"v": len([i for i in iris if i.startswith(ns)])}
    if reading == "prefix_BCIO":
        return {"v": len([i for i in iris if re.split(r"[/#]", i)[-1].startswith("BCIO_")])}
    if reading == "most_frequent_prefix":
        pref = Counter(re.split(r"[/#]", i)[-1].split("_")[0] for i in iris)
        top = sorted(pref.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return {"v": len([i for i in iris if re.split(r"[/#]", i)[-1].split("_")[0] == top])}
    raise ValueError("未知对照读法：%r" % reading)


def peer_local_classes(input_path):
    """对照件自己的本地类集（按它自己的宿主＋最集中目录规则独立判定）。"""
    scan = scan_ontology(input_path)
    _host, _ns, local = determine_local_namespace(scan)
    return {"v": len(local), "iris": sorted(local)}
