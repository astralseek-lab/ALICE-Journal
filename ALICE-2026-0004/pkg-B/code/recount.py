# -*- coding: utf-8 -*-
"""pkg-B 唯一入口件：HBO 视图包（ALICE-2026-0004）三量＋闸门量的第二次独立重算。

独立性自述（与 evidence/independence.json 一致）：
  · 解析族：xml.sax 流式事件解析，单次过文件，不建树、不用任何树型 API；
  · 遍历：事件流本身就是迭代；所在类用显式栈（list.append/pop）维护，无递归；
  · IRI 划界：urllib.parse.urlsplit 取 netloc＋path 独立判定，不串前缀；
  · 命名空间：host 取 owl:Ontology 的 rdf:about 的 netloc，dir 取该 host 下
    去重类 IRI 数最多的目录（平票按目录串升序），与任何邻包实现无关。
"""
import re
from collections import Counter
from urllib.parse import urlsplit
from xml.sax import make_parser, handler

STEP_PAGES = (8, 13)


class _Collector(handler.ContentHandler):
    """单次流式收集：本体 IRI、具名类、带 resource 的子类边、imports、label。"""

    def __init__(self):
        super().__init__()
        self.ontology_about = None
        self.named_classes = []        # 文档序（不去重，去重在判定层做）
        self.res_edges = []            # (主体 IRI 或 None, 宾语 IRI)
        self.anon_obj_edges = []       # (主体 IRI 或 None, 匿名节点序位)：宾语为匿名 Restriction
        self.anon_nodes = []           # 匿名节点文档序：("class"|"restriction",)
        self.imports_count = 0
        self.labels = []
        self._class_ctx = []           # 显式栈：所在 owl:Class 的 rdf:about（匿名压 None）
        self._anon_ctx = []            # 显式栈：所在匿名节点序位（具名类压 None）
        self._open_sub_no_res = None   # 无 rdf:resource 的 subClassOf 的主体
        self._in_label = False
        self._buf = []

    def startElement(self, name, attrs):
        if name == "owl:Ontology":
            self.ontology_about = attrs.get("rdf:about")
        elif name == "owl:imports":
            self.imports_count += 1
        elif name == "owl:Class":
            about = attrs.get("rdf:about")
            self._class_ctx.append(about)
            if about is not None:
                self.named_classes.append(about)
                self._anon_ctx.append(None)
            else:
                self.anon_nodes.append("class")
                self._anon_ctx.append(len(self.anon_nodes))
        elif name == "owl:Restriction":
            self.anon_nodes.append("restriction")
            if self._open_sub_no_res is not None:
                self.anon_obj_edges.append((self._open_sub_no_res, len(self.anon_nodes)))
        elif name == "rdfs:subClassOf":
            res = attrs.get("rdf:resource")
            subj = self._class_ctx[-1] if self._class_ctx else None
            if subj is None and self._anon_ctx and self._anon_ctx[-1] is not None:
                subj = "@anonymous#%d" % self._anon_ctx[-1]
            if res is not None:
                self.res_edges.append((subj, res))
            else:
                self._open_sub_no_res = subj
        elif name == "rdfs:label":
            self._in_label = True
            self._buf = []

    def characters(self, content):
        if self._in_label:
            self._buf.append(content)

    def endElement(self, name):
        if name == "owl:Class":
            if self._class_ctx:
                self._class_ctx.pop()
                self._anon_ctx.pop()
        elif name == "rdfs:subClassOf":
            self._open_sub_no_res = None
        elif name == "rdfs:label":
            self._in_label = False
            self.labels.append("".join(self._buf).strip())


def _collect(input_path):
    parser = make_parser()
    parser.setFeature(handler.feature_namespaces, False)
    col = _Collector()
    parser.setContentHandler(col)
    with open(str(input_path), "r", encoding="utf-8") as fh:
        parser.parse(fh)
    return col


def _namespace(col):
    host = urlsplit(col.ontology_about).netloc
    dirs = Counter()
    seen = set()
    for iri in col.named_classes:
        if iri in seen:
            continue
        seen.add(iri)
        u = urlsplit(iri)
        if u.netloc == host:
            dirs[u.path.rpartition("/")[0]] += 1
    best = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return host, best


def _local_set(col):
    host, dirn = _namespace(col)
    out = set()
    for iri in col.named_classes:
        u = urlsplit(iri)
        if u.netloc == host and u.path.rpartition("/")[0] == dirn:
            out.add(iri)
    return out


