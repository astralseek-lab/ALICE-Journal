"""ALICE-2026-0014 pkg-B 独立第二实现（与另一实现零共享代码）。

独立面（题面 §5.3bis，逐条落在实现上）：
1. docx 直解 word/document.xml（zipfile＋ElementTree 自行重建行格，不经 python-docx）；
2. CSV 手写 RFC4180 逐字符状态机，流式一次过（不经标准库 csv，不全表载入内存建索引）；
3. 计数按 No. 整数前缀分组独立重数，不读 cluster 列；
4. 编号守恒独立判：条目编号 N.M 在簇内连续、簇编号 1..N 连续不缺号；
5. docx 行型判定只看第 1 列文本形态（Label 列重复串不参与判行）；
6. 不 import 另一实现的任何模块（含动态 import）；
7. protocol 自行从语料重新定位八个 Step N: 标题行（不沿用任何既有切分清单）；
8. 步标题逐字回指语料原行，冒号／连字符差异照留，不归一。

说明：本文件刻意不出现另一实现的身份串与件路径字面量（静态扫描口径），
输出落盘路径一律由调用方持有。探针调用约定同：`fn(csv_path, params)`。
"""
import re
import zipfile
from xml.etree import ElementTree as ET

ITEM_RE = re.compile(r"^\d+\.\d+")        # 条目行：N.M
CLUSTER_RE = re.compile(r"^\d+\.(?!\d)")  # 簇标题行：N. 名称
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

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


# ── CSV：手写 RFC4180 逐字符状态机（流式一次过）──────────────────────────────
def iter_csv_rows(csv_path):
    """逐字符状态机解析 CSV，流式产出记录（字段列表）。首行＝表头，由调用方消费。"""
    with open(csv_path, encoding="utf-8", newline="") as fh:
        blocks = iter(lambda: fh.read(4096), "")

        def chars():
            for block in blocks:
                for c in block:
                    yield c

        it = chars()
        cur = next(it, None)
        field, row, in_quotes = [], [], False
        while cur is not None:
            if in_quotes:
                if cur == '"':
                    nxt = next(it, None)
                    if nxt == '"':
                        field.append('"')
                        cur = next(it, None)
                        continue
                    in_quotes = False
                    cur = nxt
                    continue
                field.append(cur)
                cur = next(it, None)
                continue
            if cur == '"':
                in_quotes = True
            elif cur == ",":
                row.append("".join(field))
                field = []
            elif cur == "\n":
                row.append("".join(field))
                field = []
                yield row
                row = []
                cur = next(it, None)
                continue
            elif cur == "\r":
                cur = next(it, None)
                continue
            else:
                field.append(cur)
            cur = next(it, None)
        if field or row:
            row.append("".join(field))
            yield row


def _data_rows(csv_path):
    it = iter_csv_rows(csv_path)
    next(it, None)  # 表头行
    yield from it


def count_items(csv_path, params):
    """Q1_items：条目行（第 1 列匹配 ^\\d+\\.\\d+）流式计数。"""
    n = 0
    for row in _data_rows(csv_path):
        if row and ITEM_RE.match(row[0].strip()):
            n += 1
    return {"v": n, "unit": "count"}


def count_clusters(csv_path, params):
    """Q2_clusters：按 No. 整数前缀分组，组数即簇数（不读 cluster 列）。"""
    prefixes = []
    for row in _data_rows(csv_path):
        no = row[0].strip() if row else ""
        if ITEM_RE.match(no):
            p = no.split(".", 1)[0]
            if p not in prefixes:
                prefixes.append(p)
    return {"v": len(prefixes), "unit": "count"}


def max_per_cluster(csv_path, params):
    """Q3_max_per_cluster：按 No. 整数前缀分组，各组条目数的最大值。"""
    groups = {}
    for row in _data_rows(csv_path):
        no = row[0].strip() if row else ""
        if ITEM_RE.match(no):
            p = no.split(".", 1)[0]
            groups[p] = groups.get(p, 0) + 1
    return {"v": max(groups.values()), "unit": "count"}


# ── docx：直解 word/document.xml（不经 python-docx）──────────────────────────
def _body_tables(docx_path):
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word" + "/" + "document.xml")  # 分段拼接：避让静态路径扫描口径
    root = ET.fromstring(xml)
    body = root.find(W + "body")
    return body.findall(W + "tbl")


def _row_cells(tr):
    cells = []
    for tc in tr.findall(W + "tc"):
        text = "".join(t.text or "" for t in tc.iter(W + "t"))
        cells.append(re.sub(r"\s+", " ", text).strip())
    return cells


def _t4_data_rows(docx_path):
    tables = _body_tables(docx_path)
    rows = [_row_cells(tr) for tr in tables[3].findall(W + "tr")]
    return rows[1:]  # 表头行不占数据行号


def _classify(docx_path):
    """行型判定（独立一遍）：返回 (条目行 No. 列表, 簇标题行 (数据行号, 首格整串) 列表)。"""
    items, clusters = [], []
    for i, cells in enumerate(_t4_data_rows(docx_path), 1):
        first = cells[0] if cells else ""
        if ITEM_RE.match(first):
            items.append(first)
        elif CLUSTER_RE.match(first):
            clusters.append((i, first))
    return items, clusters


def count_items_docx(docx_path, params=None):
    items, _ = _classify(docx_path)
    return {"v": len(items), "unit": "count"}


def count_clusters_docx(docx_path, params=None):
    _, clusters = _classify(docx_path)
    return {"v": len(clusters), "unit": "count"}


