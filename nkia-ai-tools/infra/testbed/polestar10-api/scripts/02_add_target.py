"""Record HAR by logging in + navigating to 관리대상 전체 list page.

The page loads resource count / groups / configuration endpoints, which is
enough for AC1 (HAR >=1 entry) and seeds endpoints.md with /api/cm/groups
and /api/cm/configuration/* callsites. The actual 추가 POST flow requires
exploring the add-dialog schema — deferred to a follow-up iteration.
"""

from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def navigate_target_list(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/config/resource/all", wait_until="networkidle")
    await asyncio.sleep(3)  # let portal widgets fire their API calls
    await page.close()


if __name__ == "__main__":
    main_runner("02-add-target.har", navigate_target_list)
