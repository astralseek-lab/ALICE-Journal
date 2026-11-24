<!-- alice:human -->
run_id：`r_be49086a20a5`

# ALICE-2026-0006 · Intervention Setting Ontology 结构取证（主实现包）

## 一句话结论
论文行级语料与设定本体两件输入上的六个结构量全部由本包入口现算，判分器可本地复算复核。

- 本地类数 L1 ＝ `118`；与论文自报终版实体数 `72` 的差额构成见 `deviations/diff_A01.json`（实测多）
- 子类边 L2 ＝ `313`：三档 `66`（两端皆本地）／`55`（本地子类·外部父类）／`192`（其余）；匿名 `owl:Restriction` 宾语 `4` 条；全件 `subClassOf` 元素总数 `317`，两次独立遍历同值
- 对象属性 L3 ＝ `50`（本地 `18`）；注释属性 L4 ＝ `56`（本地 `0`）
- 最大层级深度 L5 ＝ `9`（全图根起算、按边数）；本地子图读法 `4`；无任何父类的本地类 `0`
- 叶类数 L6 ＝ `78`；外部子类也算时 `76`；匿名子类 `0`；匿名 `owl:Class` 全树 `2`
- 锚 A01–A13 共 `13` 条逐条落位；A02（一致性系数）与 A03（回收份数）无同义实测端，已进 `deviations/readings.json`
- 命名空间主口径：宿主 humanbehaviourchange.org ＋ 最集中目录 `/ontology/`；三个禁法对照读数同值（`118`），属巧合、不作判据，推导见 `deviations/contrast.json`
- 复现入口：`code/quant_a.py::main`；七步切分见 `evidence/protocol.json`（按位置取、禁用标题去重）
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
    "deviations/diff_A01.json"
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
  "b_only": [],
  "corpus_lines": 84,
  "para_lines": 53,
  "body_ordinal": 1,
  "nulls": [],
  "entry": "code/quant_a.py::main",
  "params": [
    "peer_held",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
