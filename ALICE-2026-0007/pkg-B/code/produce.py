"""ALICE-2026-0007 第二实现包 · 证据件／偏差件独立生成器。

每一件产物由本文件现场从输入件重算写出；不读取、不引用另一实现包的任何件
（路径一律用 os.path.join 拼装，源码里不出现其他包的件路径字面）。

链的可信不靠它永不变，靠它变了会响。
"""

import hashlib
import json
import os
import re
from pathlib import Path

import metrics

TASK_ID = "ALICE-2026-0007"
PAPER = "paper_text.txt"
OWL = "bcio_source.owl"
PEERS = {"0005": "bcio_upper_level.owl", "0008": "bcio_style.owl"}
EVD = "evidence"
DEV = "deviations"

# 行分类口径（para_lines）：节标题逐字集合＋`Step ` 起头行＋`Table ` 起头行＋表题下一行
# （表头行）为非 p 行；其余为 p 行。
SECTION_HEADINGS = {
    "Introduction", "Methods", "Results", "Discussion", "Strengths and limitations",
    "Conclusion", "Data availability", "Underlying data", "Extended data",
    "Software availability", "Acknowledgements", "Funding Statement", "References",
}

STEP_TITLES = [
    "Step 1 – Development of the scope and definition of the Intervention Source Ontology",
    "Step 2 – Identifying key entities and developing the preliminary Intervention Source Ontology",
    "Step 3 – Refining the ontology through literature annotation, discussion and revision",
    "Step 4 – Expert stakeholder review",
    "Step 5 – Inter-rater reliability of annotations using the Intervention Source Ontology",
    "Step 6 – Specifying relationships between Intervention Source Ontology entities",
    "Step 7 – Disseminating and maintaining the Intervention Source Ontology",
]

ANCHOR_HEADS = {
    "A01": "The preliminary version 0.1 ontology of the Intervention Source Ontology encompassed",
    "A02": "Version 0.2 of the Intervention Source Ontology as a result of these refinements had",
    "A03": "Version 0.3 of the Intervention Source Ontology as a result of these expert stakeholder recommendations had",
}

ENTRY_NAMES = {
    "L1": "l1_local_classes", "L2": "l2_subclass_edges", "L3": "l3_object_properties",
    "L4": "l4_annotation_properties", "L5": "l5_max_depth", "L6": "l6_leaf_classes",
}


def _canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _set_block(keys):
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(sorted(keys))]
    return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}


def _map_block(pairs):
    items = [{"key": k, "value": v} for k, v in sorted(pairs.items())]
    return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}


def _scalar(name, value):
    payload = {"name": name, "kind": "scalar", "value": value}
    return {"name": name, "kind": "scalar", "sha256": _canon_sha(payload), "value": value}


def _paper_lines(research_dir):
    return (Path(research_dir) / PAPER).read_text(encoding="utf-8").splitlines()


def corpus_stats(input_path):
    """行统计（本包独立分类实现）：总行数／p 行数／主文 body 序位（口径常量 1，
    母件 XML 未随包投递，按规则取文档序第一个 <body>）。"""
    lines = Path(str(input_path)).read_text(encoding="utf-8").splitlines()
    para = 0
    for i, ln in enumerate(lines):
        if ln in SECTION_HEADINGS or ln.startswith("Step ") or ln.startswith("Table "):
            continue
        if i > 0 and lines[i - 1].startswith("Table "):
            continue
        para += 1
    return {"lines": len(lines), "para_lines": para, "body_ordinal": 1}


def detect_steps(research_dir):
    """独立切节：先找 Methods 与 Results 两个节标题的整行位置，再按位置取
    其间连续的七个 Step 小节；不按标题去重（区外同形重列天然不进区间）。"""
    lines = _paper_lines(research_dir)
    i_methods = next(i + 1 for i, ln in enumerate(lines) if ln == "Methods")
    i_results = next(i + 1 for i, ln in enumerate(lines) if ln == "Results")
    titles = [(i + 1, ln) for i, ln in enumerate(lines)
              if i_methods < i + 1 < i_results and re.match(r"^Step [1-9]", ln)]
    assert len(titles) == 7, f"区间内 Step 标题数 {len(titles)} ≠ 7"
    out = []
    for pos, (ln_no, title) in enumerate(titles, 1):
        end = (titles[pos][0] - 1) if pos < 7 else (i_results - 1)
        assert title == STEP_TITLES[pos - 1], f"第 {pos} 步标题不符：{title!r}"
        out.append((pos, title, ln_no, end))
    return out


