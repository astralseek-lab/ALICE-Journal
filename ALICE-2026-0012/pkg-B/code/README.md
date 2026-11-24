# pkg-B code/ 说明（独立第二实现）

- `metrics.py`：K=6 量，**直解 `xl/worksheets/*.xml`**（zipfile＋ElementTree，
  不 import openpyxl）；遍历用显式栈／iterparse，计数流式一次过；表头行按
  单元格文本独立判定。六入口函数与 A 同名（题面 §九 允许），实现各自成形。
- `make_evidence.py`：自行切节（Methods–Results 区间内整行匹配 i)–iv)）并
  生成 evidence/ 与 deviations/ 五件（含 `independence.json` 自述）。
- `csv` 对读核验在 `metrics.csv_readability_check`（csv 模块，RFC4180）。

复现：在本包 `code/` 目录下 `python metrics.py <xlsx 路径>`；`python make_evidence.py <研究夹根>`。
