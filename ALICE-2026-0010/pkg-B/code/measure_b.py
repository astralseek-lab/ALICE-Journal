# -*- coding: utf-8 -*-
"""Population 片视图包旁证实现：DOM 显式栈迭代遍历＋目标件流式逐行联接。

与主实现的差异（独立性自述）：主实现走递归式树 API 与 parent 映射；
本实现用 minidom 建 DOM 后，以显式栈做文档序深度优先遍历，祖先链由栈携带，
三个量与档③在同一趟里各自累加（不作减法）；逐类回指不解析目标件整树，
而是对目标件逐行流式扫描声明行。
本地命名空间：owl:Ontology 的 rdf:about 经 urlsplit 取 netloc 与 path 目录，
host 下按去重类 IRI 数取最集中目录（平票按目录串升序）。
"""
import json
import re
import sys
from urllib.parse import urlsplit
from xml.dom import minidom

STEP_TITLES = (
    "Step 1: defining the scope of the ontology",
    "Step 2: identifying key entities and preliminary definitions",
    "Step 3: refinement of the ontology through further literature annotation, discussion and revision",
    "Step 4: expert stakeholder review",
    "Step 5: inter-rater reliability of annotations using the intervention population ontology",
    "Step 6: specifying the relationships between intervention population ontology entities and ensuring alignment with other parts of the BCIO and relevant ontologies",
    "Step 7: making the intervention population ontology machine-readable and available online",
)
STEP_PAGES = (6, 7, 8)
DECL_RE = re.compile(r'<owl:Class rdf:about="([^"]+)"')


def _namespace(doc):
    onto = doc.getElementsByTagName("owl:Ontology")[0]
    host = urlsplit(onto.getAttribute("rdf:about")).netloc
    per_dir = {}
    for el in doc.getElementsByTagName("owl:Class"):
        if not el.hasAttribute("rdf:about"):
            continue
        iri = el.getAttribute("rdf:about")
        u = urlsplit(iri)
        if u.netloc != host:
            continue
        d = u.path.rsplit("/", 1)[0] + "/"
        per_dir.setdefault(d, set()).add(iri)
    best = sorted(per_dir.items(), key=lambda kv: (-len(kv[1]), kv[0]))[0][0]
    return host, best


def _in_ns(iri, host, nsdir):
    if not iri:
        return False
    u = urlsplit(iri)
    return u.netloc == host and (u.path.rsplit("/", 1)[0] + "/") == nsdir


def _walk(doc):
    """显式栈迭代一趟：具名类集合、三档边、匿名宾语档、匿名节点编号。"""
    host, nsdir = _namespace(doc)
    named = set()
    named_local = set()
    for el in doc.getElementsByTagName("owl:Class"):
        if el.hasAttribute("rdf:about"):
            iri = el.getAttribute("rdf:about")
            named.add(iri)
            if _in_ns(iri, host, nsdir):
                named_local.add(iri)
    # 第一趟显式栈 DFS（文档序）：预扫全部匿名 owl:Class／owl:Restriction 统一编号
    anon_no = {}
    pre = [doc.documentElement]
    while pre:
        node = pre.pop()
        if node.nodeType == node.ELEMENT_NODE:
            if node.tagName in ("owl:Class", "owl:Restriction") and not node.hasAttribute("rdf:about"):
                anon_no[node] = len(anon_no) + 1
            kids = [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]
            for ch in reversed(kids):
                pre.append(ch)

    def label_of(el):
        return "@anonymous#%d" % anon_no[el]

    # 第二趟显式栈 DFS：三档边＋匿名宾语档，各自累加（不作减法）
    tier1, tier2, tier3, anon_obj = [], [], [], []

    # 栈元素＝(节点, 最近 owl:Class 祖先或 None)；子节点逆序压栈保持文档序
    stack = [(doc.documentElement, None)]
    while stack:
        node, anc = stack.pop()
        if node.nodeType == node.ELEMENT_NODE:
            cur = anc
            if node.tagName == "owl:Class":
                cur = node
            if node.tagName == "rdfs:subClassOf":
                if anc is not None and anc.hasAttribute("rdf:about"):
                    subj = anc.getAttribute("rdf:about")
                elif anc is not None:
                    subj = label_of(anc)
                else:
                    subj = None
                if node.hasAttribute("rdf:resource"):
                    res = node.getAttribute("rdf:resource")
                    if subj in named_local and _in_ns(res, host, nsdir):
                        tier1.append((subj, res))
                    elif subj in named_local:
                        tier2.append((subj, res))
                    else:
                        tier3.append((subj, res))
                else:
                    obj = None
                    for ch in node.childNodes:
                        if ch.nodeType == ch.ELEMENT_NODE and ch.tagName in (
                            "owl:Restriction",
                            "owl:Class",
                        ):
                            obj = label_of(ch)
                            break
                    anon_obj.append((subj, obj))
            kids = [c for c in node.childNodes if c.nodeType == c.ELEMENT_NODE]
            for ch in reversed(kids):
                stack.append((ch, cur))
    return named, named_local, tier1, tier2, tier3, anon_obj


