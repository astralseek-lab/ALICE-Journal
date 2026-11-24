# code/

唯一入口 `code/quantities.py` 的 `parse(input_path, params)`，按 `params["quantity"]` 分派六量；`contrast_hits` 算三个对照读法。
本目录只放入口与库代码。

载荷哈希口径：各 deviations/evidence 件的 `sha256` ＝ 对该键 `items`（或标量 `value`）按 RFC 8785/JCS 规范化串的 UTF-8 字节取 sha256（小写十六进制）。
