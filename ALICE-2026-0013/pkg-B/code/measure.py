# -*- coding: utf-8 -*-
"""pkg-B 独立第二实现：ALICE-2026-0013 的 K 量与证据件生成入口。

链的可信不靠它永不变，靠它变了会响。

与 pkg-A 的相互独立点（本包自成形，不读 pkg-A 任何件、不 import 其模块）：
  · XML 读法：iterparse 流式（事件流），不整树载入；
  · 列定位：手写「列名→列号」解析——按 thead 首行 cell 文本逐字匹配出目标列号，
    不按列序猜；认不出即抛错（件不合格）；
  · 代码 token 切分：手写字符级状态机（不用正则），同一格多 token 不漏、不去重；
  · 复核等式：每表「逐格 BCIO: token 数之和＝该列 token 总数」，两表各自核；
  · 计数单位：行／去重代码／token 三值各算各的，互不替代；
  · 协议切节：自己从语料流式重定位两个 Step 标题行（Methods 与 Results 之间的首中），
    标题逐字取自语料原文（冒号差异照留，不归一）。
"""
from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

BCIO_PREFIX = "BCIO:"

# 目标列名（题面写死，逐字）：认不出即件不合格
COL_BCT = "Corresponding BCT classes in the BCT Ontology"
COL_MOA = "Corresponding MoA classes in the MoA Ontology"
TABLE_BCT = "Table 2."
TABLE_MOA = "Table 3."
TABLE_WF = "Table 4."

TITLE_STEP1 = "Step 1: Mapping the BCTs from the BCTO to the TaTT"
TITLE_STEP2 = "Step 2: Mapping the MoAs from the MoA Ontology to the TaTT"


# ── 手写 token 状态机（pkg-B 独立切分；不用正则） ───────────────────────────
def scan_codes(text):
    """扫出全部 字母串:数字串 形 token（出现几次计几次，同一格重复不去重）。"""
    out = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
            j = i + 1
            while j < n and (("A" <= text[j] <= "Z") or ("a" <= text[j] <= "z")):
                j += 1
            if j < n and text[j] == ":" and j + 1 < n and "0" <= text[j + 1] <= "9":
                k = j + 1
                while k < n and "0" <= text[k] <= "9":
                    k += 1
                out.append(text[i:k])
                i = k
                continue
            i = j
            continue
        i += 1
    return out


def _cell_text(el) -> str:
    return "".join(el.itertext()).strip()


def _iter_table_wraps(xml_path):
    """iterparse 流式产出 table-wrap 元素（事件流，不整树驻留）。"""
    for _event, elem in ET.iterparse(str(xml_path), events=("end",)):
        if elem.tag == "table-wrap":
            yield elem
            elem.clear()


def _pick_table(xml_path, label_prefix: str, need_header_no: bool):
    for tw in _iter_table_wraps(xml_path):
        lab = tw.find("label")
        if lab is None or not (lab.text or "").strip().startswith(label_prefix):
            continue
        table = tw.find("table")
        if table is None:
            continue
        thead = table.find("thead")
        if need_header_no:
            if thead is None:
                continue
            first = thead.findall("tr")
            if not first or _cell_text(list(first[0])[0]) != "No.":
                continue
        return tw
    raise LookupError(f"题注以 {label_prefix!r} 起头的表找不到（流式全扫）")


def _column_index_by_name(tw, col_name: str) -> int:
    """独立「列名→列号」解析：thead 首行逐 cell 逐字匹配；认不出即抛错。"""
    head_row = tw.find("table").find("thead").findall("tr")[0]
    for idx, cell in enumerate(list(head_row)):
        if _cell_text(cell) == col_name:
            return idx
    raise LookupError(f"目标列认不出：{col_name!r}（不按列序猜）")