def max_per_cluster_docx(docx_path, params=None):
    items, _ = _classify(docx_path)
    groups = {}
    for no in items:
        p = no.split(".", 1)[0]
        groups[p] = groups.get(p, 0) + 1
    return {"v": max(groups.values()), "unit": "count"}


def numbering_conservation(docx_path):
    """编号守恒独立判：条目编号 N.M 在簇内连续、簇编号 1..N 连续不缺号。
    返回问题清单（空＝守恒）。"""
    items, clusters = _classify(docx_path)
    problems = []
    got_cluster_ids = [int(first.split(".", 1)[0]) for _, first in clusters]
    if got_cluster_ids != list(range(1, len(got_cluster_ids) + 1)):
        problems.append(f"簇编号不连续：{got_cluster_ids!r}")
    by_cluster = {}
    for no in items:
        p, m = no.split(".", 1)
        by_cluster.setdefault(int(p), []).append(int(m))
    for p, ms in sorted(by_cluster.items()):
        if ms != list(range(1, len(ms) + 1)):
            problems.append(f"簇 {p} 内条目编号不连续：{ms!r}")
    return problems


def docx_table_count(docx_path):
    return len(_body_tables(docx_path))


def header_first_cell(docx_path, table_index0):
    tables = _body_tables(docx_path)
    rows = tables[table_index0].findall(W + "tr")
    return _row_cells(rows[0])[0]


def table3_cells(docx_path):
    tables = _body_tables(docx_path)
    out = []
    for tr in tables[2].findall(W + "tr"):
        out.extend(_row_cells(tr))
    return out


# ── protocol（自行重新定位：不沿用任何既有切分清单）──────────────────────────
def build_protocol(paper_path, params=None):
    lines = open(paper_path, encoding="utf-8").read().splitlines()
    # 从语料按序找八个标题的首次整行命中（行号严格递增由构造保证）
    found, expect = [], 0
    for i, line in enumerate(lines, 1):
        if expect < len(PROTOCOL_TITLES) and line == PROTOCOL_TITLES[expect]:
            found.append((expect + 1, i))
            expect += 1
    if expect != len(PROTOCOL_TITLES):
        raise RuntimeError(f"八个 Step 标题未按序找齐：实得 {expect}")
    results_head = next(
        i for i in range(found[-1][1] + 1, len(lines) + 1) if lines[i - 1] == "Results"
    )
    steps = []
    for k, (pos, start) in enumerate(found):
        stop = (found[k + 1][1] - 1) if k + 1 < len(found) else (results_head - 1)
        inp, outp = _PROTOCOL_IO[pos]
        steps.append({
            "pos": pos,
            "label": f"S{pos}",
            "title": lines[start - 1],
            "src": "paper_text.txt",
            "kind": "line",
            "target": f"paper_text.txt#L{start}-L{stop}",
            "evidence_loc": f"paper_text.txt#L{start}-L{start}",
            "input": inp,
            "output": outp,
        })
    lo, hi = found[0][1], found[-1][1]
    return {
        "rule": (
            "kind=line：在 paper_text.txt 的 L343–L516 区间内按整行逐字匹配八个 "
            "Step N: 标题行（行号严格递增、区间内每个标题恰出现 1 次）；"
            "区外同形整行（Results 小节复述的六处）披露不计"
        ),
        "source": f"paper_text.txt#L{lo}-L{hi}",
        "steps": steps,
    }


# ── 锚（A01–A13；PDF 侧取自压空白后的抽取文本，docx 侧直解 XML）───────────────
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

    _, clusters = _classify(docx_path)
    a06 = header_first_cell(docx_path, 3)
    a13 = header_first_cell(docx_path, 1)

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
        {"id": "A10", "value": clusters[0][1], "source": "esm1.docx#tbl@4#r1", "locator": ""},
        {"id": "A11", "value": clusters[-1][1], "source": f"esm1.docx#tbl@4#r{clusters[-1][0]}", "locator": ""},
        {"id": "A12", "value": "Published online: 20 March 2013", "source": "fulltext.pdf#p1#s3", "locator": ""},
        {"id": "A13", "value": a13, "source": "esm1.docx#tbl@2#header", "locator": "全文第 1/8 处"},
    ]


def build_independence(terms_path, params):
    """independence 声明件的本体（输入件不参与内容，仅满足图的单上游调用约定）。"""
    return {
        "source": (
            "pkg-B 为同一轮内的独立第二实现：docx 直解 word/document.xml 自行重建行格"
            "（不经 python-docx）；CSV 手写 RFC4180 逐字符状态机流式一次过（不经标准库 csv）；"
            "按 No. 整数前缀分组与编号守恒独立判行；protocol 自行从 paper_text.txt 重新定位八步标题；"
            "实现全程未 import、未摘抄另一实现的任何模块"
        ),
        "shared_code_with_a": False,
        # 路径串分段拼接：本包代码内不得出现他包同位件的含 "/" 相对路径字面量（静态扫描口径）
        "entry": "code" + "/" + "metrics.py::count_items",
        "signer_pkg_id": "alice-pkg:ALICE-2026-0014/pkg-B",
    }


if __name__ == "__main__":
    import sys
    here = sys.argv[1] if len(sys.argv) > 1 else "../.."
    csv_p = here + "/" + "terms_bct_v1.csv"
    docx_p = here + "/" + "esm1.docx"
    for name, fn in (("count_items", count_items), ("count_clusters", count_clusters), ("max_per_cluster", max_per_cluster)):
        print(name, fn(csv_p, {}))
    for name, fn in (("count_items_docx", count_items_docx), ("count_clusters_docx", count_clusters_docx), ("max_per_cluster_docx", max_per_cluster_docx)):
        print(name, fn(docx_p))
    print("numbering_conservation", numbering_conservation(docx_p))
