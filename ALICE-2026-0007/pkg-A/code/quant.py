"""ALICE-2026-0007 pkg-A · 六量主实现（xml.etree.ElementTree，递归遍历）。

链的可信不靠它永不变，靠它变了会响。

六个固定入口（题面 §九 给定名）：
    l1_local_classes / l2_subclass_edges / l3_object_properties /
    l4_annotation_properties / l5_max_depth / l6_leaf_classes
每个入口收一个 OWL 文件路径，返回 {"v": <整数>}。

口径（题面 §二，写死）：
  L1  有 rdf:about 且 IRI 落在本地命名空间的 owl:Class，按 IRI 去重；
      本地命名空间＝宿主（owl:Ontology@rdf:about 的 netloc）＋该类最集中的目录。
  L2  全件 rdfs:subClassOf@rdf:resource 三元组，按条计、不去重；
      宾语为匿名 owl:Restriction 的写法不带 @rdf:resource，不进 L2。
  L3  owl:ObjectProperty 按 IRI 去重，全件计（含外部内联声明）。
  L4  owl:AnnotationProperty 按 IRI 去重，全件计。
  L5  起点＝全图根（owl:Class 中不作任何 subClassOf 主语者，含外部顶层类），
      沿 subClassOf 下行（宾语＝父类、主语＝子类），深度＝到最远本地类的边数；
      环由「同边只走一次」断开。
  L6  本地类中无本地子类者（只看「本地→本地」的边；子类＝边的主语）。
"""

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from urllib.parse import urlsplit

RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL_NS = "http://www.w3.org/2002/07/owl#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"
ABOUT = "{%s}about" % RDF_NS
RESOURCE = "{%s}resource" % RDF_NS
T_CLASS = "{%s}Class" % OWL_NS
T_RESTRICTION = "{%s}Restriction" % OWL_NS
T_SUBCLASS = "{%s}subClassOf" % RDFS_NS
T_OBJPROP = "{%s}ObjectProperty" % OWL_NS
T_ANNPROP = "{%s}AnnotationProperty" % OWL_NS
T_ONTOLOGY = "{%s}Ontology" % OWL_NS


def _read_root(input_path):
    """解析 OWL 文件，返回根元素。"""
    return ET.parse(str(input_path)).getroot()


def _ontology_iri(root):
    """owl:Ontology 元素的 rdf:about（本体自述 IRI）。"""
    ont = root.find(T_ONTOLOGY)
    if ont is None:
        raise ValueError("缺 owl:Ontology 元素")
    return ont.get(ABOUT)


def _named_class_iris(root):
    """全件带 rdf:about 的 owl:Class 的 IRI 列表（文档序，含重复）。"""
    return [c.get(ABOUT) for c in root.iter(T_CLASS) if c.get(ABOUT)]


def local_namespace(root):
    """主口径命名空间判定：宿主＋最集中目录，一次算主值。

    宿主取自 owl:Ontology@rdf:about 的 netloc；在宿主相同的类 IRI 里
    取最集中的那一层目录（去末段后的目录前缀）作为本地命名空间。
    返回 (host, ns_prefix, local_iris_set)。
    """
    ont_iri = _ontology_iri(root)
    host = urlsplit(ont_iri).netloc
    iris = set(_named_class_iris(root))
    hosted = [i for i in iris if urlsplit(i).netloc == host]
    dirs = Counter(i.rsplit("/", 1)[0] + "/" for i in hosted)
    if not dirs:
        return host, "", set()
    ns = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return host, ns, {i for i in iris if i.startswith(ns)}


def _subclass_edges(root):
    """全件 subClassOf 边清单（按条计、不去重）。

    返回三元组列表 (subject_iri, object_iri_or_None, anon_object_element_or_None)。
    主体＝沿祖先链最近的带 rdf:about 的 owl:Class；宾语为匿名
    owl:Restriction／owl:Class 时 object 为 None、第三槽给该匿名元素。
    """
    parent = {c: p for p in root.iter() for c in p}

    def enclosing(el):
        cur = parent.get(el)
        while cur is not None:
            if cur.tag == T_CLASS and cur.get(ABOUT):
                return cur.get(ABOUT)
            cur = parent.get(cur)
        return None

    edges = []
    for s in root.iter(T_SUBCLASS):
        subj = enclosing(s)
        if subj is None:
            continue
        obj = s.get(RESOURCE)
        anon = None
        if obj is None:
            for ch in s:
                if ch.tag in (T_RESTRICTION, T_CLASS):
                    anon = ch
                    break
        edges.append((subj, obj, anon))
    return edges


