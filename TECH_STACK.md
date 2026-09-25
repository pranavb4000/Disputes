# Project Technology Stack & Development Standards

## 1. Purpose

This document defines the mandatory technology stack, architecture, security standards, coding conventions, and development guidelines for this project.

> **AI coding agents MUST refer to this document before creating, modifying, or reviewing code.**
>
> Do not introduce a different framework, library, architecture, or technology without explicit approval.

---

## 2. Technology Stack

| Layer | Technology | Version / Standard |
|---|---|---|
| Backend Language | Python | 3.12+ |
| Backend Framework | FastAPI | Latest stable compatible version |
| API Style | REST | JSON over HTTPS |
| ORM / Database Layer | SQLAlchemy | 2.x |
| Oracle Driver | python-oracledb | Latest stable compatible version |
| Database | Oracle Database | 19c |
| Cache | Redis | 7.x |
| Redis Client | redis-py | Latest stable compatible version |
| Authentication | JWT | HS512 |
| Data Encryption | AES-256-GCM | Required where encryption is needed |
| Frontend / Client | Flutter | Stable channel |
| Reverse Proxy | Nginx | Stable |
| API Documentation | OpenAPI | FastAPI generated |
| API Server | Uvicorn | Latest stable compatible version |
| Testing | Pytest | Latest stable compatible version |
| Containerization | Docker | — |
| Source Control | Git | Required |

> **Frontend standard:** Flutter is the only approved frontend/client framework for this project. React and other web frontend frameworks are not part of the approved technology stack.

---

## 3. High-Level Architecture

The application follows a layered client-server architecture.

```
                    ┌──────────────────┐
                    │     Flutter      │
                    │      Client      │
                    │   Web / Mobile   │
                    └────────┬─────────┘
                             │
                             │ HTTPS / REST
                             │
                    ┌────────▼─────────┐
                    │      Nginx       │
                    │  Reverse Proxy   │
                    └────────┬─────────┘
                             │
                             ▼
              ┌────────────────────────────┐
              │      FastAPI Backend       │
              │                            │
              │  API / Auth / Services     │
              │  Business Logic            │
              │  Validation                │
              │  Repository / Data Access  │
              └────────────┬───────────────┘
                           │
                 ┌─────────┴─────────┐
                 │                   │
                 ▼                   ▼
        ┌────────────────┐   ┌─────────────────┐
        │ Oracle DB 19c  │   │     Redis 7     │
        │ Persistent     │   │ Cache / Session │
        │ Data           │   │ / Temporary     │
        └────────────────┘   └─────────────────┘
```

Flutter is the sole application client and communicates with the FastAPI backend through documented HTTPS REST APIs.

---

## 4. Backend

### 4.1 Framework

The backend **MUST** use FastAPI.

FastAPI should be used for:

- REST API endpoints
- Request validation
- Response serialization
- Authentication dependencies
- OpenAPI documentation
- Dependency injection
- HTTP exception handling

Avoid introducing Flask, Django, or another backend framework unless explicitly approved.

### 4.2 Python Version

Use:

```
Python 3.12+
```

The project should use a virtual environment or containerized environment.

Dependencies **MUST** be explicitly declared in the project's dependency configuration.

Do not install packages globally.

---

## 5. Backend Architecture

Use a layered architecture.

Recommended structure:

```
backend/
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── router.py
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── ...
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   └── ...
│   │
│   ├── schemas/
│   │   ├── user.py
│   │   └── ...
│   │
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── ...
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── ...
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── session.py
│   │
│   ├── cache/
│   │   └── redis.py
│   │
│   └── utils/
│       └── ...
│
├── tests/
├── migrations/
├── requirements.txt / pyproject.toml
├── Dockerfile
└── README.md
```

### Layer responsibilities

#### API / Router

Responsible for:

- HTTP requests
- HTTP responses
- Request/response schemas
- Authentication dependencies
- Calling services

