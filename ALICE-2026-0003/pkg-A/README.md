<!-- alice:human -->

# Delivering behaviour change interventions: mode of delivery ontology 的结构计数复核

## 六个量全部自算，两处独立实现同值

对 MoD 本体发布快照按题面口径做纯结构计数：本地类 L1 = 135，子类边 L2 = 324，
对象属性 L3 = 50，注释属性 L4 = 56，最大层级深度 L5 = 5（单位 edges），本地叶类 L6 = 93。
论文自报终版为 65 个实体（quoted A01，指回 Results 末段终版句），与本地实测之差已按 IRI 列名落在
`deviations/diff_A01.json`；专家反馈回收 16 份（quoted A03）。
命名空间不由类名前缀判定：host 与目录都解析自本体身份 IRI；三条被禁读法的对照值（均巧合命中同一集合）
另记于 `deviations/contrast.json`，标注「巧合，不是判据」。

- **能拿去干什么**：复算 BCIO MoD 本体的六个结构量，并与论文自报值对账
- **复现入口**：`code/quantities.py::parse`（唯一入口，按 `quantity` 分派）
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
  "entry": "code/quantities.py::parse",
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
    "deviations/diff_A01.json"
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
