# code/ · 人门件（pkg-A 主实现）

本目录是「七件」的第 7 件：变换实现 ＋ 唯一入口。

- **唯一入口**：`code/count_steps.py::count_steps`（M1 主入口；同一入口名在
  `task.json#entry`／`evidence.graph.json#nodes[].transform.entry`／
  `claims.jsonl#derivation_ref.entry`／README 人面段「复现入口」四处对齐）。
- **三量入口各自成形**：`count_steps.py`（M1，步骤标题数，区间计数法）、
  `count_table1_terms.py`（M2，Table 1 术语行数）、`count_table2_rows.py`
  （M3，Table 2 数据行数）；每量一个入口函数，`def` 各恰一次。
- **证据件装配**：`make_evidence.py` 是 `evidence/`／`deviations/` 各交付件的
  生成入口（A-1 口径：每件产物能在本目录指到一行，落点见 `evidence.graph.json`
  里各节点的 `transform{code,entry,params}`）。
- **调用面**：入口吃一个路径实参（输入件副本落研究号夹根），返回带 `v` 的字典。
- **一句话**：链的可信不靠它永不变，靠它变了会响。
- **不放**：判分器、校验工具、库代码；数据件一律登记在 `inputs.lock`，不入本目录。
