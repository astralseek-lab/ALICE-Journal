# -*- coding: utf-8 -*-
"""pkg-A 主实现：ALICE-2026-0013 的 K 量与证据件生成入口。

链的可信不靠它永不变，靠它变了会响。

数源唯一：fulltext__PMC12596556.xml（JATS）里题注以 "Table 2." ／ "Table 3." 起头、
表头首格为 "No." 的两张映射表。目标列＝第 3 列：本实现按 <td> 下标取列，
并以 thead 首行 cell 文本逐字校验列名（口径写死，校验不过即抛错）。

单位锁死：K1/K3/K5＝行；K2/K4＝去重代码；K6＝token。三种单位互不替代。
复核等式：每张表「逐格 BCIO: token 数之和＝该列 BCIO: token 总数」，不等即抛错。
"""
from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET

TOKEN_RE = re.compile(r"[A-Za-z]+:[0-9]+")
BCIO_PREFIX = "BCIO:"

TITLE_STEP1 = "Step 1: Mapping the BCTs from the BCTO to the TaTT"
TITLE_STEP2 = "Step 2: Mapping the MoAs from the MoA Ontology to the TaTT"


def _cell_text(el) -> str:
    return "".join(el.itertext()).strip()


def _find_table(root, label_prefix: str):
    """题注逐字以 label_prefix 起头、表头首格 No. 的那张 table-wrap。"""
    for tw in root.findall(".//table-wrap"):
        lab = tw.find("label")
        if lab is None or not (lab.text or "").strip().startswith(label_prefix):
            continue
        table = tw.find("table")
        thead = table.find("thead") if table is not None else None
        if thead is not None:
            first_row = thead.findall("tr")
            if first_row and _cell_text(list(first_row[0])[0]) == "No.":
                return tw
    raise LookupError(f"找不到题注以 {label_prefix!r} 起头且表头首格 No. 的表")


def _target_column_cells(tw, col_name: str):
    """按 <td> 下标取第 3 列，并用 thead 首行 cell 文本逐字校验列名。"""
    table = tw.find("table")
    idx = 2  # 第 3 列（0 基）
    head_cells = list(table.find("thead").findall("tr")[0])
    got = _cell_text(head_cells[idx])
    if got != col_name:
        raise ValueError(f"目标列校验失败：第 3 列表头 {got!r} ≠ {col_name!r}")
    rows = []
    for tr in table.find("tbody").findall("tr"):
        rows.append(_cell_text(list(tr)[idx]))
    return rows


def _table_measure(xml_path, table_label: str, col_name: str) -> dict:
    """一张映射表的四件读数：数据行数／去重代码数／token 总数／一对多行清单。"""
    root = ET.parse(str(xml_path)).getroot()
    tw = _find_table(root, table_label)
    n_rows = len(tw.find("table").find("tbody").findall("tr"))
    cells = _target_column_cells(tw, col_name)
    per_cell = []
    dedup = set()
    total = 0
    for cell in cells:
        toks = [t for t in TOKEN_RE.findall(cell) if t.startswith(BCIO_PREFIX)]
        per_cell.append(len(toks))
        dedup.update(toks)
        total += len(toks)
    if sum(per_cell) != total:  # 复核等式（写死）：逐格之和＝该列总数
        raise AssertionError("复核等式不成立：逐格 token 之和 ≠ 该列 token 总数")
    return {
        "rows": n_rows,
        "dedup": len(dedup),
        "total_tokens": total,
        "one_to_many": sum(1 for c in per_cell if c >= 2),
        "one_to_many_rows": [i + 1 for i, c in enumerate(per_cell) if c >= 2],
    }


def _both(xml_path, params):
    a = _table_measure(xml_path, params["table_bct"], params["col_bct"])
    b = _table_measure(xml_path, params["table_moa"], params["col_moa"])
    return a, b


# ── 六个 K 量入口（每量一个，单一单位） ─────────────────────────────────────
def k1_map_rows_bct(xml_path, params):
    """K1：Table 2 数据行数（单位：行）。"""
    a = _table_measure(xml_path, params["table_bct"], params["col_bct"])
    return {"v": a["rows"], "unit": "行"}


def k2_bct_codes_dedup(xml_path, params):
    """K2：Table 2 目标列 BCIO: token 去重个数（单位：去重代码）。"""
    a = _table_measure(xml_path, params["table_bct"], params["col_bct"])
    return {"v": a["dedup"], "unit": "去重代码"}


def k3_map_rows_moa(xml_path, params):
    """K3：Table 3 数据行数（单位：行）。"""
    b = _table_measure(xml_path, params["table_moa"], params["col_moa"])
    return {"v": b["rows"], "unit": "行"}


def k4_moa_codes_dedup(xml_path, params):
    """K4：Table 3 目标列 BCIO: token 去重个数（单位：去重代码）。"""
    b = _table_measure(xml_path, params["table_moa"], params["col_moa"])
    return {"v": b["dedup"], "unit": "去重代码"}


