# code/ · 人门件（pkg-B 独立第二实现）

本目录是「七件」的第 7 件：变换实现 ＋ 唯一入口。本实现与主实现互不为据：
不读对方任何件、不 import 对方模块；XML 走 iterparse 事件流、列名→列号逐字解析、
token 手写状态机切分、协议自行流式切节（换实现，不换口径）。

- **唯一入口（人门主入口）**：`measure.py::compute_all`——一次算出六个 K 量；
  六个单量入口 `k1_map_rows_bct`／`k2_bct_codes_dedup`／`k3_map_rows_moa`／
  `k4_moa_codes_dedup`／`k5_one_to_many_rows`／`k6_target_tokens` 与之一一对应，
  同名串对齐于 `evidence.graph.json#nodes[].transform.entry` 与 `claims.jsonl#derivation_ref.entry`。
- **证据件生成入口**：`build_anchors`／`build_protocol`／`build_readings`／`build_contrast`
  逐件对应本包 `evidence/` 与 `deviations/` 下的产物（落点见 `evidence.graph.json`
  各 artifact 节点的 transform）；`evidence/independence.json` 由 `make_independence.py::build_independence` 生成（四字段）。
- **数源**：只读语料母件 XML 的两张映射表；行级语料只作锚与 protocol 的文本面。
- **单位**：行／去重代码／token 三值各算各的，互不替代；每表过一道复核等式。
- 链的可信不靠它永不变，靠它变了会响。
