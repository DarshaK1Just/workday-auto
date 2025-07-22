from playwright.async_api import Page, TimeoutError
from utils.parser import CONFIG 

async def login_to_workday(page: Page, config: dict = CONFIG) -> bool:
    print("🔐 Opening job URL …")
    try:
        await page.goto(config["job_url"], timeout=30000)
    except Exception as e:
        print(f"❌ Cannot load job page: {e}")
        return False

    try:
        print("➡️ Clicking top‑level Sign In …")
        await page.get_by_role("button", name="Sign In").click(timeout=5_000)
        await page.wait_for_timeout(1000)
    except TimeoutError:
        print("❌ Top‑level Sign In button not found.")
        return False
    
    if await page.get_by_role("button", name="Sign In").is_visible():
        print("🔄 Account created – returning to Sign In …")
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_timeout(1000)
        try:
            print("🔑 Filling login form …")
            await page.get_by_label("Email Address", exact=True).fill(config["email"])
            await page.wait_for_timeout(1000)
            await page.get_by_label("Password", exact=True).fill(config["password"])
            await page.wait_for_timeout(1000)
            await page.get_by_role("button", name="Sign In", exact=True).click()
            await page.wait_for_timeout(3000)

            # quick sanity‑check
            if await page.locator("text=Invalid").first.is_visible():
                print("❌ Login rejected – invalid credentials.")
                await page.screenshot(path="login_invalid.png")
                return False

            print("✅ Logged in.")
        except Exception as e:
            print(f"❌ Sign‑in step failed: {e}")
            await page.screenshot(path="login_failed.png")
            return False

    # ---------- create account if needed ----------
    # try:
    #     if await page.get_by_role("button", name="Create Account").is_visible():
    #         print("🆕 ‘Create Account’ detected – creating new account …")
    #         await page.get_by_role("button", name="Create Account").click()
    #         await page.wait_for_timeout(1000)

    #         await page.get_by_label("Email Address", exact=True).fill(config["email"])
    #         await page.wait_for_timeout(1000)
    #         await page.get_by_label("Password", exact=True).fill(config["password"])
    #         await page.wait_for_timeout(1000)
    #         await page.get_by_label("Verify New Password", exact=True).fill(config["password"])
    #         await page.wait_for_timeout(1000)

    #         # Check terms checkbox (if present)
    #         try:
    #             checkbox = page.locator('[data-automation-id="createAccountCheckbox"]')
    #             if not await checkbox.is_checked():
    #                 await checkbox.check()
    #             print("✅ Checked 'I Agree' checkbox.")
    #         except Exception as e:
    #             print(f"⚠️ Could not check 'I Agree' checkbox: {e}")

    #         await page.get_by_role("button", name="Create Account", exact=True).click()
    #         print("⏳ Waiting for account creation …")
    #         await page.wait_for_timeout(3000)

    #         # After creation, Workday normally returns to a “Already have an account? Sign In” link.
    #         if await page.get_by_role("button", name="Sign In").is_visible():
    #             print("🔄 Account created – returning to Sign In …")
    #             await page.get_by_role("button", name="Sign In").click()
    #             await page.wait_for_timeout(1000)
    #             # ---------- normal sign‑in ----------
    #             try:
    #                 print("🔑 Filling login form …")
    #                 await page.get_by_label("Email Address", exact=True).fill(config["email"])
    #                 await page.wait_for_timeout(1000)
    #                 await page.get_by_label("Password", exact=True).fill(config["password"])
    #                 await page.wait_for_timeout(1000)
    #                 await page.get_by_role("button", name="Sign In", exact=True).click()
    #                 await page.wait_for_timeout(3000)

    #                 # quick sanity‑check
    #                 if await page.locator("text=Invalid").first.is_visible():
    #                     print("❌ Login rejected – invalid credentials.")
    #                     await page.screenshot(path="login_invalid.png")
    #                     return False

    #                 print("✅ Logged in.")
    #             except Exception as e:
    #                 print(f"❌ Sign‑in step failed: {e}")
    #                 await page.screenshot(path="login_failed.png")
    #                 return False
    # except Exception as e:
    #     print(f"❌ Account‑creation step failed: {e}")
    #     await page.screenshot(path="create_account_failed.png")
    #     return False

    try:
        print("➡️ Clicking ‘Apply’ …")
        await page.get_by_role("button", name="Apply").click(timeout=5000)
        await page.wait_for_timeout(1000)

        print("📝 Clicking ‘Apply Manually’ …")
        await page.get_by_role("button", name="Apply Manually").click(timeout=5000)
        await page.wait_for_timeout(1500)
    except TimeoutError as e:
        print(f"⚠️ Apply buttons missing: {e}")
        await page.screenshot(path="apply_click_error.png")
        return False

    return True
