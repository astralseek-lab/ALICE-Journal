# -*- coding: utf-8 -*-
"""paper_text.txt 的语料扫描（pkg-B 独立实现：迭代扫描，不读 pkg-A 任何件）。

行号口径＝splitlines()（\\f 算行断；全件 1,044 行，B 独立数出同值）。
protocol 走行范围计数路：从语料按 sop:protocol 声明块区间（L357–L600）重新数
行首 Step N 标题（不沿用任何他包切分）。
"""
from __future__ import annotations

import re

PROTO_FROM = 357
PROTO_TO = 600
PROTO_STEPS = 7

# 题面 §4.1 表给定的七条标题（公开题面数据，两包各持一份；跨行折断已按压空白拼接）
STEP_TITLES = [
    "Step 1- Defining the scope of the BCI Schedule of Delivery Ontology through literature review",
    "Step 2- Identifying key BCI Schedule of Delivery classes and their definitions",
    "Step 3- Refinement of the BCI Schedule of Delivery Ontology through an iterative process of literature annotation, discussion and revision",
    "Step 4 – Expert stakeholder review",
    "Step 5 – Inter-rater reliability of annotations using the BCI Schedule of Delivery Ontology",
    "Step 6 - Specifying relationships between classes",
    "Step 7 – Making the Schedule of Delivery Ontology machine-readable and available online",
]

_HEAD = re.compile(r"^Step\s+(\d+)\s*[-–:]\s*\S")


def load_lines(path):
    with open(str(path), encoding="utf-8") as fh:
        return fh.read().splitlines()


def corpus_lines(path):
    return len(load_lines(path))


def collapse(text):
    return re.sub(r"\s+", " ", text)


def find_protocol_steps(path):
    """行范围计数路：区间内行首 Step N 标题，编号须 1–7 连续；标题逐条对语料核验。"""
    lines = load_lines(path)
    heads = []
    i = PROTO_FROM
    while i <= min(PROTO_TO, len(lines)):
        m = _HEAD.match(lines[i - 1])
        if m:
            heads.append((i, int(m.group(1))))
        i += 1
    if [n for _, n in heads] != list(range(1, PROTO_STEPS + 1)):
        raise ValueError(f"区间内行首 Step 标题不是 1–7 连续七条：{heads}")
    steps = []
    for idx, (line_no, num) in enumerate(heads):
        end = heads[idx + 1][0] - 1 if idx + 1 < len(heads) else PROTO_TO
        title = STEP_TITLES[num - 1]
        block = collapse(" ".join(lines[line_no - 1: min(line_no + 2, len(lines))]))
        if not (block == title or block.startswith(title + " ")):
            raise ValueError(f"Step {num} 标题核验失败：L{line_no}")
        steps.append({"pos": num, "title": title, "start": line_no, "end": end})
    return steps


def _first_hit(lines, needle):
    for i, ln in enumerate(lines, 1):
        if needle in ln:
            return i
    raise ValueError(f"定位串未命中：{needle[:60]}")


def _only_hit(lines, needle):
    hits = [i for i, ln in enumerate(lines, 1) if needle in ln]
    if len(hits) != 1:
        raise ValueError(f"定位串命中 {len(hits)} 处（应恰 1）：{needle[:60]}")
    return hits[0]


def locate_anchors(paper_path, ontology_path):
    """13 锚（与 pkg-A 同规则、独立实现；跨行标题保留原文换行逐字）。"""
    lines = load_lines(paper_path)
    anchors = {}

    ln0 = _only_hit(lines, "The final version of the BCI")
    sent = collapse(" ".join(lines[ln0 - 1: ln0 + 2]))
    sent = sent[sent.index("The final version of the BCI"):]
    sent = sent[: sent.index(".") + 1]
    m = re.search(r"contains\s+(\d+)\s+classes", sent)
    val = int(m.group(1))
    val_line = None
    for j in range(ln0, ln0 + 4):
        if re.search(rf"(?<![\w]){val}(?![\w])", lines[j - 1]):
            val_line = j
            break
    anchors["A01"] = {"value": val, "source": f"paper_text.txt#L{val_line}"}

    ln = _only_hit(lines, "Inter-rater reliability was")
    m = re.search(r"α=\s*(\d+\.\d+)", lines[ln - 1])
    anchors["A02"] = {"value": float(m.group(1)), "source": f"paper_text.txt#L{ln}"}

    ln = _only_hit(lines, "responded to the request but only")
    m = re.search(r"only\s+(\d+)", lines[ln - 1])
    anchors["A03"] = {"value": int(m.group(1)), "source": f"paper_text.txt#L{ln}"}

    for aid, caption in (("A04", "Table 1. Glossary of terms."),
                         ("A05", "Table 2. Behaviour Change Intervention Schedule of Delivery Ontology.")):
        hits = [i for i, l in enumerate(lines, 1) if l.strip() == caption]
        if len(hits) != 1:
            raise ValueError(f"{aid} 题注命中 {len(hits)} 处")
        anchors[aid] = {"value": caption, "source": f"paper_text.txt#L{hits[0]}"}

    # A06 篇名：「RESEARCH ARTICLE」行之后、「[version」行之前的连续非空行块（原文跨行）
    i0 = _first_hit(lines, "RESEARCH ARTICLE")
    block = []
    j = i0 + 1
    while j <= len(lines) and lines[j - 1].strip() and not lines[j - 1].startswith("[version"):
        block.append(lines[j - 1])
        j += 1
    anchors["A06"] = {"value": "\n".join(block), "source": "paper_text.txt#p1（第 1/2 处）"}

    for aid, word in (("A07", "Methods"), ("A08", "Results"), ("A09", "Discussion")):
        hits = [i for i, l in enumerate(lines, 1) if l.strip() == word]
        anchors[aid] = {"value": word, "source": f"paper_text.txt#L{hits[-1]}（第 2/2 处）"}

    steps = find_protocol_steps(paper_path)
    raw1 = "\n".join(lines[steps[0]["start"] - 1: steps[0]["start"] + 1])
    if collapse(raw1) != steps[0]["title"]:
        raise ValueError("A10 标题核验失败")
    anchors["A10"] = {"value": raw1, "source": "paper_text.txt#p6（第 1/2 处）"}
    hits7 = [i for i, l in enumerate(lines, 1)
             if l.startswith("Step 7") and "Making the Schedule of Delivery Ontology" in l]
    if len(hits7) != 2:
        raise ValueError(f"Step 7 重列命中 {len(hits7)} 处")
    raw7 = "\n".join(lines[hits7[-1] - 1: hits7[-1] + 1])
    if collapse(raw7) != steps[6]["title"]:
        raise ValueError("A11 标题核验失败")
    anchors["A11"] = {"value": raw7, "source": "paper_text.txt#p9（第 2/2 处）"}

    with open(str(ontology_path), encoding="utf-8") as fh:
        otext = fh.read()
    m = re.search(r'owl:versionIRI\s+rdf:resource="([^"]+)"', otext)
    anchors["A12"] = {"value": m.group(1), "source": f"bcio_schedule.owl#{m.group(1)}"}
    m = re.search(r'<owl:Ontology\s+rdf:about="([^"]+)"', otext)
    anchors["A13"] = {"value": m.group(1), "source": f"bcio_schedule.owl#{m.group(1)}"}
    return anchors
