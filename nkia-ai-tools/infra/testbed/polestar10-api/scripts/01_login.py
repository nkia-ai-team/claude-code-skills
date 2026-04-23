"""Record HAR for the login flow.

Usage:
  POLESTAR10_USER=... POLESTAR10_PASS=... python 01_login.py
"""

from __future__ import annotations

from playwright.async_api import BrowserContext

from record_har import login_via_ui, main_runner


async def login_only(context: BrowserContext) -> None:
    await login_via_ui(context)


if __name__ == "__main__":
    main_runner("01-login.har", login_only)