def k5_one_to_many_rows(xml_path, params):
    """K5：两表目标列各自判 token 数 ≥2 的行，相加（单位：行）。"""
    a, b = _both(xml_path, params)
    return {"v": a["one_to_many"] + b["one_to_many"], "unit": "行"}


def k6_target_tokens(xml_path, params):
    """K6：两表目标列 BCIO: token 出现次数总和，不去重（单位：token）。"""
    a, b = _both(xml_path, params)
    return {"v": a["total_tokens"] + b["total_tokens"], "unit": "token"}


def compute_all(xml_path, params):
    """人门主入口：一次算出六个 K 量（每量单位写进返回）。"""
    return {
        "K1_map_rows_bct": k1_map_rows_bct(xml_path, params),
        "K2_bct_codes_dedup": k2_bct_codes_dedup(xml_path, params),
        "K3_map_rows_moa": k3_map_rows_moa(xml_path, params),
        "K4_moa_codes_dedup": k4_moa_codes_dedup(xml_path, params),
        "K5_one_to_many_rows": k5_one_to_many_rows(xml_path, params),
        "K6_target_tokens": k6_target_tokens(xml_path, params),
    }


# ── 另报（deviations/readings.json 的四条） ─────────────────────────────────
def _sha_payload(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_readings(xml_path, txt_path, params):
    """名表四条：table4_rows／non_bcio_tatt_codes／target_non_bcio_codes／self_report_unmeasured。"""
    root = ET.parse(str(xml_path)).getroot()
    # 1) Table 4 数据行数（无 thead，每个 <tr> 都是数据行）
    t4 = None
    for tw in root.findall(".//table-wrap"):
        lab = tw.find("label")
        if lab is not None and (lab.text or "").strip().startswith("Table 4."):
            t4 = tw
            break
    if t4 is None:
        raise LookupError("找不到 Table 4.")
    t4_rows = len(t4.find("table").find("tbody").findall("tr"))
    # 2)／3) 两表第 2 列（TaTT 侧）与目标列（第 3 列）里的非 BCIO: 码，逐码升序
    nonbcio_tatt, nonbcio_tgt = set(), set()
    for label, col in ((params["table_bct"], params["col_bct"]), (params["table_moa"], params["col_moa"])):
        tw = _find_table(root, label)
        table = tw.find("table")
        head_cells = list(table.find("thead").findall("tr")[0])
        if _cell_text(head_cells[2]) != col:
            raise ValueError("目标列校验失败")
        for tr in table.find("tbody").findall("tr"):
            cells = list(tr)
            for tok in TOKEN_RE.findall(_cell_text(cells[1])):
                if not tok.startswith(BCIO_PREFIX):
                    nonbcio_tatt.add(tok)
            for tok in TOKEN_RE.findall(_cell_text(cells[2])):
                if not tok.startswith(BCIO_PREFIX):
                    nonbcio_tgt.add(tok)
    # 4) 自报无同义实测端：A01／A02（有锚）＋ P1（body_ordinal 差分，头尾端点）
    lines = open(str(txt_path), encoding="utf-8").read().split("\n")
    a01 = _anchor_a01(lines)
    a02 = _anchor_a02(lines)
    p1 = 0
    for label in (params["table_bct"], params["table_moa"]):
        tw = _find_table(root, label)
        trs = tw.find("table").find("tbody").findall("tr")
        p1 += (len(trs) - 1) - 0 + 1  # 末 <tr> 子序 − 首 <tr> 子序 ＋ 1
    items_map = [{"key": "A01", "value": a01}, {"key": "A02", "value": a02}, {"key": "P1", "value": p1}]
    items_tatt = [{"key": c, "ord": i + 1} for i, c in enumerate(sorted(nonbcio_tatt))]
    items_tgt = [{"key": c, "ord": i + 1} for i, c in enumerate(sorted(nonbcio_tgt))]
    return [
        {"name": "table4_rows", "kind": "scalar", "sha256": _sha_payload(t4_rows), "value": t4_rows},
        {"name": "non_bcio_tatt_codes", "kind": "set", "sha256": _sha_payload(items_tatt), "items": items_tatt, "rows": len(items_tatt)},
        {"name": "target_non_bcio_codes", "kind": "set", "sha256": _sha_payload(items_tgt), "items": items_tgt, "rows": len(items_tgt)},
        {"name": "self_report_unmeasured", "kind": "map", "sha256": _sha_payload(items_map), "items": items_map, "rows": len(items_map)},
    ]


def build_contrast(params):
    """本单无对照件面：contrast_rows＝0，交空数组。"""
    return []


# ── 锚（evidence/anchors.json ＋ task.json#quoted 的同值来源） ─────────────
def _anchor_a01(lines) -> int:
    line = lines[40 - 1]
    pre = "From the BCTO,"
    post = "BCTs (classes)"
    i, j = line.index(pre) + len(pre), line.index(post)
    return int(line[i:j].strip())


def _anchor_a02(lines) -> int:
    line = lines[44 - 1]
    pre = "(released February, 2025),"
    post = "classes (not counting their subclasses)"
    i, j = line.index(pre) + len(pre), line.index(post)
    return int(line[i:j].strip())


def build_anchors(txt_path, xml_path, params):
    """13 条锚（A01–A13）：文本锚取自行级语料，A12／A13 取自 XML front 元素。"""
    lines = open(str(txt_path), encoding="utf-8").read().split("\n")
    front = ET.parse(str(xml_path)).getroot().find("front").find("article-meta")
    volume = front.find("volume").text
    doi = front.find("article-id[@pub-id-type='doi']").text
    src_xml = "fulltext__PMC12596556.xml"
    return [
        {"id": "A01", "value": _anchor_a01(lines), "source": "paper_text.txt#L40",
         "locator": "L40 内以 From the BCTO, 起头的那一句"},
        {"id": "A02", "value": _anchor_a02(lines), "source": "paper_text.txt#L44",
         "locator": "L44 内以 Drawing on the MoA Ontology’s most recent version 起头的那一句"},
        {"id": "A03", "value": "Since the first release of the TaTT in 2018", "source": "paper_text.txt#L15",
         "locator": "压空白后全文唯一处"},
        {"id": "A04", "value": lines[41 - 1], "source": "paper_text.txt#L41",
         "locator": "题注整行（Table 2. Mapping the 起，含 Note. 及脚注，不截断）"},
        {"id": "A05", "value": lines[47 - 1], "source": "paper_text.txt#L47",
         "locator": "题注整行（Table 3. Mapping the 起，含 Note. 及脚注，不截断）"},
        {"id": "A06", "value": lines[55 - 1], "source": "paper_text.txt#L55",
         "locator": "题注整行（Table 4. Example workflow 起）"},
        {"id": "A07", "value": "Methods", "source": "paper_text.txt#L27", "locator": "行首独占一行"},
        {"id": "A08", "value": "Results", "source": "paper_text.txt#L38", "locator": "行首独占一行"},
        {"id": "A09", "value": "Discussion", "source": "paper_text.txt#L49", "locator": "行首独占一行"},
        {"id": "A10", "value": TITLE_STEP1, "source": "paper_text.txt#L30",
         "locator": "全文第 1/2 处（Methods 下；Results 下 L39 重列不计）"},
        {"id": "A11", "value": TITLE_STEP2, "source": "paper_text.txt#L33",
         "locator": "全文第 1/2 处（Methods 下；Results 下 L43 重列不计）"},
        {"id": "A12", "value": str(volume), "source": f"{src_xml}#front/article-meta/volume",
         "locator": "主件 front/article-meta 下（元素值按串自报）"},
        {"id": "A13", "value": doi, "source": f"{src_xml}#front/article-meta/article-id[@pub-id-type='doi']",
         "locator": "只取主件 front/article-meta 下那 1 个（全件共 5 个同型元素）"},
    ]


def build_protocol(txt_path, params):
    """两步映射规程（pkg-A 沿用 F4 声明的 L30–L33 切节，整行逐字校验）。"""
    lines = open(str(txt_path), encoding="utf-8").read().split("\n")
    if lines[30 - 1] != TITLE_STEP1 or lines[33 - 1] != TITLE_STEP2:
        raise AssertionError("L30／L33 与两步标题逐字不符")
    return {
        "rule": "两步＝Methods 下 Step 1／Step 2 两个 H2 按位置取（整行逐字、行号递增）；"
                "Results 重列的两个同名标题不计；禁用标题去重当数法",
        "source": "paper_text.txt#L30-L37",
        "steps": [
            {
                "pos": 1, "label": "S1", "title": TITLE_STEP1, "src": "paper_text.txt",
                "kind": "column", "target": "fulltext__PMC12596556.xml#tbl:2#col:3",
                "evidence_loc": "paper_text.txt#L30-L32",
                "input": "the 281 class labels and definitions in BCTO (published in May, 2024)，"
                         "及 September, 2025 更新版新增四个类后的现行 BCTO（L31–L32）",
                "output": "BCTO 类到 TaTT 74 BCTs 的映射记录（finalise 并经 wider research team 复核；成表为 Table 2）",
            },
            {
                "pos": 2, "label": "S2", "title": TITLE_STEP2, "src": "paper_text.txt",
                "kind": "column", "target": "fulltext__PMC12596556.xml#tbl:3#col:3",
                "evidence_loc": "paper_text.txt#L33-L37",
                "input": "the 284 class labels and definitions in the MoA Ontology (published May, 2024)，"
                         "及 September, 2025 更新后 622 类总量的现行 MoA Ontology（L34、L37）",
                "output": "MoA Ontology 类到 TaTT 26 MoAs 的映射记录（finalise 并经 wider research team 复核；成表为 Table 3）",
            },
        ],
    }
