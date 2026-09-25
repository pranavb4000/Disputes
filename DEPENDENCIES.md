# Dependency Checklist — Dispute Management System

| | |
|---|---|
| **Purpose** | Everything the project needs from JFrog Artifactory (or other internal mirrors), so availability can be checked before development starts |
| **Resolved on** | 24 Sep 2026, against public PyPI and pub.dev (updated when the scaffold was built) |
| **Target runtime** | Python 3.12 on Linux x86_64 (Docker), Flutter stable (Web) |
| **Rule** | Per `TECH_STACK.md` §22, nothing outside this list is added without approval |

Machine-checkable versions of these lists are in `docs/dependencies/`:

| File | Use |
|---|---|
| `requirements-runtime.txt` | All Python packages the application needs to run (direct + transitive, pinned) |
| `requirements-ldap.txt` | Extra packages for Phase 2 LDAP login |
| `requirements-dev.txt` | Test, lint and security-scan tools (developer machines and CI only) |
| `pubspec-check.yaml` | Throwaway Flutter project to check pub packages |

The scaffold's own install files are `backend/requirements.txt` (runtime), `backend/requirements-dev.txt` and
`backend/requirements-ldap.txt`. They pin the same versions but carry platform markers, so one file installs on both Linux (Docker)
and Windows (native development). For example, `uvloop` is skipped on Windows and `colorama` is added for Windows dev tools.
Use the `docs/dependencies/` copies for the `pip download` availability check below.

---

## 1. How to check availability quickly

**Python.** On any machine that can reach Artifactory (Windows is fine), run the command below for each requirements file. It downloads the **Linux** wheels the Docker image needs, without installing anything. Every package pip reports as "not found" is missing.

```bat
pip download -r requirements-runtime.txt --no-deps --only-binary=:all: ^
  --python-version 3.12 --platform manylinux_2_28_x86_64 --platform manylinux2014_x86_64 ^
  -d chk --index-url https://<artifactory-host>/artifactory/api/pypi/<pypi-repo>/simple
```

> The platform flags matter. Several packages (`cryptography`, `oracledb`, `pydantic-core`, `uvloop`, `httptools`) ship compiled binaries, and the Linux build is what goes into the container. This command was tested against public PyPI: all 97 files resolve.

**Flutter.** Set `PUB_HOSTED_URL` to the Artifactory pub remote, copy `pubspec-check.yaml` into an empty folder as `pubspec.yaml`, and run `flutter pub get`. Then run `flutter pub deps --style=compact` to see the full transitive list with the versions actually resolved.

If a version is missing but an older one exists, note the available version in the **Available?** column. Most packages here work fine one or two minor versions back.

---

## 2. Python — runtime (Phase 1)

Direct dependencies are what the code imports. Transitive dependencies come in automatically but still have to exist in Artifactory.

### 2.1 Direct

| # | Package | Version | Licence | Why it is needed | Available? |
|---|---|---|---|---|---|
| 1 | fastapi | 0.141.1 | MIT | Backend framework (mandated) | ☐ |
| 2 | uvicorn[standard] | 0.53.0 | BSD-3-Clause | API server (mandated). `[standard]` adds uvloop/httptools for performance | ☐ |
| 3 | pydantic-settings | 2.15.0 | MIT | Typed environment configuration (`.env`, env vars) | ☐ |
| 4 | email-validator | 2.3.0 | Unlicense | Email-format validation for user records (§12). *Optional*: drop if no email fields | ☐ |
| 5 | sqlalchemy | 2.0.54 | MIT | ORM (mandated) | ☐ |
| 6 | oracledb | 26.0.1 | UPL-1.0 / Apache-2.0 | Oracle driver (mandated). Thin mode, **no Oracle Instant Client needed** | ☐ |
| 7 | alembic | 1.20.0 | MIT | Database migrations (`migrations/` folder in §5) | ☐ |
| 8 | redis | 8.1.0 | MIT | Redis client (mandated). Works with Redis 7.x servers | ☐ |
| 9 | pyjwt | 2.15.0 | MIT | JWT HS512 signing and validation | ☐ |
| 10 | cryptography | 50.0.1 | Apache-2.0 / BSD-3 | AES-256-GCM (§9). Also needed by oracledb | ☐ |
| 11 | python-multipart | 0.0.32 | Apache-2.0 | Required by FastAPI for file uploads | ☐ |
| 12 | openpyxl | 3.1.5 | MIT | Read uploaded Excel files **and** write Excel exports (one library for both). CSV uses the Python standard library | ☐ |
| 13 | boto3 | 1.43.101 | Apache-2.0 | AWS S3 file storage | ☐ |
| 14 | httpx2 | 2.13.1 | BSD-3-Clause | FastAPI test client + future outbound API calls. *Replaces `httpx`*; the current Starlette release deprecates `httpx` for its test client | ☐ |

