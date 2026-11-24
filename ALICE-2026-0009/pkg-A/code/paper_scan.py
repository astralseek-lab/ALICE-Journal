# -*- coding: utf-8 -*-
"""paper_text.txt 的语料扫描（pkg-A）：锚定位、protocol 七步、行数。

行号口径＝splitlines()（\\f 算行断；全件 1,044 行）。
锚定位规则全部为「唯一子串 → 所在行／所在句」，取值不进定位串。
"""
from __future__ import annotations

import re

# sop:protocol 声明块（00_输入包说明.md §三，题面 §4.1 逐字引用；行范围计数路）
PROTO_FROM = 357
PROTO_TO = 600
PROTO_STEPS = 7

# 题面 §4.1 表给定的七条标题（跨行折断已按压空白拼接；代码侧逐条对语料核验）
STEP_TITLES = [
    "Step 1- Defining the scope of the BCI Schedule of Delivery Ontology through literature review",
    "Step 2- Identifying key BCI Schedule of Delivery classes and their definitions",
    "Step 3- Refinement of the BCI Schedule of Delivery Ontology through an iterative process of literature annotation, discussion and revision",
    "Step 4 – Expert stakeholder review",
    "Step 5 – Inter-rater reliability of annotations using the BCI Schedule of Delivery Ontology",
    "Step 6 - Specifying relationships between classes",
    "Step 7 – Making the Schedule of Delivery Ontology machine-readable and available online",
]

_STEP_HEAD_RE = re.compile(r"^Step\s+(\d+)\s*[-–:]\s*\S")


def load_lines(path):
    return open(str(path), encoding="utf-8").read().splitlines()


def corpus_lines(path):
    """语料行数（splitlines 口径，\\f 算行断）。"""
    return len(load_lines(path))


def collapse(text):
    return re.sub(r"\s+", " ", text)


def find_protocol_steps(path):
    """行范围计数路：L357–L600 区间内认行首 Step N 标题，编号须 1–7 连续。

    返回 [{pos, title, start, end}]；title 逐条与题面 §4.1 表核验
    （取标题行起至多三行压空白拼接，核验给定标题是其前缀）。
    """
    lines = load_lines(path)
    heads = []
    for i in range(PROTO_FROM, min(PROTO_TO, len(lines)) + 1):
        m = _STEP_HEAD_RE.match(lines[i - 1])
        if m:
            heads.append((i, int(m.group(1))))
    nums = [n for _, n in heads]
    if nums != list(range(1, PROTO_STEPS + 1)):
        raise ValueError(f"区间内行首 Step 标题编号不连续或不是 7 条：{heads}")
    steps = []
    for idx, (line_no, num) in enumerate(heads):
        end = (heads[idx + 1][0] - 1) if idx + 1 < len(heads) else PROTO_TO
        title = STEP_TITLES[num - 1]
        head_block = collapse(" ".join(lines[line_no - 1: min(line_no + 2, len(lines))]))
        if not (head_block == title or head_block.startswith(title + " ")):
            raise ValueError(f"Step {num} 标题与语料对不上：L{line_no} 起拼接 {head_block[:90]!r}")
        steps.append({"pos": num, "title": title, "start": line_no, "end": end})
    return steps


def _line_hits(lines, needle):
    return [i for i, ln in enumerate(lines, 1) if needle in ln]


