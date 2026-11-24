"""ALICE-2026-0007 pkg-A · 证据件／偏差件生成器（A-1 留痕入口）。

每件 evidence/ 与 deviations/ 产物都由 emit_artifacts 的一个分支写出；
evidence.graph.json 里对应 artifact 节点的 transform 指到本文件的同一行。

链的可信不靠它永不变，靠它变了会响。
"""

import hashlib
import json
import re
from pathlib import Path

import quant

TASK_ID = "ALICE-2026-0007"
PAPER = "paper_text.txt"
OWL = "bcio_source.owl"
PEERS = {"0005": "bcio_upper_level.owl", "0008": "bcio_style.owl"}

# paper_text.txt 行分类口径（para_lines）：节标题＝下行集合逐字匹配；
# 步骤标题＝`Step ` 起头行；表题＝`Table ` 起头行；表头行＝表题的下一行；其余为 p 行。
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


def _canon_sha(payload):
    """载荷的规范 sha256（sort_keys＋紧凑分隔符＋UTF-8 不转义）。"""
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _set_block(keys):
    """set 型装载：items[{key,ord}]（key 升序）＋ rows ＋ sha256（载荷＝items）。"""
    items = [{"key": k, "ord": i + 1} for i, k in enumerate(sorted(keys))]
    return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}


def _map_block(pairs):
    """map 型装载：items[{key,value}]（key 升序）＋ rows ＋ sha256（载荷＝items）。"""
    items = [{"key": k, "value": v} for k, v in sorted(pairs.items())]
    return {"items": items, "rows": len(items), "sha256": _canon_sha(items)}


def _scalar(name, value):
    payload = {"name": name, "kind": "scalar", "value": value}
    return {"name": name, "kind": "scalar", "sha256": _canon_sha(payload), "value": value}


def _paper_lines(research_dir):
    return (Path(research_dir) / PAPER).read_text(encoding="utf-8").splitlines()


def corpus_stats(input_path):
    """paper_text.txt 的行统计：总行数／p 行数／主文 body 序位。

    body_ordinal：母件 JATS XML 未随包投递，按范围单附三规则只取文档序第一个
    <body>（主文），其出现序号恒为 1——故此处为口径常量而非读数。
    """
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
    """按位置取七步：Methods 标题行之后、Results 标题行之前的连续 Step 小节。

    禁用标题去重（Results 内同形重列不在范围内，天然不计）。
    返回 [(pos, title, title_ln, end_ln)]，行号 1 起。
    """
    lines = _paper_lines(research_dir)
    i_methods = lines.index("Methods") + 1
    i_results = lines.index("Results") + 1
    titles = [(i + 1, ln) for i, ln in enumerate(lines) if i + 1 > i_methods and i + 1 < i_results and ln.startswith("Step ")]
    assert len(titles) == 7, f"Methods 内 Step 标题数 {len(titles)} ≠ 7"
    out = []
    for pos, (ln_no, title) in enumerate(titles, 1):
        end = (titles[pos][0] - 1) if pos < 7 else (i_results - 1)
        assert title == STEP_TITLES[pos - 1], f"第 {pos} 步标题与题面 §4.1 表不符：{title!r}"
        out.append((pos, title, ln_no, end))
    return out