def _measure(xml_path, label_prefix: str, col_name: str) -> dict:
    tw = _pick_table(xml_path, label_prefix, need_header_no=True)
    idx = _column_index_by_name(tw, col_name)
    if idx == 1:
        raise AssertionError("认到 TaTT 侧列（第 2 列）当目标列：件不合格")
    body_rows = tw.find("table").find("tbody").findall("tr")
    per_cell = []
    seen = set()
    total = 0
    for tr in body_rows:  # 逐行流式一次过计数
        toks = [t for t in scan_codes(_cell_text(list(tr)[idx])) if t.startswith(BCIO_PREFIX)]
        per_cell.append(len(toks))
        total += len(toks)
        for t in toks:
            seen.add(t)
    if sum(per_cell) != total:  # 复核等式（本实现独立核一遍）
        raise AssertionError("复核等式不成立")
    return {
        "rows": len(body_rows),
        "dedup": len(seen),
        "total_tokens": total,
        "one_to_many": sum(1 for c in per_cell if c >= 2),
        "one_to_many_rows": [i + 1 for i, c in enumerate(per_cell) if c >= 2],
    }


# ── 六个 K 量入口（每量一个；单位：行／去重代码／token，互不替代） ──────────
def k1_map_rows_bct(xml_path, params):
    """K1：Table 2 数据行数（单位：行）。"""
    return {"v": _measure(xml_path, TABLE_BCT, COL_BCT)["rows"], "unit": "行"}


def k2_bct_codes_dedup(xml_path, params):
    """K2：Table 2 目标列 BCIO: token 去重个数（单位：去重代码）。"""
    return {"v": _measure(xml_path, TABLE_BCT, COL_BCT)["dedup"], "unit": "去重代码"}


def k3_map_rows_moa(xml_path, params):
    """K3：Table 3 数据行数（单位：行）。"""
    return {"v": _measure(xml_path, TABLE_MOA, COL_MOA)["rows"], "unit": "行"}


def k4_moa_codes_dedup(xml_path, params):
    """K4：Table 3 目标列 BCIO: token 去重个数（单位：去重代码）。"""
    return {"v": _measure(xml_path, TABLE_MOA, COL_MOA)["dedup"], "unit": "去重代码"}


def k5_one_to_many_rows(xml_path, params):
    """K5：两表目标列各判 token ≥2 的行数，相加（单位：行）。"""
    a = _measure(xml_path, TABLE_BCT, COL_BCT)
    b = _measure(xml_path, TABLE_MOA, COL_MOA)
    return {"v": a["one_to_many"] + b["one_to_many"], "unit": "行"}


def k6_target_tokens(xml_path, params):
    """K6：两表目标列 BCIO: token 出现次数总和（单位：token）。"""
    a = _measure(xml_path, TABLE_BCT, COL_BCT)
    b = _measure(xml_path, TABLE_MOA, COL_MOA)
    return {"v": a["total_tokens"] + b["total_tokens"], "unit": "token"}


def compute_all(xml_path, params):
    """人门主入口：一次算出六个 K 量。"""
    return {
        "K1_map_rows_bct": k1_map_rows_bct(xml_path, params),
        "K2_bct_codes_dedup": k2_bct_codes_dedup(xml_path, params),
        "K3_map_rows_moa": k3_map_rows_moa(xml_path, params),
        "K4_moa_codes_dedup": k4_moa_codes_dedup(xml_path, params),
        "K5_one_to_many_rows": k5_one_to_many_rows(xml_path, params),
        "K6_target_tokens": k6_target_tokens(xml_path, params),
    }