### 2.2 Transitive (pulled in by the above)

| Package | Version | Licence | Required by | Available? |
|---|---|---|---|---|
| annotated-doc | 0.0.5 | MIT | fastapi | ☐ |
| annotated-types | 0.8.0 | MIT | pydantic | ☐ |
| anyio | 4.15.1 | MIT | httpx2, starlette, watchfiles | ☐ |
| botocore | 1.43.101 | Apache-2.0 | boto3 | ☐ |
| cffi | 2.1.1 | MIT-0 | cryptography | ☐ |
| click | 8.5.0 | BSD-3-Clause | uvicorn | ☐ |
| dnspython | 2.8.0 | ISC | email-validator | ☐ |
| et-xmlfile | 2.0.0 | MIT | openpyxl | ☐ |
| greenlet | 3.5.6 | MIT / PSF-2.0 | sqlalchemy | ☐ |
| h11 | 0.16.0 | MIT | httpcore2, uvicorn | ☐ |
| httpcore2 | 2.13.1 | BSD-3-Clause | httpx2 | ☐ |
| httptools | 0.8.0 | MIT | uvicorn | ☐ |
| idna | 3.20 | BSD-3-Clause | anyio, email-validator, httpx2 | ☐ |
| jmespath | 1.1.0 | MIT | boto3, botocore | ☐ |
| mako | 1.4.3 | MIT | alembic | ☐ |
| markupsafe | 3.0.3 | BSD-3-Clause | mako | ☐ |
| pycparser | 3.0 | BSD-3-Clause | cffi | ☐ |
| pydantic | 2.13.5 | MIT | fastapi, pydantic-settings | ☐ |
| pydantic-core | 2.46.5 | MIT | pydantic | ☐ |
| python-dateutil | 2.9.0.post0 | BSD / Apache-2.0 | botocore | ☐ |
| python-dotenv | 1.2.3 | BSD-3-Clause | pydantic-settings, uvicorn | ☐ |
| pyyaml | 6.0.3 | MIT | uvicorn | ☐ |
| s3transfer | 0.19.2 | Apache-2.0 | boto3 | ☐ |
| six | 1.17.0 | MIT | python-dateutil | ☐ |
| starlette | 1.7.0 | BSD-3-Clause | fastapi | ☐ |
| truststore | 0.10.4 | MIT | httpx2 | ☐ |
| typing-extensions | 4.16.0 | PSF-2.0 | many | ☐ |
| typing-inspection | 0.4.4 | MIT | fastapi, pydantic | ☐ |
| urllib3 | 2.8.0 | MIT | botocore | ☐ |
| uvloop | 0.22.1 | Apache-2.0 / MIT | uvicorn[standard] | ☐ |
| watchfiles | 1.3.0 | MIT | uvicorn[standard] (dev auto-reload) | ☐ |
| websockets | 17.1 | BSD-3-Clause | uvicorn[standard] | ☐ |

