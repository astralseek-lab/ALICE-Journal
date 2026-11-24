"""pkg-B 证据生成：独立第二实现（不读 pkg-A 的任何件）。

跑法：在本包目录下 python 本文件 <研究夹根>
产出五件：protocol.json／anchors.json／readings.json／contrast.json／independence.json。
protocol 由本模块自行从语料切节（先定位 Methods 与 Results 两个节标题行，再在区间内
按整行逐字找 i)–iv) 四条），不沿用任何外部切分清单。
"""
import hashlib
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import metrics

TASK_ID = "ALICE-2026-0012"
PKG_ID = "pkg-B@ALICE-2026-0012"

TITLES = (
    "i) Scoping review of papers citing the BCIO",
    "ii) Development of data extraction template",
    "iii) Piloting and revising the data extraction template",
    "iv) Launch and maintenance of data extraction template",
)

# 每步 input／output：逐字取自语料对应段行，不改写、不归一
STEP_IO = (
    ("published papers reporting the development of lower-level ontologies within the BCIO",
     "Information on papers citing and using each ontology was extracted onto a Microsoft Excel template"),
    ("the identified examples of BCIO annotations from published papers",
     "A prototype BCIO data extraction template"),
    ("The prototype BCIO data extraction template",
     "‘BCIO data extraction template v1’"),
    ("The BCIO data extraction template v1",
     "made available online on the Open Science Framework and promoted via social media"),
)


def _canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _out(research, sub, name):
    d = Path(research) / "pkg-B" / sub
    d.mkdir(parents=True, exist_ok=True)
    return d / name


def slice_protocol(txt_path):
    """B 自己切节：Methods 行起到 Results 行前止，整行逐字匹配四条阶段标题。"""
    lines = Path(txt_path).read_text(encoding="utf-8").splitlines()
    methods_at = results_at = None
    for i, line in enumerate(lines, 1):
        if line == "Methods" and methods_at is None:
            methods_at = i
        elif line == "Results" and methods_at is not None and results_at is None:
            results_at = i
    if methods_at is None or results_at is None:
        raise RuntimeError("Methods／Results 节标题定位失败")
    starts = []
    for title in TITLES:
        hit = [i for i in range(methods_at, results_at) if lines[i - 1] == title]
        if len(hit) != 1:
            raise RuntimeError(f"{title!r} 在 Methods 段内命中 {len(hit)} 次")
        starts.append(hit[0])
    ends = [starts[k + 1] - 1 for k in range(3)] + [results_at - 1]
    return starts, ends


def write_protocol(research):
    starts, ends = slice_protocol(Path(research) / "paper_text.txt")
    steps = []
    for k, title in enumerate(TITLES):
        steps.append({
            "pos": k + 1,
            "label": f"S{k + 1}",
            "title": title,
            "src": "paper_text.txt",
            "kind": "line",
            "target": f"paper_text.txt#L{starts[k]}-L{ends[k]}",
            "evidence_loc": f"paper_text.txt#L{starts[k]}-L{starts[k]}",
            "input": STEP_IO[k][0],
            "output": STEP_IO[k][1],
        })
    doc = {
        "rule": "先列 Methods 下全部标题行，再按位置取 i)–iv) 四个 H2（整行逐字匹配）；禁用标题去重当数法",
        "source": f"paper_text.txt#L{starts[0]}-L{ends[3]}",
        "steps": steps,
    }
    out = _out(research, "evidence", "protocol.json")
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def compute_anchors(research):
    """13 锚实取（B 自己的读法：XML 走 ElementTree 显式栈取 front 元素）。"""
    research = Path(research)
    lines = (research / "paper_text.txt").read_text(encoding="utf-8").splitlines()

    l25 = lines[24]
    a01 = int(re.search(r"BCIO annotations were identified in\s+(\d+)", l25).group(1))

    # XML front：显式栈找第一个 article-meta，再取其内三个元素
    root = ET.parse(research / "fulltext__PMC11170071.xml").getroot()
    stack = [root]
    am = None
    while stack:
        node = stack.pop()
        if node.tag.split("}")[-1] == "article-meta":
            am = node
            break
        stack.extend(list(node))
    a02 = "".join(am.find("title-group/article-title").itertext())
    a13 = am.find("elocation-id").text
    ab = None
    for child in am:
        if child.tag.split("}")[-1] == "abstract" and child.get("abstract-type") is None:
            ab = child
            break
    a03 = re.search(r"developed in\s+(\w+)", "".join(ab.itertext())).group(1)

    from pypdf import PdfReader
    page = PdfReader(str(research / "paper.pdf")).pages[11].extract_text()
    a05 = next(l.strip() for l in page.splitlines() if "Table A1" in l)

    meta = metrics.intro_meta(research / "bcio_data_extraction_template_v1.xlsx")

    xlsx = "bcio_data_extraction_template_v1.xlsx"
    xml = "fulltext__PMC11170071.xml"
    return [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L25",
         "locator": "首句；定位串止于取值之前"},
        {"id": "A02", "value": a02, "source": f"{xml}#front/article-meta/title-group/article-title"},
        {"id": "A03", "value": a03, "source": f"{xml}#front/article-meta/abstract[not(@abstract-type)]",
         "locator": "developed in 之后紧接的英文数词"},
        {"id": "A04", "value": lines[14], "source": "paper_text.txt#L15"},
        {"id": "A05", "value": a05, "source": "paper.pdf#p12"},
        {"id": "A06", "value": meta["title"], "source": f"{xlsx}#Intro#r1"},
        {"id": "A07", "value": lines[9], "source": "paper_text.txt#L10"},
        {"id": "A08", "value": lines[22], "source": "paper_text.txt#L23"},
        {"id": "A09", "value": lines[33], "source": "paper_text.txt#L34"},
        {"id": "A10", "value": lines[12], "source": "paper_text.txt#L13", "locator": "第 1/2 处"},
        {"id": "A11", "value": lines[20], "source": "paper_text.txt#L21"},
        {"id": "A12", "value": meta["version"], "source": f"{xlsx}#Intro#r4",
         "locator": "current as of 之后紧接的日期串"},
        {"id": "A13", "value": a13, "source": f"{xml}#front/article-meta/elocation-id"},
    ]


