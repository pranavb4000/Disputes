"""Phase 2: verify credentials against the bank's AD / LDAP over LDAPS.

Flow: bind with a read-only service account -> find the user's DN -> bind as the user.
No password is ever stored. The user must also exist and be ACTIVE in app_user with auth_source=LDAP.
Requires `pip install -r requirements-ldap.txt` (ldap3).
"""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.core.exceptions import ServiceUnavailableError
from app.models.user import AppUser
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class LdapAuthProvider:
    source = "LDAP"

    def __init__(self, settings: Settings, users: UserRepository) -> None:
        self._s = settings
        self._users = users

    def authenticate(self, username: str, password: str) -> AppUser | None:
        try:
            from ldap3 import NONE, SUBTREE, Connection, Server  # imported lazily: Phase 2 dependency
            from ldap3.core.exceptions import LDAPException
            from ldap3.utils.conv import escape_filter_chars
        except ImportError as exc:  # pragma: no cover - depends on optional install
            raise ServiceUnavailableError("LDAP support is not installed") from exc

        if not self._s.ldap_url.lower().startswith("ldaps://"):
            raise ServiceUnavailableError("LDAP_URL must use ldaps://")

        server = Server(self._s.ldap_url, use_ssl=True, get_info=NONE, connect_timeout=self._s.ldap_timeout_seconds)
        try:
            with Connection(
                server,
                user=self._s.ldap_bind_dn,
                password=self._s.ldap_bind_password.get_secret_value(),
                auto_bind=True,
                receive_timeout=self._s.ldap_timeout_seconds,
            ) as service_conn:
                search_filter = self._s.ldap_user_filter.format(username=escape_filter_chars(username))
                service_conn.search(self._s.ldap_user_search_base, search_filter, SUBTREE, attributes=[])
                if len(service_conn.entries) != 1:
                    return None
                user_dn = service_conn.entries[0].entry_dn
            user_conn = Connection(
                server, user=user_dn, password=password, receive_timeout=self._s.ldap_timeout_seconds
            )
            if not password or not user_conn.bind():
                return None
            user_conn.unbind()
        except LDAPException as exc:
            logger.error("LDAP authentication error", extra={"error_type": type(exc).__name__})
            raise ServiceUnavailableError("Login service is temporarily unavailable") from exc

        user = self._users.get_by_username(username)
        if user is None or user.auth_source != self.source or not user.is_active:
            return None
        return user
