# -*- coding: utf-8 -*-
"""Self-contained API contract checker for the api-contract-check skill."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def check_record(r: dict) -> list[dict]:
    out = []

    def bad(code: str, msg: str) -> None:
        out.append({"code": code, "message": msg})

    text_chars = int(r.get("visible_text_chars") or 0)
    if r.get("terminal_event") is True and not r.get("terminal_event_type"):
        bad("C1_TERMINAL_TYPE_MISSING", "terminal_event=true but terminal_event_type is empty")
    if r.get("terminal_event") is not True and not r.get("failure_reason"):
        if text_chars == 0:
            bad("C2_EMPTY_NO_REASON", "no terminal event, empty text, no failure_reason")
        else:
            bad("C3_INCOMPLETE_NO_REASON", "no terminal event, non-empty text, no failure_reason")
    u = r.get("usage", "MISSING")
    if u == "MISSING" or u is None:
        bad("C4_USAGE_MISSING", "usage missing")
    else:
        try:
            if int(u.get("input", -1)) < 0 or int(u.get("output", -1)) < 0:
                bad("C4_USAGE_NEGATIVE", "usage negative")
        except Exception:
            bad("C4_USAGE_BAD_SHAPE", "usage is not {input:int, output:int}")
    if r.get("first_token_s") is not None and r.get("first_token_definition") not in ("any_event", "visible_text"):
        bad("C5_FIRST_TOKEN_UNDEFINED", "first_token_s without definition")
    if r.get("failure_reason") == "max_tokens" and not r.get("finish_reason"):
        bad("C6_MAX_TOKENS_NO_FINISH_REASON", "max_tokens without finish_reason")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    lines = [x for x in args.path.read_text(encoding="utf-8").splitlines() if x.strip() and not x.lstrip().startswith("#")]
    records = [json.loads(x) for x in lines]
    violations = []
    codes: dict[str, int] = {}
    for r in records:
        vs = check_record(r)
        if vs:
            violations.append({"call_id": r.get("call_id"), "violations": vs})
            for v in vs:
                codes[v["code"]] = codes.get(v["code"], 0) + 1
    summary = {"total": len(records), "violating_records": len(violations), "violation_codes": codes, "clean": not violations}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for v in violations:
        for x in v["violations"]:
            print(f"{v['call_id']}\t{x['code']}\t{x['message']}")
    if args.json:
        args.json.write_text(json.dumps({"summary": summary, "violations": violations}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if summary["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
