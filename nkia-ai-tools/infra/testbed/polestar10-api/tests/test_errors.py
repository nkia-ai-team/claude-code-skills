"""Env-independent unit tests for errors + client scaffold.

These run without POLESTAR10_USER/POLESTAR10_PASS so the default pytest
invocation always exercises the fall-through contract.
"""

from __future__ import annotations

import pytest

from polestar10_client import FallThroughRequired, PolestarApiError
from polestar10_client.client import ClientConfig, Polestar10Client


def _dummy_config() -> ClientConfig:
    return ClientConfig(
        base_url="https://invalid.local",
        username="u",
        password="p",
        verify_ssl=False,
    )


def test_fall_through_is_api_error_subclass():
    err = FallThroughRequired("x", "hint")
    assert isinstance(err, PolestarApiError)
    assert err.operation == "x"
    assert err.ui_hint == "hint"


@pytest.mark.parametrize(
    "method,kwargs",
    [
        # Write-side endpoints whose schema is TBD — these MUST raise
        # FallThroughRequired without any network I/O (pure contract).
        # login + list_targets + list_groups are wired (see test_roundtrip.py).
        ("add_target", {"payload": {"name": "x"}}),
        ("delete_target", {"target_id": "id"}),
        ("assign_owner", {"target_id": "id", "user_id": "u"}),
        ("register_nms", {"payload": {"name": "n"}}),
        ("register_dpm", {"payload": {"name": "d"}}),
        ("add_alert_policy", {"payload": {"metric": "cpu"}}),
    ],
)
def test_unmapped_write_ops_raise_fall_through(method, kwargs):
    with Polestar10Client(_dummy_config()) as client:
        with pytest.raises(FallThroughRequired) as exc_info:
            getattr(client, method)(**kwargs)
        assert exc_info.value.operation
        assert exc_info.value.ui_hint
