from playwright.async_api import Page
from utils.parser import CONFIG

async def submit_review(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("📝 Step 6: Final Review & Submit")

        # Optional config: allow disabling real submission (e.g. for test mode)
        submission_enabled = config.get("step6", {}).get("submit", True)
        if not submission_enabled:
            print("⚠️ Submission disabled in config (step6.submit = false). Skipping submit.")
            await page.wait_for_timeout(1000)
            return True

        # Scroll to the bottom to load all dynamic content
        await page.mouse.wheel(0, 5000)
        print("📜 Scrolled to bottom.")
        await page.wait_for_timeout(2000)

        # Try locating and clicking the Submit button
        try:
            print("🔍 Looking for the Submit button...")
            submit_button = page.locator('button[data-automation-id="pageFooterNextButton"]')

            await submit_button.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)

            await submit_button.wait_for(state="visible", timeout=5000)
            print("✅ Submit button is visible. Clicking in 1s...")
            await page.wait_for_timeout(1000)

            await submit_button.click()
            await page.wait_for_timeout(3000)

            print("🎯 Submit button clicked.")
            print("✅ Application submitted successfully!")
            return True

        except Exception as e:
            print(f"❌ Submit failed: {e}")
            await page.screenshot(path="submit_failed.png")
            return False

    except Exception as e:
        print(f"❌ Review/Submit step failed: {e}")
        try:
            await page.screenshot(path="step6_submit_error.png")
        except Exception as ss_err:
            print(f"⚠️ Screenshot also failed: {ss_err}")
        return False
