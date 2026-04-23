"""Record HAR by navigating toward NMS network registration."""

from __future__ import annotations

import asyncio

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def navigate_nms(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/config/resource/nms", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.goto(_base_url() + "/nms", wait_until="networkidle")
    await asyncio.sleep(2)
    await page.close()


if __name__ == "__main__":
    main_runner("04-register-nms.har", navigate_nms)
