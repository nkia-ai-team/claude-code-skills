"""Record HAR by navigating toward 알람 정책 설정."""

from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def navigate_alert_policy(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/alarm/policy", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.goto(_base_url() + "/alert/policy", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.close()


if __name__ == "__main__":
    main_runner("05-add-alert-policy.har", navigate_alert_policy)
