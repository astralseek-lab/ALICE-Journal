<!-- alice:human -->

# Wright2025Population · 视图包（原始复算）

## 一句话结论

回指数等于本地类数——闸门为绿，未回指为零；本包声明的本地类全部能在目标件的类集合里按 IRI 原样找到。

本包从 Population 本体出发自算三个量（本地类数、本地到外部子类边数、本地子类边数），再算闸门量回指数与派生量未回指、目标独有；三档边清单、命名空间留痕、逐类命中、七步判定、另报值与自报数对账逐件交齐。论文自报的实体数与实测不同口径，差额落在本地类的载体上，差值与方向见偏差件。

- **能拿去干什么**：复核该本体切片的结构计数与逐类回指，或作为同族切片任务的对照施工样例。
- **复现入口**：包内 `code/` 的唯一入口按 quantity 分派；扰动探针取值见 `claims.jsonl`。
- **原文转述的数**：见 `task.json` 的 `quoted`（十三条锚逐条指回语料或本包件）。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0010",
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
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "not_applicable": [
    "deviations/overlap.json"
  ],
  "must": [
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "b_only": [],
  "corpus_lines": 24,
  "para_lines": null,
  "body_ordinal": null,
  "nulls": [
    {
      "path": "protocol.steps[0].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[0].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[1].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[1].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[2].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[2].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[3].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[3].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[4].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[4].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[5].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[5].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "protocol.steps[6].input",
      "reason": "该步在语料里没有可逐字引用的输入串"
    },
    {
      "path": "protocol.steps[6].output",
      "reason": "该步在语料里没有可逐字引用的输出串"
    },
    {
      "path": "readme.para_lines",
      "reason": "PDF 抽取面无 <p> 段落结构"
    },
    {
      "path": "readme.body_ordinal",
      "reason": "PDF 抽取面无 <body> 序位"
    }
  ],
  "entry": "code/quant.py::measure",
  "params": [
    "quantity",
    "ns_rule",
    "v2_derivation",
    "partition_rule",
    "target_sha256",
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
