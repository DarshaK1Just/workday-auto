from playwright.async_api import Page
from utils.parser import CONFIG

async def fill_application_questions(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("📝 Step 3: Application Questions")

        # Work Authorization
        try:
            print("🔘 Selecting Work Authorization...")
            auth_value = config['step3']['authorization']
            
            auth_dropdown = page.locator('[aria-label=" Select One"]').nth(0)
            # auth_dropdown = page.locator('[aria-label=" Select One Required"]').nth(0)
            
            await auth_dropdown.click()
            await page.get_by_role("option", name=auth_value).click()
            await page.wait_for_timeout(1000)
            print(f"✅ Work Authorization set to '{auth_value}'.")
        except Exception as e:
            print(f"✔️ Work Authorization selection failed or already selected: {e}")

        # Visa Sponsorship
        try:
            print("🔘 Selecting Visa Sponsorship...")
            sponsor_value = config['step3']['sponsorship']
            
            sponsor_dropdown = page.locator('[aria-label=" Select One"]').nth(0)
            # sponsor_dropdown = page.locator('[aria-label=" Select One Required"]').nth(0)
            
            await sponsor_dropdown.click()
            await page.get_by_role("option", name=sponsor_value).click()
            await page.wait_for_timeout(1000)
            print(f"✅ Visa Sponsorship set to '{sponsor_value}'.")
        except Exception as e:
            print(f"✔️ Visa Sponsorship selection failed or already selected: {e}")

        # Save and Continue
        try:
            await page.click('button[data-automation-id="pageFooterNextButton"]')
            print("✅ Clicked 'Save and Continue'.")
            print("✅ Step 3 completed.")
            return True
        except Exception as e:
            print(f"❌ Could not click Save and Continue: {e}")
            return False

    except Exception as e:
        print(f"❌ Step 3 failed: {e}")
        try:
            await page.screenshot(path="step3_failed.png")
        except Exception as ss_err:
            print(f"⚠️ Screenshot failed: {ss_err}")
        return False