Routers **MUST NOT** contain significant business logic.

#### Service

Responsible for:

- Business rules
- Workflows
- Validation beyond basic schema validation
- Coordinating repositories
- Coordinating external services

#### Repository

Responsible for:

- Database queries
- Persistence
- Database-specific operations

Repositories **SHOULD NOT** contain business rules.

#### Models

Represent database entities.

#### Schemas

Represent API request and response models.

Do not expose database models directly as API responses.

---

## 6. Database

### 6.1 Oracle

The primary relational database is:

```
Oracle Database 19c
```

Use:

```
SQLAlchemy 2.x
+
python-oracledb
```

Oracle-specific functionality should be isolated where possible.

### 6.2 Database Rules

AI agents **MUST**:

- Use parameterized queries.
- Never construct SQL using string concatenation with user input.
- Use transactions appropriately.
- Avoid unnecessary database round trips.
- Use indexes for frequently queried columns.
- Use pagination for large result sets.
- Avoid loading large datasets into memory unnecessarily.
- Handle database exceptions consistently.
- Keep database credentials outside source code.

Never hardcode:

- username
- password
- connection strings
- secrets
- API keys
- JWT secrets
- encryption keys

---

## 7. Redis

Use:

```
Redis 7.x
```

Redis may be used for:

- Caching
- Short-lived data
- Rate limiting
- Temporary state
- Token/session-related data where required
- Distributed locks where required

Redis **MUST NOT** automatically become the primary source of truth for persistent business data.

Persistent business data belongs in Oracle unless explicitly designed otherwise.

### Cache rules

- Every cache entry **SHOULD** have an appropriate TTL.
- Cache invalidation **MUST** be considered when modifying the underlying database data.
- Do not cache sensitive information unnecessarily.

---

## 8. Authentication & Authorization

### 8.1 JWT

Authentication uses:

```
JWT
HS512
```

The JWT signing secret **MUST**:

- Be stored in environment variables or a secure secret manager.
- Never be committed to Git.
- Never be hardcoded in source code.
- Have sufficient entropy.
- Be different between development, testing, staging, and production.

Example conceptual flow:

```
Login
  ↓
Validate credentials
  ↓
Generate JWT
  ↓
Sign JWT using HS512
  ↓
Return access token
  ↓
Flutter sends:
Authorization: Bearer <token>
  ↓
FastAPI validates JWT
  ↓
Extract user identity / claims
  ↓
Authorize request
```

### 8.2 JWT Claims

JWT claims **SHOULD** contain only information required by the application.

Typical claims:

- `sub`
- `iat`
- `exp`
- `jti`
- roles / permissions

Do not place sensitive information such as the following inside JWT claims:

- Passwords
- Encryption keys
- Personal secrets
- Confidential business data

Remember that a signed JWT is **not** automatically encrypted.

---

## 9. AES-256-GCM

When application data requires encryption, use:

```
AES-256-GCM
```

AES-GCM provides authenticated encryption.

Encryption implementations **MUST**:

- Use a secure random nonce/IV.
- Never reuse a nonce with the same encryption key.
- Keep encryption keys outside source code.
- Authenticate ciphertext using GCM authentication tags.
- Clearly define key management and rotation strategy.

Do not implement cryptographic algorithms manually.

Use a well-maintained cryptographic library.

### Important

JWT HS512 and AES-256-GCM serve different purposes:

```
HS512       → JWT integrity/authentication
AES-256-GCM → Data confidentiality + integrity
```

- Do not assume HS512 encrypts JWT contents.
- Do not add AES encryption to JWTs unless the application requirements specifically require encrypted tokens.

---

## 10. API Design

All APIs **MUST** be RESTful and use JSON unless there is an explicit reason otherwise.

Recommended API structure:

```
/api/v1/auth/login
/api/v1/auth/refresh
/api/v1/users
/api/v1/users/{id}
```

