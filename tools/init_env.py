"""Create .env from .env.example, replacing every __GENERATE__ with a strong random value.

    python tools/init_env.py            # creates .env (refuses to overwrite)
    python tools/init_env.py --force    # regenerate (existing .env is backed up to .env.bak)

Standard library only, so it runs before any package is installed. Works on Windows, macOS, Linux.
"""

from __future__ import annotations

import argparse
import base64
import secrets
import shutil
import string
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE, TARGET = ROOT / ".env.example", ROOT / ".env"

# Oracle passwords: letters+digits only (avoids quoting problems in connect strings and shells),
# must start with a letter.
_ALNUM = string.ascii_letters + string.digits


def _oracle_password(length: int = 24) -> str:
    while True:
        pwd = secrets.choice(string.ascii_letters) + "".join(secrets.choice(_ALNUM) for _ in range(length - 1))
        if any(c.isdigit() for c in pwd) and any(c.isupper() for c in pwd) and any(c.islower() for c in pwd):
            return pwd


def _value_for(key: str) -> str:
    if key == "JWT_SECRET":
        return base64.b64encode(secrets.token_bytes(64)).decode()
    if key in ("AES_ENCRYPTION_KEY", "BLIND_INDEX_KEY"):
        return base64.b64encode(secrets.token_bytes(32)).decode()
    return _oracle_password()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="overwrite an existing .env (backup kept)")
    args = parser.parse_args()

    if TARGET.exists() and not args.force:
        print(f"{TARGET} already exists. Use --force to regenerate (a backup will be kept).")
        return 1
    if TARGET.exists():
        shutil.copy2(TARGET, TARGET.with_suffix(".bak"))

    lines = []
    generated = []
    for line in EXAMPLE.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep and value.strip() == "__GENERATE__" and not line.lstrip().startswith("#"):
            line = f"{key}={_value_for(key.strip())}"
            generated.append(key.strip())
        lines.append(line)
    # Always LF line endings (even on Windows) so docker compose, Python and the Mac read it identically.
    TARGET.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"Created {TARGET}")
    print("Generated: " + ", ".join(generated))
    dev_pwd = next(l.split("=", 1)[1] for l in lines if l.startswith("DEV_USER_PASSWORD="))
    print(f"\nDev login  ->  username: dev_user   password: {dev_pwd}")
    print("(stored in .env as DEV_USER_PASSWORD; dev_checker uses DEV_CHECKER_PASSWORD)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
