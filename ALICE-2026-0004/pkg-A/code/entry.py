# -*- coding: utf-8 -*-
"""pkg-A 唯一入口件：HBO 视图包（ALICE-2026-0004）三个量＋闸门量＋派生量。

口径：只做 RDF/XML 结构解析，不做 OWL 推理，不联网，不手改输入。
解析族：xml.etree.ElementTree，递归遍历（本包允许）。
命名空间：host 取自 owl:Ontology@rdf:about 的 netloc；dir＝该 host 下唯一类 IRI
数最集中的目录（平票按目录串升序取第一）；「本地」＝IRI 的 netloc＝host 且
path 目录＝dir。本函数链上没有任何按类名前缀／按文件名的早退。
"""
import re
import xml.etree.ElementTree as ET
from collections import Counter
from urllib.parse import urlsplit

RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
OWL = "http://www.w3.org/2002/07/owl#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
ABOUT = "{%s}about" % RDF
RESOURCE = "{%s}resource" % RDF
T_CLASS = "{%s}Class" % OWL
T_SUB = "{%s}subClassOf" % RDFS
T_ONT = "{%s}Ontology" % OWL
T_IMPORTS = "{%s}imports" % OWL
T_LABEL = "{%s}label" % RDFS

STEP_PAGES = (8, 13)  # 声明块 pages=8-13：Methods 节的抽取面（页序＝行号）


def _root(input_path):
    return ET.parse(str(input_path)).getroot()


def namespace_of(root):
    """从 owl:Ontology@rdf:about 解析 host，再取该类 host 下类最集中的目录。"""
    ont = root.find(T_ONT)
    about = ont.get(ABOUT)
    host = urlsplit(about).netloc
    dirs = Counter()
    seen = set()
    for el in root.iter(T_CLASS):
        iri = el.get(ABOUT)
        if iri is None or iri in seen:
            continue
        seen.add(iri)
        u = urlsplit(iri)
        if u.netloc == host:
            dirs[u.path.rpartition("/")[0]] += 1
    best = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return host, best


def local_classes(root):
    """本包本地类：带 rdf:about 且落在本包命名空间的 owl:Class，按 IRI 去重。"""
    host, dirn = namespace_of(root)
    out = set()
    for el in root.iter(T_CLASS):
        iri = el.get(ABOUT)
        if iri is None:
            continue
        u = urlsplit(iri)
        if u.netloc == host and u.path.rpartition("/")[0] == dirn:
            out.add(iri)
    return out


def count_v2(root):
    """V2：主体本地、宾语非本地的 rdfs:subClassOf@rdf:resource 条数。

    一次独立遍历；过滤条件两段可读：cur in local（主体本地）且 res not in local
    （宾语非本地）；满足即累加 n += 1。不用全件总数减其他档反推。
    """
    local = local_classes(root)
    n = 0

    def walk(el, enclosing):
        nonlocal n
        cur = enclosing
        if el.tag == T_CLASS:
            cur = el.get(ABOUT)
        if el.tag == T_SUB:
            res = el.get(RESOURCE)
            if res is not None and cur in local and res not in local:
                n += 1
        for ch in el:
            walk(ch, cur)

    walk(root, None)
    return n


def count_v3(root):
    """V3：两端都是本地类的 rdfs:subClassOf@rdf:resource 条数（一次独立遍历，累加）。"""
    local = local_classes(root)
    n = 0

    def walk(el, enclosing):
        nonlocal n
        cur = enclosing
        if el.tag == T_CLASS:
            cur = el.get(ABOUT)
        if el.tag == T_SUB:
            res = el.get(RESOURCE)
            if res is not None and cur in local and res in local:
                n += 1
        for ch in el:
            walk(ch, cur)

    walk(root, None)
    return n


def count_steps(input_path, pages):
    """steps：声明页范围内 `Step N:` 的不同步号个数（按文档序去重，须成 1..n）。"""
    text = open(str(input_path), encoding="utf-8").read()
    segs = text.split("\f")
    lo, hi = pages
    face = "\f".join(segs[lo - 1:hi])
    order = []
    for m in re.finditer(r"Step (\d+):", face):
        num = int(m.group(1))
        if num not in order:
            order.append(num)
    if order != list(range(1, len(order) + 1)):
        raise ValueError("步号序列不是 1..n 连续：%r" % (order,))
    return len(order)


