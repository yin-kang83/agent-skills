# Security and data boundary

## Allowed

- synthetic examples;
- public dataset ids;
- hashes and counts;
- sanitized per-call records;
- tool/version metadata.

## Forbidden

- prompts, problem statements, raw model output;
- API keys, tokens, cookies;
- customer data, personal data;
- private repository paths;
- unpublished manuscripts/reviews;
- raw financial/annual-report databases.

## Release checklist

- [ ] no secrets in `git grep` / tests;
- [ ] no absolute local paths;
- [ ] examples are synthetic or explicitly public;
- [ ] tests are offline;
- [ ] license files present;
- [ ] README states limits.