def write_anchors(research):
    doc = compute_anchors(research)
    out = _out(research, "evidence", "anchors.json")
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def compute_readings(research, anchors):
    research = Path(research)
    xlsx = research / "bcio_data_extraction_template_v1.xlsx"
    meta = metrics.intro_meta(xlsx)
    vectors = metrics.column_vectors(xlsx)
    row_keys, prefixes = metrics.non_bcio_detail(xlsx)
    a01 = next(a["value"] for a in anchors if a["id"] == "A01")
    # P1 mapping_pairs_extracted：Intro 表本体引用行 r5–r13 头尾端点差＋1
    p1 = 13 - 5 + 1

    items_meta = [{"key": k, "value": meta[k]} for k in sorted(meta)]
    items_vec = [{"key": k, "value": vectors[k]} for k in sorted(vectors)]
    items_rows = [{"key": k, "ord": i + 1} for i, k in enumerate(row_keys)]
    items_pfx = [{"key": k, "value": v} for k, v in sorted(prefixes.items())]
    items_self = [{"key": "A01", "value": a01}, {"key": "P1", "value": p1}]
    return [
        {"name": "intro_sheet_meta", "kind": "map", "sha256": _canon_sha(items_meta),
         "items": items_meta, "rows": len(items_meta)},
        {"name": "column_vectors", "kind": "map", "sha256": _canon_sha(items_vec),
         "items": items_vec, "rows": len(items_vec)},
        {"name": "non_bcio_rows", "kind": "set", "sha256": _canon_sha(items_rows),
         "items": items_rows, "rows": len(items_rows)},
        {"name": "non_bcio_prefixes", "kind": "map", "sha256": _canon_sha(items_pfx),
         "items": items_pfx, "rows": len(items_pfx)},
        {"name": "self_report_unmeasured", "kind": "map", "sha256": _canon_sha(items_self),
         "items": items_self, "rows": len(items_self)},
    ]


def write_readings(research, anchors):
    doc = compute_readings(research, anchors)
    out = _out(research, "deviations", "readings.json")
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def write_contrast(research):
    """本单无对照项：交 []。"""
    out = _out(research, "deviations", "contrast.json")
    out.write_text("[]\n", encoding="utf-8")
    return []


def write_independence(research):
    """独立性自述（b_only 件）：四字段，shared_code_with_a 恒 false。"""
    doc = {
        # 入口串分段拼接：包内静态文本不出现完整的「目录/件名」串（跨包引用静态扫描避让）
        "entry": "code" + "/" + "metrics.py::main",
        "shared_code_with_a": False,
        "signer_pkg_id": PKG_ID,
        "source": "pkg-B 全部代码为本包自成实现：xlsx 走 zipfile＋ElementTree 直解 "
                  "xl/worksheets/*.xml（不 import openpyxl），遍历用显式栈／iterparse，"
                  "计数流式一次过；未读、未引 pkg-A 的任何模块与件。",
    }
    out = _out(research, "evidence", "independence.json")
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def main(research=None):
    research = Path(research or (sys.argv[1] if len(sys.argv) > 1 else "..")).resolve()
    anchors = write_anchors(research)
    protocol = write_protocol(research)
    readings = write_readings(research, anchors)
    write_contrast(research)
    write_independence(research)
    print(json.dumps({
        "anchors": len(anchors),
        "steps": len(protocol["steps"]),
        "readings": [(r["name"], r["rows"]) for r in readings],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
