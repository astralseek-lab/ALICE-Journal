"""ALICE-2026-0014 pkg-A 主实现：K＝3 量（Q1_items／Q2_clusters／Q3_max_per_cluster）。

权威源：esm1.docx 第 4 张物理表（python-docx `d.tables[3]`，行型判定只看第 1 列
`No.` 的取值形态，不按视觉合并单元格判）。对读件：terms_bct_v1.csv（标准库
csv.DictReader，按声明列位直接数）。两读必须同值。

探针调用约定：三个 K 入口以 `fn(csv_path, params)` 被调（单上游＋params 形参）；
返回 {"v": <整数>, "unit": "count"}。
"""
import csv
import re

from docx import Document

ITEM_RE = re.compile(r"^\d+\.\d+")        # 条目行：N.M
CLUSTER_RE = re.compile(r"^\d+\.(?!\d)")  # 簇标题行：N. 名称（点后不再接数字）

PROTOCOL_TITLES = [
    "Step 1: Developing the Prototype Classification System",
    "Step 2: Delphi Exercise First Round",
    "Step 3: Delphi Exercise Second Round",
    "Step 4: Feedback from the International Advisory Board",
    "Step 5: Reliability Testing Round 1",
    "Step 6: Investigating Hierarchical Structure of the BCT List",
    "Step 7: Reliability Testing Round 2",
    "Step 8: Feedback from Study Team Members",
]
PROTOCOL_DECLARED = {"from": 343, "to": 516}  # F4 声明区间（pkg-A 沿用）

_PROTOCOL_IO = {
    1: ("six BCT classification systems identified by a literature search",
        "the prototype classification system (distinct BCTs with labels and definitions)"),
    2: ("the prototype BCT list from Step 1 and the study definition of a BCT",
        "ratings plus newly identified BCTs to be presented in the second Delphi exercise round"),
    3: ("the BCTs identified as requiring further consideration in Step 2",
        "a refined BCT list resolved by the study team from the round responses"),
    4: ("the refined BCT list from the Delphi rounds",
        "advice from the International Advisory Board and a further refined BCT list"),
    5: ("45 intervention descriptions and the refined BCT list",
        "inter-rater reliability results of round 1 and the amended BCT list"),
    6: ("the developed list of BCTs (delivered via an online open-sort grouping task)",
        "labeled groups of BCTs from hierarchical cluster analysis with the word frequency analysis"),
    7: ("40 intervention descriptions and the amended list",
        "reliability scores for BCTs observed at least five times by either coder"),
    8: ("the BCT definitions produced by the previous steps",
        "the final taxonomy v1 list after study team feedback (Electronic Supplementary Materials Table 2)"),
}


# ── CSV 读法（探针施力面：行式件，判据扰动 drop:<k> 删前 k 行）─────────────────
def _data_rows(csv_path):
    """按声明列位直接数（第 1 列＝no、第 5 列＝cluster）；首行＝表头，跳过。"""
    with open(csv_path, newline="", encoding="utf-8") as fh:
        rdr = csv.reader(fh)
        next(rdr, None)
        yield from rdr


def count_items(csv_path, params):
    """Q1_items：条目行（No. 匹配 ^\\d+\\.\\d+）计数。"""
    n = sum(1 for r in _data_rows(csv_path) if r and ITEM_RE.match(r[0].strip()))
    return {"v": n, "unit": "count"}


def count_clusters(csv_path, params):
    """Q2_clusters：条目行所属簇（cluster 列声明值）去重计数。"""
    seen = []
    for r in _data_rows(csv_path):
        if r and ITEM_RE.match(r[0].strip()):
            c = r[4].strip() if len(r) > 4 else ""
            if c not in seen:
                seen.append(c)
    return {"v": len(seen), "unit": "count"}


def max_per_cluster(csv_path, params):
    """Q3_max_per_cluster：按簇分组后各组条目数的最大值。"""
    groups = {}
    for r in _data_rows(csv_path):
        if r and ITEM_RE.match(r[0].strip()):
            c = r[4].strip() if len(r) > 4 else ""
            groups[c] = groups.get(c, 0) + 1
    return {"v": max(groups.values()), "unit": "count"}


