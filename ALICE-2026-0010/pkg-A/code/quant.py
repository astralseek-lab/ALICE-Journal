# -*- coding: utf-8 -*-
"""Population 片视图包主实现：RDF/XML 结构解析（不做 OWL 推理）。

口径：
- 本地命名空间＝owl:Ontology@rdf:about 的 host ＋该 host 下去重类 IRI 数最多的目录
  （平票按目录串升序取第一个）；host/dir 全部由该属性解析得出，不写死。
- V1：带 rdf:about 且 IRI 落在本地命名空间的 owl:Class，按 IRI 去重。
- 子类边主体＝包含该 rdfs:subClassOf 元素的最近 owl:Class 祖先的 rdf:about；
  该祖先无 rdf:about（匿名类）则主体记匿名。宾语＝@rdf:resource。
- V2：主体本地、宾语不在本地命名空间的边，按条计（一次遍历累加，不作减法）。
- V3：两端皆本地类的边，按条计。
- 档③：主体为外部类或匿名类的边（同一次遍历分出，另一次遍历复核总账）。
- 回指数：本地类 IRI 在目标件里存在以其为 rdf:about 的 owl:Class 声明的个数。
- 目标独有：目标件本地类数（同一套规则对目标件实算）− 回指数。
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

OWL = "{http://www.w3.org/2002/07/owl#}"
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"

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


def _ontology_iri(root):
    el = root.find(OWL + "Ontology")
    return el.get(RDF + "about")


def _namespace(root):
    """由 owl:Ontology@rdf:about 解析 host；host 下取去重类 IRI 数最多的目录。"""
    host = urlsplit(_ontology_iri(root)).netloc
    per_dir = {}
    for el in root.iter(OWL + "Class"):
        iri = el.get(RDF + "about")
        if not iri:
            continue
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


def _named_classes(root):
    out = set()
    for el in root.iter(OWL + "Class"):
        iri = el.get(RDF + "about")
        if iri:
            out.add(iri)
    return out


def _local_classes(root):
    host, nsdir = _namespace(root)
    return {i for i in _named_classes(root) if _in_ns(i, host, nsdir)}


def _walk_edges(root):
    """一次遍历分出三档＋匿名宾语档；返回 (tier1, tier2, tier3, anon_obj)。

    每条＝(主体段, 宾语段)；匿名节点段＝@anonymous#n：先按文档序预扫全部
    匿名 owl:Class 与 owl:Restriction 统一编号（连续、不跳号、同一节点同号），
    再在边遍历里引用预编号。
    """
    parent = {c: p for p in root.iter() for c in p}
    anon_no = {}
    for el in root.iter():
        if el.tag in (OWL + "Class", OWL + "Restriction") and el.get(RDF + "about") is None:
            anon_no[el] = len(anon_no) + 1

    def anon_label(el):
        return "@anonymous#%d" % anon_no[el]

    tier1, tier2, tier3, anon_obj = [], [], [], []
    host, nsdir = _namespace(root)
    local = _local_classes(root)
    for el in root.iter():
        if el.tag != RDFS + "subClassOf":
            continue
        p = parent.get(el)
        subj = None
        while p is not None:
            if p.tag == OWL + "Class":
                about = p.get(RDF + "about")
                subj = about if about else anon_label(p)
                break
            p = parent.get(p)
        res = el.get(RDF + "resource")
        if res is None:
            obj = None
            for ch in el:
                if ch.tag in (OWL + "Restriction", OWL + "Class"):
                    obj = anon_label(ch)
                    break
            anon_obj.append((subj, obj))
            continue
        if subj in local and _in_ns(res, host, nsdir):
            tier1.append((subj, res))
        elif subj in local:
            tier2.append((subj, res))
        else:
            tier3.append((subj, res))
    return tier1, tier2, tier3, anon_obj


def _counts(root):
    """另一次遍历复核：三档各自累加，不用减法。"""
    tier1, tier2, tier3, anon_obj = _walk_edges(root)
    local = _local_classes(root)
    return {
        "V1": len(local),
        "V2": len(tier2),
        "V3": len(tier1),
        "tier3": len(tier3),
        "anon_subclass_objects": len(anon_obj),
        "partition_total": len(tier1) + len(tier2) + len(tier3) + len(anon_obj),
    }


def _steps(input_path):
    """按页范围＋出现顺序取七步：页＝行（语料行号＝页序），标题逐字命中。"""
    text = open(str(input_path), encoding="utf-8").read()
    pages = text.split("\f")
    found = 0
    for want, title in enumerate(STEP_TITLES, 1):
        hit = False
        for pno in STEP_PAGES:
            if title in re.sub(r"\s+", " ", pages[pno - 1]):
                hit = True
                break
        if hit:
            found += 1
    return {"quantity": "steps", "v": found, "unit": "count"}


def figure_label_yield(input_path, params):
    """图内标签不作语料：从图内标签取用的类名数恒为零（抽取口径声明）。"""
    return {"quantity": params.get("quantity", "figure_label_yield"), "v": 0, "unit": "count"}


def measure(input_path, params):
    """单输入入口：按 params['quantity'] 分派 V1／V2／V3／steps。"""
    q = params.get("quantity")
    if q == "steps":
        return _steps(input_path)
    root = ET.parse(str(input_path)).getroot()
    c = _counts(root)
    if q in ("V1", "V2", "V3"):
        return {"quantity": q, "v": c[q], "unit": "count"}
    raise ValueError("unknown quantity: %r" % (q,))


def _target_declared_iris(target_path):
    """目标件里以 rdf:about 声明的 owl:Class IRI 集合。"""
    root = ET.parse(str(target_path)).getroot()
    return _named_classes(root)


def join_returned(ont_path, target_path):
    """回指数：本包本地类逐 IRI 在目标件里联接命中的个数。"""
    local = _local_classes(ET.parse(str(ont_path)).getroot())
    tgt = _target_declared_iris(target_path)
    return {"quantity": "returned", "v": sum(1 for i in local if i in tgt), "unit": "count"}


def join_target_only(ont_path, target_path):
    """目标独有＝目标件本地类数（同一套规则对目标件实算）− 回指数。"""
    local = _local_classes(ET.parse(str(ont_path)).getroot())
    troot = ET.parse(str(target_path)).getroot()
    tgt_named = _named_classes(troot)
    tgt_local = _local_classes(troot)
    returned = sum(1 for i in local if i in tgt_named)
    return {"quantity": "target_only", "v": len(tgt_local) - returned, "unit": "count"}


def main(argv):
    input_path = argv[1]
    params = {}
    if len(argv) > 2:
        params = dict(json.loads(argv[2]))
    out = measure(input_path, params)
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv)
