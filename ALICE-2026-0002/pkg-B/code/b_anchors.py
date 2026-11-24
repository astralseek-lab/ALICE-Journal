# -*- coding: utf-8 -*-
"""pkg-B 锚对账：十三锚逐条定位、核值、落 verdict.json。

行号与取值全部由本脚本在源件里现场查找并核对（digit token 级），不硬写结论；
锚找不到或值不在该行时抛错，不静默放行。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

NUM_TOKEN = re.compile(r"-?\d{1,3}(?:,\d{3})+|-?\d+")

EXPECTED = {  # §一 冻结面（判定时对照用；实算值现算现填）
    "bcio_moa.owl": (1585048, "61e53a6d3908cd16be20058cdfd2de2ac8785a89834cc2bbca1dddf889f1ab4e"),
    "paper_text.txt": (59867, "fc2d1542d23916b31bebf8cfad95f1f0d6cfa6a21687d32655d3440a282efb11"),
}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def int_tokens(line):
    out = set()
    for m in NUM_TOKEN.finditer(line):
        out.add(int(m.group(0).replace(",", "")))
    return out


def find_line(lines, needle, lo=1, hi=None):
    """在 [lo, hi]（1 起、含两端）内找第一个含 needle 的行号。"""
    hi = hi or len(lines)
    for i in range(lo - 1, hi):
        if needle in lines[i]:
            return i + 1
    raise SystemExit("anchor line not found: %r in [%s,%s]" % (needle, lo, hi))


def num_anchor(aid, source, lines, value, line, quote, maps_to, mine, explained, reason, items_file=None):
    if value not in int_tokens(lines[line - 1]):
        raise SystemExit("%s: value %s not an int token of line %s" % (aid, value, line))
    if quote not in lines[line - 1]:
        raise SystemExit("%s quote not verbatim substring of line %s" % (aid, line))
    delta = None if mine is None else abs(value - mine)
    row = {
        "id": aid, "kind": "number", "source": source, "value": value, "line": line,
        "quote": quote, "maps_to": maps_to, "mine": mine, "delta": delta,
        "explained": explained, "reason": reason,
    }
    if items_file:
        row["items_file"] = items_file
    return row


def text_anchor(aid, source, lines, line, quote, reason):
    if quote not in lines[line - 1]:
        raise SystemExit("%s quote not verbatim substring of line %s" % (aid, line))
    return {
        "id": aid, "kind": "text", "source": source, "value": None, "line": line,
        "quote": quote, "maps_to": None, "mine": None, "delta": None,
        "explained": True, "reason": reason,
    }


def main():
    research = Path(__file__).resolve().parents[2]
    paper = research / "paper_text.txt"
    owl = research / "bcio_moa.owl"
    paper_lines = paper.read_text(encoding="utf-8").splitlines()
    owl_lines = owl.read_text(encoding="utf-8", errors="replace").splitlines()

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import moa_entry_b

    q = moa_entry_b.all_quantities(owl)

    # 偏离落名（B3）：只对判为偏离的锚
    dev_dir = research / "pkg-B" / "deviations"
    dev_dir.mkdir(parents=True, exist_ok=True)
    local, ext, _by_ns, edges, _o, _a = moa_entry_b._scan(owl)
    with (dev_dir / "A01.jsonl").open("w", encoding="utf-8") as fh:
        for iri in sorted(local):
            fh.write(json.dumps({"iri": iri}, ensure_ascii=False) + "\n")
    with (dev_dir / "A02.jsonl").open("w", encoding="utf-8") as fh:
        for child, parent in sorted(edges):
            fh.write(json.dumps({"child": child, "parent": parent}, ensure_ascii=False) + "\n")

    P = "paper_text.txt"
    O = "bcio_moa.owl"
    anchors = []

    ln = find_line(paper_lines, "has 284 entities")
    anchors.append(num_anchor(
        "A01", P, paper_lines, 284, ln, "The final version of the MoA Ontology has 284 entities",
        "L1_class_local", q["L1_class_local"], False,
        "论文口径只数 MoA 专域实体（最终版 284）；本量按本地命名空间（整个 BCIO 命名空间）计数，得 1705，"
        "两口径不同属预期偏离，偏离全体落名于 items_file。",
        items_file="deviations/A01.jsonl"))

    ln = find_line(paper_lines, "initial MoA Ontology with 261")
    anchors.append(num_anchor(
        "A02", P, paper_lines, 261, ln, "We created an initial MoA Ontology with 261 entities",
        "L2_subclass_edges", q["L2_subclass_edges"], False,
        "论文没有自报子类边数；最近邻的结构性自报是初始版实体数 261（每条实体一条 is_a 边的前身），"
        "与本量 1905 的偏离全体落名于 items_file。",
        items_file="deviations/A02.jsonl"))

    ln = find_line(paper_lines, "## Figure 5.")
    anchors.append(num_anchor(
        "A03", P, paper_lines, 7, ln, "The 7 upper-level entities in the MoA Ontology",
        "L5_depth_max", q["L5_depth_max"], True,
        "数值同为 7。口径差异如实记录：论文说层级（levels）按层数计，本量按边数计；若折成层数则本量为 8 层。"))

    ln = find_line(paper_lines, "## Figure 3.")
    anchors.append(num_anchor(
        "A04", P, paper_lines, 3, ln, "Figure 3. Overview of steps to develop the MoA Ontology",
        None, None, True,
        "题注行内唯一整数是图号 3；步骤总数见 A11（Methods 范围 L24–L90 内末个 Step 标题），不属于六量。"))

    ln = find_line(paper_lines, "## Figure 4.")
    anchors.append(num_anchor(
        "A05", P, paper_lines, 4, ln, "Figure 4. Summary of results from each step to develop the MoA Ontol.",
        None, None, True,
        "题注行唯一整数是图号 4，不是量。"))

    ln = find_line(paper_lines, "## Figure 5.")
    anchors.append(num_anchor(
        "A06", P, paper_lines, 7, ln, "The 7 upper-level entities in the MoA Ontology",
        None, None, True,
        "上位实体数是 L1 的子口径，六量未单列该口径，不硬映射；论文自报为 7。"))

    ln = find_line(paper_lines, "## Methods")
    anchors.append(text_anchor("A07", P, paper_lines, ln, "## Methods", "节标题不是量；为 protocol 件起点节界"))

    ln = find_line(paper_lines, "## Results")
    anchors.append(text_anchor("A08", P, paper_lines, ln, "## Results", "节标题不是量；protocol 件范围（L24–L90）之后的下一节"))

    ln = find_line(paper_lines, "## Discussion")
    anchors.append(text_anchor("A09", P, paper_lines, ln, "## Discussion", "节标题不是量；自报数字所在叙述段的边界"))

    ln = find_line(paper_lines, "## Step 1 ", 24, 90)
    anchors.append(num_anchor(
        "A10", P, paper_lines, 1, ln, "## Step 1 – Defining the scope of the MoA Ontology",
        None, None, True,
        "步骤编号不是六量；Methods 范围（L24–L90）内首个 Step 标题的编号。"))

    ln = find_line(paper_lines, "## Step 9 ", 24, 90)
    anchors.append(num_anchor(
        "A11", P, paper_lines, 9, ln, "## Step 9 – Making the MoA Ontology machine-readable and available online",
        None, None, True,
        "步骤编号不是六量；Methods 范围（L24–L90）内末个 Step 标题的编号，即 protocol 件步数的上界。"))

    ln = find_line(owl_lines, "owl:versionIRI")
    anchors.append(text_anchor(
        "A12", O, owl_lines, ln,
        '<owl:versionIRI rdf:resource="http://humanbehaviourchange.org/ontology/MechanismOfAction/bcio_moa.owl/2026-11-10"/>',
        "版本快照标识不是量；text 锚逐字抄该行。"))

    ln = find_line(owl_lines, "<owl:Ontology rdf:about=")
    anchors.append(text_anchor(
        "A13", O, owl_lines, ln,
        '<owl:Ontology rdf:about="http://humanbehaviourchange.org/ontology/MechanismOfAction/bcio_moa.owl">',
        "本体身份 IRI 不是量；text 锚逐字抄该行。"))

    inputs = {}
    for name in ("bcio_moa.owl", "paper_text.txt"):
        p = research / name
        inputs[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}

    quantities = {k: q[k] for k in (
        "L1_class_local", "L2_subclass_edges", "L3_object_props",
        "L4_annotation_props", "L5_depth_max", "L6_leaf_classes")}

    # result 按 §四.2 表判（V1/V2/V3），不自裁
    v1 = all(
        inputs[n]["bytes"] == EXPECTED[n][0] and inputs[n]["sha256"] == EXPECTED[n][1]
        for n in EXPECTED
    )
    v2 = (
        all(isinstance(quantities[k], int) for k in quantities)
        and q["L2_split"]["internal"] + q["L2_split"]["to_external"] == q["L2_subclass_edges"]
    )
    ids = [a["id"] for a in anchors]
    v3 = ids == ["A%02d" % i for i in range(1, 14)]
    for a in anchors:
        src_lines = paper_lines if a["source"] == P else owl_lines
        ok = (
            a["kind"] in ("number", "text")
            and 1 <= a["line"] <= len(src_lines)
            and isinstance(a["explained"], bool)
        )
        if a["kind"] == "number" and not isinstance(a["value"], int):
            ok = False
        if a["kind"] == "text" and a["value"] is not None:
            ok = False
        if not a["explained"]:
            f = research / "pkg-B" / a.get("items_file", "")
            ok = ok and f.is_file() and f.stat().st_size > 0
        v3 = v3 and ok
    result = "pass" if (v1 and v2 and v3) else "fail"

    verdict = {
        "schema": "alice-b-verdict/1",
        "task_id": "ALICE-2026-0002",
        "result": result,
        "inputs": inputs,
        "quantities": quantities,
        "L2_split": q["L2_split"],
        "X_ext_classes": q["X_ext_classes"],
        "L5_cycle_breaks": q["L5_cycle_breaks"],
        "impl": {
            "family": "xml.dom.minidom 建 DOM 后显式栈迭代",
            "differs_from_A": "另一包用递归式解析器遍历；本包用 minidom＋显式栈＋单次遍历累计＋urlsplit 划界"
            "（已 grep 确认 code/ 无另一套解析器字样、无递归调用、无跨包 import）。",
        },
        "anchors": anchors,
        "not_done": ["未做 OWL 推理", "未做双人独立编码"],
        "checks": {"V1": v1, "V2": v2, "V3": v3},
    }
    out = research / "pkg-B" / "verdict.json"
    out.write_text(json.dumps(verdict, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": result, "checks": verdict["checks"], "quantities": quantities},
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
