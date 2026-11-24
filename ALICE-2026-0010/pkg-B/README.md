<!-- alice:human -->

# Wright2025Population · 视图包（独立重算）

## 一句话结论

换一套实现重算的三个量与闸门量，与主包同值；回指数等于本地类数，闸门为绿。

本包是旁证包：换实现族（DOM 显式栈迭代＋目标件流式逐行联接）把同样的量再算一遍，独立生成同一形状的逐类命中表，并按抽样规则交出逐类回指的抽样核验件；与主包之间没有任何代码级共享。

- **能拿去干什么**：作为第二次独立实现，抓主实现写错或口径理解错这两类失效。
- **复现入口**：包内 `code/` 的唯一入口按 quantity 分派。
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
    "deviations/diff_A01.json",
    "evidence/independence.json",
    "deviations/join_sample.json"
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
  "b_only": [
    "evidence/independence.json",
    "deviations/join_sample.json"
  ],
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
  "entry": "code/measure_b.py::measure",
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
