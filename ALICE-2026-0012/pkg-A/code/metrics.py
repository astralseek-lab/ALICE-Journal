r"""pkg-A 主实现：K=6 量，openpyxl 读法（data_only=True）。

六个入口函数签名统一为 (xlsx_path, params)，供证据图 transform 与判分探针调用：
xlsx_path 为 bcio_data_extraction_template_v1.xlsx 的本机路径，params 为任务卡参数（本单为空）。

口径（题面 §二，写死）：
- 表头行＝该 sheet 内首格（A 列）逐字为 "ID" 的行（各 sheet 有标题行偏移，不按固定行号）；
- 列数＝表头行非空格数；数据行＝表头行之后 ID 列非空的行；合并单元格按左上角值计；
- 层级标签列两支都要吃到：^Level\s*\d+\s*label$ ｜ ^Level\s*label\s*\d+$；
- 脚注整句行（ID 列以 ^ 或 * 起首）不计入 T3/T4/T6。
"""
import json
import re
import sys

from openpyxl import load_workbook

LVL_NUM_FIRST = re.compile(r"^Level\s*\d+\s*label$")
LVL_LABEL_FIRST = re.compile(r"^Level\s*label\s*\d+$")


def _is_level_col(text):
    return bool(LVL_NUM_FIRST.match(text) or LVL_LABEL_FIRST.match(text))


def _norm_id(text):
    """ID 规范化：去首尾与内部空白、统一大小写。"""
    return "".join(str(text).split()).lower()


def _load(path):
    return load_workbook(path, data_only=True)


def _header_row_index(ws):
    """表头行＝首格为 "ID" 的行；返回 1 起算行号，找不到返回 None。"""
    for row in ws.iter_rows():
        first = row[0].value
        if isinstance(first, str) and first.strip() == "ID":
            return row[0].row
    return None


def _header_cols(ws, header_row):
    return [
        str(c.value).strip()
        for c in ws[header_row]
        if c.value is not None and str(c.value).strip() != ""
    ]


def _sheet_info(ws):
    hr = _header_row_index(ws)
    if hr is None:
        return None
    cols = _header_cols(ws, hr)
    return {"header_row": hr, "cols": cols, "level_cols": [c for c in cols if _is_level_col(c)]}


def _ontology_sheets(wb):
    """本体表三条同时成立：名不以 Intro 开头、表头行首格为 ID、表头含层级标签列。"""
    out = []
    for name in sorted(wb.sheetnames):
        if name.startswith("Intro"):
            continue
        info = _sheet_info(wb[name])
        if info is not None and len(info["level_cols"]) >= 1:
            out.append(name)
    return out


def _data_rows(ws, header_row):
    """表头行之后 ID 列非空的行；排除以 ^／* 起首的脚注整句行。产出 (行号, ID 串)。"""
    out = []
    for row in ws.iter_rows(min_row=header_row + 1):
        v = row[0].value
        if v is None or str(v).strip() == "":
            continue
        s = str(v).strip()
        if s.startswith("^") or s.startswith("*"):
            continue
        out.append((row[0].row, s))
    return out


def t1_sheet_count(xlsx_path, params):
    """T1：工作簿全部 sheet 数（含 Intro），按名字排序后取个数。"""
    wb = _load(xlsx_path)
    return len(sorted(wb.sheetnames))


def t2_ontology_sheets(xlsx_path, params):
    """T2：本体表数（三判据同时成立）。"""
    wb = _load(xlsx_path)
    return len(_ontology_sheets(wb))


def t3_external_class_count(xlsx_path, params):
    """T3：全部本体表 ID 列里非 BCIO 起首的值，规范化后按实体去重的个数。"""
    wb = _load(xlsx_path)
    seen = set()
    for name in _ontology_sheets(wb):
        ws = wb[name]
        for _rowno, idv in _data_rows(ws, _sheet_info(ws)["header_row"]):
            nid = _norm_id(idv)
            if not nid.startswith("bcio"):
                seen.add(nid)
    return len(seen)


def t4_data_rows_sum(xlsx_path, params):
    """T4：全部本体表数据行数之和（排除脚注整句行）。"""
    wb = _load(xlsx_path)
    total = 0
    for name in _ontology_sheets(wb):
        ws = wb[name]
        total += len(_data_rows(ws, _sheet_info(ws)["header_row"]))
    return total


def t5_level_cols_sum(xlsx_path, params):
    """T5：层级标签列总数（跨本体表相加；两支写法都吃到）。"""
    wb = _load(xlsx_path)
    total = 0
    for name in _ontology_sheets(wb):
        total += len(_sheet_info(wb[name])["level_cols"])
    return total


def t6_cross_sheet_ids(xlsx_path, params):
    """T6：规范化后 BCIO: 起首的同一 ID 出现在 ≥2 个本体表的个数。"""
    wb = _load(xlsx_path)
    seen = {}
    for name in _ontology_sheets(wb):
        ws = wb[name]
        for _rowno, idv in _data_rows(ws, _sheet_info(ws)["header_row"]):
            nid = _norm_id(idv)
            if nid.startswith("bcio"):
                seen.setdefault(nid, set()).add(name)
    return sum(1 for sheets in seen.values() if len(sheets) >= 2)


def column_vectors(xlsx_path):
    """另报料：key＝表名，value＝该表列数（表头行非空格数）。含 Intro。"""
    wb = _load(xlsx_path)
    out = {}
    for name in sorted(wb.sheetnames):
        info = _sheet_info(wb[name])
        out[name] = len(info["cols"]) if info else 0
    return out


def intro_meta(xlsx_path):
    """另报料：Intro sheet 的标题串（r1 首格）与版本日期串（r4 current as of 之后）。"""
    wb = _load(xlsx_path)
    ws = wb["Intro"]
    title = str(ws.cell(row=1, column=1).value).strip()
    r4 = str(ws.cell(row=4, column=1).value)
    m = re.search(r"current as of\s+([^);:.]+)", r4)
    version = m.group(1).strip() if m else ""
    return {"title": title, "version": version}


def non_bcio_rows(xlsx_path):
    """另报料：非 BCIO: 本体码数据行，key＝<表名>#r<行号>；序＝表名升序、同表行号升序。"""
    wb = _load(xlsx_path)
    out = []
    for name in _ontology_sheets(wb):
        ws = wb[name]
        for rowno, idv in _data_rows(ws, _sheet_info(ws)["header_row"]):
            if not _norm_id(idv).startswith("bcio"):
                out.append((name, rowno, idv))
    out.sort(key=lambda x: (x[0], x[1]))
    return [f"{name}#r{rowno}" for name, rowno, _idv in out]


def non_bcio_prefixes(xlsx_path):
    """另报料：非 BCIO: 前缀 → 行数（按行计）。"""
    wb = _load(xlsx_path)
    counts = {}
    for name in _ontology_sheets(wb):
        ws = wb[name]
        for _rowno, idv in _data_rows(ws, _sheet_info(ws)["header_row"]):
            if _norm_id(idv).startswith("bcio"):
                continue
            m = re.match(r"^([A-Za-z]+)", idv)
            prefix = m.group(1) if m else idv
            counts[prefix] = counts.get(prefix, 0) + 1
    return dict(sorted(counts.items()))


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
