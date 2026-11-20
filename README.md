# agent-skills

> Reusable agent skills for evidence-driven engineering and research.
> 面向“可核对、可复现、可审计”的 Agent 技能包。

## Skills

| Skill | Purpose | Status |
|---|---|---|
| [`api-contract-check`](skills/api-contract-check/SKILL.md) | Audit sanitized LLM API records for termination/usage/first-token contract issues | v0.1.0 |
| `paper-code-release` | Sanitize, test and publish a paper's code/evidence package | planned |
| `evidence-ledger` | Track claims, evidence levels, and unknowns | planned |

## Design rules

1. Every skill has `SKILL.md` with **when to use / when NOT to use**.
2. Every skill has a runnable script and at least one synthetic example.
3. No prompts, raw outputs, customer data, keys, or local paths.
4. Tests are offline; no API calls.
5. Prefer explicit failure over silent skipping.

## Quick test

```bash
python -m pytest -q
python skills/api-contract-check/scripts/check_records.py skills/api-contract-check/examples/records.sample.jsonl
```

The sample intentionally contains bad records, so the checker exits 1 by design.

## Data boundary

See [`docs/SECURITY-AND-DATA-BOUNDARY.md`](docs/SECURITY-AND-DATA-BOUNDARY.md).

## License

- Code: MIT (`LICENSE`)
- Documentation: CC BY 4.0 (`LICENSE-DOCS.md`)
