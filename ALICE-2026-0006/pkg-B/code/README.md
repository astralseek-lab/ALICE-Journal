# code/（独立第二实现包）

- 唯一件：`quant_b.py`；六量固定入口与题面同名，各返 `{"v": 整数}`
- 复现：`python code/quant_b.py <bcio_setting.owl 路径>` 打印六量 JSON（确定性）
- 解析栈：xml.dom.minidom；显式栈迭代；流式一次过计数；urlsplit 取 netloc＋path 划界
- 证据件发射：`emit_artifacts(input_path, {"only": <相对路径>})`
