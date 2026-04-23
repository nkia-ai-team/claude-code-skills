"""Polestar10Client — HTTP direct-call client for polestar10 web operations.

Populated from HAR captures under ../har-captures/ and documented in
../endpoints.md. Each method maps to exactly one endpoint discovered during
the Issue NKIAAI-539 exploration phase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

from .errors import FallThroughRequired, PolestarApiError


@dataclass
class ClientConfig:
    base_url: str
    username: str
    password: str
    verify_ssl: bool = False
    timeout: float = 15.0

    @classmethod
    def from_env(cls) -> "ClientConfig":
        try:
            return cls(
                base_url=os.environ.get("POLESTAR10_BASE_URL", "https://192.168.230.104"),
                username=os.environ["POLESTAR10_USER"],
                password=os.environ["POLESTAR10_PASS"],
                verify_ssl=os.environ.get("POLESTAR10_VERIFY_SSL", "false").lower() == "true",
                timeout=float(os.environ.get("POLESTAR10_TIMEOUT", "15")),
            )
        except KeyError as missing:
            raise PolestarApiError(
                f"missing required env var: {missing.args[0]}"
            ) from missing


class Polestar10Client:
    """Thin HTTP client. Endpoint paths resolved from endpoints.md.

    Method bodies are wired after AC1 (HAR capture) + AC2 (endpoint doc)
    complete. Until then, each method raises FallThroughRequired with a
    descriptive ui_hint so an orchestrator caller can still integrate.
    """

    def __init__(self, config: ClientConfig):
        self.config = config
        self._http = httpx.Client(
            base_url=config.base_url,
            verify=config.verify_ssl,
            timeout=config.timeout,
            follow_redirects=True,
        )
        self._csrf_token: str | None = None
        self._logged_in: bool = False

    @classmethod
    def from_env(cls) -> "Polestar10Client":
        return cls(ClientConfig.from_env())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Polestar10Client":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Endpoints — skeleton. Bodies filled after HAR analysis (US-003/004).
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Establish session + capture CSRF token.

        Wire to the POST endpoint discovered from 01-login.har.
        """
        raise FallThroughRequired(
            operation="login",
            ui_hint="manual login at /login — POST endpoint not yet captured",
        )

    def list_targets(self) -> list[dict[str, Any]]:
        """List existing management targets."""
        raise FallThroughRequired(
            operation="list_targets",
            ui_hint="관리대상 메뉴 > 목록 — GET endpoint not yet captured",
        )

    def add_target(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new management target (관리대상 추가)."""
        raise FallThroughRequired(
            operation="add_target",
            ui_hint="관리대상 > + 버튼 — POST endpoint not yet captured",
        )

    def delete_target(self, target_id: str) -> None:
        """Remove a management target."""
        raise FallThroughRequired(
            operation="delete_target",
            ui_hint="관리대상 행 > 삭제 — DELETE endpoint not yet captured",
        )

    def assign_owner(self, target_id: str, user_id: str) -> None:
        """Assign owner / permission to a target (담당자 권한)."""
        raise FallThroughRequired(
            operation="assign_owner",
            ui_hint="담당자 관리 > 권한 부여 — endpoint not yet captured",
        )

    def register_nms(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register an NMS network (NMS 네트워크 등록)."""
        raise FallThroughRequired(
            operation="register_nms",
            ui_hint="SMS > 네트워크 > NMS 등록 — endpoint not yet captured",
        )

    def register_dpm(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a DPM network."""
        raise FallThroughRequired(
            operation="register_dpm",
            ui_hint="SMS > 네트워크 > DPM 등록 — endpoint not yet captured",
        )

    def add_alert_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Add an individual alert policy (개별 알람 정책 등록)."""
        raise FallThroughRequired(
            operation="add_alert_policy",
            ui_hint="알람 > 정책 > + 버튼 — endpoint not yet captured",
        )
