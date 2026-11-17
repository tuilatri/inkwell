# `.agent/rules/` — Agent bootstrap & router

This directory holds the rule files an agent reads **before starting a task** — the
repo's bootstrap/router: pre-task resource loading order, the skill auto-select
table by task type, the workflow auto-select table by complexity (pattern of
`AUTO_AGENT_LOADING.md` + `GEMINI.md` — see the sample at the link below).

This repo has one active rule file: **`ROUTER.md`** (pre-task loading order + task→doc/skill map). Everything below is the upstream template guidance, kept for reference:


1. **Write a minimal rule file yourself**, e.g. `.agent/rules/ROUTER.md` (already done here):
   - Pre-task loading order: AGENTS.md → `docs/ai-context/` (name which files to read)
   - A "task type → which doc/skill" table — 3–6 rows is enough
   - General rules (commit convention, plan location) already live in AGENTS.md —
     reference them, don't duplicate.
2. **Port from the sample**: https://github.com/tuilatri/engineering-kit/tree/main/example/.agent/rules
   When porting, **scrub the project-specific parts**: accounts/palette files, chat-language
   rules, app names, and any skill/workflow that does not exist in your repo.
