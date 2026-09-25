# Dispute Management System (DMS)

Scaffold for IDFC FIRST Bank's dispute management application (UPI first; IMPS, AEPS, E-Toll later).
This first cut has **login, logout and a home page**, wired through every layer of the approved stack, so the
bank laptop + Artifactory set-up can be proven before feature work starts.

| Read first | Why |
|---|---|
| [`TECH_STACK.md`](TECH_STACK.md) | Mandatory stack and coding rules (source of truth) |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Process analysis and target design |
| [`DEPENDENCIES.md`](DEPENDENCIES.md) | Every package, image and tool to check in Artifactory |

```
Browser ──> Nginx :8080 ──/api/──> FastAPI (Uvicorn) :8000 ──> Oracle XE 21 (XEPDB1)
              │                         │                  └──> Redis 7
              └─ Flutter Web build      └─ Worker (same image): Oracle job queue + scheduler
```

## What is in the box

| Area | Included |
|---|---|
| **Backend** (`backend/`) | FastAPI layered app (api → services → repositories → models), standard response envelope, central error handling, JSON logs with request IDs |
| Auth | Dev-only local login (scrypt), JWT **HS512** access token (15 min), rotating **HttpOnly refresh cookie** stored hashed in Redis with reuse detection, logout with token deny-list, login rate-limit and lockout, CSRF checks on cookie endpoints, LDAP provider ready for Phase 2 |
| Authorisation | Roles per module (ADMIN / MAKER / CHECKER) → permissions, re-checked on every request |
| Data | SQLAlchemy 2 + python-oracledb (thin), Alembic migration hand-written for Oracle 19c, tamper-evident audit log (hash chain) |
| Background jobs | Worker process on an Oracle job table + Redis wake-ups; scheduler (heartbeat every 5 min, audit-chain check hourly) |
| Other | AES-256-GCM field encryption + blind index, S3 / local file storage, dependency smoke-test script, 45 pytest tests |
| **Frontend** (`frontend/`) | Flutter Web: Riverpod, go_router, dio; access token in memory only; silent session restore; login page, home page (KPI tiles, module cards, activity table, chart); IDFC colour guardrails; fonts bundled (no Google CDN calls) |
| **Local stack** | `docker-compose.yml`: Oracle XE 21 slim, Redis 7, migrate + seed, API, worker, Nginx |

---

## 1. Prerequisites (bank laptop)

- Docker Desktop, Rancher Desktop or Podman (with compose)
- Flutter SDK, stable channel, **3.27 or newer**
- Python **3.12** (only needed to run `tools/init_env.py` and for native backend development)
- Git

## 2. Point everything at Artifactory

Nothing in this repo needs the public internet if these four are set.

**a) Container images.** Pull through your Artifactory Docker registry and set the names in `.env` (step 3):
`ORACLE_IMAGE` (you already have `oracle-xe:21-slim`), `REDIS_IMAGE`, `PYTHON_IMAGE`, `NGINX_IMAGE`.

**b) Python packages.** Set `PIP_INDEX_URL` in `.env` for the Docker build. For native installs on Windows, create
`%APPDATA%\pip\pip.ini`:

```ini
[global]
index-url = https://<artifactory-host>/artifactory/api/pypi/<pypi-repo>/simple
```

**c) Flutter / Dart packages** (PowerShell, current user):

```powershell
[Environment]::SetEnvironmentVariable("PUB_HOSTED_URL", "https://<artifactory-host>/artifactory/api/pub/<pub-repo>", "User")
[Environment]::SetEnvironmentVariable("FLUTTER_STORAGE_BASE_URL", "https://<artifactory-host>/artifactory/<flutter-storage-repo>", "User")
```

**d) Corporate TLS certificate.** If Artifactory or the proxy uses the bank's own CA, copy the root CA
certificate(s) as `*.crt` into `backend/certs/`. The backend image trusts them at build time.

## 3. First run

