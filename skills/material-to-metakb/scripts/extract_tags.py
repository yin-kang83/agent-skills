# -*- coding: utf-8 -*-
"""文本标签抽取 + 双门禁演示（离线、无外部依赖；仅合成样例）。

用法：
  python extract_tags.py --text sample.txt --topics topics.json --out outdir

流程：读取 → CJK 清洗 → 第一道核验（字符变化/非空）→ 标签匹配 → 第二道核验（标签非空/来源可回指）
→ 输出 tags.jsonl / clean_report.json / clean_verify.json / verify_record.json。

退出码：0 PASS；2 FAIL（门禁未通过）。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CJK_GAP = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])")
PUNCT_GAP = re.compile(r"(?<=[\u4e00-\u9fff])\s+(?=[，。；：、（）])")


def normalize(text: str) -> tuple[str, list[str]]:
    ops: list[str] = []
    cleaned = CJK_GAP.sub("", text)
    if cleaned != text:
        ops.append("collapse_cjk_spaces")
    cleaned2 = PUNCT_GAP.sub("", cleaned)
    if cleaned2 != cleaned:
        ops.append("collapse_cjk_punct_spaces")
    cleaned3 = re.sub(r"[ \t]+", " ", cleaned2).strip()
    if cleaned3 != cleaned2:
        ops.append("collapse_whitespace")
    return cleaned3, ops


def clean_verify(raw: str, cleaned: str) -> dict:
    change = 1 - (len(cleaned) / max(1, len(raw)))
    ok = bool(cleaned.strip()) and change <= 0.30
    return {"pass": ok, "chars_raw": len(raw), "chars_clean": len(cleaned),
            "shrink_ratio": round(change, 4), "rule": "非空且清洗收缩≤30%"}


def pre_ingest_verify(tags: list[dict], source: str) -> dict:
    problems = []
    if not tags:
        problems.append("标签为空")
    for item in tags:
        if not item.get("tag") or not item.get("source"):
            problems.append("标签缺少 tag/source")
        if item.get("source") != source:
            problems.append("source 不可回指")
    return {"pass": not problems, "problems": problems}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--topics", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    text_path = Path(args.text)
    topics = json.loads(Path(args.topics).read_text(encoding="utf-8"))
    raw = text_path.read_text(encoding="utf-8")
    cleaned, ops = normalize(raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {"source": text_path.name, "ops": ops,
              "sha256": hashlib.sha256(cleaned.encode("utf-8")).hexdigest()}
    (out_dir / "clean_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    gate1 = clean_verify(raw, cleaned)
    (out_dir / "clean_verify.json").write_text(
        json.dumps(gate1, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not gate1["pass"]:
        print("[FAIL] clean-verify 未通过，禁止进入结构化")
        return 2

    tags = []
    for tag, keywords in topics.items():
        count = sum(cleaned.count(word) for word in keywords)
        if count:
            tags.append({"tag": tag, "count": count, "source": text_path.name,
                         "reliability": "auto_match_unverified"})
    tags.sort(key=lambda item: (-item["count"], item["tag"]))
    with (out_dir / "tags.jsonl").open("w", encoding="utf-8") as fh:
        for item in tags:
            fh.write(json.dumps(item, ensure_ascii=False) + "\n")

    gate2 = pre_ingest_verify(tags, text_path.name)
    (out_dir / "verify_record.json").write_text(
        json.dumps({"pass": gate2["pass"], "problems": gate2["problems"],
                    "sample": tags[:5]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    if not gate2["pass"]:
        print("[FAIL] pre-ingest verify 未通过：", gate2["problems"])
        return 2
    print(f"[PASS] tags={len(tags)} -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
