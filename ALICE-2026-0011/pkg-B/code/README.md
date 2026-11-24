# code/ · 人门件（pkg-B 独立第二实现）

本目录是「七件」的第 7 件：变换实现 ＋ 唯一入口。本包是**独立第二实现**：
按小节流式读（语料逐行迭代、XML 走 iterparse 事件流，不整篇载入）、自切节
（从语料重新定位各 Step 步）、逐字回指（步标题不改写、不归一），不引用、
不导入另一实现的任何模块。

- **唯一入口**：`code/step_tally.py::tally_step_titles`（M1 主入口，序列法；
  四处对齐：`task.json#entry`／`evidence.graph.json#transform.entry`／
  `claims.jsonl#derivation_ref.entry`／README 人面段）。
- **三量入口各自成形**：`step_tally.py`（M1，编号恰 1..N 连续的序列校验法）、
  `table_one_terms.py`（M2，iterparse 流式数 Table 1 的 Term 列非空行）、
  `table_two_rows.py`（M3，按 tbody 归属直接数 Table 2 数据行）；
  每量一个入口函数，`def` 各恰一次。
- **证据件装配**：`assemble_evidence.py` 是 `evidence/`／`deviations/` 各交付件
  的生成入口；`declare_independence.py` 是 `evidence/independence.json` 的
  生成入口（A-1 口径，落点见 `evidence.graph.json` 各节点 `transform`）。
- **一句话**：链的可信不靠它永不变，靠它变了会响。
- **不放**：判分器、校验工具、库代码；数据件一律登记在 `inputs.lock`。
