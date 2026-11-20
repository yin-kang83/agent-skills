# Per-call record schema (v0.1)

| Field | Type | Required | Notes |
|---|---|---|---|
| `call_id` | string | yes | local unique id; no user info |
| `provider` | string | yes | e.g. `deepseek` |
| `protocol` | string | yes | `chat` / `responses` / `anthropic` |
| `dataset` | string | yes | public dataset name |
| `problem_id` | string | yes | public item id |
| `terminal_event` | bool | yes | explicit terminal event observed |
| `terminal_event_type` | string | yes | e.g. `stop`, `response.completed`, `[DONE]` |
| `visible_text_chars` | int | yes | visible text characters, excluding thinking |
| `failure_reason` | string | yes | empty string if successful |
| `usage` | object/null | yes | `{"input": int, "output": int}` |
| `finish_reason` | string | yes | provider finish/stop reason |
| `first_token_s` | number/null | yes | time to first token |
| `first_token_definition` | string/null | yes | `any_event` or `visible_text` |
| `stream_event_count` | int | yes | number of stream events |
| `latency_s` | number | yes | total latency |
| `prompt_sha256` | string | optional | hash only, not content |
| `answer_sha256` | string | optional | hash only, not content |

## Violation codes

- `C1_TERMINAL_TYPE_MISSING`: `terminal_event=true` but no type.
- `C2_EMPTY_NO_REASON`: no terminal event, empty text, no reason.
- `C3_INCOMPLETE_NO_REASON`: no terminal event, non-empty text, no reason.
- `C4_USAGE_MISSING` / `C4_USAGE_NEGATIVE` / `C4_USAGE_BAD_SHAPE`.
- `C5_FIRST_TOKEN_UNDEFINED`: `first_token_s` without definition.
- `C6_MAX_TOKENS_NO_FINISH_REASON`.
