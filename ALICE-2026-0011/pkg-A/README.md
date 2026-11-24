<!-- alice:human -->

# 本体开发方法论文的 protocol 复算包（pkg-A，主实现）

run_id：r_58170f072267

## 一句话结论

语料 Methods 节下标题以 Step 起首的 H2 步骤标题共 7 个，`Table 1` 的术语数据行 25 行，`Table 2` 的数据行 22 行；三量均由本包入口从输入件直接复算，两次遍历同值。

- **能拿去干什么**：复算本篇方法论文的三个结构量，并与原文自报步数对账；另报读数与对账差额见 `deviations/` 各件。
- **复现入口**：`code/count_steps.py::count_steps`（唯一入口约定见 `code/README.md`）。
- **原文转述的数**：原文自报该方法初版有 seven 步（锚 `A01`，`paper_text.txt#L24`），与实测 7 同值而异型（英文数词对整数），按口径不做算术。
- **M1 与 M3 的差额是内容不是错误**：M1 数步骤标题行（`Methods` 下 Step 起首的 H2），M3 数 `Table 2` 的数据行（一步可含多行活动，`colspan` 横幅行照计）；两量的成员集合逐行见 `deviations/diff_A01.json` 的 `items[]` 与 `deviations/readings.json` 的 `table2_rows`。
- **探针的 JATS 适配（照实申报）**：M2／M3 的施力点是 JATS XML 输入节点，件内不存在四类 owl 实体，drop 探针对其无可删对象（两次独立实测 `dropped=0`）；按令方裁③-b（`2026-11-22` 三裁）`判据 10` 的 drop 探针对 JATS 数源件型不激活——本包在 `判据 10` 的红是「判分器严于签件」，灵敏度由双实现旁证（两包同值）与人判承接。

<!-- alice:machine -->

```json
{
  "task_id": "ALICE-2026-0011",
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
    "evidence/protocol.json",
    "evidence/anchors.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "not_applicable": [
    "evidence/ns.json",
    "evidence/mapping.jsonl",
    "deviations/tiers.json",
    "deviations/overlap.json"
  ],
  "must": [
    "evidence/protocol.json",
    "evidence/anchors.json",
    "deviations/contrast.json",
    "deviations/readings.json",
    "deviations/diff_A01.json"
  ],
  "b_only": [],
  "corpus_lines": 94,
  "para_lines": 64,
  "body_ordinal": 1,
  "nulls": [
    {
      "path": "diff_A01.gap",
      "reason": "self_reported 为 str 型英文数词（A01 锚值）、measured 为整数，两侧不同型，按题面 §10.2 不对 str 做算术，gap 置 null"
    },
    {
      "path": "diff_A01.direction",
      "reason": "同上：两侧不同型，方向不裁定，direction 置 null"
    }
  ],
  "entry": "code/count_steps.py::count_steps",
  "params": [
    "peer_held",
    "peer_unheld",
    "peer_universe",
    "readings_names",
    "reads_count"
  ],
  "judge": "task.json#judge"
}
```
