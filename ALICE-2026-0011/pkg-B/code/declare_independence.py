# -*- coding: utf-8 -*-
"""pkg-B 独立性声明件的生成入口（A-1 口径：`evidence/independence.json` 的出处）。

四字段：source（实现来源自述）／shared_code_with_a（恒 false 声明）／
entry（本包唯一入口）／signer_pkg_id（签声明的包）。机器面只核四字段非空与
shared_code_with_a === false；独立性真伪由 VA1 人判读本目录代码。
"""
from __future__ import annotations

ENTRY_NAME = "code/step_tally.py::tally_step_titles"


def declare_independence(source_note):
    return {
        "source": source_note,
        "shared_code_with_a": False,
        "entry": ENTRY_NAME,
        "signer_pkg_id": "pkg-B",
    }
