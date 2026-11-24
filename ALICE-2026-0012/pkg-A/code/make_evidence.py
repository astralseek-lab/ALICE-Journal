"""pkg-A 证据生成：从输入件实算 evidence/ 与 deviations/ 四件。

跑法：python code/make_evidence.py <研究夹根>
产出：evidence/protocol.json、evidence/anchors.json、deviations/readings.json、
      deviations/contrast.json（本单无对照项，交 []）。
"""
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import metrics

TASK_ID = "ALICE-2026-0012"

PROTOCOL_TITLES = [
    "i) Scoping review of papers citing the BCIO",
    "ii) Development of data extraction template",
    "iii) Piloting and revising the data extraction template",
    "iv) Launch and maintenance of data extraction template",
]

# 每步 input／output：逐字取自语料段行（paper_text.txt L14/L18/L20/L22）
STEP_IO = [
    ("published papers reporting the development of lower-level ontologies within the BCIO",
     "Information on papers citing and using each ontology was extracted onto a Microsoft Excel template"),
    ("the identified examples of BCIO annotations from published papers",
     "A prototype BCIO data extraction template"),
    ("The prototype BCIO data extraction template",
     "‘BCIO data extraction template v1’"),
    ("The BCIO data extraction template v1",
     "made available online on the Open Science Framework and promoted via social media"),
]


def _canon_sha(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_protocol_span(txt_path):
    """在 paper_text.txt 里定位 Methods 下 i)–iv) 四个整行标题；返回 (行号列表, 段止列表)。"""
    lines = Path(txt_path).read_text(encoding="utf-8").splitlines()
    hits = {}
    for i, line in enumerate(lines, 1):
        if line in PROTOCOL_TITLES and line not in hits:
            hits[line] = i
    missing = [t for t in PROTOCOL_TITLES if t not in hits]
    if missing:
        raise RuntimeError(f"标题行定位失败: {missing}")
    starts = [hits[t] for t in PROTOCOL_TITLES]
    # 段止于下一个标题行的前一行；第 4 步止于 Results 标题行的前一行
    ends = []
    for k, s in enumerate(starts):
        if k + 1 < len(starts):
            ends.append(starts[k + 1] - 1)
        else:
            results_at = next(i for i, l in enumerate(lines, 1) if l == "Results" and i > s)
            ends.append(results_at - 1)
    return starts, ends


def write_protocol(research):
    lines = None  # 行号由 find_protocol_span 实算
    starts, ends = find_protocol_span(Path(research) / "paper_text.txt")
    steps = []
    for k, title in enumerate(PROTOCOL_TITLES):
        s, e = starts[k], ends[k]
        steps.append({
            "pos": k + 1,
            "label": f"S{k + 1}",
            "title": title,
            "src": "paper_text.txt",
            "kind": "line",
            "target": f"paper_text.txt#L{s}-L{ends[k]}",
            "evidence_loc": f"paper_text.txt#L{s}-L{s}",
            "input": STEP_IO[k][0],
            "output": STEP_IO[k][1],
        })
    doc = {
        "rule": "先列 Methods 下全部标题行，再按位置取 i)–iv) 四个 H2（整行逐字匹配）；禁用标题去重当数法",
        "source": "paper_text.txt#L13-L22",
        "steps": steps,
    }
    out = Path(research) / "pkg-A" / "evidence" / "protocol.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def compute_anchors(research):
    """13 锚：值全部从输入件实取，不预填。"""
    research = Path(research)
    lines = (research / "paper_text.txt").read_text(encoding="utf-8").splitlines()

    # A01：Results 节首个 p（L25）首句，"BCIO annotations were identified in" 紧接的整数
    l25 = lines[24]
    m = re.search(r"BCIO annotations were identified in\s+(\d+)", l25)
    a01 = int(m.group(1))

    # A02/A03/A13：XML front 元素
    root = ET.parse(research / "fulltext__PMC11170071.xml").getroot()
    am = root.find(".//front/article-meta")
    a02 = "".join(am.find("title-group/article-title").itertext())
    a13 = am.find("elocation-id").text
    ab = None
    for child in am:
        if child.tag.split("}")[-1] == "abstract" and child.get("abstract-type") is None:
            ab = child
            break
    ab_text = "".join(ab.itertext())
    m3 = re.search(r"developed in\s+(\w+)", ab_text)
    a03 = m3.group(1)

    # A05：paper.pdf 物理页 12 的 Table A1 题注行
    from pypdf import PdfReader
    page = PdfReader(str(research / "paper.pdf")).pages[11].extract_text()
    a05 = next(l.strip() for l in page.splitlines() if "Table A1" in l)

    # A06/A12：xlsx Intro
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
    out = Path(research) / "pkg-A" / "evidence" / "anchors.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def compute_readings(research, anchors):
    """另报名表恰五条（题面 §二.3 行序）。"""
    research = Path(research)
    xlsx = research / "bcio_data_extraction_template_v1.xlsx"
    meta = metrics.intro_meta(xlsx)
    vectors = metrics.column_vectors(xlsx)
    rows = metrics.non_bcio_rows(xlsx)
    prefixes = metrics.non_bcio_prefixes(xlsx)
    a01 = next(a["value"] for a in anchors if a["id"] == "A01")
    # P1 mapping_pairs_extracted：Intro 表术语行 r5–r13 的 body_ordinal 差分（令方七裁·6）
    p1 = 13 - 5 + 1

    items_meta = [{"key": k, "value": meta[k]} for k in sorted(meta)]
    items_vec = [{"key": k, "value": vectors[k]} for k in sorted(vectors)]
    items_rows = [{"key": k, "ord": i + 1} for i, k in enumerate(rows)]
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
    out = Path(research) / "pkg-A" / "deviations" / "readings.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def write_contrast(research):
    """本单无对照项：contrast_rows=0，交 []（不是 hits=0）。"""
    out = Path(research) / "pkg-A" / "deviations" / "contrast.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("[]\n", encoding="utf-8")
    return []


def main(research=None):
    research = Path(research or (sys.argv[1] if len(sys.argv) > 1 else "..")).resolve()
    anchors = write_anchors(research)
    protocol = write_protocol(research)
    readings = write_readings(research, anchors)
    write_contrast(research)
    print(json.dumps({
        "anchors": len(anchors),
        "steps": len(protocol["steps"]),
        "readings": [(r["name"], r["rows"]) for r in readings],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