**Total runtime: 46 packages.** If `uvloop`, `httptools`, `watchfiles` or `websockets` are unavailable, use plain `uvicorn` instead of `uvicorn[standard]`. It works; it is just slower.

### 2.3 Deliberately **not** used (the standard library or the mandated stack covers it)

| Need | Using instead | Avoided package |
|---|---|---|
| Background jobs and scheduler | Oracle job table + Redis (approved design, see ARCHITECTURE §6) | Celery, RabbitMQ, APScheduler, RQ |
| CSV read/write | Python `csv` module | pandas, Polars |
| JSON logging | Python `logging` + small custom JSON formatter | structlog, python-json-logger |
| Password hashing (dev-only local login) | `hashlib.scrypt` (standard library) | bcrypt, argon2-cffi |
| Retries | Small in-house helper | tenacity |
| Virus scanning of uploads | AWS GuardDuty Malware Protection for S3 (managed) | ClamAV client |

---

## 3. Python — Phase 2 (LDAP login)

| Package | Version | Licence | Why | Available? |
|---|---|---|---|---|
| ldap3 | 2.9.1 | **LGPL-3.0** | Validate user credentials against the bank's AD/LDAP (pure Python, no system libraries) | ☐ |
| pyasn1 | 0.6.4 | BSD-2-Clause | Required by ldap3 | ☐ |

> **Licence note:** ldap3 is LGPL-3.0. Using it unmodified as a library is usually acceptable, but check with your open-source/licensing policy. The alternative, `python-ldap`, has a permissive licence but needs OpenLDAP C libraries in the Docker image. Also note ldap3's last release (2.9.1) is several years old, so confirm it passes your maintenance criteria.

---

## 4. Python — development, testing and CI only

These never go into the production image.

| Package | Version | Licence | Why | Available? |
|---|---|---|---|---|
| pytest | 9.1.1 | MIT | Test runner (mandated) | ☐ |
| pytest-cov | 7.1.0 | MIT | Coverage reports | ☐ |
| ruff | 0.16.8 | MIT | Linter + formatter (replaces flake8/black/isort) | ☐ |
| mypy | 2.3.1 | MIT | Static type checking (§21) | ☐ |
| moto[s3] | 5.2.3 | Apache-2.0 | Fake S3 for unit tests (no AWS account needed) | ☐ |
| bandit | 1.9.4 | Apache-2.0 | Python security linting (SAST) | ☐ |
| pip-audit | 2.10.1 | Apache-2.0 | Known-vulnerability scan of dependencies. *Optional* if the bank already runs Xray/Snyk/Dependency-Check | ☐ |
| boto3-stubs[s3] | 1.43.101 | MIT | Type hints for boto3 (mypy). *Optional* | ☐ |
| types-openpyxl | 3.1.5.20260827 | Apache-2.0 | Type hints for openpyxl (mypy). *Optional* | ☐ |

**Transitive dev packages (40):** ast-serialize, boolean-py, botocore-stubs, cachecontrol, certifi, charset-normalizer, coverage, cyclonedx-python-lib, defusedxml, filelock, iniconfig, librt, license-expression, markdown-it-py, mdurl, msgpack, mypy-boto3-s3, mypy-extensions, packageurl-python, packaging, pathspec, pip, pip-api, pip-requirements-parser, platformdirs, pluggy, py-partiql-parser, py-serializable, pygments, pyparsing, requests, responses, rich, sortedcontainers, stevedore, tomli, tomli-w, types-s3transfer, werkzeug, xmltodict. Exact versions are in `requirements-dev.txt`. Most come from `pip-audit`, `moto` and `bandit`; dropping pip-audit removes about 15 of them.

---

## 5. Flutter / Dart packages (pub)

Versions as of 24 Sep 2026. The scaffold's `pubspec.yaml` uses **version ranges**, so `flutter pub get` picks the newest versions that work with the Flutter SDK you have. The minimum is **Flutter 3.27**; newer is fine. Only **one** package per concern is used (§15: no competing patterns).