Use API versioning:

```
/api/v1/...
```

### HTTP methods

Use standard HTTP semantics:

| Method | Purpose |
|---|---|
| `GET` | Retrieve |
| `POST` | Create |
| `PUT` | Replace |
| `PATCH` | Partial update |
| `DELETE` | Delete |

### HTTP status codes

Use appropriate status codes. Examples:

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

Do not return `200 OK` for every type of operation.

---

## 11. API Response Format

The API should use a consistent response structure.

Example:

```json
{
  "success": true,
  "data": {},
  "message": null
}
```

For errors:

```json
{
  "success": false,
  "data": null,
  "message": "Resource not found",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

The exact response contract should be defined centrally and reused.

Do not create arbitrary response formats for individual endpoints without a valid reason.

---

## 12. Validation

Use Pydantic models for API validation.

Validate:

- Required fields
- Data types
- String lengths
- Numeric ranges
- Enumerations
- Email formats
- Dates
- Business-specific constraints

Never trust client-side validation alone.

All security-sensitive validation **MUST** happen on the backend.

---

## 13. Error Handling

Use centralized exception handling.

Do not expose the following to API clients:

- Stack traces
- SQL statements
- Database credentials
- Internal file paths
- Secrets
- Internal infrastructure details

Detailed technical information belongs in server logs, not API responses.

---

## 14. Logging

Use structured application logging where practical.

Logs **SHOULD** contain useful context such as:

- timestamp
- log level
- request ID
- user ID when appropriate
- endpoint
- operation
- duration
- result

Never log:

- passwords
- JWT tokens
- refresh tokens
- encryption keys
- API secrets
- database passwords
- sensitive personal data

---

## 15. Flutter Client

Flutter is the only approved frontend/client framework for this project.

Use:

```
Flutter
Stable channel
```

Flutter is responsible for the application user interface and client-side presentation.

Flutter communicates with the FastAPI backend exclusively through documented HTTPS REST APIs.

Flutter **MUST NOT** connect directly to:

- Oracle
- Redis

The Flutter application should consume the documented backend API contracts.

Where practical, shared API contracts should be used consistently across all supported Flutter targets.

### Flutter architecture

The Flutter application should separate concerns such as:

```
UI / Widgets
    ↓
Pages / Features
    ↓
State / Application Logic
    ↓
API Client
    ↓
REST API
```

The exact internal Flutter architecture may be selected based on project requirements, but it **MUST** remain consistent with the project's established patterns.

Do not introduce multiple competing state-management or architectural patterns without explicit approval.

### Flutter security

Authentication tokens should be stored using platform-appropriate secure storage mechanisms rather than plain local storage.

Flutter **MUST NOT** contain:

- Database credentials
- JWT signing secrets
- AES encryption master keys
- Backend infrastructure credentials
- Other server-side secrets

Client-side validation may improve UX but does not replace backend validation.

Do not duplicate backend business rules unnecessarily in Flutter.

---

## 16. Nginx

Nginx acts as the reverse proxy.

Typical production flow:

```
Internet
   ↓
HTTPS
   ↓
Nginx
   ↓
FastAPI / Uvicorn
```

Nginx may handle:

- TLS termination
- Reverse proxying
- Compression
- Request size limits
- Security headers
- Rate limiting where appropriate

The FastAPI application should not be directly exposed to the public internet in production.

---

## 17. HTTPS

Production communication **MUST** use HTTPS.

Plain HTTP should not be used for authenticated production traffic.

Security-sensitive cookies, if used, should have appropriate attributes:

- `Secure`
- `HttpOnly`
- `SameSite`

---

## 18. Environment Configuration

Configuration **MUST** be environment-specific.

Recommended environments:

- development
- test
- staging
- production

Use environment variables or a secure configuration/secret-management solution.

Example:

```env
APP_ENV=development

