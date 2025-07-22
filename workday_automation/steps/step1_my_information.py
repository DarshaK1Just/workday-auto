from playwright.async_api import Page
from utils.parser import CONFIG
async def fill_my_information(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("📄 Step 1: My Information")

        # --- How Did You Hear About Us ---
        try:
            print("📬 Selecting multiple sources in 'How Did You Hear About Us?'")
            source_container = page.locator('[data-automation-id="multiselectInputContainer"]').nth(0)
            await source_container.click()
            await page.wait_for_timeout(2000)

            options = config['step1']['hear_about_us']
            for option in options:
                try:
                    await page.get_by_role("option", name=option).click()
                    await page.wait_for_timeout(2000)
                except:
                    print(f"⚠️ Option '{option}' not found")

            await page.mouse.click(0, 0)  # Dismiss dropdown
        except Exception as e:
            print(f"⚠️ Dropdown 'How Did You Hear About Us?' failed: {e}")

        # --- Previous GM Employment ---
        try:
            await page.get_by_role("radio", name="No").click()
            await page.wait_for_timeout(2000)
        except:
            print("⚠️ Could not select 'No' for GM employment")

        # --- Legal Name ---
        try:
            await page.fill('#name--legalName--firstName', config['step1']['first_name'])
            await page.wait_for_timeout(2000)
            await page.fill('#name--legalName--lastName', config['step1']['last_name'])
            await page.wait_for_timeout(2000)
        except:
            print("⚠️ Could not fill legal name")

        # --- Address Information ---
        try:
            await page.locator('[data-automation-id="formField-addressLine1"] input').fill(config['step1']['address_line1'])
            await page.wait_for_timeout(2000)
            await page.locator('[data-automation-id="formField-city"] input').fill(config['step1']['city'])
            await page.wait_for_timeout(2000)

            await page.locator('[name="countryRegion"]').click()
            await page.get_by_role("option", name=config['step1']['state']).click()
            await page.mouse.click(0, 0)
            await page.wait_for_timeout(2000)

            await page.locator('[data-automation-id="formField-postalCode"] input').fill(config['step1']['postal_code'])
            await page.wait_for_timeout(2000)
            
            # For GAP only            
            # await page.locator('[data-automation-id="formField-regionSubdivision1"] input').fill(config['step1']['country'])
            # await page.wait_for_timeout(2000)
        except:
            print("⚠️ Could not fill address fields")

        # --- Phone Information ---
        try:
            await page.locator('[name="phoneType"]').click()
            await page.wait_for_timeout(2000)
            await page.get_by_role("option", name=config['step1']['phone_type'], exact=True).click()
            await page.mouse.click(0, 0)
            await page.wait_for_timeout(2000)
            await page.locator('[name="phoneNumber"]').fill(config['step1']['phone_number'])
        except:
            print("⚠️ Could not fill phone info")

        # --- Save and Continue ---
        try:
            await page.click('button[data-automation-id="pageFooterNextButton"]')
            print("✅ Clicked 'Save and Continue'.")
            print("✅ Step 1 completed.")
            return True
        except:
            print("❌ Could not click Save and Continue.")
            return False

    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        try:
            await page.screenshot(path="step1_failed.png")
        except Exception as ss_err:
            print(f"⚠️ Screenshot failed: {ss_err}")
        return False