def find_anchors(research_dir):
    """13 锚定位与取值（数值锚的 source 只到 #L<行>，句序进 locator）。"""
    lines = _paper_lines(research_dir)
    owl_root = quant._read_root(Path(research_dir) / OWL)
    rows = []

    def grab_int(aid, head, marker):
        hits = [i + 1 for i, ln in enumerate(lines) if ln.startswith(head)]
        assert len(hits) == 1, f"{aid} 起头串命中 {len(hits)} 处"
        ln = lines[hits[0] - 1]
        m = re.search(r"(\d[\d,]*)\s*" + re.escape(marker), ln)
        assert m, f"{aid} 在行内找不到标记 {marker!r}"
        return {"id": aid, "value": int(m.group(1).replace(",", "")),
                "source": f"{PAPER}#L{hits[0]}", "locator": "#s1"}

    rows.append(grab_int("A01", ANCHOR_HEADS["A01"], "unique entities"))
    rows.append(grab_int("A02", ANCHOR_HEADS["A02"], "unique entities"))
    rows.append(grab_int("A03", ANCHOR_HEADS["A03"], "-level hierarchical structure"))

    t1 = [i + 1 for i, ln in enumerate(lines) if ln.startswith("Table 1.")]
    t2 = [i + 1 for i, ln in enumerate(lines) if ln.startswith("Table 2.")]
    assert len(t1) == 1 and len(t2) == 1
    rows.append({"id": "A04", "value": lines[t1[0] - 1], "source": f"{PAPER}#L{t1[0]}"})
    rows.append({"id": "A05", "value": lines[t2[0] - 1], "source": f"{PAPER}#L{t2[0]}"})
    head_ln = t2[0] + 1
    rows.append({"id": "A06", "value": lines[head_ln - 1].split()[0], "source": f"{PAPER}#L{head_ln}"})

    for aid, text in (("A07", "Methods"), ("A08", "Results"), ("A09", "Conclusion")):
        hits = [i + 1 for i, ln in enumerate(lines) if ln == text]
        assert len(hits) == 1, f"{aid} 节标题命中 {len(hits)} 处"
        rows.append({"id": aid, "value": text, "source": f"{PAPER}#L{hits[0]}"})

    for aid, title in (("A10", STEP_TITLES[0]), ("A11", STEP_TITLES[6])):
        hits = [i + 1 for i, ln in enumerate(lines) if ln == title]
        assert len(hits) == 1, f"{aid} 方法段名命中 {len(hits)} 处"
        rows.append({"id": aid, "value": title, "source": f"{PAPER}#L{hits[0]}"})

    ont_iri = quant._ontology_iri(owl_root)
    ver_iri = owl_root.find(quant.T_ONTOLOGY).find("{%s}versionIRI" % quant.OWL_NS).get(quant.RESOURCE)
    rows.append({"id": "A12", "value": ver_iri, "source": f"{OWL}#{ver_iri}",
                 "locator": f'rdf:resource="{ver_iri}"'})
    rows.append({"id": "A13", "value": ont_iri, "source": f"{OWL}#{ont_iri}",
                 "locator": f'rdf:about="{ont_iri}"'})
    return rows