DATABASE_HOST=
DATABASE_PORT=
DATABASE_SERVICE=
DATABASE_USER=
DATABASE_PASSWORD=

REDIS_HOST=
REDIS_PORT=

JWT_SECRET=
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=

AES_ENCRYPTION_KEY=
```

Never commit real credentials to Git.

Provide an example configuration such as `.env.example` with placeholder values only.

---

## 19. Testing

Backend testing should use:

```
pytest
```

Tests **SHOULD** include:

- Unit tests
- Service tests
- Repository tests where appropriate
- API/integration tests
- Authentication tests
- Authorization tests
- Validation tests
- Error-handling tests

Security-sensitive functionality requires tests.

At minimum, authentication tests should cover:

- Valid credentials
- Invalid credentials
- Expired JWT
- Invalid JWT
- Missing JWT
- Insufficient permissions

Flutter functionality **SHOULD** also be tested using the appropriate Flutter/Dart testing mechanisms where applicable.

---

## 20. Code Quality

Python code **MUST** follow standard Python conventions.

| Prefer | Avoid |
|---|---|
| Type hints | Giant functions |
| Small functions | Giant router files |
| Clear naming | Global mutable state |
| Dependency injection | Circular dependencies |
| Single responsibility | Copy/paste implementations |
| Reusable services | Hardcoded configuration |
| Explicit error handling | Unnecessary abstractions |
| Automated tests | Unnecessary dependencies |

Flutter/Dart code should similarly favor:

- Clear naming
- Small, focused widgets/classes
- Separation of UI and application logic
- Reusable components
- Explicit state management
- Automated tests
- Consistent project conventions

---

## 21. Type Safety

Use Python type hints throughout the backend.

Example:

```python
def get_user(user_id: int) -> UserResponse:
    ...
```

Avoid unnecessary use of `Any` when a specific type can be defined.

Pydantic models should be preferred for API contracts.

Flutter/Dart code should use Dart's type system and null-safety features appropriately.

---

## 22. Dependency Management

All dependencies **MUST** be explicitly declared.

Before adding a dependency, the AI agent should consider:

- Is it actually necessary?
- Is the functionality already available in the existing stack?
- Is the library actively maintained?
- Does it introduce security or licensing concerns?
- Does it significantly increase project complexity?

Do not add dependencies simply for convenience.

Do not introduce React, Angular, Vue, or another frontend framework.

---

## 23. Security Principles

All development **MUST** follow these principles:

| Principle | Meaning |
|---|---|
| **Never trust client input** | Every request must be validated server-side. |
| **Least privilege** | Users, services, database accounts, and applications should receive only the permissions they need. |
| **Secure defaults** | New functionality should be secure without requiring developers to remember additional security steps. |
| **Defense in depth** | Do not rely on a single security mechanism. |
| **Secrets stay secret** | Never commit credentials or keys. |
| **Fail securely** | Unexpected failures should not expose sensitive information. |

---

## 24. Database Transaction Rules

Business operations involving multiple database modifications should use appropriate transactions.

Example:

```
BEGIN
   ↓
Create Order
   ↓
Create Order Items
   ↓
Update Inventory
   ↓
