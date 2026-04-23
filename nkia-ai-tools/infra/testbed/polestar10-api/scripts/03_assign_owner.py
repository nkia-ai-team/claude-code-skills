"""Record HAR by navigating toward the owner/permission page.

Selectors for the actual 권한 부여 modal require further exploration; this
capture at least exercises the sidebar + any preset endpoints reachable
via URL. Deeper capture deferred.
"""

from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def navigate_owner(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    # Best guess paths — SPA falls back to dashboard if unknown but API calls
    # still fire, which is what we want for the HAR.
    await page.goto(_base_url() + "/account/user", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.goto(_base_url() + "/account/role", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.close()


if __name__ == "__main__":
    main_runner("03-assign-owner.har", navigate_owner)