```powershell
git clone https://github.com/pranavb4000/Disputes.git
cd Disputes

python tools\init_env.py                # creates .env with random passwords/keys and prints the dev login
notepad .env                            # set ORACLE_IMAGE / REDIS_IMAGE / PYTHON_IMAGE / NGINX_IMAGE / PIP_INDEX_URL

cd frontend
flutter pub get
flutter build web --release --no-web-resources-cdn
cd ..

docker compose up -d --build            # first Oracle start takes 2-5 minutes
docker compose ps                       # wait until oracle is "healthy" and migrate "exited (0)"
```

Open **http://localhost:8080** and sign in as **`dev_user`** with the password `init_env.py` printed
(it is `DEV_USER_PASSWORD` in `.env`). `dev_checker` (`DEV_CHECKER_PASSWORD`) exists for testing approvals,
because maker-checker never lets the same person approve their own action.

## 4. Verify the stack (the go / no-go checklist)

| # | Check | Command / action | Expected |
|---|---|---|---|
| 1 | Python packages from Artifactory work | `docker compose exec api python -m scripts.check_dependencies` | `ALL GOOD` |
| 2 | API + Oracle + Redis | open http://localhost:8080/api/v1/health/ready | `"oracle": "ok", "redis": "ok"` |
| 3 | Migration + seed | `docker compose logs migrate` | `created: dev_user`, `created: dev_checker` |
| 4 | Login | sign in at http://localhost:8080 | Home page shows "Welcome, Developer", UPI card active |
| 5 | Session restore | press F5 on the home page | still signed in (refresh cookie) |
| 6 | Logout | account menu → Log out | back to the sign-in page; F5 stays signed out |
| 7 | Worker + scheduler | `docker compose logs worker` | `Worker heartbeat` and `Audit chain verified` lines |
| 8 | No external calls | browser DevTools → Network, reload | only `localhost` requests (no gstatic / Google fonts) |
| 9 | API docs | http://localhost:8000/api/v1/docs | Swagger UI with auth, health, home endpoints |
| 10 | Flutter packages | `cd frontend; flutter pub get; flutter test` | all tests pass |

If all ten pass, the stack and architecture are confirmed for this environment.

## 5. Day-to-day development

**Backend with hot reload** (Oracle and Redis still in Docker):

```powershell
docker compose up -d oracle redis
cd backend
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
alembic upgrade head
python -m scripts.seed_dev
uvicorn app.main:app --reload --port 8000
# second terminal (venv active):  python -m app.worker
```

**Frontend with hot reload** against that backend:

```powershell
cd frontend
flutter run -d chrome --web-port 5000 --dart-define=API_BASE_URL=http://localhost:8000
```

(`CORS_ORIGINS=http://localhost:5000` in `.env` allows this. Behind Nginx no CORS is needed.)

**After changing JSON models** annotated with `@JsonSerializable`:
`dart run build_runner build --delete-conflicting-outputs`

## 6. Tests and quality gates

```powershell
cd backend
pytest                                   # 45 tests: auth, permissions, tokens, crypto, jobs, audit, storage
ruff check . ; ruff format --check .     # lint + format
mypy app scripts                         # strict typing
bandit -c pyproject.toml -r app scripts  # security lint
pip-audit -r requirements.txt            # known vulnerabilities (or the bank's scanner)

cd ..\frontend
flutter analyze
flutter test
```

Backend tests use in-memory SQLite and a fake Redis, so they run anywhere. Behaviour that only Oracle has is
checked by the running stack (section 4). Integration tests belong under `@pytest.mark.integration`.

## 7. Project layout

