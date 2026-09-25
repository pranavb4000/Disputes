"""Initial schema: users, modules, roles, audit log, job queue.

Written by hand for Oracle 19c (no features newer than 19c). Reviewed DDL is preferred over
autogenerate for Oracle-specific objects such as the function-based unique index below.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GENESIS_HASH = "0" * 64


def _ts(name: str, nullable: bool = False) -> sa.Column:
    return sa.Column(name, sa.TIMESTAMP(), nullable=nullable)


def upgrade() -> None:
    op.create_table(
        "app_module",
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.String(400)),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("code", name="pk_app_module"),
    )

    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(254)),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("auth_source", sa.String(10), nullable=False),
        sa.Column("password_hash", sa.String(255)),
        _ts("last_login_at", nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_app_user"),
        sa.UniqueConstraint("username", name="uq_app_user_username"),
        sa.CheckConstraint("status IN ('ACTIVE','DISABLED')", name="status"),
        sa.CheckConstraint("auth_source IN ('LOCAL','LDAP')", name="auth_source"),
    )

    op.create_table(
        "user_module_role",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("module_code", sa.String(20), nullable=False),
        sa.Column("role_code", sa.String(20), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_user_module_role"),
        sa.ForeignKeyConstraint(["user_id"], ["app_user.id"], name="fk_user_module_role_user_id"),
        sa.ForeignKeyConstraint(["module_code"], ["app_module.code"], name="fk_user_module_role_module_code"),
        sa.UniqueConstraint("user_id", "module_code", "role_code", name="uq_user_module_role_user_id_module_code_role_code"),
        sa.CheckConstraint("role_code IN ('ADMIN','MAKER','CHECKER')", name="role_code"),
    )
    op.create_index("ix_user_module_role_user_id", "user_module_role", ["user_id"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        _ts("occurred_at"),
        sa.Column("actor_user_id", sa.Integer()),
        sa.Column("actor_username", sa.String(100)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", sa.String(100)),
        sa.Column("module_code", sa.String(20)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("request_id", sa.String(64)),
        sa.Column("details", sa.Text()),
        sa.Column("prev_hash", sa.String(64), nullable=False),
        sa.Column("row_hash", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )
    op.create_index("ix_audit_log_occurred_at", "audit_log", ["occurred_at"])
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"])

    op.create_table(
        "audit_chain",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("last_hash", sa.String(64), nullable=False),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_chain"),
        sa.CheckConstraint("id = 1", name="single_row"),
    )

    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("queue_name", sa.String(30), nullable=False),
        sa.Column("payload", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        _ts("run_after"),
        sa.Column("locked_by", sa.String(100)),
        _ts("lease_until", nullable=True),
        sa.Column("dedup_key", sa.String(200)),
        sa.Column("last_error", sa.String(2000)),
        sa.Column("created_by", sa.String(100)),
        _ts("finished_at", nullable=True),
        _ts("created_at"),
        _ts("updated_at"),
        sa.PrimaryKeyConstraint("id", name="pk_job"),
        sa.CheckConstraint("status IN ('QUEUED','RUNNING','DONE','FAILED','CANCELLED')", name="status"),
    )
    op.create_index("ix_job_claim", "job", ["status", "queue_name", "run_after", "priority"])
    # Function-based unique index: only one QUEUED/RUNNING job per dedup_key (NULLs are not indexed).
    op.create_index(
        "ux_job_active_dedup",
        "job",
        [sa.text("CASE WHEN status IN ('QUEUED','RUNNING') THEN dedup_key END")],
        unique=True,
    )

    op.create_table(
        "job_schedule",
        sa.Column("id", sa.Integer(), sa.Identity(always=True), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("queue_name", sa.String(30), nullable=False),
        sa.Column("payload", sa.Text()),
        sa.Column("interval_seconds", sa.Integer(), nullable=False),
        _ts("next_run_at"),
        _ts("last_run_at", nullable=True),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_job_schedule"),
        sa.UniqueConstraint("job_type", name="uq_job_schedule_job_type"),
    )

    # Reference data -------------------------------------------------------------------------------
    # Timestamps are stored as UTC (see app/utils/time.py).
    now = sa.text("SYS_EXTRACT_UTC(SYSTIMESTAMP)")
    op.execute(
        sa.table(
            "audit_chain",
            sa.column("id", sa.Integer()),
            sa.column("last_hash", sa.String()),
            sa.column("updated_at", sa.TIMESTAMP()),
        )
        .insert()
        .values(id=1, last_hash=GENESIS_HASH, updated_at=now)
    )
    modules = sa.table(
        "app_module",
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("is_enabled", sa.Boolean()),
        sa.column("display_order", sa.Integer()),
    )
    op.bulk_insert(
        modules,
        [
            {"code": "UPI", "name": "UPI", "description": "Unified Payments Interface disputes",
             "is_enabled": True, "display_order": 1},
            {"code": "IMPS", "name": "IMPS", "description": "Immediate Payment Service disputes",
             "is_enabled": False, "display_order": 2},
            {"code": "AEPS", "name": "AEPS", "description": "Aadhaar Enabled Payment System disputes",
             "is_enabled": False, "display_order": 3},
            {"code": "ETOLL", "name": "E-Toll", "description": "FASTag / NETC disputes",
             "is_enabled": False, "display_order": 4},
        ],
    )
    schedules = sa.table(
        "job_schedule",
        sa.column("job_type", sa.String()),
        sa.column("queue_name", sa.String()),
        sa.column("interval_seconds", sa.Integer()),
        sa.column("next_run_at", sa.TIMESTAMP()),
        sa.column("is_enabled", sa.Boolean()),
    )
    op.execute(schedules.insert().values(job_type="SYSTEM_HEARTBEAT", queue_name="light",
                                         interval_seconds=300, next_run_at=now, is_enabled=True))
    op.execute(schedules.insert().values(job_type="SYSTEM_VERIFY_AUDIT_CHAIN", queue_name="light",
                                         interval_seconds=3600, next_run_at=now, is_enabled=True))


def downgrade() -> None:
    op.drop_table("job_schedule")
    op.drop_index("ux_job_active_dedup", table_name="job")
    op.drop_index("ix_job_claim", table_name="job")
    op.drop_table("job")
    op.drop_table("audit_chain")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_occurred_at", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_index("ix_user_module_role_user_id", table_name="user_module_role")
    op.drop_table("user_module_role")
    op.drop_table("app_user")
    op.drop_table("app_module")
