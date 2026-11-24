<!-- alice:human -->
run_id：`r_be49086a20a5`

# ALICE-2026-0006 · Intervention Setting Ontology 结构取证（独立第二实现包）

## 一句话结论
与主实现包同题独立重算：换解析族（minidom）、显式栈迭代、流式一次过计数、urlsplit 划界；六量逐值一致。

- 六量复算：L1 ＝ `118`、L2 ＝ `313`（三档 `66`／`55`／`192`，匿名宾语 `4`，总数 `317`）、L3 ＝ `50`、L4 ＝ `56`、L5 ＝ `9`、L6 ＝ `78`
- 另报：L3 本地 `18`、L4 本地 `0`、L5 本地子图读法 `4`、无任何父类的本地类 `0`、L6 外部子类也算 `76`、匿名 `owl:Class` `2`
- 命名空间主值独立算得同值；三个对照读数亦为 `118`，属巧合、不作判据
- 锚 A01–A13 共 `13` 条独立抽取落位，与主实现包逐条同值；差额件 `deviations/diff_A01.json` 为实测多 `46`
- 七步由本包代码从语料按位置自切，未读主实现包的 protocol；两读法（L5／L6 各两条）全部算出
- 独立性自述见 `evidence/independence.json`；复现入口：`code/quant_b.py::main`
- 已登记偏差：`inputs.lock` 按题面四列（无 license／retrieved_at，判分器多列即红）；自检包旧 schema 仍要求 license 属已知漂移，以判分器为准

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0006",
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
    "evidence/anchors.json",
    "evidence/protocol.json",
    "evidence/entries.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "evidence/independence.json"
  ],
  "not_applicable": [
    "evidence/mapping.jsonl"
  ],
  "must": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "evidence/entries.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 84,
  "para_lines": 53,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/quant_b.py::main",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