def locate_anchors(path, ontology_path):
    """13 锚：返回 {id: {"value": …, "source": …}}。

    source 基座：文本锚＝paper_text.txt（投递面内真件；单行串用 #L<n>，
    跨行串用 #p<页> 全件子串核验），本体锚＝bcio_schedule.owl#<IRI 全串>。
    """
    lines = load_lines(path)
    anchors = {}

    # A01 终版自报类数：唯一起头句，值＝句内第一个整数，行＝值所在行
    hits = _line_hits(lines, "The final version of the BCI")
    assert len(hits) == 1, hits
    sent = " ".join(lines[hits[0] - 1: hits[0] + 2])
    sent = sent[sent.index("The final version of the BCI"):]
    sent = sent[: sent.index(".") + 1]
    m = re.search(r"contains\s+(\d+)\s+classes", sent)
    # 值所在行：从起头行往后找第一个含该整数（整值边界）的行
    val_line = None
    for j in range(hits[0], hits[0] + 4):
        if re.search(rf"(?<![\w]){m.group(1)}(?![\w])", lines[j - 1]):
            val_line = j
            break
    anchors["A01"] = {"value": int(m.group(1)), "source": f"paper_text.txt#L{val_line}"}

    # A02 信度：唯一起头行，值＝「α= 」（等号后带空格）后的小数
    hits = _line_hits(lines, "Inter-rater reliability was")
    assert len(hits) == 1, hits
    m = re.search(r"Inter-rater reliability was\s*α=\s*(\d+\.\d+)", lines[hits[0] - 1])
    anchors["A02"] = {"value": float(m.group(1)), "source": f"paper_text.txt#L{hits[0]}"}

    # A03 完成数：唯一起头行，值＝only 后的整数
    hits = _line_hits(lines, "responded to the request but only")
    assert len(hits) == 1, hits
    m = re.search(r"responded to the request but only\s+(\d+)", lines[hits[0] - 1])
    anchors["A03"] = {"value": int(m.group(1)), "source": f"paper_text.txt#L{hits[0]}"}

    # A04／A05 表题：整行恰为该题注
    for aid, caption in (("A04", "Table 1. Glossary of terms."),
                         ("A05", "Table 2. Behaviour Change Intervention Schedule of Delivery Ontology.")):
        hits = [i for i, ln in enumerate(lines, 1) if ln.strip() == caption]
        assert len(hits) == 1, (aid, hits)
        anchors[aid] = {"value": caption, "source": f"paper_text.txt#L{hits[0]}"}

    # A06 篇名：p1「RESEARCH ARTICLE」之后、「[version」之前的非空行块（原文跨行，值保留换行逐字）
    i0 = next(i for i, ln in enumerate(lines, 1) if ln.strip() == "RESEARCH ARTICLE")
    block = []
    j = i0
    while j + 1 <= len(lines) and lines[j].strip() and not lines[j].startswith("[version"):
        j += 1
        if lines[j - 1].strip() == "RESEARCH ARTICLE":
            continue
        block.append(lines[j - 1])
    title_raw = "\n".join(block)
    assert collapse(title_raw).count("Specifying the Schedule of Delivery") == 1
    anchors["A06"] = {"value": title_raw, "source": "paper_text.txt#p1（第 1/2 处）"}

    # A07／A08／A09 节标题：整行等于该词，取第 2/2 处（压空白全件口径）
    for aid, word, page in (("A07", "Methods", 6), ("A08", "Results", 8), ("A09", "Discussion", 9)):
        hits = [i for i, ln in enumerate(lines, 1) if ln.strip() == word]
        assert hits, aid
        line_no = hits[-1]
        anchors[aid] = {"value": word, "source": f"paper_text.txt#L{line_no}（第 2/2 处）"}

    # A10／A11 步骤标题：原文跨两行，值保留换行逐字；A10 取 Methods 段第 1/2 处，A11 取 Results 重列第 2/2 处
    steps = find_protocol_steps(path)
    t1 = steps[0]["title"]   # Step 1（Methods）
    raw1 = "\n".join(load_lines(path)[steps[0]["start"] - 1: steps[0]["start"] + 1])
    assert collapse(raw1) == t1, (raw1, t1)
    anchors["A10"] = {"value": raw1, "source": "paper_text.txt#p6（第 1/2 处）"}
    t7 = steps[6]["title"]   # Step 7（Methods 行）；Results 重列在 L600 之后
    lines_all = load_lines(path)
    hits7 = [i for i, ln in enumerate(lines_all, 1)
             if ln.startswith("Step 7") and "Making the Schedule of Delivery Ontology" in ln]
    assert len(hits7) == 2, hits7
    res7 = hits7[-1]
    raw7 = "\n".join(lines_all[res7 - 1: res7 + 1])
    assert collapse(raw7) == t7, (raw7, t7)
    anchors["A11"] = {"value": raw7, "source": "paper_text.txt#p9（第 2/2 处）"}

    # A12／A13 本体自述（定位串带属性名前缀在整件内恰 1 处；value 交裸 IRI）
    otext = open(str(ontology_path), encoding="utf-8").read()
    m = re.search(r'owl:versionIRI\s+rdf:resource="([^"]+)"', otext)
    assert otext.count(f'rdf:resource="{m.group(1)}"') == 1
    anchors["A12"] = {"value": m.group(1), "source": f"bcio_schedule.owl#{m.group(1)}"}
    m2 = re.search(r'<owl:Ontology\s+rdf:about="([^"]+)"', otext)
    assert otext.count(f'rdf:about="{m2.group(1)}"') == 1
    anchors["A13"] = {"value": m2.group(1), "source": f"bcio_schedule.owl#{m2.group(1)}"}
    return anchors