def recount_quantity(input_path, params):
    """入口：按 params["quantity"] 分派。三个量各走一次独立事件流。"""
    q = (params or {}).get("quantity")
    if q == "steps":
        spec = (params or {}).get("protocol_pages", "%d-%d" % STEP_PAGES)
        lo, _, hi = spec.partition("-")
        text = open(str(input_path), encoding="utf-8").read()
        segs = text.split("\f")
        face = "\f".join(segs[int(lo) - 1:int(hi)])
        order = []
        for m in re.finditer(r"Step (\d+):", face):
            num = int(m.group(1))
            if num not in order:
                order.append(num)
        if order != list(range(1, len(order) + 1)):
            raise ValueError("步号序列不连续：%r" % (order,))
        return {"quantity": q, "v": len(order), "unit": "count"}
    col = _collect(input_path)
    local = _local_set(col)
    if q == "V1":
        v = len(local)
    elif q in ("V2", "V3"):
        v = 0
        for subj, obj in col.res_edges:
            if subj in local:
                if q == "V2" and obj not in local:
                    v += 1
                elif q == "V3" and obj in local:
                    v += 1
    else:
        raise ValueError("未知 quantity：%r" % (q,))
    return {"quantity": q, "v": v, "unit": "count"}


def recount_returned(ontology_path, target_path):
    """闸门量：逐 IRI 联接，本包本地类出现在目标件具名类里的个数。"""
    local = _local_set(_collect(ontology_path))
    target_named = set(_collect(target_path).named_classes)
    v = 0
    for iri in local:
        if iri in target_named:
            v += 1
    return {"quantity": "returned", "v": v, "unit": "count"}


def recount_target_only(ontology_path, target_path):
    """派生量：目标件本地类数 − 回指数（两侧各自从事件流数出）。"""
    local = _local_set(_collect(ontology_path))
    target_col = _collect(target_path)
    target_local = _local_set(target_col)
    target_named = set(target_col.named_classes)
    v = 0
    for iri in target_local:
        if iri not in local or iri not in target_named:
            v += 1
    return {"quantity": "target_only", "v": v, "unit": "count"}


FIGURE_KEY_LABELS = (
    "human behaviour",
    "individual human behaviour",
    "individual human behaviour pattern",
    "individual human behaviour change",
    "population behaviour",
    "population behaviour pattern",
)


def recount_figure(input_path, params):
    """图题关键类：六个上层类名按 rdfs:label 逐字命中数（事件流收集的 label 集）。"""
    col = _collect(input_path)
    labels = set(col.labels)
    found = sorted(lb for lb in FIGURE_KEY_LABELS if lb in labels)
    return {"quantity": "figure_key_classes", "v": len(found), "unit": "count"}


def recount_contrast(input_path, params):
    """三个对照读法＋imports 空判定（对照值，不作判据；与主值同值纯属巧合）。"""
    rule = (params or {}).get("rule")
    col = _collect(input_path)
    named = []
    seen = set()
    for iri in col.named_classes:
        if iri not in seen:
            seen.add(iri)
            named.append(iri)
    if rule == "rdf_about_dir":
        # 对照读法①：rdf:about 去文件名当目录（禁法，只作对照）
        onto = urlsplit(col.ontology_about)
        host, dirn = onto.netloc, onto.path.rpartition("/")[0]
        hits = 0
        for iri in named:
            u = urlsplit(iri)
            if u.netloc == host and u.path.rpartition("/")[0] == dirn:
                hits += 1
    elif rule == "prefix_bcio":
        # 对照读法②：类名前缀 BCIO_（禁法，只作对照）
        hits = 0
        for iri in named:
            name = urlsplit(iri).path.rpartition("/")[2]
            if name.startswith("BCIO_"):
                hits += 1
    elif rule == "top_prefix":
        local = _local_set(col)
        prefs = Counter()
        for iri in local:
            name = urlsplit(iri).path.rpartition("/")[2]
            prefs[name.split("_", 1)[0]] += 1
        winner = sorted(prefs.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        hits = 0
        for iri in local:
            name = urlsplit(iri).path.rpartition("/")[2]
            if name.split("_", 1)[0] == winner:
                hits += 1
    elif rule == "imports_empty":
        hits = 1 if col.imports_count == 0 else 0
    else:
        raise ValueError("未知对照规则：%r" % (rule,))
    return {"quantity": "contrast_" + str(rule), "v": hits, "unit": "count"}
