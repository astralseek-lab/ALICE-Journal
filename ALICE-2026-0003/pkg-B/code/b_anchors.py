#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B 侧十三锚定位与取值（ALICE-2026-0003 旁证包）。

每条锚的 value／line／quote 都由本脚本在源件里按题面 §四.4／§八 的规则现场找出：
  A01 Results 末段终版句（comprising 之后、entities 之前的整数）；
  A02 % agreement 括号内 Kappa 之后、')' 之前的逐字区间；
  A03 'Feedback was received from' 句的回收份数；
  A04–A06 表题行（含 Table N. 标签；A05 止于缩写对照前、A06 止于 Note. 前）；
  A07–A09 节标题行（整行逐字相等匹配，表头行同串不算）；
  A10／A11 Methods 范围内首／末 'Step N:' 标题行；
  A12／A13 本体 versionIRI／Ontology IRI（定位串带属性名前缀）。
数值型锚的 source／quote 不含取值本身。
"""
import json
import re
import sys
from xml.dom import minidom


def _lines(path):
    return open(path, encoding="utf-8").read().split("\n")


def _find_line(lines, needle, start=0):
    for i in range(start, len(lines)):
        if needle in lines[i]:
            return i + 1  # 1 起算
    raise RuntimeError("找不到行: %s" % needle)


def _find_line_startswith(lines, prefix, start=0):
    """题注行按行首匹配（正文里的 'described in Table 3.' 一处不算）。"""
    for i in range(start, len(lines)):
        if lines[i].startswith(prefix):
            return i + 1
    raise RuntimeError("找不到行首: %s" % prefix)


def _find_exact(lines, text, start=0):
    for i in range(start, len(lines)):
        if lines[i].strip() == text:
            return i + 1
    raise RuntimeError("找不到整行: %s" % text)


def extract_anchors(paper_path, owl_path):
    lines = _lines(paper_path)
    anchors = []

    # A01：终版句（'The final MoD Ontology presents a' 起），取 comprising 之后、entities 之前的整数
    ln = _find_line(lines, "The final MoD Ontology presents a")
    line = lines[ln - 1]
    m = re.search(r"The final MoD Ontology presents a[^{]*?comprising (\d+) entities", line)
    value = int(m.group(1))
    sent_start = line.find("The final MoD Ontology presents a")
    quote = line[sent_start:m.end()].replace(str(value), "").strip()
    # quote 取到 comprising 为止（不含取值）
    quote = line[sent_start:line.find(str(value), sent_start)].strip()
    anchors.append({"id": "A01", "kind": "number", "source": "paper_text.txt#L%d" % ln,
                    "value": value, "line": ln, "quote": quote,
                    "maps_to": "L1_class_local"})

    # A02：% agreement 括号内 '; Kappa ' 之后、')' 之前的逐字区间
    ln = _find_line(lines, "Inter-rater reliability was calculated for each level of the hierarchy separately")
    line = lines[ln - 1]
    p0 = line.find("(% agreement")
    p1 = line.find(")", p0)
    inner = line[p0:p1]
    kappa = inner.split("; Kappa ", 1)[1].strip()
    anchors.append({"id": "A02", "kind": "text", "source": "paper_text.txt#L%d" % ln,
                    "value": kappa, "line": ln,
                    "quote": line[line.find("Inter-rater reliability was calculated"):p1 + 1],
                    "maps_to": None})

    # A03：'Feedback was received from' 起头句，取回收份数（邀请数不取）
    ln = _find_line(lines, "Feedback was received from")
    line = lines[ln - 1]
    m = re.search(r"Feedback was received from (\d+) of the (\d+) experts invited", line)
    anchors.append({"id": "A03", "kind": "number", "source": "paper_text.txt#L%d" % ln,
                    "value": int(m.group(1)), "line": ln,
                    "quote": "Feedback was received from",
                    "maps_to": None})

    # A04–A06：表题行（行首匹配）
    ln = _find_line_startswith(lines, "Table 1. ")
    anchors.append({"id": "A04", "kind": "text", "source": "paper_text.txt#L%d" % ln,
                    "value": lines[ln - 1].strip(), "line": ln, "quote": lines[ln - 1].strip(),
                    "maps_to": None})
    ln = _find_line_startswith(lines, "Table 2. ")
    line = lines[ln - 1]
    cut = line.find(" MoD, mode of delivery;")
    value = line[:cut].strip()
    anchors.append({"id": "A05", "kind": "text", "source": "paper_text.txt#L%d" % ln,
                    "value": value, "line": ln, "quote": value, "maps_to": None})
    ln = _find_line_startswith(lines, "Table 3. ")
    line = lines[ln - 1]
    cut = line.find(" Note.")
    value = line[:cut].strip()
    anchors.append({"id": "A06", "kind": "text", "source": "paper_text.txt#L%d" % ln,
                    "value": value, "line": ln, "quote": value, "maps_to": None})

    # A07–A09：节标题（整行逐字；'Phase Step Methods' 这类表头行因整行不等而天然排除）
    ln_m = _find_exact(lines, "Methods")
    ln_r = _find_exact(lines, "Results")
    ln_d = _find_exact(lines, "Discussion")
    anchors.append({"id": "A07", "kind": "text", "source": "paper_text.txt#L%d" % ln_m,
                    "value": "Methods", "line": ln_m, "quote": "Methods", "maps_to": None})
    anchors.append({"id": "A08", "kind": "text", "source": "paper_text.txt#L%d" % ln_r,
                    "value": "Results", "line": ln_r, "quote": "Results", "maps_to": None})
    anchors.append({"id": "A09", "kind": "text", "source": "paper_text.txt#L%d" % ln_d,
                    "value": "Discussion", "line": ln_d, "quote": "Discussion", "maps_to": None})

    # A10／A11：Methods 范围内首／末 'Step N:' 标题行
    step_re = re.compile(r"^Step \d+: ")
    steps = [(i + 1, lines[i]) for i in range(ln_m, ln_r - 1) if step_re.match(lines[i])]
    first_ln, first_t = steps[0]
    last_ln, last_t = steps[-1]
    anchors.append({"id": "A10", "kind": "text", "source": "paper_text.txt#L%d" % first_ln,
                    "value": first_t, "line": first_ln, "quote": first_t, "maps_to": None})
    anchors.append({"id": "A11", "kind": "text", "source": "paper_text.txt#L%d" % last_ln,
                    "value": last_t, "line": last_ln, "quote": last_t, "maps_to": None})

    # A12／A13：本体自述（minidom 只取两个属性的值；定位串带属性名前缀）
    doc = minidom.parse(str(owl_path))
    stack = [doc.documentElement]
    version_iri = None
    ontology_about = None
    while stack:
        node = stack.pop()
        if node.nodeType == node.ELEMENT_NODE:
            if node.tagName == "owl:versionIRI" and version_iri is None:
                version_iri = node.getAttribute("rdf:resource")
            if node.tagName == "owl:Ontology" and ontology_about is None:
                ontology_about = node.getAttribute("rdf:about")
            ch = node.firstChild
            kids = []
            while ch is not None:
                kids.append(ch)
                ch = ch.nextSibling
            for k2 in reversed(kids):
                stack.append(k2)
    doc.unlink()
    owl_lines = _lines(owl_path)
    ln_v = _find_line(owl_lines, '<owl:versionIRI rdf:resource="%s"' % version_iri)
    ln_o = _find_line(owl_lines, '<owl:Ontology rdf:about="%s"' % ontology_about)
    anchors.append({"id": "A12", "kind": "text",
                    "source": "bcio_mode_of_delivery.owl#%s" % version_iri,
                    "value": version_iri, "line": ln_v,
                    "quote": '<owl:versionIRI rdf:resource="%s"/>' % version_iri,
                    "maps_to": None})
    anchors.append({"id": "A13", "kind": "text",
                    "source": "bcio_mode_of_delivery.owl#%s" % ontology_about,
                    "value": ontology_about, "line": ln_o,
                    "quote": '<owl:Ontology rdf:about="%s">' % ontology_about,
                    "maps_to": None})
    return anchors


_REASONS = {
    "A02": "论文自报一致性区间（str），六量中无同义实测端",
    "A03": "论文自报专家回收份数，六量中无同义实测端",
    "A04": "表题（术语表），语料表题不作六量实测端",
    "A05": "表题（开发步骤表），不作六量实测端",
    "A06": "表题（实体清单表），不作六量实测端",
    "A07": "节标题（Methods 起点节界），非六量",
    "A08": "节标题（Results 终点节界），非六量",
    "A09": "节标题（Discussion 段界），非六量",
    "A10": "Methods 步骤序列首项段名，非六量",
    "A11": "Methods 步骤序列末项段名，非六量",
    "A12": "本体版本快照 IRI（结构自述，不作识别锚）",
    "A13": "本体身份 IRI（识别锚），非六量",
}


def main(paper_path, owl_path):
    anchors = extract_anchors(paper_path, owl_path)
    out = []
    for a in anchors:
        row = dict(a)
        if row["maps_to"] is None:
            row["reason"] = _REASONS[row["id"]]
        out.append(row)
    print(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True))
    return out


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
