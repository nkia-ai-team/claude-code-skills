"""Integration test against a live polestar10 instance.

AC3 requires login -> add_target -> list_targets(신규 포함) ->
delete_target -> list_targets(제거 확인). This iteration delivers the
login + list half; add/delete raise FallThroughRequired (documented in
endpoints.md) and are marked xfail until the write-side endpoints are
captured from a live UI session.
"""

from __future__ import annotations

import os

import pytest

from polestar10_client import FallThroughRequired, Polestar10Client

_HAS_CREDS = bool(os.environ.get("POLESTAR10_USER") and os.environ.get("POLESTAR10_PASS"))


@pytest.mark.skipif(not _HAS_CREDS, reason="POLESTAR10_USER / POLESTAR10_PASS not provided")
def test_login_returns_session():
    with Polestar10Client.from_env() as client:
        data = client.login()
        assert data["loginId"]
        assert data["organizationId"]


@pytest.mark.skipif(not _HAS_CREDS, reason="POLESTAR10_USER / POLESTAR10_PASS not provided")
def test_list_targets_returns_list():
    with Polestar10Client.from_env() as client:
        client.login()
        targets = client.list_targets()
        assert isinstance(targets, list)


@pytest.mark.skipif(not _HAS_CREDS, reason="POLESTAR10_USER / POLESTAR10_PASS not provided")
def test_list_groups_contains_default():
    with Polestar10Client.from_env() as client:
        client.login()
        groups = client.list_groups()
        names = [g.get("name") for g in groups]
        assert "Default" in names or "Root" in names


@pytest.mark.skipif(not _HAS_CREDS, reason="POLESTAR10_USER / POLESTAR10_PASS not provided")
@pytest.mark.xfail(
    strict=True,
    reason=(
        "write-side endpoints (add/delete) TBD — this test asserts the "
        "documented contract: every write op MUST raise FallThroughRequired "
        "until its schema is captured from a live UI session (see "
        "endpoints.md, 'TBD' sections)."
    ),
    raises=FallThroughRequired,
)
def test_add_target_roundtrip_is_not_yet_wired():
    with Polestar10Client.from_env() as client:
        client.login()
        client.add_target({"name": "nkiaai539-probe", "ip": "10.250.250.250"})
