"""Artifactory smoke test: import every declared package and exercise it briefly.

    python -m scripts.check_dependencies            # runtime packages
    python -m scripts.check_dependencies --dev      # also test/lint tools
    python -m scripts.check_dependencies --ldap     # also Phase 2 LDAP

Needs no database or Redis. Exit code 0 means every package installed and works.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as md
import io
import os
import sys
import time
from collections.abc import Callable

RUNTIME: list[tuple[str, str]] = [  # (distribution name, import name)
    ("fastapi", "fastapi"),
    ("starlette", "starlette"),
    ("pydantic", "pydantic"),
    ("pydantic-settings", "pydantic_settings"),
    ("uvicorn", "uvicorn"),
    ("sqlalchemy", "sqlalchemy"),
    ("oracledb", "oracledb"),
    ("alembic", "alembic"),
    ("redis", "redis"),
    ("pyjwt", "jwt"),
    ("cryptography", "cryptography"),
    ("python-multipart", "python_multipart"),
    ("openpyxl", "openpyxl"),
    ("boto3", "boto3"),
    ("httpx2", "httpx2"),
    ("email-validator", "email_validator"),
]
UVICORN_EXTRAS = [
    ("httptools", "httptools"),
    ("websockets", "websockets"),
    ("watchfiles", "watchfiles"),
    ("python-dotenv", "dotenv"),
    ("pyyaml", "yaml"),
]
if sys.platform != "win32":
    UVICORN_EXTRAS.append(("uvloop", "uvloop"))
DEV = [
    ("pytest", "pytest"),
    ("pytest-cov", "pytest_cov"),
    ("ruff", "ruff"),
    ("mypy", "mypy"),
    ("moto", "moto"),
    ("bandit", "bandit"),
    ("pip-audit", "pip_audit"),
]
LDAP = [("ldap3", "ldap3")]


def _smoke_tests() -> dict[str, Callable[[], None]]:
    def jwt_hs512() -> None:
        import jwt

        secret = os.urandom(64)
        token = jwt.encode({"sub": "1", "exp": int(time.time()) + 60}, secret, algorithm="HS512")
        assert jwt.decode(token, secret, algorithms=["HS512"])["sub"] == "1"

    def aes_gcm() -> None:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        key, nonce = AESGCM.generate_key(bit_length=256), os.urandom(12)
        assert AESGCM(key).decrypt(nonce, AESGCM(key).encrypt(nonce, b"ok", b"aad"), b"aad") == b"ok"

    def excel_round_trip() -> None:
        import openpyxl

        wb = openpyxl.Workbook(write_only=True)
        ws = wb.create_sheet()
        ws.append(["case_number", "rrn", "amount"])
        ws.append(["C1", "123456789012", 100.50])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        sheet = openpyxl.load_workbook(buf, read_only=True).active
        assert sheet is not None
        rows = list(sheet.iter_rows(values_only=True))
        assert rows[1][0] == "C1"

    def oracle_dialect() -> None:
        import oracledb
        from sqlalchemy import create_engine

        engine = create_engine("oracle+oracledb://u:p@localhost:1521/?service_name=XEPDB1")
        assert engine.dialect.name == "oracle" and oracledb.is_thin_mode()

    def fastapi_app() -> None:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.get("/ping")(lambda: {"pong": True})
        assert TestClient(app).get("/ping").json() == {"pong": True}

    def email() -> None:
        from email_validator import validate_email

        assert validate_email("ops.user@example.com", check_deliverability=False).normalized

    def s3_client() -> None:
        import boto3

        client = boto3.client("s3", region_name="ap-south-1", aws_access_key_id="x", aws_secret_access_key="x")  # noqa: S106  # nosec B106
        assert client.meta.region_name == "ap-south-1"

    return {
        "JWT HS512": jwt_hs512,
        "AES-256-GCM": aes_gcm,
        "Excel read/write": excel_round_trip,
        "Oracle dialect (thin)": oracle_dialect,
        "FastAPI test client": fastapi_app,
        "Email validation": email,
        "boto3 S3 client": s3_client,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--ldap", action="store_true")
    args = parser.parse_args()

    groups = [("Runtime", RUNTIME + UVICORN_EXTRAS)]
    if args.dev:
        groups.append(("Dev/test", DEV))
    if args.ldap:
        groups.append(("LDAP (Phase 2)", LDAP))

    failures = 0
    print(f"Python {sys.version.split()[0]} on {sys.platform}\n")
    for title, packages in groups:
        print(f"== {title} packages ==")
        for dist, module in packages:
            try:
                importlib.import_module(module)
                print(f"  OK    {dist:<20} {md.version(dist)}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"  FAIL  {dist:<20} {type(exc).__name__}: {exc}")
    print("\n== Smoke tests ==")
    for name, test in _smoke_tests().items():
        try:
            test()
            print(f"  OK    {name}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    print(f"\n{'ALL GOOD' if failures == 0 else f'{failures} problem(s) found'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
