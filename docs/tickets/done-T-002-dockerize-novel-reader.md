# T-002 — Dockerize novel_reader

Spec: SPEC-docker-novel-reader
Blocks: —
Blocked by: —
Labels: reader, devops, docker

## Why
The reader only runs on the owner's Windows machine (local venv + npm); deploying or reproducing it elsewhere is manual, and the verify gates hardcode Windows paths.

## What
- Add backend/frontend Dockerfiles, nginx config and docker-compose.yml (port 8080, `env_file: .env`, `drafts/Novel/` mounted read-only).
- Add a cross-platform gate wrapper so `verify.mjs` works on host and in containers.
- Verify golden paths inside containers and keep host gates green.

## Done when
- [ ] `docker compose up` works with the repo's untracked `.env`
- [ ] SPA + `/api` reachable on :8080; login → library → read → progress/search verified
- [ ] No secrets/content baked into images; `.dockerignore` in place
- [ ] Host `verify.mjs` 5/5 PASS; docs synced
- [ ] Rename this file `doing-T-002-…` when work starts, then `done-T-002-…` when all boxes pass