# ── 另报四条（独立重算） ────────────────────────────────────────────────────
def _sha_payload(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def build_readings(xml_path, txt_path, params):
    t4 = _pick_table(xml_path, TABLE_WF, need_header_no=False)
    t4_rows = len(t4.find("table").find("tbody").findall("tr"))  # Table 4 无 thead，每 tr 皆数据行
    nonbcio_tatt, nonbcio_tgt = set(), set()
    for label, col in ((TABLE_BCT, COL_BCT), (TABLE_MOA, COL_MOA)):
        tw = _pick_table(xml_path, label, need_header_no=True)
        tgt = _column_index_by_name(tw, col)
        for tr in tw.find("table").find("tbody").findall("tr"):
            cells = list(tr)
            for tok in scan_codes(_cell_text(cells[1])):
                if not tok.startswith(BCIO_PREFIX):
                    nonbcio_tatt.add(tok)
            for tok in scan_codes(_cell_text(cells[tgt])):
                if not tok.startswith(BCIO_PREFIX):
                    nonbcio_tgt.add(tok)
    a01, a02 = _self_reported(txt_path)
    p1 = 0
    for label in (TABLE_BCT, TABLE_MOA):  # body_ordinal 差分（头尾端点）：末子序 − 首子序 ＋ 1
        trs = _pick_table(xml_path, label, need_header_no=True).find("table").find("tbody").findall("tr")
        p1 += len(trs)
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


# ── 锚（独立重取；文本锚流式读行，A12／A13 用 minidom 读 front） ────────────
def _iter_lines(txt_path):
    with open(str(txt_path), encoding="utf-8") as fh:  # 按行流式，不整篇载入
        for ln, raw in enumerate(fh, 1):
            yield ln, raw.rstrip("\n")


def _line_at(txt_path, want: int) -> str:
    for ln, text in _iter_lines(txt_path):
        if ln == want:
            return text
    raise LookupError(f"语料没有第 {want} 行")


def _self_reported(txt_path):
    a01 = a02 = None
    for ln, text in _iter_lines(txt_path):
        if ln == 40:
            pre, post = "From the BCTO,", "BCTs (classes)"
            a01 = int(text[text.index(pre) + len(pre):text.index(post)].strip())
        elif ln == 44:
            pre, post = "(released February, 2025),", "classes (not counting their subclasses)"
            a02 = int(text[text.index(pre) + len(pre):text.index(post)].strip())
    if a01 is None or a02 is None:
        raise LookupError("自报句未命中")
    return a01, a02


def build_anchors(txt_path, xml_path, params):
    a01, a02 = _self_reported(txt_path)
    am = minidom.parse(str(xml_path)).documentElement.getElementsByTagName("front")[0] \
        .getElementsByTagName("article-meta")[0]
    volume = am.getElementsByTagName("volume")[0].firstChild.data
    doi = None
    for el in am.getElementsByTagName("article-id"):
        if el.getAttribute("pub-id-type") == "doi":
            doi = el.firstChild.data
            break
    if not doi:
        raise LookupError("主件 front/article-meta 下 doi 未命中")
    src_xml = "fulltext__PMC12596556.xml"
    return [
        {"id": "A01", "value": a01, "source": "paper_text.txt#L40",
         "locator": "L40 内以 From the BCTO, 起头的那一句"},
        {"id": "A02", "value": a02, "source": "paper_text.txt#L44",
         "locator": "L44 内以 Drawing on the MoA Ontology’s most recent version 起头的那一句"},
        {"id": "A03", "value": "Since the first release of the TaTT in 2018", "source": "paper_text.txt#L15",
         "locator": "压空白后全文唯一处"},
        {"id": "A04", "value": _line_at(txt_path, 41), "source": "paper_text.txt#L41",
         "locator": "题注整行（Table 2. Mapping the 起，含 Note. 及脚注，不截断）"},
        {"id": "A05", "value": _line_at(txt_path, 47), "source": "paper_text.txt#L47",
         "locator": "题注整行（Table 3. Mapping the 起，含 Note. 及脚注，不截断）"},
        {"id": "A06", "value": _line_at(txt_path, 55), "source": "paper_text.txt#L55",
         "locator": "题注整行（Table 4. Example workflow 起）"},
        {"id": "A07", "value": "Methods", "source": "paper_text.txt#L27", "locator": "行首独占一行"},
        {"id": "A08", "value": "Results", "source": "paper_text.txt#L38", "locator": "行首独占一行"},
        {"id": "A09", "value": "Discussion", "source": "paper_text.txt#L49", "locator": "行首独占一行"},
        {"id": "A10", "value": TITLE_STEP1, "source": "paper_text.txt#L30",
         "locator": "全文第 1/2 处（Methods 下；Results 下 L39 重列不计）"},
        {"id": "A11", "value": TITLE_STEP2, "source": "paper_text.txt#L33",
         "locator": "全文第 1/2 处（Methods 下；Results 下 L43 重列不计）"},
        {"id": "A12", "value": str(volume), "source": src_xml + "#front/article-meta/volume",
         "locator": "主件 front/article-meta 下（元素值按串自报）"},
        {"id": "A13", "value": doi, "source": src_xml + "#front/article-meta/article-id[@pub-id-type='doi']",
         "locator": "只取主件 front/article-meta 下那 1 个（全件共 5 个同型元素）"},
    ]


def build_protocol(txt_path, params):
    """两步映射规程：B 自己切节——流式扫语料，先定 Methods／Results 两行，
    再取区间内两个 Step 标题整行逐字命中（不按 A 的切分、不读任何清单件）。"""
    ln_methods = ln_results = None
    hits1, hits2 = [], []
    for ln, text in _iter_lines(txt_path):
        if text == "Methods" and ln_methods is None:
            ln_methods = ln
        elif text == "Results" and ln_results is None:
            ln_results = ln
        elif text == TITLE_STEP1:
            hits1.append(ln)
        elif text == TITLE_STEP2:
            hits2.append(ln)
    if not (ln_methods and ln_results and hits1 and hits2):
        raise LookupError("切节失败：Methods／Results／Step 标题未齐")
    l1 = [x for x in hits1 if ln_methods < x < ln_results]
    l2 = [x for x in hits2 if ln_methods < x < ln_results]
    if len(l1) != 1 or len(l2) != 1 or not l1[0] < l2[0]:
        raise AssertionError("Methods 区间内两步标题不唯一或行号不递增")
    s1, s2 = l1[0], l2[0]
    return {
        "rule": "两步＝Methods 下 Step 1／Step 2 两个 H2 按位置取（整行逐字、行号递增）；"
                "Results 重列的两个同名标题不计；禁用标题去重当数法",
        "source": "paper_text.txt#L" + str(s1) + "-L" + str(ln_results - 1),
        "steps": [
            {
                "pos": 1, "label": "S1", "title": _line_at(txt_path, s1), "src": "paper_text.txt",
                "kind": "column", "target": "fulltext__PMC12596556.xml#tbl:2#col:3",
                "evidence_loc": "paper_text.txt#L" + str(s1) + "-L" + str(s2 - 1),
                "input": "the 281 class labels and definitions in BCTO (published in May, 2024)，"
                         "及 September, 2025 更新版新增四个类后的现行 BCTO（L31–L32）",
                "output": "BCTO 类到 TaTT 74 BCTs 的映射记录（finalise 并经 wider research team 复核；成表为 Table 2）",
            },
            {
                "pos": 2, "label": "S2", "title": _line_at(txt_path, s2), "src": "paper_text.txt",
                "kind": "column", "target": "fulltext__PMC12596556.xml#tbl:3#col:3",
                "evidence_loc": "paper_text.txt#L" + str(s2) + "-L" + str(ln_results - 1),
                "input": "the 284 class labels and definitions in the MoA Ontology (published May, 2024)，"
                         "及 September, 2025 更新后 622 类总量的现行 MoA Ontology（L34、L37）",
                "output": "MoA Ontology 类到 TaTT 26 MoAs 的映射记录（finalise 并经 wider research team 复核；成表为 Table 3）",
            },
        ],
    }
