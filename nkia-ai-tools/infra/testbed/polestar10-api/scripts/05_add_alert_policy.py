"""Record HAR for the add_alert_policy flow (개별 알람 정책 등록).

Placeholder selectors; refine after first HAR pass.
"""

from __future__ import annotations

from playwright.async_api import BrowserContext

from record_har import _base_url, login_via_ui, main_runner


async def add_alert_policy(context: BrowserContext) -> None:
    await login_via_ui(context)
    page = await context.new_page()
    await page.goto(_base_url() + "/#/alert/policy")
    await page.wait_for_load_state("networkidle")
    try:
        await page.click('button:has-text("정책 추가"), button:has-text("+")', timeout=5000)
        await page.wait_for_load_state("networkidle")
    except Exception as exc:
        print(f"warn: add_alert_policy UI flow raised {exc!r} — inspect HAR")
    finally:
        await page.close()


if __name__ == "__main__":
    main_runner("05-add-alert-policy.har", add_alert_policy)