def find_anchors(research_dir):
    """十三锚独立定位：数值锚 source 只到 #L<行>，句序进 locator。"""
    lines = _paper_lines(research_dir)
    scan = metrics.scan_ontology(Path(research_dir) / OWL)
    rows = []

    def grab_int(aid, head, marker):
        hits = [i + 1 for i, ln in enumerate(lines) if ln.startswith(head)]
        assert len(hits) == 1, f"{aid} 起头串命中 {len(hits)} 处"
        m = re.search(r"(\d[\d,]*)\s*" + re.escape(marker), lines[hits[0] - 1])
        assert m, f"{aid} 在行内找不到标记 {marker!r}"
        return {"id": aid, "value": int(m.group(1).replace(",", "")),
                "source": "%s#L%d" % (PAPER, hits[0]), "locator": "#s1"}

    rows.append(grab_int("A01", ANCHOR_HEADS["A01"], "unique entities"))
    rows.append(grab_int("A02", ANCHOR_HEADS["A02"], "unique entities"))
    rows.append(grab_int("A03", ANCHOR_HEADS["A03"], "-level hierarchical structure"))

    t1 = [i + 1 for i, ln in enumerate(lines) if ln.startswith("Table 1.")]
    t2 = [i + 1 for i, ln in enumerate(lines) if ln.startswith("Table 2.")]
    assert len(t1) == 1 and len(t2) == 1
    rows.append({"id": "A04", "value": lines[t1[0] - 1], "source": "%s#L%d" % (PAPER, t1[0])})
    rows.append({"id": "A05", "value": lines[t2[0] - 1], "source": "%s#L%d" % (PAPER, t2[0])})
    head_ln = t2[0] + 1
    rows.append({"id": "A06", "value": lines[head_ln - 1].split()[0], "source": "%s#L%d" % (PAPER, head_ln)})

    for aid, text in (("A07", "Methods"), ("A08", "Results"), ("A09", "Conclusion")):
        hits = [i + 1 for i, ln in enumerate(lines) if ln == text]
        assert len(hits) == 1, f"{aid} 节标题命中 {len(hits)} 处"
        rows.append({"id": aid, "value": text, "source": "%s#L%d" % (PAPER, hits[0])})

    for aid, title in (("A10", STEP_TITLES[0]), ("A11", STEP_TITLES[6])):
        hits = [i + 1 for i, ln in enumerate(lines) if ln == title]
        assert len(hits) == 1, f"{aid} 方法段名命中 {len(hits)} 处"
        rows.append({"id": aid, "value": title, "source": "%s#L%d" % (PAPER, hits[0])})

    ont_iri = scan["ontology_iri"]
    ver_iri = None
    dom = metrics.minidom.parse(str(Path(research_dir) / OWL))
    for el in dom.getElementsByTagName("owl:versionIRI"):
        ver_iri = el.getAttribute("rdf:resource")
        break
    assert ont_iri and ver_iri
    rows.append({"id": "A12", "value": ver_iri, "source": "%s#%s" % (OWL, ver_iri),
                 "locator": 'rdf:resource="%s"' % ver_iri})
    rows.append({"id": "A13", "value": ont_iri, "source": "%s#%s" % (OWL, ont_iri),
                 "locator": 'rdf:about="%s"' % ont_iri})
    return rows


def _entry_line_spans(code_path, entries):
    """读本包 code 源文件，算每个入口的 [def 行, 函数体末行]（1 起）。"""
    src = Path(code_path).read_text(encoding="utf-8").splitlines()
    out = {}
    for entry in entries:
        hits = [i for i, ln in enumerate(src, 1) if re.match(rf"\s*def {re.escape(entry)}\s*\(", ln)]
        assert len(hits) == 1, f"{entry} 的 def 出现 {len(hits)} 次"
        d = hits[0]
        indent = len(src[d - 1]) - len(src[d - 1].lstrip())
        end = d
        for i in range(d + 1, len(src) + 1):
            ln = src[i - 1]
            if not ln.strip():
                continue
            cur = len(ln) - len(ln.lstrip())
            if cur <= indent and not ln.lstrip().startswith("#"):
                break
            if not ln.lstrip().startswith("#"):
                end = i
        out[entry] = [d, end]
    return out


