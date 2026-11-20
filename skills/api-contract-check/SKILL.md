---
name: api-contract-check
description: Audit sanitized per-call LLM API records for missing terminal events, unexplained empty text, missing/invalid usage, and undefined first-token semantics. Use when checking provider protocol consistency or validating a sanitized evidence bundle.
license: MIT
---

# API Contract Check

## When to use

Use this skill when you have **per-call JSONL records** from a streaming LLM API and need to answer:

- Did every successful call end with an explicit terminal event?
- Are empty or truncated streams accompanied by a failure reason?
- Are `usage` fields present and non-negative?
- Is `first_token_s` paired with an explicit definition (`any_event` vs `visible_text`)?

Typical contexts: provider compatibility audits, evaluation-pipeline sanity checks, reproducing an API bug report.

## When NOT to use

- Do **not** use this as a model benchmark or quality ranking.
- Do **not** use it to claim a provider has fixed/not fixed a defect without new calls.
- Do **not** feed prompts, raw completions, keys, or customer data into the checker.
- Do **not** treat `0 violations` as proof the protocol is correct; it only means the records are well-formed enough to audit.

## Input contract

One JSON object per line. Minimum fields:

```text
call_id, provider, protocol, dataset, problem_id,
terminal_event, terminal_event_type, visible_text_chars,
failure_reason, usage, first_token_s, first_token_definition
```

See `references/record-schema.md` for the full schema.

## Workflow

1. Confirm the input is sanitized (no prompt/raw text).
2. Run the checker:
   ```bash
   python scripts/check_records.py records.jsonl --json report.json
   ```
3. If `clean=false`, inspect each violation code (C1–C6) before drawing conclusions.
4. Separate:
   - **record-level violations** (fields missing/inconsistent);
   - **protocol observations** (e.g., missing terminal event even when `failure_reason` is present).
5. Report counts, protocol, dataset, and limitations. Never report only a success rate.

## Failure handling

- `FileNotFoundError`: check the path; do not synthesize records.
- `JSONDecodeError`: report the line number; do not skip silently.
- `clean=false`: treat as data-quality finding, not as model behavior.
- If tool and skill disagree, the tool (`llm-api-contract`) is authoritative; record the version.

## Data boundary

Allowed: ids, hashes, counts, statuses, timings, usage numbers.

Forbidden: prompts, problem statements, raw model output, API keys, customer data, local absolute paths.

## Output

A JSON summary plus a short Markdown note containing:

- total records, violating records, violation codes;
- protocol/dataset breakdown;
- what the result does **not** prove.

## Related

- Tool: `llm-api-contract` (code DOI `10.5281/zenodo.24399656`)
- Background: `10.5281/zenodo.24269158`