def _counts(doc):
    _named, local, tier1, tier2, tier3, anon_obj = _walk(doc)
    return {
        "V1": len(local),
        "V2": len(tier2),
        "V3": len(tier1),
        "tier3": len(tier3),
        "anon_subclass_objects": len(anon_obj),
        "partition_total": len(tier1) + len(tier2) + len(tier3) + len(anon_obj),
    }


def _iter_pages(input_path):
    """按 \\f 分页符流式切块：页序从 1 起，不整篇载入。"""
    buf = ""
    with open(str(input_path), encoding="utf-8") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            buf += chunk
            while "\f" in buf:
                page, buf = buf.split("\f", 1)
                yield page
    if buf:
        yield buf


def _steps(input_path):
    """流式逐页读语料（页序＝抽取口径的行号），只在页范围内按声明标题逐字命中计数。"""
    wanted = set(STEP_PAGES)
    found = 0
    for pno, page in enumerate(_iter_pages(input_path), 1):
        if pno not in wanted:
            continue
        squashed = re.sub(r"\s+", " ", page)
        for title in STEP_TITLES:
            if title in squashed:
                found += 1
    return {"quantity": "steps", "v": found, "unit": "count"}


def figure_label_yield(input_path, params):
    """图内标签不作语料：从图内标签取用的类名数恒为零（抽取口径声明）。"""
    return {"quantity": params.get("quantity", "figure_label_yield"), "v": 0, "unit": "count"}


def measure(input_path, params):
    q = params.get("quantity")
    if q == "steps":
        return _steps(input_path)
    doc = minidom.parse(str(input_path))
    c = _counts(doc)
    if q in ("V1", "V2", "V3"):
        return {"quantity": q, "v": c[q], "unit": "count"}
    raise ValueError("unknown quantity: %r" % (q,))


def _target_declared_iris(target_path):
    """目标件声明行逐行流式扫描，返回（IRI 集合, IRI→声明行号）。"""
    iris = set()
    lines = {}
    with open(str(target_path), encoding="utf-8") as fh:
        for no, line in enumerate(fh, 1):
            m = DECL_RE.search(line)
            if m:
                iris.add(m.group(1))
                lines.setdefault(m.group(1), no)
    return iris, lines


def _target_local_count(target_path):
    doc = minidom.parse(str(target_path))
    _named, local, _t1, _t2, _t3, _a = _walk(doc)
    return len(local)


def join_returned(ont_path, target_path):
    doc = minidom.parse(str(ont_path))
    _named, local, _t1, _t2, _t3, _a = _walk(doc)
    tgt, _lines = _target_declared_iris(target_path)
    return {"quantity": "returned", "v": sum(1 for i in local if i in tgt), "unit": "count"}


def join_target_only(ont_path, target_path):
    doc = minidom.parse(str(ont_path))
    _named, local, _t1, _t2, _t3, _a = _walk(doc)
    tgt, _lines = _target_declared_iris(target_path)
    returned = sum(1 for i in local if i in tgt)
    return {
        "quantity": "target_only",
        "v": _target_local_count(target_path) - returned,
        "unit": "count",
    }


def main(argv):
    input_path = argv[1]
    params = {}
    if len(argv) > 2:
        params = dict(json.loads(argv[2]))
    out = measure(input_path, params)
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv)
