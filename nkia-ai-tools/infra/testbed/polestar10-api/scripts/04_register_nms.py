"""Record HAR for the register_nms flow (NMS 네트워크 등록).

Placeholder selectors; refine after first HAR pass.
"""

from __future__ import annotations

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def register_nms(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/#/sms/network/nms")
    await page.wait_for_load_state("networkidle")
    try:
        await page.click('button:has-text("등록"), button:has-text("+")', timeout=5000)
        await page.wait_for_load_state("networkidle")
    except Exception as exc:
        print(f"warn: register_nms UI flow raised {exc!r} — inspect HAR")
    finally:
        await page.close()


if __name__ == "__main__":
    main_runner("04-register-nms.har", register_nms)
