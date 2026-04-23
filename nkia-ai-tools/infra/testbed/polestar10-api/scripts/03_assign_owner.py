"""Record HAR for the assign_owner flow (담당자 권한 부여).

Placeholder selectors; refine after first HAR pass.
"""

from __future__ import annotations

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def assign_owner(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/#/management/owner")
    await page.wait_for_load_state("networkidle")
    try:
        await page.click('button:has-text("권한 부여"), button:has-text("할당")', timeout=5000)
        await page.wait_for_load_state("networkidle")
    except Exception as exc:
        print(f"warn: assign_owner UI flow raised {exc!r} — inspect HAR")
    finally:
        await page.close()


if __name__ == "__main__":
    main_runner("03-assign-owner.har", assign_owner)
