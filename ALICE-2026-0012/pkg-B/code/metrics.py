"""pkg-B 独立第二实现：K=6 量，直解 xl/worksheets/*.xml（zipfile + ElementTree）。

与 pkg-A 的关系：换实现、不换口径。本模块——
- 不 import openpyxl（也不 import pkg-A 的任何模块）；
- 遍历用显式栈／iterparse 流式（迭代，不递归）；
- 计数逐行流式一次过，不全表载入内存后再数；
- 表头行独立找（按单元格文本判，不读任何外部行号清单）。

入口函数签名同样是 (xlsx_path, params)，供证据图 transform 与判分探针调用。
"""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

LEVEL_PATTERNS = (re.compile(r"^Level\s*\d+\s*label$"), re.compile(r"^Level\s*label\s*\d+$"))


def _looks_like_level_col(text):
    return any(p.match(text) for p in LEVEL_PATTERNS)


def _normalize_id(text):
    return "".join(str(text).split()).lower()


def _col_index(cell_ref):
    letters = re.match(r"[A-Z]+", cell_ref).group(0)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def _shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    out = []
    # iterparse 流式过 sharedStrings
    with zf.open("xl/sharedStrings.xml") as fh:
        for _event, elem in ET.iterparse(fh, events=("end",)):
            if elem.tag == f"{NS}si":
                out.append("".join(t.text or "" for t in elem.iter(f"{NS}t")))
                elem.clear()
    return out


def _sheet_targets(zf):
    """sheet 名 → 工作表 XML 路径。workbook.xml 与 rels 都是小件，直接解析。"""
    relroot = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rels = {r.get("Id"): r.get("Target") for r in relroot}
    wbroot = ET.fromstring(zf.read("xl/workbook.xml"))
    out = []
    sheets_el = wbroot.find(f"{NS}sheets")
    for sh in list(wbroot.iter(f"{NS}sheet")):
        target = rels[sh.get(f"{NS_R}id")]
        out.append((sh.get("name"), target if target.startswith("xl/") else "xl/" + target))
    return out


def _iter_rows(zf, sheet_path, shared):
    """流式逐行产出 (行号, {列序号: 值})——不全表载入。"""
    with zf.open(sheet_path) as fh:
        for _event, row in ET.iterparse(fh, events=("end",)):
            if row.tag != f"{NS}row":
                continue
            rowno = int(row.get("r"))
            cells = {}
            for c in row.findall(f"{NS}c"):
                ci = _col_index(c.get("r"))
                ctype = c.get("t")
                v = c.find(f"{NS}v")
                if ctype == "s":
                    val = shared[int(v.text)] if v is not None and v.text is not None else None
                elif ctype == "inlineStr":
                    is_el = c.find(f"{NS}is")
                    val = "".join(t.text or "" for t in is_el.iter(f"{NS}t")) if is_el is not None else None
                else:
                    val = v.text if v is not None else None
                if val is not None:
                    cells[ci] = val
            yield rowno, cells
            row.clear()


def _sheet_scan(zf, sheet_path, shared):
    """一次流式扫描，同时判出：表头行号、表头列清单、数据行 (行号, ID) 列表。"""
    header_row = None
    header_cols = []
    data = []
    for rowno, cells in _iter_rows(zf, sheet_path, shared):
        first = cells.get(0)
        if header_row is None:
            if isinstance(first, str) and first.strip() == "ID":
                header_row = rowno
                header_cols = [str(v).strip() for _ci, v in sorted(cells.items()) if str(v).strip() != ""]
            continue
        if first is None or str(first).strip() == "":
            continue
        s = str(first).strip()
        if s.startswith("^") or s.startswith("*"):
            continue  # 脚注整句行不是实体
        data.append((rowno, s))
    return header_row, header_cols, data


def _scan_book(xlsx_path):
    """整簿一次过：每表一份扫描结果。"""
    zf = zipfile.ZipFile(xlsx_path)
    shared = _shared_strings(zf)
    book = {}
    for name, target in _sheet_targets(zf):
        book[name] = _sheet_scan(zf, target, shared)
    zf.close()
    return book


def _ontology_sheet_names(book):
    names = []
    for name in sorted(book):
        if name.startswith("Intro"):
            continue
        header_row, header_cols, _data = book[name]
        if header_row is None:
            continue
        if any(_looks_like_level_col(c) for c in header_cols):
            names.append(name)
    return names


def t1_sheet_count(xlsx_path, params):
    """T1：全部 sheet 数（含 Intro），按名排序取个数。"""
    zf = zipfile.ZipFile(xlsx_path)
    names = sorted(name for name, _t in _sheet_targets(zf))
    zf.close()
    return len(names)


