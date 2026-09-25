"""Module-scoped roles and the permissions they grant (ARCHITECTURE.md §9.3).

Roles are assigned per module (UPI, IMPS, ...). Permissions are checked per module on every request.
Adding a role (e.g. VIEWER, AUDITOR) is a change to this mapping only.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    MAKER = "MAKER"
    CHECKER = "CHECKER"


class Permission(StrEnum):
    DISPUTE_VIEW = "dispute.view"
    DISPUTE_ACT = "dispute.act"
    DISPUTE_APPROVE = "dispute.approve"
    UPLOAD_CREATE = "upload.create"
    EXPORT_RUN = "export.run"
    FILE_CONFIRM_UPLOAD = "file.confirm_upload"
    RULE_MANAGE = "rule.manage"
    USER_MANAGE = "user.manage"
    AUDIT_VIEW = "audit.view"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.MAKER: frozenset(
        {
            Permission.DISPUTE_VIEW,
            Permission.DISPUTE_ACT,
            Permission.UPLOAD_CREATE,
            Permission.EXPORT_RUN,
            Permission.FILE_CONFIRM_UPLOAD,
        }
    ),
    Role.CHECKER: frozenset({Permission.DISPUTE_VIEW, Permission.DISPUTE_APPROVE, Permission.EXPORT_RUN}),
    Role.ADMIN: frozenset(
        {Permission.DISPUTE_VIEW, Permission.RULE_MANAGE, Permission.USER_MANAGE, Permission.AUDIT_VIEW}
    ),
}


def permissions_for(roles: set[str]) -> set[str]:
    granted: set[str] = set()
    for role in roles:
        try:
            granted |= {p.value for p in ROLE_PERMISSIONS[Role(role)]}
        except ValueError:
            continue  # unknown role in DB: grant nothing
    return granted
