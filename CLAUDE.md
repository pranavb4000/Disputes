# Instructions for Claude (and other AI coding agents)

1. Read `TECH_STACK.md` before changing any code. It is the source of truth for technology and conventions;
   section 31 lists the approved additions (AWS, S3, Oracle job-table worker, auth phases).
2. Read `ARCHITECTURE.md` for the dispute process, state machine and module design.
3. Follow the existing layers: HTTP in `backend/app/api`, business rules in `services`, SQL only in `repositories`,
   API contracts in `schemas`. Flutter: `presentation` → `application` (Riverpod) → `data`.
4. Do not add a dependency that is not in `DEPENDENCIES.md` without asking; the bank installs only from Artifactory.
5. Oracle 19c is production: no SQL features newer than 19c (local dev runs Oracle XE 21).
6. Before finishing: `pytest`, `ruff check .`, `mypy app scripts` in `backend/`; `flutter analyze` and `flutter test` in `frontend/`.
7. Never weaken security controls, never hardcode secrets, never commit `.env`.