**Why go_router < 18 and data_table_2 < 3:** Flutter 3.47 moved Material widgets into a separate `material_ui` package, and those two releases switched to it. Mixing the two Material libraries breaks the build, so the scaffold stays on `package:flutter/material.dart` until the bank standardises on Flutter ≥ 3.47 (see README §9).

### 5.1 App dependencies

| # | Package | Version | Licence | Why | Direct dependencies it pulls in | Available? |
|---|---|---|---|---|---|---|
| 1 | flutter_riverpod | 3.4.3 | MIT | **The** state-management approach | riverpod, state_notifier, collection, meta | ☐ |
| 2 | go_router | latest **< 18** (17.x) | BSD-3-Clause | URL routing + role-based route guards; browser back/refresh work on web | collection, logging, meta, flutter_web_plugins (SDK) | ☐ |
| 3 | dio | 5.11.1 | MIT | HTTP client: interceptors for JWT refresh, request ID, error mapping | async, collection, http_parser, meta, mime, path, dio_web_adapter | ☐ |
| 4 | intl | 0.20.3 | BSD-3-Clause | Dates, amounts in Indian number format (₹1,00,000.00) | clock, meta, path | ☐ |
| 5 | file_picker | 13.1.0 | MIT | Choose the Excel file to upload | file_picker_platform_interface, file_picker_web, cross_file (+ platform packages for mobile/desktop) | ☐ |
| 6 | web | 1.1.1 | BSD-3-Clause | Official Dart browser API: trigger file downloads, read `window.location` | — | ☐ |
| 7 | data_table_2 | latest **< 3** (2.8.0) | *check pub.dev* | Data grid with fixed header, sorting and **server-side pagination** for dispute queues | async | ☐ |
| 8 | fl_chart | 1.2.0 | MIT | Dashboard charts (volumes, ageing, SLA) | equatable, vector_math | ☐ |
| 9 | json_annotation | 4.12.0 | BSD-3-Clause | Annotations for JSON model code generation | meta | ☐ |

Transitive packages also reported by pub.dev: `riverpod` → async, clock, listen, stack_trace, test_api, uuid. `flutter_riverpod` also lists `flutter_test` (part of the SDK). Confirm the complete list with `flutter pub deps`.

**Fallbacks if unavailable:**
- data_table_2 → Flutter's built-in `PaginatedDataTable` (zero dependencies, less polished)
- fl_chart → phase 1 dashboards as tables and number tiles
- json_annotation/json_serializable → hand-written `fromJson`/`toJson` (more code, zero dependencies)

A commercial grid (`syncfusion_flutter_datagrid`) is **not** proposed. It needs a paid licence at bank scale.

### 5.2 Dev / test only

| Package | Version | Licence | Why | Available? |
|---|---|---|---|---|
| flutter_test, integration_test, flutter_driver | SDK | BSD-3-Clause | Widget and integration tests (ship with Flutter) | n/a |

Note: `flutter_driver` (for the optional browser end-to-end test) pulls in SDK-pinned pub packages such as `webdriver`, `sync_http`, `vm_service` and `file`. `flutter pub get` will show whether they are in Artifactory. If they are missing, remove `flutter_driver` and the `test_driver/` folder; the rest of the app is unaffected.
| flutter_lints | 6.0.0 | BSD-3-Clause | Standard lint rules (pulls `lints`) | ☐ |
| mocktail | 1.0.5 | MIT | Mocking in tests (pulls matcher, test_api) | ☐ |
| build_runner | 2.16.1 | BSD-3-Clause | Runs JSON code generation. *Heavy*: about 30 transitive packages (analyzer, build, shelf, …) | ☐ |
| json_serializable | 6.14.1 | BSD-3-Clause | Generates `fromJson`/`toJson` (pulls analyzer, source_gen, dart_style, …) | ☐ |

### 5.3 Flutter SDK and web engine files

