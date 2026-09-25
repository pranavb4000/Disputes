"""Unit tests for password hashing, JWT helpers, AES-256-GCM field encryption and settings guards."""

from __future__ import annotations

import base64
import os

import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.crypto import DecryptionError, FieldCipher, mask
from app.core.exceptions import TokenError
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def _key() -> bytes:
    return os.urandom(32)


def test_password_hash_round_trip() -> None:
    stored = hash_password("S3cure-password!")
    assert stored.startswith("scrypt$")
    assert verify_password("S3cure-password!", stored)
    assert not verify_password("wrong", stored)
    assert not verify_password("anything", None)
    assert hash_password("same") != hash_password("same")  # random salt


def test_access_token_round_trip(settings: Settings) -> None:
    token, claims = create_access_token(settings, user_id=7, username="u", roles={"UPI": ["MAKER"]})
    decoded = decode_access_token(settings, token)
    assert decoded.user_id == 7 and decoded.jti == claims.jti


def test_tampered_token_fails(settings: Settings) -> None:
    token, _ = create_access_token(settings, user_id=7, username="u", roles={})
    head, payload, sig = token.split(".")
    with pytest.raises(TokenError):
        decode_access_token(settings, f"{head}.{payload}.{sig[:-4]}AAAA")


def test_aes_gcm_round_trip_and_aad_binding() -> None:
    cipher = FieldCipher({1: _key()}, 1, _key())
    token = cipher.encrypt("123456789012", "dispute.customer_account:1")
    assert token.startswith("v1:")
    assert cipher.decrypt(token, "dispute.customer_account:1") == "123456789012"
    with pytest.raises(DecryptionError):
        cipher.decrypt(token, "dispute.customer_account:2")  # copied to another row


def test_aes_gcm_detects_tampering_and_uses_fresh_nonces() -> None:
    cipher = FieldCipher({1: _key()}, 1, _key())
    a, b = cipher.encrypt("same", "x"), cipher.encrypt("same", "x")
    assert a != b
    raw = bytearray(base64.b64decode(a[3:]))
    raw[-1] ^= 0x01
    with pytest.raises(DecryptionError):
        cipher.decrypt("v1:" + base64.b64encode(bytes(raw)).decode(), "x")


def test_key_rotation_keeps_old_ciphertext_readable() -> None:
    old_key, new_key, bidx = _key(), _key(), _key()
    old_token = FieldCipher({1: old_key}, 1, bidx).encrypt("9876", "t")
    rotated = FieldCipher({1: old_key, 2: new_key}, 2, bidx)
    assert rotated.decrypt(old_token, "t") == "9876"
    assert rotated.needs_rotation(old_token)
    assert rotated.encrypt("9876", "t").startswith("v2:")


def test_blind_index_is_deterministic_and_normalised() -> None:
    cipher = FieldCipher({1: _key()}, 1, _key())
    assert cipher.blind_index(" abc123 ") == cipher.blind_index("ABC123")
    assert cipher.blind_index("ABC123") != cipher.blind_index("ABC124")


def test_mask() -> None:
    assert mask("123456789012") == "XXXXXXXX9012"
    assert mask("12") == "XX"
    assert mask(None) == ""


def _settings(**overrides: str) -> Settings:
    base = {
        "jwt_secret": "x" * 64,
        "aes_encryption_key": base64.b64encode(_key()).decode(),
        "blind_index_key": base64.b64encode(_key()).decode(),
    }
    return Settings(**{**base, **overrides}, _env_file=None)  # type: ignore[call-arg, arg-type]


def test_local_login_is_refused_in_production() -> None:
    with pytest.raises(ValidationError, match="development only"):
        _settings(app_env="production", auth_provider="local")


def test_short_jwt_secret_is_refused() -> None:
    with pytest.raises(ValidationError, match="at least 64 bytes"):
        _settings(jwt_secret="short")


def test_bad_aes_key_is_refused() -> None:
    with pytest.raises(ValidationError, match="32 bytes"):
        _settings(aes_encryption_key=base64.b64encode(b"too-short").decode())


def test_cors_origins_accepts_csv_and_json() -> None:
    assert _settings(cors_origins="http://a:1, http://b:2").cors_origins == ["http://a:1", "http://b:2"]
    assert _settings(cors_origins='["http://a:1"]').cors_origins == ["http://a:1"]
