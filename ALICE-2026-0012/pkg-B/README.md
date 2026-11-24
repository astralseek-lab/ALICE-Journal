<!-- alice:human -->

run_id：r_b0bff8d2092c

# ALICE-2026-0012 · pkg-B（独立第二实现：直解 sheet XML）

## 一句话结论
同一批 `6` 个表格结构量由本包独立重算——xlsx 走 zipfile＋ElementTree 直解（不 import openpyxl）、遍历用显式栈／iterparse、计数流式一次过、表头行独立判定：sheet 数 10、本体表数 9、外部本体类实体数 123、数据行总数 1488、层级标签列总数 55、跨表重复 ID 数 23，与 pkg-A 逐一同值。

- **能拿去干什么**：作为 pkg-A 的独立旁证；`table_template_v1.csv` 全簿转储经 `csv` 模块（RFC4180）对读核验可读（仅可读性，不作第二数源）。
- **复现入口**：`code/metrics.py::main`（六量）；`code/make_evidence.py::main`（证据件五件，含独立性自述）。
- **原文转述的数**：论文自报引文数 14（锚 A01）；其余 `12` 条锚与 A 同值同位。
- **语料面读数**：`corpus_lines`＝`43`，`para_lines`＝`26`，`body_ordinal`＝`1`（本包独立判出，与 A 同值）。
- **勘误（令方裁／变更单 S1-01_041）**：`para_lines` 初值「`24`」漏计表一之题注行与表头行，改为「`26`」——同 A 勘误（锁后题面 §5.2 归行规则，本包与 A 同值同勘）。

## 判分器已知红（判分器严于签件；理由在案，供 F9 人判销账）
1. 判据 `10`（扰动探针）：六条主值 claim 均按签件 §六 申报 `sensitivity{input: xlsx 节点, perturb: drop:1}`。本尺的 `drop` 算子只定义在 RDF/XML 式与行式件上，`.xlsx` 两不沾，探针对该件型报「无法判」。按令方七裁第 `3` 条，xlsx-数源件型不激活探针；灵敏度由双实现旁证（openpyxl 对直解 sheet XML 同值）承接。
2. 判据 `1` 的 E1 扩面（锚回指）：A05（`paper.pdf#p12`）、A06（`Intro#r1`）、A12（`Intro#r4`）三条锚的 `source` 按签件 §三 写死；本尺 E1 扩面要求取值为原件裸文本子串，而 PDF／xlsx 是压缩二进制、裸文本不含取值，故三条记红。取值本身经实跑命中：A05 在 PDF 物理页 `12` 唯一；A06／A12 双读法（openpyxl 对直解 XML）同值。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0012",
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
    "deviations/contrast.json",
    "deviations/readings.json",
    "evidence/anchors.json",
    "evidence/independence.json",
    "evidence/protocol.json"
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
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 43,
  "para_lines": 26,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/metrics.py::main",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
