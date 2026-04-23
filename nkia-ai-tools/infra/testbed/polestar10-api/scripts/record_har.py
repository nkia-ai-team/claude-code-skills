"""Shared HAR recording harness for polestar10 web operation scripts.

Each script under scripts/0N_<operation>.py imports `record_operation` and
passes an async callable that performs the operation via Playwright. The
harness spins up a BrowserContext with `record_har_path` set and flushes
the HAR when the callable returns.

Requires env: POLESTAR10_BASE_URL (default https://192.168.230.104),
POLESTAR10_USER, POLESTAR10_PASS.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Awaitable, Callable

from playwright.async_api import BrowserContext, async_playwright

HAR_DIR = Path(__file__).resolve().parent.parent / "har-captures"

OperationFn = Callable[[BrowserContext], Awaitable[None]]


def _base_url() -> str:
    return os.environ.get("POLESTAR10_BASE_URL", "https://192.168.230.104")


def _credentials() -> tuple[str, str]:
    try:
        return os.environ["POLESTAR10_USER"], os.environ["POLESTAR10_PASS"]
    except KeyError as e:
        sys.stderr.write(
            f"error: missing env var {e.args[0]} — export POLESTAR10_USER/POLESTAR10_PASS\n"
        )
        raise SystemExit(2) from e


async def record_operation(har_name: str, operation: OperationFn, *, headless: bool = True) -> Path:
    """Run `operation(context)` with HAR recording enabled.

    Returns the written HAR path.
    """
    HAR_DIR.mkdir(parents=True, exist_ok=True)
    har_path = HAR_DIR / har_name

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            ignore_https_errors=True,
            record_har_path=str(har_path),
            record_har_content="embed",
        )
        try:
            await operation(context)
        finally:
            await context.close()
            await browser.close()

    return har_path


async def login_via_ui(context: BrowserContext) -> None:
    """Perform a UI login so the HAR captures the auth flow.

    Kept here because every operation script needs it before the
    authenticated request. Selectors are placeholders refined after
    inspecting the /login page DOM; see 01_login.py for the canonical flow.
    """
    user, password = _credentials()
    page = await context.new_page()
    await page.goto(_base_url() + "/login", wait_until="networkidle")
    await page.fill('input[name="username"], input[type="text"]', user)
    await page.fill('input[name="password"], input[type="password"]', password)
    await page.click('button[type="submit"], button:has-text("로그인")')
    await page.wait_for_load_state("networkidle")
    await page.close()


def main_runner(har_name: str, operation: OperationFn) -> None:
    """Sync wrapper for script entry points."""
    headless = os.environ.get("POLESTAR10_HEADED", "").lower() not in ("1", "true", "yes")
    har_path = asyncio.run(record_operation(har_name, operation, headless=headless))
    print(f"HAR written: {har_path}")