def _named_edges(root):
    """只取宾语带 rdf:resource 的边（主, 宾）。"""
    return [(a, b) for a, b, _anon in _subclass_edges(root) if b]


def l1_local_classes(input_path):
    """L1：本地命名空间内的具名 owl:Class 数（按 IRI 去重）。"""
    root = _read_root(input_path)
    _host, _ns, local = local_namespace(root)
    return {"v": len(local)}


def l2_subclass_edges(input_path):
    """L2：全件 rdfs:subClassOf@rdf:resource 三元组数（按条计）。"""
    root = _read_root(input_path)
    return {"v": len(_named_edges(root))}


def l3_object_properties(input_path):
    """L3：owl:ObjectProperty 按 IRI 去重、全件计。"""
    root = _read_root(input_path)
    iris = {p.get(ABOUT) for p in root.iter(T_OBJPROP) if p.get(ABOUT)}
    return {"v": len(iris)}


def l4_annotation_properties(input_path):
    """L4：owl:AnnotationProperty 按 IRI 去重、全件计。"""
    root = _read_root(input_path)
    iris = {p.get(ABOUT) for p in root.iter(T_ANNPROP) if p.get(ABOUT)}
    return {"v": len(iris)}


def l5_max_depth(input_path):
    """L5：全图根沿 subClassOf 下行到最远本地类的边数。"""
    root = _read_root(input_path)
    named = set(_named_class_iris(root))
    _host, _ns, local = local_namespace(root)
    edges = _subclass_edges(root)
    subjects_any = {a for a, _b, _an in edges}
    children = defaultdict(list)
    for a, b, _an in edges:
        if b:
            children[b].append(a)
    roots = sorted(i for i in named if i not in subjects_any)
    best = {}

    def dfs(node, depth, seen_edges):
        if depth > best.get(node, -1):
            best[node] = depth
        for ch in children.get(node, []):
            edge = (ch, node)
            if edge in seen_edges:
                continue  # 环由「同边只走一次」断开
            dfs(ch, depth + 1, seen_edges | {edge})

    for r in roots:
        dfs(r, 0, frozenset())
    return {"v": max((best.get(i, 0) for i in local), default=0)}


def l6_leaf_classes(input_path):
    """L6：本地类中无本地子类者（只看「本地→本地」的边）。"""
    root = _read_root(input_path)
    _host, _ns, local = local_namespace(root)
    edges = _named_edges(root)
    has_local_child = {b for a, b in edges if a in local and b in local}
    return {"v": len([i for i in local if i not in has_local_child])}


# ── 另报与对照（非 K 量；供 emit 层调用）────────────────────────────────


def alt_readings(root):
    """题面 §二.3 的七条另报中由 OWL 件算出的全部读数。"""
    named = set(_named_class_iris(root))
    _host, ns, local = local_namespace(root)
    edges = _subclass_edges(root)
    res_edges = [(a, b) for a, b, _an in edges if b]

    op_all = {p.get(ABOUT) for p in root.iter(T_OBJPROP) if p.get(ABOUT)}
    ap_all = {p.get(ABOUT) for p in root.iter(T_ANNPROP) if p.get(ABOUT)}

    # L5_alt：只走两端皆本地的边，起点＝本地类中无本地父类者
    lchildren = defaultdict(list)
    lparents = defaultdict(list)
    for a, b in res_edges:
        if a in local and b in local:
            lchildren[b].append(a)
            lparents[a].append(b)
    lroots = sorted(i for i in local if not lparents.get(i))
    best = {}

    def dfs(node, depth, seen_edges):
        if depth > best.get(node, -1):
            best[node] = depth
        for ch in lchildren.get(node, []):
            edge = (ch, node)
            if edge in seen_edges:
                continue
            dfs(ch, depth + 1, seen_edges | {edge})

    for r in lroots:
        dfs(r, 0, frozenset())
    l5_alt = max(best.values(), default=0)

    # L5_selfcheck：本地类中无任何父类者（不作任何 subClassOf 主语）
    subjects_any = {a for a, _b, _an in edges}
    l5_selfcheck = len([i for i in local if i not in subjects_any])

    # L6_alt：外部子类也算子类时的叶类数
    has_any_named_child = {b for a, b in res_edges}
    l6_alt = len([i for i in local if i not in has_any_named_child])

    # 匿名 owl:Class：全树计；另一读法＝直接子节点（父元素即 owl:Class）中不带 rdf:about 者
    anon_classes = [c for c in root.iter(T_CLASS) if not c.get(ABOUT)]
    parent = {c: p for p in root.iter() for c in p}
    anon_direct = [c for c in anon_classes if parent.get(c) is not None and parent[c].tag == T_CLASS]

    return {
        "L3_local": len([i for i in op_all if i.startswith(ns)]),
        "L4_local": len([i for i in ap_all if i.startswith(ns)]),
        "L5_alt": l5_alt,
        "L5_selfcheck": l5_selfcheck,
        "L6_alt": l6_alt,
        "anonymous_class": len(anon_classes),
        "anonymous_class_direct": len(anon_direct),
    }


