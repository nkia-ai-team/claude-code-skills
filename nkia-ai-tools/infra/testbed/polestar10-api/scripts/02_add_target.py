"""Record HAR for the add_target flow (관리대상 추가).

Usage:
  POLESTAR10_USER=... POLESTAR10_PASS=... python 02_add_target.py
"""

from __future__ import annotations

import os
import uuid

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def add_target(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    unique = f"nkiaai539-{uuid.uuid4().hex[:6]}"
    # Selectors refined after inspecting the 관리대상 등록 dialog.
    await page.goto(_base_url() + "/#/management/target")
    await page.wait_for_load_state("networkidle")
    try:
        await page.click('button:has-text("추가"), button:has-text("등록")', timeout=5000)
        await page.fill('input[name="name"]', unique)
        await page.fill('input[name="ip"]', os.environ.get("POLESTAR10_TEST_IP", "10.250.250.250"))
        await page.click('button:has-text("저장"), button[type="submit"]')
        await page.wait_for_load_state("networkidle")
    except Exception as exc:  # selectors drift; HAR still records what happened
        print(f"warn: add_target UI flow raised {exc!r} — inspect HAR")
    finally:
        await page.close()


if __name__ == "__main__":
    main_runner("02-add-target.har", add_target)
