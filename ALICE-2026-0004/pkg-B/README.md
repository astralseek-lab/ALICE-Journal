<!-- alice:human -->

# pkg-B · Schenk2024HBO（视图包 · 旁证包）

本包是**第二次独立**：换一套实现（SAX 流式＋显式栈迭代＋urlsplit 划界）把同样三个量、同一个闸门量再算一遍，并独立生成同一形状的逐类命中表；不读另一包的任何件。

- 三个量各走一次独立事件流；闸门量由逐 IRI 联接得出，未回指为零——闸绿。
- 命名空间独立算一次主值；三条禁法读法只作对照值进 contrast，同值处已写明「巧合，不是判据」。
- 论文自报数与实测不同口径，差额进 diff 件，不判谁错。
- 自述：本件无段落 XML 面，para_lines 与 body_ordinal 记 null；匿名类两种读法（全树／直接子元素）结果不同，已并列另报于 readings。
- 独立性声明见 evidence/independence.json；两包命中表的逐行比对由验收方做。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0004",
  "entry": "code/recount.py::recount_quantity",
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
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json",
    "evidence/independence.json"
  ],
  "not_applicable": [],
  "must": [
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "deviations/diff_A02.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 31,
  "para_lines": null,
  "body_ordinal": null,
  "nulls": [
    {
      "path": "readme.para_lines",
      "reason": "本件为 PDF 页级抽取语料，无 <p> 段落面"
    },
    {
      "path": "readme.body_ordinal",
      "reason": "本件无 JATS XML，无 <body> 可归行"
    },
    {
      "path": "protocol.steps[0].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[0].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[1].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[1].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[2].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[2].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[3].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[3].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[4].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[4].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[5].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[5].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[6].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[6].output",
      "reason": "该步无逐字输出串可摘录"
    },
    {
      "path": "protocol.steps[7].input",
      "reason": "该步无逐字输入串可摘录"
    },
    {
      "path": "protocol.steps[7].output",
      "reason": "该步无逐字输出串可摘录"
    }
  ]
}
```