def t2_ontology_sheets(xlsx_path, params):
    """T2：名不以 Intro 开头 且 表头行首格为 ID 且 表头含层级标签列 的 sheet 数。"""
    return len(_ontology_sheet_names(_scan_book(xlsx_path)))


def t3_external_class_count(xlsx_path, params):
    """T3：非 BCIO 起首的 ID 按规范化串去重后的实体数。"""
    book = _scan_book(xlsx_path)
    entities = set()
    for name in _ontology_sheet_names(book):
        for _rowno, idv in book[name][2]:
            nid = _normalize_id(idv)
            if not nid.startswith("bcio"):
                entities.add(nid)
    return len(entities)


def t4_data_rows_sum(xlsx_path, params):
    """T4：全部本体表数据行数之和（脚注整句行已排除）。"""
    book = _scan_book(xlsx_path)
    return sum(len(book[name][2]) for name in _ontology_sheet_names(book))


def t5_level_cols_sum(xlsx_path, params):
    """T5：层级标签列总数（两种写法都计入，跨表相加）。"""
    book = _scan_book(xlsx_path)
    total = 0
    for name in _ontology_sheet_names(book):
        total += sum(1 for c in book[name][1] if _looks_like_level_col(c))
    return total


def t6_cross_sheet_ids(xlsx_path, params):
    """T6：规范化后 BCIO: 起首 ID 出现在 ≥2 个本体表的个数。"""
    book = _scan_book(xlsx_path)
    where = {}
    for name in _ontology_sheet_names(book):
        for _rowno, idv in book[name][2]:
            nid = _normalize_id(idv)
            if nid.startswith("bcio"):
                where.setdefault(nid, set()).add(name)
    return sum(1 for sheets in where.values() if len(sheets) >= 2)


def column_vectors(xlsx_path):
    """另报料：key＝表名，value＝表头行非空格数。"""
    book = _scan_book(xlsx_path)
    return {name: (len(book[name][1]) if book[name][0] is not None else 0) for name in sorted(book)}


def non_bcio_detail(xlsx_path):
    """另报料：非 BCIO 行清单（key＝<表名>#r<行号>）与前缀分布，按行计。"""
    book = _scan_book(xlsx_path)
    keys = []
    prefixes = {}
    for name in _ontology_sheet_names(book):
        for rowno, idv in book[name][2]:
            if _normalize_id(idv).startswith("bcio"):
                continue
            keys.append(f"{name}#r{rowno}")
            m = re.match(r"^([A-Za-z]+)", idv)
            pfx = m.group(1) if m else idv
            prefixes[pfx] = prefixes.get(pfx, 0) + 1
    keys.sort(key=lambda k: (k.split("#r")[0], int(k.split("#r")[1])))
    return keys, dict(sorted(prefixes.items()))


def intro_meta(xlsx_path):
    """另报料：Intro 表 r1 标题串与 r4 版本日期串（直解 sheet XML 取格）。"""
    zf = zipfile.ZipFile(xlsx_path)
    shared = _shared_strings(zf)
    target = dict(_sheet_targets(zf))["Intro"]
    wanted = {}
    for rowno, cells in _iter_rows(zf, target, shared):
        if rowno in (1, 4) and cells.get(0) is not None:
            wanted[rowno] = str(cells[0])
        if rowno > 4:
            break
    zf.close()
    m = re.search(r"current as of\s+([^);:.]+)", wanted.get(4, ""))
    return {"title": wanted.get(1, "").strip(), "version": m.group(1).strip() if m else ""}


def csv_readability_check(csv_path):
    """G3 对读件核验：csv 模块（RFC4180 状态机）全簿转储可读、行数大于零。"""
    import csv
    with open(csv_path, newline="", encoding="utf-8") as fh:
        n = sum(1 for _row in csv.reader(fh))
    return n


ENTRIES = {
    "T1_sheet_count": t1_sheet_count,
    "T2_ontology_sheets": t2_ontology_sheets,
    "T3_external_class_count": t3_external_class_count,
    "T4_data_rows_sum": t4_data_rows_sum,
    "T5_level_cols_sum": t5_level_cols_sum,
    "T6_cross_sheet_ids": t6_cross_sheet_ids,
}


def main(xlsx_path=None):
    """主入口：六量一次算全，打印 JSON。"""
    path = xlsx_path or (sys.argv[1] if len(sys.argv) > 1 else "../bcio_data_extraction_template_v1.xlsx")
    result = {name: fn(path, {}) for name, fn in ENTRIES.items()}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
