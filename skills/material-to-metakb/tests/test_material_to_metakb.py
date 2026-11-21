# -*- coding: utf-8 -*-
"""离线测试：文本标签抽取 + 双门禁（不联网、不依赖外部服务）。"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
SCRIPT = SKILL / "scripts" / "extract_tags.py"
EXAMPLES = SKILL / "examples"


def run(text_file: Path, out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--text", str(text_file),
         "--topics", str(EXAMPLES / "topics.json"), "--out", str(out_dir)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )


def test_sample_passes_both_gates(tmp_path):
    result = run(EXAMPLES / "sample_exam_text.txt", tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    tags = [json.loads(line) for line in (tmp_path / "tags.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert tags, "应至少命中一个标签"
    names = {item["tag"] for item in tags}
    assert {"收入确认", "租赁", "合并报表"} <= names
    assert all(item["source"] == "sample_exam_text.txt" for item in tags)
    record = json.loads((tmp_path / "verify_record.json").read_text(encoding="utf-8"))
    assert record["pass"] is True


def test_empty_text_fails_clean_verify(tmp_path):
    empty = tmp_path / "empty.txt"
    empty.write_text("", encoding="utf-8")
    result = run(empty, tmp_path / "out")
    assert result.returncode == 2
    assert "clean-verify" in result.stdout


def test_no_keyword_text_fails_pre_ingest(tmp_path):
    unrelated = tmp_path / "unrelated.txt"
    unrelated.write_text("这是一段与主题无关的合成文本，用于测试门禁。", encoding="utf-8")
    result = run(unrelated, tmp_path / "out")
    assert result.returncode == 2
    assert "pre-ingest" in result.stdout
