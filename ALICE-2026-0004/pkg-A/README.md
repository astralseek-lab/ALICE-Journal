<!-- alice:human -->

# pkg-A · Schenk2024HBO（视图包）

本包回答一件事：HBO 发布件（bcio_behaviour.owl）作为目标件的切片，三个结构量各是多少、切片关系是否成立。

- 三个量：本包本地类数、本地→外部子类边数、本地子类边数，各由一次独立遍历累加得出，不做减法反推。
- 闸门量：逐类把本包本地类 IRI 在目标件里原样联接，全部命中、未回指为零——闸绿。
- 派生量：目标件另有本包没有的本地类（目标独有），差是单向的。
- 语料侧：构建规程八步，按声明块八条标题逐字定位，每条在抽取面恰出现一次。
- 与论文自报数的关系：摘要两个自报类数与本包实测不同口径（初版／终版 vs 本发布件），差额逐条进 diff 件，不判谁错。
- 自述：本件无段落 XML 面（PDF 页级抽取），para_lines 与 body_ordinal 记 null；匿名类两种读法（全树／直接子元素）结果不同，已并列另报于 readings。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0004",
  "entry": "code/entry.py::quantity",
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
    "deviations/diff_A02.json"
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
  "b_only": [],
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
