"""Create the DEVELOPMENT-ONLY login accounts.

    python -m scripts.seed_dev

- dev_user     : the shared developer login (ADMIN + MAKER on UPI)
- dev_checker  : second account, only for testing maker-checker approvals (CHECKER on UPI)

Passwords come from DEV_USER_PASSWORD / DEV_CHECKER_PASSWORD in .env. Refuses to run outside
development/test. Safe to run repeatedly (updates passwords, adds missing roles).
"""

from __future__ import annotations

import sys

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.database import SessionLocal, get_engine
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository

DEV_ACCOUNTS = [
    # username, display name, setting holding the password, [(module, role)]
    ("dev_user", "Developer", "dev_user_password", [("UPI", "ADMIN"), ("UPI", "MAKER")]),
    ("dev_checker", "Developer (Checker)", "dev_checker_password", [("UPI", "CHECKER")]),
]


def main() -> int:
    settings = get_settings()
    if not settings.is_development:
        print("Refusing to seed dev accounts outside development/test.", file=sys.stderr)
        return 1
    get_engine()
    with SessionLocal() as db:
        users = UserRepository(db)
        for username, display_name, password_field, roles in DEV_ACCOUNTS:
            password = getattr(settings, password_field).get_secret_value()
            if len(password) < 12:
                print(
                    f"{password_field.upper()} must be set in .env (min 12 chars); skipping {username}", file=sys.stderr
                )
                continue
            user = users.get_by_username(username)
            if user is None:
                user = users.add(
                    AppUser(
                        username=username,
                        display_name=display_name,
                        status="ACTIVE",
                        auth_source="LOCAL",
                        password_hash=hash_password(password),
                    )
                )
                action = "created"
            else:
                user.password_hash = hash_password(password)
                action = "updated"
            for module_code, role_code in roles:
                users.add_role(user.id, module_code, role_code)
            print(f"{action}: {username} ({', '.join(f'{m}:{r}' for m, r in roles)})")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
