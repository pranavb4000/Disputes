"""Field-level encryption with AES-256-GCM and HMAC blind indexes (TECH_STACK.md §9).

Ciphertext format:  v{key_version}:{base64(nonce[12] || ciphertext || tag[16])}

- A fresh random 96-bit nonce per encryption (never reused with the same key).
- Associated data binds a ciphertext to its location (e.g. "dispute.customer_account:42"),
  so an encrypted value cannot be copied into another row or column unnoticed.
- Versioned keys allow rotation: new writes use the current key; old versions still decrypt.
- blind_index() gives a deterministic HMAC-SHA256 for exact-match search on encrypted columns.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings

_NONCE_BYTES = 12


class DecryptionError(Exception):
    """Ciphertext is malformed, was tampered with, or the key is unknown."""


class FieldCipher:
    def __init__(self, keys: dict[int, bytes], current_version: int, blind_index_key: bytes) -> None:
        if current_version not in keys:
            raise ValueError("Current AES key version is not configured")
        for version, key in keys.items():
            if len(key) != 32:
                raise ValueError(f"AES key v{version} must be 32 bytes (AES-256)")
        self._keys = {v: AESGCM(k) for v, k in keys.items()}
        self._current = current_version
        self._bidx_key = blind_index_key

    @classmethod
    def from_settings(cls, settings: Settings) -> FieldCipher:
        return cls(settings.aes_keys, settings.aes_key_version, settings.blind_index_key_bytes)

    def encrypt(self, plaintext: str, associated_data: str) -> str:
        nonce = os.urandom(_NONCE_BYTES)
        sealed = self._keys[self._current].encrypt(nonce, plaintext.encode(), associated_data.encode())
        return f"v{self._current}:{base64.b64encode(nonce + sealed).decode()}"

    def decrypt(self, token: str, associated_data: str) -> str:
        try:
            version_part, payload = token.split(":", 1)
            aesgcm = self._keys[int(version_part.removeprefix("v"))]
            raw = base64.b64decode(payload, validate=True)
            plain = aesgcm.decrypt(raw[:_NONCE_BYTES], raw[_NONCE_BYTES:], associated_data.encode())
        except (ValueError, KeyError, InvalidTag) as exc:
            raise DecryptionError("Unable to decrypt value") from exc
        return plain.decode()

    def needs_rotation(self, token: str) -> bool:
        return not token.startswith(f"v{self._current}:")

    def blind_index(self, value: str) -> str:
        normalised = value.strip().upper()
        return hmac.new(self._bidx_key, normalised.encode(), hashlib.sha256).hexdigest()


def mask(value: str | None, visible: int = 4, char: str = "X") -> str:
    """Mask all but the last `visible` characters, e.g. XXXXXX1234."""
    if not value:
        return ""
    if len(value) <= visible:
        return char * len(value)
    return char * (len(value) - visible) + value[-visible:]
