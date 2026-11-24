<!-- alice:human -->
run_id＝`r_aefb213ba00a`（同一轮两包同串；件名面与研究夹名不是一回事）

# TaTT↔BCIO 映射表的 K 量复算包（pkg-A·主实现）

## 一句话结论
只读语料母件 `fulltext__PMC12596556.xml` 里题注以 `Table 2.`／`Table 3.` 起头的两张映射表，本包自算六个量：K1＝74 行、K2＝106 去重代码、K3＝26 行、K4＝60 去重代码、K5＝36 行、K6＝169 token。

## 口径与单位（每量一种单位，互不替代）
- K1／K3／K5 的单位是**行**（映射表 `<tbody>` 数据行；表头行另计）：K1＝74、K3＝26、K5＝36。
- K2／K4 的单位是**去重代码**（目标列内 `BCIO:` token 去重后的个数）：K2＝106、K4＝60。
- K6 的单位是**token**（两表目标列 `BCIO:` token 出现次数总和，不去重）：K6＝169；每表过复核等式「逐格 token 之和＝该列 token 总数」，两表各自成立再合算。
- 目标列认法：按 `thead` 首行 cell 文本**逐字**匹配列名认出第 `3` 列；第 `2` 列（TaTT 侧）不作目标列；`MFOEM:`／`GO:`／`ENVO:`／`ADDICTO:`／`MF:` 等非 `BCIO:` 码不进 K（逐码另报在 `deviations/readings.json`）。

## 与论文自报数的对照（不同物，不设 diff 件）
- 论文自报本体侧 85 个 BCT 类（锚 `A01`，`paper_text.txt#L40`）与 56 个 MoA 类（锚 `A02`，`paper_text.txt#L44`）。
- 自报是**类数**，K2／K4 数的是**目标列去重代码**——口径不同物，故不等属预期（两表题注脚注另注明部分行同时列出类与其子类）；两值按名表第 `4` 条进了 `deviations/readings.json` 的 `self_report_unmeasured`。

## K5 的判行清单（两表各自按行判 token≥`2`，逐行另报）
- `Table 2` 一对多行（No. 列取值）：`[1, 3, 10, 14, 17, 18, 19, 20, 23, 25, 28, 32, 34, 51, 54, 59, 61, 74]`。
- `Table 3` 一对多行（No. 列取值）：`[2, 3, 4, 5, 6, 7, 10, 12, 14, 15, 16, 17, 18, 20, 22, 24, 25, 26]`。
- 两表相加得 K5＝36 行。

## 另报（不进 K；落在 `deviations/readings.json`，恰 `4` 条）
- `table4_rows`（scalar）：`Table 4` 数据行数（该表无 `thead`）。
- `non_bcio_tatt_codes`（set）：两表 TaTT 侧列的非 `BCIO:` 码（本件为空集）。
- `target_non_bcio_codes`（set）：两表目标列的非 `BCIO:` 码（逐码升序，不计入 K2／K4）。
- `self_report_unmeasured`（map）：`A01`／`A02`／`P1`（`P1`＝映射对提取对数，取 body_ordinal 差分〔头尾端点〕）。

## 已知挂账（诚实声明）
- `判据 10` 的扰动探针对本件型无可施力对象：数源是 JATS XML，`owl:Class` 等四类可删元素各 `0` 个，`drop` 探针施力即报「元素不足」。按令方裁③-b 该件型探针不激活，六条主值 claim 仍照写 `sensitivity{input, perturb}` 申报；灵敏度由双实现旁证＋人判销账承接，不是本包做错。
- 语料形态：行级语料 `paper_text.txt` 共 `82` 行；主文 `<body>` 取文档序第 `1` 个（全件共 `8` 个 `<body>`）；按归行规则数得正文段落 `44` 行。

## 复现
- 复现入口：`code/kquant.py::compute_all`（人门主入口；六个单量入口见包内 `code/README.md`）。
- 原文转述的数：锚 `A01`＝85、锚 `A02`＝56（quoted，指回 `paper_text.txt` 行号）；锚 `A12`／`A13` 为语料 `front` 元素自述（串形）。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0013",
  "files": [
    "README.md",
    "task.json",
    "evidence.graph.json",
    "claims.jsonl",
    "env.lock",
    "inputs.lock",
    "code/"
  ],
  "extras": [
    "evidence/protocol.json",
    "evidence/anchors.json",
    "deviations/contrast.json",
    "deviations/readings.json"
  ],
  "not_applicable": [
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "deviations/tiers.json",
    "deviations/overlap.json"
  ],
  "must": [
    "evidence/protocol.json",
    "evidence/anchors.json",
    "deviations/contrast.json",
    "deviations/readings.json"
  ],
  "b_only": [],
  "corpus_lines": 82,
  "para_lines": 44,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/kquant.py::compute_all",
  "params": [
    "col_bct",
    "col_moa",
    "peer_held",
    "readings_names",
    "reads_count",
    "table_bct",
    "table_moa"
  ],
  "judge": "task.json#judge"
}
```
