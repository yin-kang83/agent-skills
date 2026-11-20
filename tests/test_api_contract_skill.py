# -*- coding: utf-8 -*-
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "api-contract-check"


def test_skill_files_exist():
    for name in ["SKILL.md", "scripts/check_records.py", "examples/records.sample.jsonl", "references/record-schema.md"]:
        assert (SKILL / name).exists(), name


def test_skill_has_usage_boundaries():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "When NOT to use" in text
    assert "Data boundary" in text


def test_checker_detects_bad_records():
    out = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "check_records.py"), str(SKILL / "examples" / "records.sample.jsonl")],
        capture_output=True, text=True, encoding="utf-8",
    )
    assert out.returncode == 1
    assert "C2_EMPTY_NO_REASON" in out.stdout
    assert "C4_USAGE_MISSING" in out.stdout
    assert "C6_MAX_TOKENS_NO_FINISH_REASON" in out.stdout
