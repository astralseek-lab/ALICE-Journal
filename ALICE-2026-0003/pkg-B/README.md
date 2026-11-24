<!-- alice:human -->

# MoD 本体结构计数的旁证包（第二套实现）

## 换实现重算六量并逐条对账十三锚

本包用另一套实现（DOM 加载后显式栈迭代、单遍累计、`urlsplit` 独立划界）重算同一批量：
本地类 L1 = 135，子类边 L2 = 324，对象属性 L3 = 50，注释属性 L4 = 56，
最大层级深度 L5 = 5（单位 edges），本地叶类 L6 = 93；两读法、三档、三个对照值均各自独立算出。
十三锚逐条对账落在 `verdict.json`；论文自报终版 65 个实体（quoted A01）与实测之差按 IRI 列名于
`deviations/A01.jsonl` 与 `deviations/diff_A01.json`；回收 16 份（quoted A03）。

- **能拿去干什么**：独立复核第一套实现的六个量与十三锚对账
- **复现入口**：`code/b_quantities.py::parse`（唯一入口，按 `quantity` 分派）
- **原文转述的数**：终版 65 个实体（quoted A01）；回收 16 份（quoted A03）


<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0003",
  "files": [
    "README.md",
    "task.json",
    "evidence.graph.json",
    "claims.jsonl",
    "env.lock",
    "inputs.lock",
    "code/"
  ],
  "entry": "code/b_quantities.py::parse",
  "params": [
    "quantity",
    "rule"
  ],
  "judge": "task.json#judge",
  "extras": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "evidence/independence.json",
    "verdict.json",
    "replay.receipt.json",
    "deviations/A01.jsonl"
  ],
  "not_applicable": [
    "evidence/mapping.jsonl"
  ],
  "must": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 77,
  "para_lines": 44,
  "body_ordinal": 1,
  "nulls": [
    {
      "path": "protocol.steps[0].input",
      "reason": "首步输入为 20 篇外抽语料报告，无既有版本产出可指名"
    },
    {
      "path": "protocol.steps[5].input",
      "reason": "第六步输入为本体实体自身，正文未逐字指名来自哪一节或哪一版的已有产出"
    }
  ]
}
```
