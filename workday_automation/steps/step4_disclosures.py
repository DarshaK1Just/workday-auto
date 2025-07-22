# from playwright.async_api import Page
# from utils.parser import CONFIG

# async def fill_voluntary_disclosures(page: Page, config: dict = CONFIG) -> bool:
#     try:
#         print("🛂 Step 4: Voluntary Disclosures")

#         disclosure = config.get('step4', {})

#         # --- Nationality ---
#         try:
#             print("🌍 Selecting nationality...")
#             await page.get_by_label("Primary Nationality Select One Required").click()
#             await page.get_by_role("option", name=disclosure["nationality"], exact=True).click()
#             await page.wait_for_timeout(1000)
#             print(f"✅ Nationality: {disclosure['nationality']}")
#         except Exception as e:
#             print(f"⚠️ Nationality selection failed: {e}")

#         # --- Gender ---
#         try:
#             print("🚻 Selecting gender...")
            
#             # await page.get_by_label("Gender Select One Required").click()
#             await page.locator('[name="gender"]').click()
            
#             await page.get_by_role("option", name=disclosure["gender"], exact=True).click()
#             await page.wait_for_timeout(1000)
#             print(f"✅ Gender: {disclosure['gender']}")
#         except Exception as e:
#             print(f"⚠️ Gender selection failed: {e}")

#         # --- Consent Checkbox ---
#         if disclosure.get("consent", False):
#             try:
#                 print("☑️ Checking consent...")
#                 consent_checkbox = page.locator('input[name="acceptTermsAndAgreements"]')
#                 if not await consent_checkbox.is_checked():
#                     await consent_checkbox.check()
#                 print("✅ Consent checkbox checked.")
#             except Exception as e:
#                 print(f"⚠️ Consent checkbox fallback: {e}")
#                 try:
#                     await page.locator('input[type="checkbox"]').first.check()
#                 except:
#                     print("❌ Could not find any checkbox to check.")

#         # --- Save and Continue ---
#         try:
#             await page.click('button[data-automation-id="pageFooterNextButton"]')
#             print("✅ Clicked 'Save and Continue'.")
#             print("✅ Step 4 completed.")
#             return True
#         except Exception as e:
#             print(f"❌ Could not click Save and Continue: {e}")
#             return False

#     except Exception as e:
#         print(f"❌ Step 4 failed: {e}")
#         try:
#             await page.screenshot(path="step4_failed.png")
#         except Exception as ss_err:
#             print(f"⚠️ Screenshot failed: {ss_err}")
#         return False



from playwright.async_api import Page
from utils.parser import CONFIG


async def _choose_from_dropdown(dropdown, option_text: str) -> None:
    """Open a WD dropdown and pick an option (exact match)."""
    await dropdown.page.wait_for_timeout(500) 
    await dropdown.click()
    await dropdown.page.wait_for_timeout(500) 
    await dropdown.page.get_by_role("option", name=option_text, exact=True).click()


async def fill_voluntary_disclosures(page: Page, config: dict = CONFIG) -> bool:
    """
    Step 4: Voluntary Disclosures.
    Supports Ethnicity, Gender, Protected‑Veteran and Terms checkbox.
    All answers must live in CONFIG['step4'].
    """
    try:
        print("🛂  Step 4 – Voluntary Disclosures")

        answers = config.get("step4", {})
        if not answers:
            print("⚠️  No step4 config; skipping screen.")
            await page.click('button[data-automation-id="pageFooterNextButton"]')
            return True

        # ---------- Ethnicity ----------
        try:
            print("🌈  Selecting ethnicity …")
            eth_dropdown = page.locator(
                '[name="ethnicity"]'
            )
            await _choose_from_dropdown(eth_dropdown, answers["ethnicity"])
            print(f"   ✔  Ethnicity → {answers['ethnicity']}")
        except Exception as e:
            print(f"   ⚠️  Ethnicity selection issue: {e}")

        # ---------- Gender ----------
        try:
            print("🚻  Selecting gender …")
            gender_dropdown = page.locator(
                '[name="gender"]'
            )
            await _choose_from_dropdown(gender_dropdown, answers["gender"])
            print(f"   ✔  Gender → {answers['gender']}")
        except Exception as e:
            print(f"   ⚠️  Gender selection issue: {e}")

        # ---------- Protected‑Veteran ----------
        try:
            print("🎖  Selecting protected‑veteran status …")
            vet_dropdown = page.locator(
                '[name="veteranStatus"]'
            )
            await _choose_from_dropdown(vet_dropdown, answers["veteran_status"])
            print(f"   ✔  Veteran → {answers['veteran_status']}")
        except Exception as e:
            print(f"   ⚠️  Veteran selection issue: {e}")

        # ---------- Consent checkbox ----------
        if answers.get("consent", False):
            try:
                await page.wait_for_timeout(1000)
                consent = page.locator(
                    'input[data-automation-id="createAccountCheckbox"], '
                    'input[name="acceptTermsAndAgreements"]'
                ).first
                if not await consent.is_checked():
                    await consent.check()
                print("☑️  Terms & Conditions accepted.")
            except Exception as e:
                print(f"   ⚠️  Could not tick consent box: {e}")

        # ---------- Next ----------
        await page.click('button[data-automation-id="pageFooterNextButton"]')
        print("✅  Step 4 complete.")
        return True

    except Exception as top_err:
        print(f"❌  Step 4 FAILED: {top_err}")
        try:
            await page.screenshot(path="step4_failed.png")
        except Exception:
            pass
        return False
