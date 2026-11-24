# code/（主实现包）

- 唯一件：`quant_a.py`；六量固定入口 `l1_local_classes`…`l6_leaf_classes`，各返 `{"v": 整数}`
- 复现：`python code/quant_a.py <bcio_setting.owl 路径>` 打印六量 JSON（sort_keys，确定性）
- 解析栈：xml.etree.ElementTree；递归遍历；建索引后计数；前缀比较划界
- 证据件发射：`emit_artifacts(input_path, {"only": <相对路径>})`，逐件对应 evidence/ 与 deviations/
