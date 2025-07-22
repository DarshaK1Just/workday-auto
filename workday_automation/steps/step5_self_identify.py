from playwright.async_api import Page
from utils.parser import CONFIG

async def fill_self_identify(page: Page, config: dict = CONFIG) -> bool:
    """
    Step 5 – Self‑Identify page.
    Pulls data from CONFIG["step5"].
    """
    try:
        data = config.get("step5", {})
        print("🧬 Step 5: Self‑Identify")

        # ---------- Name ----------
        if "name" in data:
            await page.locator('[name="name"]').fill(data["name"])
            print(f"👤 Name filled: {data['name']}")
        else:
            raise ValueError("Missing 'name' in step5 config")

        # ---------- “Signed on” date ----------
        if "date" not in data:
            raise ValueError("Missing 'date' in step5 config")

        date_vals = data["date"]
        DATE_ID = "selfIdentifiedDisabilityData--dateSignedOn"

        await page.fill(f"#{DATE_ID}-dateSectionMonth-input", date_vals["month"])
        await page.fill(f"#{DATE_ID}-dateSectionDay-input", date_vals["day"])
        await page.fill(f"#{DATE_ID}-dateSectionYear-input", date_vals["year"])
        print(f"📅 Date selected: {date_vals['month']}/{date_vals['day']}/{date_vals['year']}")

        # ---------- Disability status ----------
        if "disability_status" in data:
            status_lbl = data["disability_status"]
            await page.get_by_label(status_lbl, exact=True).check()
            print(f"♿ Disability status selected: {status_lbl}")
        else:
            raise ValueError("Missing 'disability_status' in step5 config")

        # ---------- Continue ----------
        await page.click('button[data-automation-id="pageFooterNextButton"]')
        await page.wait_for_timeout(1000)
        print("✅ Step 5 completed.")
        return True

    except Exception as err:
        print(f"❌ Step 5 failed: {err}")
        try:
            await page.screenshot(path="step5_self_identify_error.png")
        except:
            pass
        return False