def _entry_line_spans(code_path, entries):
    """读 code 源文件，给每个入口函数算 [def 行, 函数体末行]（1 起）。"""
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
    """生成单件 evidence/ 或 deviations/ 产物。返回写出的相对路径。"""
    research_dir, pkg_dir = Path(research_dir), Path(pkg_dir)
    owl_path = research_dir / OWL
    root = quant._read_root(owl_path)
    host, ns, local = quant.local_namespace(root)
    l1 = quant.l1_local_classes(owl_path)["v"]
    l5 = quant.l5_max_depth(owl_path)["v"]
    quant_path = pkg_dir / "code" / "quant.py"

    if only == "evidence/ns.json":
        named = sorted(set(quant._named_class_iris(root)))
        prefix_iris = sorted(i for i in named if re.split(r"[/#]", i)[-1].startswith("BCIO_"))
        in_ns = {i for i in named if i.startswith(ns)}
        sym = sorted(in_ns.symmetric_difference(set(prefix_iris)))
        f0, f1 = _func_span(quant_path, "local_namespace")
        doc = {
            "rule": (f"宿主＋最集中目录：owl:Ontology@rdf:about 取宿主（netloc），"
                     f"再取宿主内类 IRI 最集中目录作本地命名空间；实现 code/quant.py#L{f0}-L{f1}"),
            "host": host,
            "dir": ns,
            "count": len(in_ns),
            "prefix_count": len(prefix_iris),
            "coincidence": {"equal": len(sym) == 0, "sym_diff": sym},
            "classes": [{"iri": i, "in_ns": i in in_ns} for i in named],
            "prefix_iris": prefix_iris,
        }
    elif only == "evidence/anchors.json":
        doc = find_anchors(research_dir)
    elif only == "evidence/protocol.json":
        steps = []
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
        for (pos, title, ln0, ln1), (inp, outp) in zip(detect_steps(research_dir), io_text):
            seg = "\n".join(plines[ln0 - 1:ln1])
            assert inp in seg and outp in seg, f"第 {pos} 步 input/output 片段不在行段内"
            steps.append({
                "pos": pos, "label": f"S{pos}", "title": title, "src": PAPER, "kind": "line",
                "target": f"{PAPER}#L{ln0}-L{ln1}",
                "evidence_loc": f"{PAPER}#L{ln0}-L{ln0}",
                "input": inp, "output": outp,
            })
        doc = {
            "rule": "先列 Methods 下全部标题，再按位置取前七个 Step 小节；禁用标题去重",
            "source": f"{PAPER}#L11-L27",
            "steps": steps,
        }
    elif only == "evidence/entries.json":
        names = ["l1_local_classes", "l2_subclass_edges", "l3_object_properties",
                 "l4_annotation_properties", "l5_max_depth", "l6_leaf_classes"]
        spans = _entry_line_spans(quant_path, names)
        doc = {k: {"file": "code/quant.py", "entry": n, "lines": spans[n]}
               for k, n in zip(("L1", "L2", "L3", "L4", "L5", "L6"), names)}
    elif only == "deviations/tiers.json":
        t1, t2, t3, anon_objs, total = quant.tier_partition(root)
        anon_no = quant.anonymous_node_numbers(root)
        doc = {
            "tier1": _set_block([f"{a}|{b}" for a, b in t1]),
            "tier2": _set_block([f"{a}|{b}" for a, b in t2]),
            "tier3": _set_block([f"{a}|{b}" for a, b in t3]),
            "anon_subclass_objects": _set_block(
                [f"{a}|@anonymous#{anon_no[id(el)]}" for a, el in anon_objs]),
            "readings_alt": _map_block({"partition_total": total}),
        }
    elif only == "deviations/overlap.json":
        peers = {}
        for pid, fname in PEERS.items():
            p_local = set(quant.peer_local_classes(research_dir / fname)["iris"])
            both = local & p_local
            peers[pid] = {
                "both": _set_block(both),
                "only_in_this": _set_block(local - p_local),
                "only_in_peer": _set_block(p_local - local),
            }
        doc = {"peers": peers, "unavailable": []}
    elif only == "deviations/contrast.json":
        ont = quant._ontology_iri(root)
        strip_ns = ont.rsplit("/", 1)[0] + "/"
        rows = [
            ("strip_filename",
             f"rdf:about 去文件名：本体 IRI 去末段得 {strip_ns}，按前缀隶属计 "
             f"{quant.ns_contrast_readings(owl_path, {'reading': 'strip_filename'})['v']} 类"
             f"（与主值同值：巧合，不是判据；主口径推导见 evidence/ns.json 的 host＋dir）"),
            ("prefix_BCIO",
             f"前缀 BCIO_：类 IRI 本地名以 BCIO_ 起头者计 "
             f"{quant.ns_contrast_readings(owl_path, {'reading': 'prefix_BCIO'})['v']} 类"
             f"（与主值同值：巧合，不是判据；主口径推导见 evidence/ns.json 的 host＋dir）"),
            ("most_frequent_prefix",
             f"出现最多的前缀：本地名首段（_ 前）计数降序取首为 BCIO，命中 "
             f"{quant.ns_contrast_readings(owl_path, {'reading': 'most_frequent_prefix'})['v']} 类"
             f"（与主值同值：巧合，不是判据；主口径推导见 evidence/ns.json 的 host＋dir）"),
        ]
        doc = [{"rule": rule,
                "hits": quant.ns_contrast_readings(owl_path, {"reading": r})["v"],
                "derivation_ref": {"code": "code/quant.py", "entry": "ns_contrast_readings",
                                   "params": {"reading": r}}}
               for r, rule in rows]
    elif only == "deviations/readings.json":
        alt = quant.alt_readings(root)
        doc = [_scalar(name, alt[name]) for name in (
            "L3_local", "L4_local", "L5_alt", "L5_selfcheck",
            "L6_alt", "anonymous_class", "anonymous_class_direct")]
    elif only in ("deviations/diff_A01.json", "deviations/diff_A02.json", "deviations/diff_A03.json"):
        aid = only[len("deviations/diff_"):-len(".json")]
        anchors = {r["id"]: r for r in find_anchors(research_dir)}
        if aid in ("A01", "A02"):
            measured = l1
            items = [{"key": iri, "ord": i + 1} for i, iri in enumerate(sorted(local))]
        else:
            # 层级数同尺：实测端＝L5＋1；items＝最深链上子类为本地的边（key＝子类 IRI）
            measured = l5 + 1
            _depth, chain = quant.deepest_local_chain(root)
            edges_on_chain = [(chain[i], chain[i - 1]) for i in range(1, len(chain))]
            items = [{"key": child, "ord": i + 1}
                     for i, (child, _parent) in enumerate(e for e in edges_on_chain if e[0] in local)]
        self_reported = anchors[aid]["value"]
        gap = measured - self_reported
        direction = "实测多" if gap > 0 else ("自报多" if gap < 0 else "相等")
        doc = {
            "anchor": aid, "measured": measured, "self_reported": self_reported,
            "items": items, "rows": len(items), "gap": gap, "direction": direction,
        }
        doc["sha256"] = _canon_sha({k: doc[k] for k in ("anchor", "measured", "self_reported", "items")})
    else:
        raise ValueError(f"未知产物：{only}")

    out = pkg_dir / only
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return only


ARTIFACTS = [
    "evidence/ns.json", "evidence/anchors.json", "evidence/protocol.json", "evidence/entries.json",
    "deviations/tiers.json", "deviations/overlap.json", "deviations/contrast.json",
    "deviations/readings.json", "deviations/diff_A01.json", "deviations/diff_A02.json",
    "deviations/diff_A03.json",
]