def quantity(input_path, params):
    """入口：按 params["quantity"] 分派，数放在键 v 上。"""
    q = (params or {}).get("quantity")
    if q == "V1":
        v = len(local_classes(_root(input_path)))
    elif q == "V2":
        v = count_v2(_root(input_path))
    elif q == "V3":
        v = count_v3(_root(input_path))
    elif q == "steps":
        spec = (params or {}).get("protocol_pages", "%d-%d" % STEP_PAGES)
        lo, _, hi = spec.partition("-")
        v = count_steps(input_path, (int(lo), int(hi)))
    else:
        raise ValueError("未知 quantity：%r" % (q,))
    return {"quantity": q, "v": v, "unit": "count"}


def returned(ontology_path, target_path):
    """闸门量 回指数：本包本地类里能在目标件里按 IRI 原样找到的个数（逐 IRI 联接）。"""
    local = local_classes(_root(ontology_path))
    target_root = _root(target_path)
    target_named = set()
    for el in target_root.iter(T_CLASS):
        iri = el.get(ABOUT)
        if iri is not None:
            target_named.add(iri)
    return {"quantity": "returned", "v": len(local & target_named), "unit": "count"}


def target_only(ontology_path, target_path):
    """派生量 目标独有：目标件本地类数 − 回指数（两侧各自数出）。"""
    local = local_classes(_root(ontology_path))
    target_root = _root(target_path)
    target_local = local_classes(target_root)
    hit = 0
    for iri in local:
        if iri in target_local:
            hit += 1
    return {"quantity": "target_only", "v": len(target_local) - hit, "unit": "count"}


# 图题（Figure 1）依据的 BCIO 关键类标签：来自摘要终版句的六个上层类名
FIGURE_KEY_LABELS = (
    "human behaviour",
    "individual human behaviour",
    "individual human behaviour pattern",
    "individual human behaviour change",
    "population behaviour",
    "population behaviour pattern",
)


def figure_key_classes(input_path, params):
    """图题关键类检索：六个上层类名各有几个能按 rdfs:label 逐字在本包类集合里找到。"""
    root = _root(input_path)
    labels = set()
    for el in root.iter(T_LABEL):
        if el.text:
            labels.add(el.text.strip())
    found = sorted(lb for lb in FIGURE_KEY_LABELS if lb in labels)
    return {"quantity": "figure_key_classes", "v": len(found), "unit": "count"}


def contrast_hits(input_path, params):
    """对照读法命中数（对照值，不作判据；与主值同值纯属巧合）。"""
    rule = (params or {}).get("rule")
    root = _root(input_path)
    named = []
    for el in root.iter(T_CLASS):
        iri = el.get(ABOUT)
        if iri is not None and iri not in named:
            named.append(iri)
    if rule == "rdf_about_dir":
        # 对照读法①：rdf:about 去文件名当目录（禁法，只作对照）
        about = root.find(T_ONT).get(ABOUT)
        base = about.rpartition("/")[0] + "/"
        hits = sum(1 for iri in named if iri.startswith(base))
    elif rule == "prefix_bcio":
        # 对照读法②：类名前缀 BCIO_（禁法，只作对照）
        hits = sum(
            1 for iri in named
            if urlsplit(iri).path.rpartition("/")[2].startswith("BCIO_")
        )
    elif rule == "top_prefix":
        # 对照读法③：出现最多的前缀（本地类名第一个 _ 之前段；禁法，只作对照）
        local = local_classes(root)
        prefs = Counter()
        for iri in local:
            name = urlsplit(iri).path.rpartition("/")[2]
            prefs[name.split("_", 1)[0]] += 1
        winner = sorted(prefs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        hits = sum(
            1 for iri in local
            if urlsplit(iri).path.rpartition("/")[2].split("_", 1)[0] == winner
        )
    elif rule == "imports_empty":
        # 对照判定④：owl:imports 元素数为空（成立记一条）
        hits = 1 if len(root.findall("%s/%s" % (T_ONT, T_IMPORTS))) == 0 else 0
    else:
        raise ValueError("未知对照规则：%r" % (rule,))
    return {"quantity": "contrast_" + str(rule), "v": hits, "unit": "count"}