| Item | Why | Available? |
|---|---|---|
| Flutter SDK, stable channel (≥ 3.27) | Build tool | ☐ |
| Flutter engine / web artifacts (CanvasKit, skwasm) mirror, via `FLUTTER_STORAGE_BASE_URL` | `flutter` downloads these on first build. Without a mirror, CI builds fail on a closed network | ☐ |
| pub mirror, via `PUB_HOSTED_URL` | Package downloads | ☐ |

We build with `flutter build web --release --no-web-resources-cdn`. This bundles CanvasKit and fonts inside the app so the browser never calls Google's CDN (gstatic), which bank proxies usually block. Flutter can still fetch fallback fonts from `fonts.gstatic.com` even with this flag, so the app also bundles its own font files (e.g. Roboto/Noto Sans, OFL licence) as assets. The UAT check is that the browser network tab shows no calls to Google domains.

---

## 6. Container images and tools

| Image / tool | Where used | Notes | Available? |
|---|---|---|---|
| `python:3.12-slim` (Debian) | API + worker image | Or the bank's hardened Python 3.12 base image | ☐ |
| `nginx:stable-alpine` (or `nginxinc/nginx-unprivileged:stable-alpine`) | Web container: serves Flutter build, reverse proxy to API (mandated) | Unprivileged variant preferred (runs as non-root) | ☐ |
| `redis:7-alpine` | **Local development only**. AWS uses ElastiCache | | ☐ |
| Oracle for local development: **`gvenzl/oracle-xe:21-slim`** (already in Artifactory, used by the scaffold) | Local/CI database | XE 21 is newer than production 19c; developers must not use features newer than 19c. The migration SQL is 19c-compatible. A shared **RDS Oracle 19c** test instance should also run CI | ☑ |
| Flutter build image (e.g. `ghcr.io/cirruslabs/flutter:stable`) or Flutter SDK on the CI agent | CI build of the web app | | ☐ |
| Docker Engine / Docker Desktop | Developer machines | Docker Desktop needs a paid licence in large organisations; Rancher Desktop or Podman are free alternatives | ☐ |
| Git | Source control (mandated) | | ☐ |
| AWS CLI v2 | Deployment scripts, local S3 testing | | ☐ |

---

## 7. AWS services (cloud approval, not Artifactory)

These are needed for the AWS deployment described in `ARCHITECTURE.md` §10. They go through the bank's cloud approval / CSP process, not the package repository.

| Service | Use |
|---|---|
| Region **ap-south-1 (Mumbai)**, DR **ap-south-2 (Hyderabad)** | Data stays in India (RBI payment-data storage rules) |
| Amazon ECS on Fargate + Amazon ECR | Run the three containers (web, api, worker); private image registry |
| Application Load Balancer (internal) + AWS WAF + ACM | HTTPS entry point from the bank network |
| Amazon RDS for Oracle 19c (Multi-AZ) | Database (mandated Oracle 19c). **Licence decision needed**; see ARCHITECTURE §7.1 |
| Amazon ElastiCache (Redis OSS 7.x) | Cache, locks, rate limits, token deny-list |
| Amazon S3 (+ Object Lock, versioning) | Uploaded files, NPCI files, exports, evidence |
| GuardDuty Malware Protection for S3 | Virus-scan every uploaded file before processing (*confirm it is enabled for ap-south-1 in your account*) |
| AWS KMS | Encryption keys for S3/RDS; protects the AES-256-GCM application key |
| AWS Secrets Manager | DB password, JWT secret, AES key, injected as environment variables |
| Amazon CloudWatch (Logs, metrics, alarms) | Logging and monitoring |
| VPC endpoints (S3, ECR, Secrets Manager, CloudWatch Logs, KMS) | Keep traffic private, no internet egress needed |
| Direct Connect or Site-to-Site VPN | Users reach the app from the bank network; later, reach on-prem AD/LDAP and CBS/Switch extracts |
| AWS Backup | Backup policy for RDS and S3 |
