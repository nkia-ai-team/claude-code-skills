"""Integration test: login -> add_target -> list_targets -> delete_target.

Runs against a live polestar10 instance. Expects env:
  POLESTAR10_BASE_URL  (default https://192.168.230.104)
  POLESTAR10_USER
  POLESTAR10_PASS

Skipped when env is missing so CI without a live instance stays green.
"""

from __future__ import annotations

import os
import uuid

import pytest

from polestar10_client import FallThroughRequired, Polestar10Client

pytestmark = pytest.mark.skipif(
    not (os.environ.get("POLESTAR10_USER") and os.environ.get("POLESTAR10_PASS")),
    reason="POLESTAR10_USER / POLESTAR10_PASS not provided",
)


def test_add_list_delete_roundtrip():
    with Polestar10Client.from_env() as client:
        client.login()

        unique_name = f"nkiaai539-{uuid.uuid4().hex[:8]}"
        created = client.add_target({"name": unique_name, "ip": "10.250.250.250"})
        created_id = created["id"]

        try:
            targets = client.list_targets()
            assert any(t["id"] == created_id for t in targets), "created target not in list"
        finally:
            client.delete_target(created_id)

        targets_after = client.list_targets()
        assert not any(t["id"] == created_id for t in targets_after), "target not deleted"


def test_fall_through_is_raised_for_unmapped_operation():
    """Until AC1/AC2 wire the real endpoints, every operation must raise
    FallThroughRequired so an orchestrator caller can still integrate."""
    with Polestar10Client.from_env() as client:
        with pytest.raises(FallThroughRequired) as exc_info:
            client.register_nms({"name": "x", "ip": "1.1.1.1"})
        assert exc_info.value.operation == "register_nms"
        assert exc_info.value.ui_hint