def tier_partition(root):
    """L2 三档＋匿名宾语档（同一次遍历分出）。

    返回 (tier1, tier2, tier3, anon_objects, partition_total)：
    tier1 两端皆本地；tier2 主体本地·宾语外部；tier3 其余（本件＝主体外部）；
    anon_objects＝宾语为匿名 owl:Restriction／owl:Class 的 (主体, 匿名元素) 清单；
    partition_total＝全件 subClassOf 元素总数（逐元素计）。
    """
    _host, _ns, local = local_namespace(root)
    edges = _subclass_edges(root)
    tier1, tier2, tier3, anon_objects = [], [], [], []
    for subj, obj, anon in edges:
        if obj is not None:
            if subj in local and obj in local:
                tier1.append((subj, obj))
            elif subj in local:
                tier2.append((subj, obj))
            else:
                tier3.append((subj, obj))
        else:
            anon_objects.append((subj, anon))
    return tier1, tier2, tier3, anon_objects, len(edges)


def anonymous_node_numbers(root):
    """匿名节点编号：按文档序对无 rdf:about 的 owl:Class 与 owl:Restriction
    统一从 1 起连续编号；返回 {id(element): n}。"""
    numbers = {}
    n = 0
    for el in root.iter():
        if el.tag in (T_CLASS, T_RESTRICTION) and not el.get(ABOUT):
            n += 1
            numbers[id(el)] = n
    return numbers


def deepest_local_chain(root):
    """L5 最深链：从全图根到最远本地类的链；并列最深时取链节点 IRI
    字典序最小的那条。返回 (深度, [节点 IRI 链])。"""
    named = set(_named_class_iris(root))
    _host, _ns, local = local_namespace(root)
    edges = _subclass_edges(root)
    subjects_any = {a for a, _b, _an in edges}
    children = defaultdict(list)
    for a, b, _an in edges:
        if b:
            children[b].append(a)
    roots = sorted(i for i in named if i not in subjects_any)
    best = {}

    def dfs(node, depth, path, seen_edges):
        cur = best.get(node)
        if cur is None or depth > cur[0] or (depth == cur[0] and tuple(path) < tuple(cur[1])):
            best[node] = (depth, list(path))
        for ch in sorted(children.get(node, [])):
            edge = (ch, node)
            if edge in seen_edges:
                continue
            dfs(ch, depth + 1, path + [ch], seen_edges | {edge})

    for r in roots:
        dfs(r, 0, [r], frozenset())
    reachable = [i for i in local if i in best]
    if not reachable:
        return 0, []
    maxdepth = max(best[i][0] for i in reachable)
    deepest = min((i for i in reachable if best[i][0] == maxdepth), key=lambda i: tuple(best[i][1]))
    return best[deepest][0], best[deepest][1]


def ns_contrast_readings(input_path, params):
    """三个对照读法（题面 §7.4 留痕，不作判据）：
    reading ∈ {strip_filename, prefix_BCIO, most_frequent_prefix}。
    返回 {"v": 该读法下的类数}。"""
    root = _read_root(input_path)
    iris = set(_named_class_iris(root))
    reading = (params or {}).get("reading", "")
    if reading == "strip_filename":
        ont = _ontology_iri(root)
        ns = ont.rsplit("/", 1)[0] + "/"
        return {"v": len([i for i in iris if i.startswith(ns)])}
    if reading == "prefix_BCIO":
        return {"v": len([i for i in iris if re.split(r"[/#]", i)[-1].startswith("BCIO_")])}
    if reading == "most_frequent_prefix":
        pref = Counter(re.split(r"[/#]", i)[-1].split("_")[0] for i in iris)
        top = sorted(pref.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        return {"v": len([i for i in iris if re.split(r"[/#]", i)[-1].split("_")[0] == top])}
    raise ValueError("未知对照读法：%r" % reading)


def peer_local_classes(input_path):
    """对照件自己的本地类集（按它自己的宿主＋最集中目录规则）。"""
    root = _read_root(input_path)
    _host, _ns, local = local_namespace(root)
    return {"v": len(local), "iris": sorted(local)}