COMMIT
```

If an operation fails:

```
ROLLBACK
```

Do not leave partially completed business operations unless explicitly designed for eventual consistency.

---

## 25. API Documentation

FastAPI's OpenAPI documentation should be maintained as part of the API implementation.

Endpoints **SHOULD** include:

- Summary
- Description
- Request schema
- Response schema
- Authentication requirements
- Possible error responses

The API documentation should remain synchronized with the implementation.

---

## 26. Git Rules

Never commit:

- `.env`
- secrets
- private keys
- database passwords
- JWT secrets
- production credentials

Use meaningful commits. Examples:

```
feat: add user registration
fix: handle expired access token
refactor: extract user repository
test: add authentication tests
docs: update API documentation
```

---

## 27. AI Coding Agent Rules

Before modifying code, the AI agent **MUST**:

1. Read this `TECH_STACK.md`.
2. Inspect the existing project structure.
3. Reuse existing patterns before introducing new ones.
4. Check whether the required functionality already exists.
5. Follow the architecture defined in this document.
6. Avoid introducing alternative frameworks without approval.
7. Avoid unnecessary dependencies.
8. Preserve existing API contracts unless the task explicitly requires a breaking change.
9. Add or update tests for meaningful backend changes.
10. Never introduce hardcoded secrets.
11. Never weaken existing security controls to make a feature easier.
12. Keep database access inside the repository/data-access layer.
13. Keep business logic inside services.
14. Keep HTTP concerns inside API/router layers.
15. Keep Flutter UI concerns separate from backend business logic.
16. Do not introduce React or another frontend framework.

---

## 28. Technology Decision Rules

The following are the default technologies and **SHOULD NOT** be replaced without explicit approval.

```
Backend        → FastAPI
Language       → Python 3.12+
Database       → Oracle 19c
ORM            → SQLAlchemy 2.x
Oracle Driver  → python-oracledb
Cache          → Redis 7
API            → REST / JSON
Authentication → JWT HS512
Encryption     → AES-256-GCM
Frontend       → Flutter
Proxy          → Nginx
Testing        → Pytest
```

React is not part of the approved technology stack.

If an implementation requires a new technology, the AI agent should first determine whether the existing stack can solve the problem.

---

## 29. Architecture Priority

When making implementation decisions, follow this priority:

1. Security
2. Correctness
3. Maintainability
4. Reliability
5. Performance
6. Simplicity
7. Convenience

Do not sacrifice security or correctness merely to make implementation faster.

---

## 30. Final Rule for AI Agents

This document is the source of truth for the project's technology stack and architectural conventions.

When generating or modifying code:

```
Read TECH_STACK.md
       ↓
Inspect existing code
       ↓
Follow existing project patterns
       ↓
Follow this technology stack
       ↓
Implement the smallest clean solution
       ↓
Add/update tests
       ↓
Review security implications
       ↓
Return the implementation
```

If a requested change conflicts with this document, do not silently switch technologies or architectural patterns.

Clearly identify the conflict and request approval before introducing a major deviation.

> **Frontend standard:** Flutter only. React and other frontend frameworks are explicitly excluded unless the project owner provides explicit approval to change this technology decision.

---

## 31. Approved Project-Specific Additions

Recorded so AI agents do not treat these as unapproved deviations. Details are in `ARCHITECTURE.md`.

| # | Addition | Status | Approved by / date |
|---|---|---|---|
| 1 | **Hosting on AWS**: ap-south-1 (Mumbai) primary, ap-south-2 (Hyderabad) DR. Oracle 19c on Amazon RDS for Oracle, Redis 7 on Amazon ElastiCache, containers on Amazon ECS | Approved | Project owner, 2026-09-24 |
| 2 | **Amazon S3** for file storage (uploads, NPCI files, exports, evidence) via `boto3`. A local-folder implementation is used in development | Approved | Project owner, 2026-09-24 |
| 3 | **Background processing** with an Oracle `job` table + worker process (same codebase) + Redis wake-up/locks. No Celery, RabbitMQ or other job framework | Approved | Project owner, 2026-09-24 |
| 4 | **Authentication phases**: dev-only local login now (must never run in staging/production); LDAP (`ldap3`) in Phase 2 | Approved | Project owner, 2026-09-24 |
| 5 | **Token handling (Flutter Web)**: JWT HS512 access token held in memory; refresh token in an HttpOnly/Secure/SameSite=Strict cookie with rotation (ARCHITECTURE §9.2) | Recommended, **pending confirmation** | — |
| 6 | Additional libraries listed in `DEPENDENCIES.md` | **Pending** Artifactory availability check | — |
