<!-- alice:human -->

run_id：r_b0bff8d2092c

# ALICE-2026-0012 · pkg-A（主实现：openpyxl 读法）

## 一句话结论
Norris 等（`2024`，Wellcome Open Research，DOI `10.12688/wellcomeopenres.20872.1`）BCIO 数据提取模板的 `6` 个表格结构量由本包从 xlsx 原件自算：sheet 数 10、本体表数 9、外部本体类实体数 123、数据行总数 1488、层级标签列总数 55、跨表重复 ID 数 23；与 pkg-B 的直解 sheet XML 独立实现逐一同值。

- **能拿去干什么**：复算该模板的结构清单；`13` 条锚（A01–A13）把语料自报数与件内定位接通；`4` 步开发规程（`paper_text.txt` L13–L22）落 `evidence/protocol.json`。
- **复现入口**：`code/metrics.py::main`（六量）；`code/make_evidence.py::main`（证据件）。
- **原文转述的数**：论文自报引文数 14（锚 A01，指回 `paper_text.txt#L25` 首句）；模板标题与版本日期自述见锚 A06／A12；映射对数按 Intro 表术语行头尾差分计（见 `deviations/readings.json` 的 `self_report_unmeasured`）。
- **语料面读数**：`corpus_lines`＝`43`，`para_lines`＝`26`，`body_ordinal`＝`1`（主文为全件 `6` 个 body 中文档序第一个）。
- **勘误（令方裁／变更单 S1-01_041）**：`para_lines` 初值「`24`」漏计表一之题注行与表头行，改为「`26`」——锁后题面 §5.2 归行规则（`<fig>`／`<table-wrap>` 题注行与表头行各一行）；监考官亲算、Q08 二轮、题面沿革勘误、语料行数互证四路同指。

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
  "b_only": [],
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