```
backend/
  app/
    api/            HTTP only: routers, dependencies (auth, permissions, CSRF)
    core/           config, security (JWT, passwords), crypto (AES-GCM), errors, logging, permissions
    models/         SQLAlchemy entities       schemas/   Pydantic API contracts
    repositories/   all SQL                   services/  business rules (auth, access, audit, jobs, home)
    jobs/           job registry + handlers   storage/   S3 / local files
    worker.py       background worker + scheduler
  migrations/       Alembic (Oracle 19c DDL)
  scripts/          seed_dev.py, check_dependencies.py
  tests/
frontend/
  lib/core/         config, theme (IDFC colours), network (dio + auth interceptor), router
  lib/shared/       brand widgets, app shell (maroon top bar + side navigation)
  lib/features/     auth (login, splash), home
  assets/fonts/     bundled fonts + licences
deploy/nginx/       Nginx site config + security headers
docs/dependencies/  pinned lists for the Artifactory availability check
tools/init_env.py   creates .env with generated secrets
```

## 8. Branding notes

- The colours in `frontend/lib/core/theme/brand_colors.dart` follow IDFC_UI_GUARDRAILS.md §2–3.1. Yellow is only used for notices and
  attention dots, which keeps it well under the 10% limit.
- **Font:** the guardrails specify **Helvetica** for digital. Helvetica is a licensed font, and Flutter Web must bundle font files,
  so the scaffold ships **Liberation Sans**. It is metrically compatible with Helvetica and Arial and uses the SIL OFL licence.
  To switch, drop the bank's licensed Helvetica web font files into `frontend/assets/fonts/` and point the `BrandSans` family in
  `pubspec.yaml` at them.
- **Logo:** the header uses a text wordmark ("IDFC FIRST" in caps + "Bank"). Replace it with the official artwork from the brand
  team in `lib/shared/widgets/brand_wordmark.dart`, keeping the 2.8:1 ratio and breathing space.
- **Open points for the brand team:**
  - Table alternating rows are `#D9ADA1` in §2.3 but `#DEB9AE` in §3.1; the scaffold uses §3.1.
  - Secondary text `#BCBEC0` on white has low contrast (≈1.9:1, below WCAG AA), so the scaffold uses it sparingly.
  - No error colour is defined in the pages received; a standard red is a placeholder.

## 9. Flutter 3.47+ note

Flutter 3.47 moved Material widgets into the separate `material_ui` package. `package:flutter/material.dart` still works but is frozen.
This scaffold keeps `package:flutter/material.dart` and caps `go_router` (<18) and `data_table_2` (<3) at their last versions that
use it. That way it builds on both older and newer SDKs. When the bank standardises on ≥ 3.47, run
`dart fix --apply --code=migrate_design_widgets` and lift those caps.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `pip` SSL / certificate errors during `docker compose build` | Put the bank root CA (`*.crt`) in `backend/certs/`; set `PIP_INDEX_URL` (and `PIP_TRUSTED_HOST` only if told to) |
| `migrate` exits with ORA-12514 / connection refused | Oracle is still starting: `docker compose logs -f oracle` until `DATABASE IS READY TO USE`, then `docker compose up -d` |
| Blank page at :8080 | `frontend/build/web` missing: run `flutter build web --release --no-web-resources-cdn`. Otherwise check the browser console |
| CSP warnings in the console | The policy is report-only by default; send the messages so the policy can be tuned before enforcing it |
| 403 `CSRF_CHECK_FAILED` on refresh | The page origin is not `PUBLIC_ORIGIN` / `CORS_ORIGINS` in `.env` |
| 429 `ACCOUNT_LOCKED` | 5 failed logins; wait 15 min or `docker compose exec redis redis-cli -a <REDIS_PASSWORD> --scan --pattern "dms:loginfail:*"` and delete the key |
| Port already in use | Change `WEB_HOST_PORT` / `API_HOST_PORT` / `ORACLE_HOST_PORT` / `REDIS_HOST_PORT` in `.env` |
| Podman: `service_completed_successfully` not supported | Use a recent `podman compose` (Docker Compose v2 provider), or run `docker compose run --rm migrate` first |
| Rotating secrets | `python tools\init_env.py --force` (old file kept as `.env.bak`), then `docker compose down -v` to recreate Oracle users |
