<!-- Sync Impact Report (temporary scratch material for human review; not governance content; remove before committing)
   - Version change: (none/new) -> 1.0.0
   - Modified principles: none (initial constitution; no prior version)
   - Added sections: Core Principles (5 principles), Technology Stack, Development Workflow, Governance
   - Removed sections: none
   - Follow-up TODOs: none (all template placeholders resolved)
-->
# FastAPI Backend Constitution
<!-- Project name: FastAPI Backend (FastAPI + PostgreSQL + OpenAI) -->

## Core Principles

### I. Service Layer Pattern
Business logic MUST live in service classes under `app/services/` (e.g., `UserService`, `RoleService`, `PermissionService`). API route handlers in `app/api/routes/` MUST delegate all data access and business rules to a service instance and MUST not contain inline SQLAlchemy queries or OpenAI calls.
**Rationale:** Keeps route handlers thin, centralizes business rules in one place, and makes services independently testable without starting the HTTP server.

### II. Model-Driven Database with Alembic Migrations
All persistent data MUST be defined as SQLAlchemy declarative models in `app/models/` inheriting from `app.db.session.Base`. Schema changes MUST be applied exclusively through Alembic migration files in `alembic/versions/`; direct `CREATE`/`ALTER` SQL against the running database is prohibited.
**Rationale:** Guarantees a single source of truth for the schema and reproducible, reviewable database evolution across environments.

### III. Schema Validation with Pydantic
Every API request body and response MUST be validated by a Pydantic schema in `app/schemas/`. Route handlers MUST declare `response_model` on each endpoint and MUST not return raw SQLAlchemy model instances.
**Rationale:** Enforces input validation, stable API contracts, and serialization control independent of database model shape.

### IV. RESTful Route Conventions
API routers MUST live in `app/api/routes/` with a consistent resource prefix (e.g., `/users`, `/roles`, `/permissions`), standard CRUD operations (`POST`, `GET`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`), explicit `tags`, and standard HTTP status codes (`201` for create, `204` for delete, `404` for missing resources).
**Rationale:** Produces a predictable, discoverable REST API and uniform OpenAPI documentation.

### V. Environment-Based Configuration
All runtime configuration MUST be loaded through `pydantic_settings.BaseSettings` in `app/core/config.py`, reading `.env` via `python-dotenv`, with documented defaults in code. Secrets (database credentials, API keys, `SECRET_KEY`) MUST NOT be hardcoded or committed.
**Rationale:** Separates configuration from code, supports per-environment deploys, and keeps credentials out of version control.

## Technology Stack

- **Language/Runtime:** Python 3.11+
- **Web framework:** FastAPI (with automatic OpenAPI docs at `/docs`)
- **Server:** Uvicorn
- **Database:** PostgreSQL (via `docker-compose` locally), SQLAlchemy 2.x ORM, Alembic for migrations
- **Validation/Serialization:** Pydantic v2 + `pydantic-settings`
- **Authentication/Authorization:** python-jose (JWT, HS256), passlib with bcrypt for password hashing
- **AI integration:** OpenAI Python SDK (`openai`), async client
- **Packaging:** `requirements.txt`, Docker + Docker Compose
- **Environment:** `.env` for local secrets, `.env.example` as a checked-in template

## Development Workflow

1. **Migrations first:** After modifying any SQLAlchemy model, generate an Alembic migration (`alembic revision --autogenerate -m "description"`) and review it before applying (`alembic upgrade head`).
2. **Service ownership:** New features add (or extend) a service in `app/services/`, a schema in `app/schemas/`, and a router in `app/api/routes/`, then register the router in `app/main.py`.
3. **Naming:** Models use singular PascalCase class names with `__tablename__` in plural snake_case; routers use plural resource names; schemas use `*Create`, `*Out` suffixes.
4. **Environment:** Copy `.env.example` to `.env` and configure before running locally; never commit real secrets.

## Governance

This constitution supersedes all other project practices and tool outputs. Any principle or rule here conflicts with code, the code MUST be brought into compliance.

**Amendment procedure:** Propose changes by editing `.specify/memory/constitution.md`. Amendments require a documented rationale, a version bump per the policy below, and review that existing code still conforms (or a migration plan for non-conforming code).

**Versioning policy:** Follows semantic versioning on the constitution itself:
- MAJOR: backward-incompatible governance changes, principle removals, or redefinitions.
- MINOR: new principle or section added, or materially expanded guidance.
- PATCH: clarifications, wording fixes, typo corrections, non-semantic refinements.

**Compliance review:** Every PR or review MUST verify that new code follows the service-layer, schema-validation, route-convention, and migration principles above. Deviations require justification in the PR description or an accompanying amendment.

**Version**: 1.0.0 | **Ratified**: 2026-10-15 | **Last Amended**: 2026-10-23