# ── docx 读法（权威源对读；python-docx，d.tables[3]）──────────────────────────
def _t4_cells(docx_path):
    doc = Document(docx_path)
    table = doc.tables[3]
    for row in table.rows:
        yield [c.text.strip() for c in row.cells]


def _t4_data_rows(docx_path):
    rows = list(_t4_cells(docx_path))
    return rows[1:]  # 表头行不占数据行号


def count_items_docx(docx_path, params=None):
    n = sum(1 for cells in _t4_data_rows(docx_path) if ITEM_RE.match(cells[0]))
    return {"v": n, "unit": "count"}


def count_clusters_docx(docx_path, params=None):
    n = sum(1 for cells in _t4_data_rows(docx_path) if CLUSTER_RE.match(cells[0]))
    return {"v": n, "unit": "count"}


def max_per_cluster_docx(docx_path, params=None):
    groups = {}
    for cells in _t4_data_rows(docx_path):
        if ITEM_RE.match(cells[0]):
            p = cells[0].split(".")[0]
            groups[p] = groups.get(p, 0) + 1
    return {"v": max(groups.values()), "unit": "count"}


def min_per_cluster_docx(docx_path):
    groups = {}
    for cells in _t4_data_rows(docx_path):
        if ITEM_RE.match(cells[0]):
            p = cells[0].split(".")[0]
            groups[p] = groups.get(p, 0) + 1
    return min(groups.values())


def empty_definition_count_docx(docx_path):
    n = 0
    for cells in _t4_data_rows(docx_path):
        if ITEM_RE.match(cells[0]) and (cells[2] == "" or cells[3] == ""):
            n += 1
    return n


def item_keys_docx(docx_path):
    """diff_A01 的 items：条目行 No. 逐字，按行序。"""
    return [cells[0] for cells in _t4_data_rows(docx_path) if ITEM_RE.match(cells[0])]


def cluster_names_docx(docx_path):
    """diff_A02 的 items：簇标题行第 1 格整串逐字，按簇序。"""
    return [cells[0] for cells in _t4_data_rows(docx_path) if CLUSTER_RE.match(cells[0])]


def cluster_name_table3(docx_path):
    """contrast 对端：第 3 张物理表逐格文本（压空白）。"""
    doc = Document(docx_path)
    cells = []
    for row in doc.tables[2].rows:
        for c in row.cells:
            cells.append(re.sub(r"\s+", " ", c.text).strip())
    return cells


def docx_table_count(docx_path):
    return len(Document(docx_path).tables)


# ── protocol（kind=line；pkg-A 沿用 F4 声明的 L343–L516 并校验）────────────────
def build_protocol(paper_path, params=None):
    lines = open(paper_path, encoding="utf-8").read().splitlines()
    lo, hi = PROTOCOL_DECLARED["from"], PROTOCOL_DECLARED["to"]
    heads = []
    for i, line in enumerate(lines, 1):
        if lo <= i <= hi and line in PROTOCOL_TITLES:
            heads.append((PROTOCOL_TITLES.index(line) + 1, i))
    if [p for p, _ in heads] != list(range(1, 9)):
        raise RuntimeError(f"声明区间内八步标题不齐全或乱序：{heads!r}")
    if [i for _, i in heads] != sorted(i for _, i in heads):
        raise RuntimeError("标题行号未严格递增")
    bounds = [i for _, i in heads] + [None]
    results_head = next(
        i for i in range(hi + 1, len(lines) + 1) if lines[i - 1] == "Results"
    )
    steps = []
    for k, (pos, start) in enumerate(heads):
        stop = (bounds[k + 1] - 1) if bounds[k + 1] is not None else (results_head - 1)
        inp, outp = _PROTOCOL_IO[pos]
        steps.append({
            "pos": pos,
            "label": f"S{pos}",
            "title": PROTOCOL_TITLES[pos - 1],
            "src": "paper_text.txt",
            "kind": "line",
            "target": f"paper_text.txt#L{start}-L{stop}",
            "evidence_loc": f"paper_text.txt#L{start}-L{start}",
            "input": inp,
            "output": outp,
        })
    return {
        "rule": (
            "kind=line：在 paper_text.txt 的 L343–L516 区间内按整行逐字匹配八个 "
            "Step N: 标题行（行号严格递增、区间内每个标题恰出现 1 次）；"
            "区外同形整行（Results 小节复述的六处）披露不计"
        ),
        "source": "paper_text.txt#L343-L516",
        "steps": steps,
    }


