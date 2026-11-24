<!-- alice:human -->
run_id: `r_8ca461c01376`

# ALICE-2026-0009 任务包（pkg-B 独立第二实现）

Marques `2024`《Specifying the Schedule of Delivery of Interventions within the Behaviour Change Intervention Ontology》（Wellcome Open Research，DOI `10.12688/wellcomeopenres.23236.1`）的 BCI Schedule of Delivery Ontology（`bcio_schedule.owl`）K＝`6` 量自算包。全部数值由本包 `code/` 内交付码对本件实算产出。

## 六量实测（本件自算，题面不给期望值）
- L1 本地类数＝`114`（命名空间＝宿主＋最集中目录 `http://humanbehaviourchange.org/ontology/`；宿主取自 `owl:Ontology@rdf:about`）
- L2 子类边数＝`303`（三档 `71`／`46`／`186`；匿名 `owl:Restriction` 宾语 `27` 条单列于 `anon_subclass_objects`；`71`＋`46`＋`186`＋`27`＝`330`＝全件 `subClassOf` 元素数；三档与总数同一次遍历分出，另一次独立遍历复核同值）
- L3 对象属性数＝`50`（本地一档 `18` 另报）；L4 注释属性数＝`56`（本地一档 `0` 另报）
- L5 最大层级深度＝`8`（全图根 `10` 个含外部顶层类，沿 `subClassOf` 下行至最远本地类的边数；本件无环，无环边需记）；另一读法（本地子图）＝`4`、自检值（本地类中无任何父类者）＝`0`，均另报于 `readings.json`
- L6 叶类数＝`75`（只看本地→本地的边）；另一读法（外部子类也算）＝`72` 另报；匿名子类 `0` 条

## 与论文自报的对账
- 锚 A01：论文自报终版 `49` 类 vs 实测 L1 `114`，gap＝`65`（实测多），差额件 `deviations/diff_A01.json`（`items`＝L1 全集 `114` 条 IRI 升序，不选子集——论文只给总数）
- 锚 A02 信度 `0.54`、A03 完成数 `17`：无同义实测端，入 `readings.self_report_unmeasured`
- 初版 `9` 类：入 `readings.initial_version_class_count`

## 三个对照读法（禁法留痕，`deviations/contrast.json`，非判据）
- `rdf:about` 去文件名 → `0`：本件 `owl:Ontology@rdf:about` 带 `Schedule/` 子目录、其下 `0` 个类，落零即实证该读法在本件失效
- 前缀 `BCIO_` → `114`：与主值同值——巧合，不是判据（`ns.json` 的 `coincidence.equal=true`、`sym_diff` 为空）
- 出现最多的前缀 → `http://purl.obolibrary.org/obo/` 共 `169`（外部类群）：与主值 `114` 不同，本件恰是能反证该读法的件

## 对照件交叠（`deviations/overlap.json`，逐类 IRI 三组差值）
- peer `0005`（`bcio_upper_level.owl`）：both `66`／only_in_this `48`／only_in_peer `0`
- peer `0003`（`bcio_mode_of_delivery.owl`）：both `66`／only_in_this `48`／only_in_peer `69`
- 同源切片非新增：本件 `114` 个本地类＝`66` 个共享上层类＋`48` 个本件自有类；对照件只服务交叠求差，不进任何 K 量推导链

## protocol（行范围计数路）
`paper_text.txt` 的 `L357`–`L600` 区间内行首 `Step N` 标题恰 `7` 条、编号连续（区外另有 `7` 条同形标题如实披露、不计；全文去重 `8`／不去重 `14`，均只作对照）；七步行段与标题逐字见 `evidence/protocol.json`（标题跨行折断处压空白拼接核验，连字符／en dash 差异照留）。

## 探针（判据 `10`，k 为实算最小值）
L1 `drop:owl:Class:24`／L2 `drop:rdfs:subClassOf:1`／L3 `drop:owl:ObjectProperty:1`／L4 `drop:owl:AnnotationProperty:1`／L5 `drop:rdfs:subClassOf:70`／L6 `drop:rdfs:subClassOf:26`。

## 口径与尺子的出入声明（诚实申报）
1. 文本锚 `source` 基座：题面 §三写 `fulltext.pdf#p<页>`，但母件 PDF 按题面不投递，随件判分器的锚回指（E1）与人面数字核对（判据 `11`）只认研究夹内真件的行定位或全件子串；按题面 §7.7「件形状与载荷以随件判分器为准」，文本锚写 `paper_text.txt#L<n>`（跨行串 A06／A10／A11 用 `#p<页>` 全件子串形态、值保留原文换行逐字），页码与「第 k/n 处」信息保留在 `source` 尾注。
2. `readings` 两件 map（`dir_class_counts`／`self_report_unmeasured`）按签面模板 `{name,kind,value,sha256}` 装载（`value` 为对象）：A02 是小数，`items` 形装载的机器校验只收整数或字符串。
3. L5 起点根的两种读法（「任何 `subClassOf` 主语」与「仅 `rdf:resource` 边主语」）在本件同值：根集同为 `10` 个，L5 同为 `8`；L5_selfcheck 两读法同为 `0`。
4. `para_lines`／`body_ordinal`：本单为 PDF 抽文语料，无 `<p>`／`<body>`（本单无 <p>／</<body>），写 `null` 并在机器段 `nulls[]` 记账。
5. 匿名节点共 `29` 个（无 `rdf:about` 的 `owl:Class` 与 `owl:Restriction`，按文档序连续编号）；`owl:equivalentClass` 内联匿名类 `2` 个（名表第 `8` 行）。
## 实现面（pkg-B，十道独立性逐条落）
`xml.dom.minidom` 解析（不用 ElementTree）；显式栈迭代遍历（无递归）；流式一次过计数；`urlsplit`（netloc＋path）独立划界；命名空间主值独立另算一次、三个对照读法按件实算进 `contrast.json`；L2 三档由 `xml.dom.pulldom` 流式复核且三档之和＝L2；匿名类独立判定（不读他包清单）；L5／L6 两读法均实算；protocol 按声明块区间从语料重数 `7` 步（不读他包 `protocol.json`）；`code/` 对他包的路径与包名引用 `0` 处。

<!-- alice:machine -->
```json
{
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
    "deviations/contrast.json",
    "deviations/diff_A01.json",
    "deviations/overlap.json",
    "deviations/readings.json",
    "deviations/tiers.json",
    "evidence/anchors.json",
    "evidence/entries.json",
    "evidence/ns.json",
    "evidence/protocol.json"
  ],
  "b_only": [
    "evidence/independence.json"
  ],
  "corpus_lines": 1044,
  "para_lines": null,
  "body_ordinal": null,
  "nulls": [
    {
      "path": "readme.para_lines",
      "reason": "本单为 PDF 抽文语料（多行一页、页间 \\f），无 <p> 段标记——本单无 <p>／<body>"
    },
    {
      "path": "readme.body_ordinal",
      "reason": "同上：无 <body> 序号可回推——本单无 <p>／<body>"
    }
  ]
}
```
