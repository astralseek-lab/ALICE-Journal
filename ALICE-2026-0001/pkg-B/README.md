<!-- alice:human -->
run_id：`r_074a2f703f02`

# ALICE-2026-0001 · pkg-B（独立第二实现）

本包是同一题面（§一–§十一）的独立第二实现，与 pkg-A 不共享任何代码
（`evidence/independence.json` 四字段担责声明，`shared_code_with_a=false`）。
按题面 §5.3bis 逐维换法：解析用 `xml.sax` 流式事件流（不用 ElementTree）；遍历为
显式栈迭代（不递归）；计数为一次过流式收集（不建索引后数）；IRI 划界用 urlsplit 取
netloc＋path 独立实现；命名空间主值独立算一次，三个对照值（rdf:about 去文件名／前缀
BCIO_／出现最多的前缀）按件实算并附推导于 `deviations/contrast.json`（同值属巧合，
不是判据）；L5／L6 两读法都算（主口径入 K，另读法入 readings）；protocol 语料按行
流式读、自行切节（先定 Methods／Results 标题行，再取区间内 Step 前缀连续成 `1..6`
的 `6` 个标题行并各算止界，未读 A 的任何清单件）；Step `2` 标题内双冒号逐字照留。

## 复跑

在本包目录下执行 `python code/bcto_build.py` 可从研究夹根的三件输入重算
`evidence/` 与 `deviations/` 全部内容；六个 K 量入口在 `code/bcto_scan.py`。

## 口径备注

- 六量与另报七条经独立重算，与 pkg-A 同值（差额为零，见判分表 deviations 行）；
  同值不互证——两包读法不同（ET 递归索引 ↔ SAX 流式迭代），口径同源自题面 §二。
- A05 记伤、`self_report_unmeasured` 装载形态、`inputs.lock` 语料行 uri＋doi 并置、
  L5 与论文自报层级数的口径差登记，与 pkg-A 人读段同（两处独立成立）。
- 判分器已知红：无。

<!-- alice:machine -->
```json
{
  "b_only": [
    "evidence/independence.json"
  ],
  "body_ordinal": 1,
  "corpus_lines": 99,
  "extras": [
    "evidence/ns.json",
    "evidence/anchors.json",
    "evidence/protocol.json",
    "deviations/tiers.json",
    "deviations/overlap.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json",
    "evidence/independence.json"
  ],
  "files": [
    "README.md",
    "task.json",
    "evidence.graph.json",
    "claims.jsonl",
    "env.lock",
    "inputs.lock",
    "code/"
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
  "not_applicable": [
    "evidence/mapping.jsonl"
  ],
  "nulls": [
    {
      "path": "protocol.steps[0].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[0].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[1].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[1].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[2].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[2].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[3].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[3].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[4].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[4].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[5].input",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    },
    {
      "path": "protocol.steps[5].output",
      "reason": "范围单未给逐步的逐字输入/输出串，自撰即违「只许引用」（题面 §4.2）"
    }
  ],
  "para_lines": 66
}
```
