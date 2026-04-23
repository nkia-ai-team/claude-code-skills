"""Polestar10Client — HTTP direct-call client for polestar10 web operations.

Populated from HAR captures under ../har-captures/ and documented in
../endpoints.md. Each method maps to exactly one endpoint discovered during
the Issue NKIAAI-539 exploration phase.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from typing import Any

import httpx

from .errors import FallThroughRequired, PolestarApiError


def _sha512(text: str) -> str:
    return hashlib.sha512(text.encode("utf-8")).hexdigest()


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
        self._organization_id: str | None = None

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

    def login(self) -> dict[str, Any]:
        """Establish session via polestar10 3-step challenge-response flow.

        1. POST /api/account/pre-login {loginId, password=sha512(pwd)}
           -> {challenge, organizations}
        2. POST /api/cm/two-factor-authentication/enable {parameter:"SECONDARY_CERTIFICATION"}
           -> {enable, email, sms, otp}; raise if MFA on and no secret
        3. POST /api/account/login {loginId, challenge,
              challengeResponse=sha512(sha512(pwd)+challenge), organizationId}
           -> sets accessToken + refreshToken cookies; returns user info
        """
        hashed_pwd = _sha512(self.config.password)

        try:
            r1 = self._http.post(
                "/api/account/pre-login",
                json={"loginId": self.config.username, "password": hashed_pwd},
            )
            r1.raise_for_status()
            pre = r1.json()
            if not pre.get("success"):
                raise PolestarApiError(
                    f"pre-login failed: {pre.get('errorCode')}", payload=pre
                )
            challenge = pre["data"]["challenge"]
            orgs = pre["data"]["organizations"]
            if not orgs:
                raise PolestarApiError("pre-login returned no organizations", payload=pre)
            organization_id = orgs[0]["organizationId"]

            r2 = self._http.post(
                "/api/cm/two-factor-authentication/enable",
                json={"parameter": "SECONDARY_CERTIFICATION"},
            )
            r2.raise_for_status()
            mfa = r2.json().get("data", {})
            if any(mfa.get(k) for k in ("enable", "email", "sms", "otp")):
                raise FallThroughRequired(
                    operation="login",
                    ui_hint=(
                        f"MFA enabled for {self.config.username} ({mfa}); "
                        "use UI login — no TOTP path implemented"
                    ),
                )

            challenge_response = _sha512(hashed_pwd + challenge)
            r3 = self._http.post(
                "/api/account/login",
                json={
                    "loginId": self.config.username,
                    "challenge": challenge,
                    "challengeResponse": challenge_response,
                    "organizationId": organization_id,
                },
            )
            r3.raise_for_status()
            login = r3.json()
            if not login.get("success"):
                raise PolestarApiError(
                    f"login failed: {login.get('errorCode')}", payload=login
                )
        except httpx.HTTPError as exc:
            raise PolestarApiError(f"login transport error: {exc}") from exc

        self._logged_in = True
        self._organization_id = organization_id
        return login["data"]

    def list_targets(
        self,
        *,
        page: int = 0,
        size: int = 50,
        resource_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """List existing management targets via `/api/cm/configuration/list`.

        Spring endpoint has multiple aliases (list / search / find / paging /
        list-paging / find-all) — all map to the same handler. We use `list`.
        """
        self._ensure_logged_in()
        body: dict[str, Any] = {"page": page, "size": size}
        if resource_type is not None:
            body["resourceType"] = resource_type
        r = self._http.post("/api/cm/configuration/list", json=body)
        r.raise_for_status()
        data = r.json()
        if not data.get("success"):
            raise PolestarApiError(
                f"list_targets failed: {data.get('errorCode')}", payload=data
            )
        return data.get("data", {}).get("configItems", [])

    def list_groups(self) -> list[dict[str, Any]]:
        """List resource groups via `/api/cm/groups/list`."""
        self._ensure_logged_in()
        r = self._http.post("/api/cm/groups/list", json={})
        r.raise_for_status()
        return r.json().get("data", [])

    def add_target(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new management target (관리대상 추가).

        The write-side endpoint is not captured in the exploratory HARs: the
        SPA submits from a deeply nested modal dialog whose DOM path depends
        on a licensed widget bundle that the CI environment does not expose
        via direct URL routes. Follow-up iteration should use `playwright
        codegen` while an operator clicks through the 관리대상 추가 dialog,
        then replace this FallThroughRequired.
        """
        raise FallThroughRequired(
            operation="add_target",
            ui_hint="전체구성 > 관리대상 > (리소스타입 선택) > + 추가 — POST endpoint TBD",
        )

    def delete_target(self, target_id: str) -> None:
        """Remove a management target."""
        raise FallThroughRequired(
            operation="delete_target",
            ui_hint="전체구성 > 관리대상 > (행 선택) > 삭제 — DELETE endpoint TBD",
        )

    def assign_owner(self, target_id: str, user_id: str) -> None:
        """Assign owner / permission to a target (담당자 권한)."""
        raise FallThroughRequired(
            operation="assign_owner",
            ui_hint="시스템 관리 > 사용자/권한 — endpoint TBD (/api/account/* 후속 탐색 필요)",
        )

    def register_nms(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register an NMS network (NMS 네트워크 등록)."""
        raise FallThroughRequired(
            operation="register_nms",
            ui_hint="NMS > 네트워크 > 등록 — /api/nms/* 경로, 스키마 후속 탐색 필요",
        )

    def register_dpm(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Register a DPM network."""
        raise FallThroughRequired(
            operation="register_dpm",
            ui_hint="DPM > 등록 — /api/dpm/* 경로, 스키마 후속 탐색 필요",
        )

    def add_alert_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Add an individual alert policy (개별 알람 정책 등록)."""
        raise FallThroughRequired(
            operation="add_alert_policy",
            ui_hint="알람 > 정책 관리 > 개별 정책 등록 — /api/alarm/* 경로, 스키마 후속 탐색 필요",
        )

    # ------------------------------------------------------------------
    def _ensure_logged_in(self) -> None:
        if not self._logged_in:
            self.login()