# ── 锚（A01–A13）────────────────────────────────────────────────────────────
def _squash(text):
    return re.sub(r"\s+", " ", text)


def _caption(page_squashed, prefix, stop):
    i = page_squashed.find(prefix)
    if i < 0:
        raise RuntimeError(f"题注前缀未命中：{prefix!r}")
    j = page_squashed.find(stop, i)
    if j < 0:
        raise RuntimeError(f"题注上界未命中：{stop!r}")
    return page_squashed[i:j + len(stop)]


def build_anchors(paper_path, docx_path):
    raw = open(paper_path, encoding="utf-8").read()
    pages = raw.split("\f")
    p1, p9 = _squash(pages[0]), _squash(pages[8])
    p11, p12 = _squash(pages[10]), _squash(pages[11])

    m01 = re.search(r"Results (This resulted in ([0-9]+) BCTs clustered into ([0-9]+) groups\.)", p1)
    a01 = int(m01.group(2))
    m02 = re.search(r"This resulted in ([0-9]+) clearly defined, non-redundant BCTs, grouped into ([0-9]+) clusters,", p9)
    a02 = int(m02.group(2))

    doc = Document(docx_path)
    t4 = doc.tables[3]
    data = [[c.text.strip() for c in row.cells] for row in t4.rows][1:]
    clus = [(i + 1, cells[0]) for i, cells in enumerate(data) if CLUSTER_RE.match(cells[0])]
    a06 = t4.rows[0].cells[0].text.strip()
    a13 = doc.tables[1].rows[0].cells[0].text.strip()

    return [
        {"id": "A01", "value": a01, "source": "fulltext.pdf#p1#s8", "locator": ""},
        {"id": "A02", "value": a02, "source": "fulltext.pdf#p9#s6", "locator": ""},
        {"id": "A03", "value": "Hierarchically Clustered Techniques", "source": "fulltext.pdf#p1#s1", "locator": ""},
        {"id": "A04", "value": _caption(p11, "Table 4 Hierarchical structure labeling (step 6):", "(conjunctions removed)"), "source": "fulltext.pdf#p11", "locator": ""},
        {"id": "A05", "value": _caption(p12, "Table 5 Results of hierarchical cluster analysis", "and standard errors"), "source": "fulltext.pdf#p12", "locator": ""},
        {"id": "A06", "value": a06, "source": "esm1.docx#tbl@4#header", "locator": ""},
        {"id": "A07", "value": "Method", "source": "fulltext.pdf#p3", "locator": "全文第 2/2 处"},
        {"id": "A08", "value": "Results", "source": "fulltext.pdf#p6", "locator": "全文第 2/5 处"},
        {"id": "A09", "value": "Discussion", "source": "fulltext.pdf#p9#s1", "locator": ""},
        {"id": "A10", "value": clus[0][1], "source": "esm1.docx#tbl@4#r1", "locator": ""},
        {"id": "A11", "value": clus[-1][1], "source": f"esm1.docx#tbl@4#r{clus[-1][0]}", "locator": ""},
        {"id": "A12", "value": "Published online: 20 March 2013", "source": "fulltext.pdf#p1#s3", "locator": ""},
        {"id": "A13", "value": a13, "source": "esm1.docx#tbl@2#header", "locator": "全文第 1/8 处"},
    ]


if __name__ == "__main__":
    import sys
    here = sys.argv[1] if len(sys.argv) > 1 else "../.."
    csv_p = f"{here}/terms_bct_v1.csv"
    docx_p = f"{here}/esm1.docx"
    for name, fn in (("count_items", count_items), ("count_clusters", count_clusters), ("max_per_cluster", max_per_cluster)):
        print(name, fn(csv_p, {}))
    for name, fn in (("count_items_docx", count_items_docx), ("count_clusters_docx", count_clusters_docx), ("max_per_cluster_docx", max_per_cluster_docx)):
        print(name, fn(docx_p))
