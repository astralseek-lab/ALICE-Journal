<!-- alice:human -->

run_id：`r_2114348c9f87`（本单执行 run 回执原串；pkg-A 与 pkg-B 同一 run_id）

# ALICE-2026-0008 · Style of Delivery Ontology 六量复核 — pkg-B（独立第二实现：minidom／显式栈迭代／流式一次过／urlsplit 划界）

## 结论一行
本地类 1304、子类边 1496、对象属性 53、注释属性 56、最大层级深度 10、叶类 955；论文自报实体数 145（锚 A01），实测大于自报，逐类差额清单见 `deviations/diff_A01.json`。

- **能拿去干什么**：六个量的可复算基线——只凭主件 `bcio_style.owl` 即可由 `code/` 的六个固定入口逐一复算；两包实现独立、结果同值。
- **复现入口**：`code/sod_metrics.py`；入口声明（文件＋行号区间）见 `evidence/entries.json`。
- **L2 两次遍历对账**：分档与总数出自同一次遍历，第二次独立遍历复核同值——两端本地 `1212`、主体本地宾语外部 `98`、其余 `186`（构成：外部→外部 `182`、外部→本地 `4`），匿名宾语 `25`，四键合计 `1521`＝`partition_total`，与全件 subClassOf 元素数一致。
- **匿名类两读**：全树 `13`，仅根直接子节点 `0`——两读不同（匿名类全部嵌套在具名类的表达式内），照实并列另报于 `deviations/readings.json`。
- **三个对照读法**（`deviations/contrast.json`）：`rdf:about` 去文件名、`BCIO_` 前缀、出现最多的前缀，三读与主口径同值——巧合，不是判据；推导逐行附在件内。
- **命名空间推导**：宿主 `humanbehaviourchange.org`＋最集中目录 `/ontology/`，逐类判定见 `evidence/ns.json`。
- **对照件交叠**：`0004` 与 `0005` 两件的具名类 IRI 集均为本件子集（only_in_peer 均为 `0`，同源切片非新增），逐类清单见 `deviations/overlap.json`。
- **原文转述的数**：自报实体数 145（锚 A01）；信度系数 0.77（锚 A02）与标注量 100（锚 A03）无同义实测端，已收入 `readings.self_report_unmeasured`。
- **不确定项**：`para_lines`（`43`）与 `body_ordinal`（`1`）由语料行型按归行规则回推（母件 XML 未投递），pkg-B 独立回推同值。
- **扰动探针 k 的选择**：六条主值各取使值真变的最小 k——L1 `drop:owl:Class:24`（第 `24` 个类元素是首个本地类）、L2 `drop:rdfs:subClassOf:1`、L5 `drop:rdfs:subClassOf:915`（前 `914` 条边不动最深链）、L6 `drop:rdfs:subClassOf:27`、L3／L4 各 `1`；均为实算最小值。
- **独立性**：本包代码未 import、未读取 pkg-A 的任何文件；声明见 `evidence/independence.json`。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0008",
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
    "deviations/diff_A01.json",
    "deviations/overlap.json",
    "deviations/readings.json",
    "deviations/tiers.json",
    "evidence/anchors.json",
    "evidence/entries.json",
    "evidence/independence.json",
    "evidence/ns.json",
    "evidence/protocol.json"
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
    "deviations/diff_A01.json",
    "evidence/entries.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 71,
  "para_lines": 43,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/sod_metrics.py::l1_local_classes",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