def _func_span(code_path, func):
    return _entry_line_spans(code_path, [func])[func]


def emit_artifacts(research_dir, pkg_dir, only):
    """生成单件产物（only＝包内相对路径的两段名，如 ('evidence','ns.json')）。"""
    research_dir, pkg_dir = Path(research_dir), Path(pkg_dir)
    if isinstance(only, str):
        only = tuple(only.split("/"))
    rel = os.path.join(*only)
    owl_path = research_dir / OWL
    scan = metrics.scan_ontology(owl_path)
    host, ns, local = metrics.determine_local_namespace(scan)
    l1 = len(local)
    l5 = metrics.l5_max_depth(owl_path)["v"]
    code_file = os.path.join("code", "metrics.py")
    metrics_path = pkg_dir / code_file

    if rel == os.path.join(EVD, "ns.json"):
        named = sorted(set(scan["named_classes"]))
        prefix_iris = sorted(i for i in named if re.split(r"[/#]", i)[-1].startswith("BCIO_"))
        in_ns = {i for i in named if i.startswith(metrics.determine_local_namespace(scan)[1])}
        sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
        f0, f1 = _func_span(metrics_path, "determine_local_namespace")
        doc = {
            "rule": ("宿主＋最集中目录：owl:Ontology@rdf:about 以 urlsplit 取 netloc，"
                     "再取宿主内类 IRI 的 path 目录计数最集中者；实现 %s#L%d-L%d" % (code_file, f0, f1)),
            "host": host,
            "dir": ns,
            "count": len(in_ns),
            "prefix_count": len(prefix_iris),
            "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
            "classes": [{"iri": i, "in_ns": i in in_ns} for i in named],
            "prefix_iris": prefix_iris,
        }
    elif rel == os.path.join(EVD, "anchors.json"):
        doc = find_anchors(research_dir)
    elif rel == os.path.join(EVD, "protocol.json"):
        io_text = [
            ("dictionaries and the TIDieR reporting guidelines",
             "A definition and overall topic for the ontology"),
            ("100 published reports of behaviour change interventions",
             "An initial prototype version of the ontology"),
            ("120 behaviour change intervention evaluation reports",
             "the ontology structure, definitions and annotation guidance were revised accordingly"),
            ("123 members of an existing international panel",
             "the Intervention Source Ontology and annotation guidance were revised"),
            ("50 papers from Cochrane reviews",
             "Inter-rater reliability was assessed using Krippendorff’s Alpha"),
            ("Basic Formal Ontology principles",
             "relationships between ontology entities to formalise the knowledge present in the ontology"),
            ("a table of entities",
             "Web Ontology Language (OWL)"),
        ]
        plines = _paper_lines(research_dir)
        steps = []
        for (pos, title, ln0, ln1), (inp, outp) in zip(detect_steps(research_dir), io_text):
            seg = "\n".join(plines[ln0 - 1:ln1])
            assert inp in seg and outp in seg, f"第 {pos} 步片段不在行段内"
            steps.append({
                "pos": pos, "label": "S%d" % pos, "title": title, "src": PAPER, "kind": "line",
                "target": "%s#L%d-L%d" % (PAPER, ln0, ln1),
                "evidence_loc": "%s#L%d-L%d" % (PAPER, ln0, ln0),
                "input": inp, "output": outp,
            })
        doc = {
            "rule": "先列 Methods 下全部标题，再按位置取前七个 Step 小节；禁用标题去重",
            "source": "%s#L11-L27" % PAPER,
            "steps": steps,
        }
    elif rel == os.path.join(EVD, "entries.json"):
        spans = _entry_line_spans(metrics_path, list(ENTRY_NAMES.values()))
        doc = {k: {"file": code_file, "entry": n, "lines": spans[n]}
               for k, n in ENTRY_NAMES.items()}
    elif rel == os.path.join(EVD, "independence.json"):
        doc = {
            "entry": code_file,
            "shared_code_with_a": False,
            "signer_pkg_id": "pkg-B",
            "source": ("独立第二实现：minidom 解析＋显式栈迭代＋流式一次过计数＋urlsplit 划界；"
                       "全程不读取、不引用另一实现包的任何件，六量与全部产物由本包 code 现场重算"),
        }
    elif rel == os.path.join(DEV, "tiers.json"):
        t1, t2, t3, anon_objs, total = metrics.tier_partition(scan)
        anon_no = metrics.anonymous_numbers(scan)
        doc = {
            "tier1": _set_block(["%s|%s" % (a, b) for a, b in t1]),
            "tier2": _set_block(["%s|%s" % (a, b) for a, b in t2]),
            "tier3": _set_block(["%s|%s" % (a, b) for a, b in t3]),
            "anon_subclass_objects": _set_block(
                ["%s|@anonymous#%d" % (a, anon_no[id(el)]) for a, el in anon_objs]),
            "readings_alt": _map_block({"partition_total": total}),
        }
    elif rel == os.path.join(DEV, "overlap.json"):
        peers = {}
        for pid, fname in PEERS.items():
            p_local = set(metrics.peer_local_classes(research_dir / fname)["iris"])
            peers[pid] = {
                "both": _set_block(local & p_local),
                "only_in_this": _set_block(local - p_local),
                "only_in_peer": _set_block(p_local - local),
            }
        doc = {"peers": peers, "unavailable": []}
    elif rel == os.path.join(DEV, "contrast.json"):
        base_ont = scan["ontology_iri"]
        strip_ns = base_ont.rsplit("/", 1)[0] + "/"
        deriv = "主口径推导见 " + os.path.join(EVD, "ns.json") + " 的 host＋dir"
        rows = []
        for reading, label in (
            ("strip_filename", "rdf:about 去文件名（本体 IRI 去末段得 %s）" % strip_ns),
            ("prefix_BCIO", "前缀 BCIO_（类 IRI 本地名以 BCIO_ 起头）"),
            ("most_frequent_prefix", "出现最多的前缀（本地名首段计数降序取首，本件为 BCIO）"),
        ):
            hits = metrics.contrast_reading(owl_path, {"reading": reading})["v"]
            same = "与主值同值：巧合，不是判据；" if hits == l1 else ""
            rows.append({
                "rule": "%s：命中 %d 类（%s%s）" % (label, hits, same, deriv),
                "hits": hits,
                "derivation_ref": {"code": code_file, "entry": "contrast_reading",
                                   "params": {"reading": reading}},
            })
        doc = rows
    elif rel == os.path.join(DEV, "readings.json"):
        alt = metrics.alt_readings(scan)
        doc = [_scalar(name, alt[name]) for name in (
            "L3_local", "L4_local", "L5_alt", "L5_selfcheck",
            "L6_alt", "anonymous_class", "anonymous_class_direct")]
    elif only[0] == DEV and re.fullmatch(r"diff_A0[123]\.json", only[1]):
        aid = only[1][len("diff_"):-len(".json")]
        anchors = {r["id"]: r for r in find_anchors(research_dir)}
        if aid in ("A01", "A02"):
            measured = l1
            items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(sorted(local))]
        else:
            measured = l5 + 1
            _depth, chain = metrics.deepest_local_chain(scan)
            pairs = [(chain[i], chain[i - 1]) for i in range(1, len(chain))]
            items = [{"key": child, "ord": i + 1}
                     for i, (child, _parent) in enumerate(p for p in pairs if p[0] in local)]
        self_reported = anchors[aid]["value"]
        gap = measured - self_reported
        direction = "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等")
        doc = {
            "anchor": aid, "measured": measured, "self_reported": self_reported,
            "items": items, "rows": len(items), "gap": gap, "direction": direction,
        }
        doc["sha256"] = _canon_sha({k: doc[k] for k in ("anchor", "measured", "self_reported", "items")})
    else:
        raise ValueError("未知产物：%r" % (rel,))

    out = pkg_dir / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return rel


ARTIFACTS = [
    (EVD, "ns.json"), (EVD, "anchors.json"), (EVD, "protocol.json"), (EVD, "entries.json"),
    (DEV, "tiers.json"), (DEV, "overlap.json"), (DEV, "contrast.json"),
    (DEV, "readings.json"), (DEV, "diff_A01.json"), (DEV, "diff_A02.json"), (DEV, "diff_A03.json"),
]
B_ONLY_ARTIFACTS = [(EVD, "independence.json")]
