# from playwright.async_api import Page
# from utils.parser import CONFIG

# async def section_exists(page: Page, section_id: str) -> bool:
#     return await page.locator(f"div[aria-labelledby='{section_id}-1-panel']").is_visible()

# async def click_add_button_if_needed(page: Page, section: str) -> bool:
#     if not await section_exists(page, section):
#         try:
#             await page.locator(f"div[aria-labelledby='{section}-section'] button[data-automation-id='add-button']").click()
#             print(f"➕ {section.replace('-', ' ').title()} section added.")
#             return True
#         except Exception as e:
#             print(f"⚠️ Failed to add {section} section: {e}")
#             return False
#     else:
#         print(f"🟡 {section.replace('-', ' ').title()} section already exists.")
#         return True

# async def fill_my_experience(page: Page, config: dict = CONFIG) -> bool:
#     try:
#         print("\n💼 Step 2: My Experience")

#         # Delete all existing experience blocks
#         delete_buttons = await page.get_by_role("button", name="Delete").all()
#         for btn in delete_buttons:
#             await btn.click()

#         # Work Experience
#         await click_add_button_if_needed(page, "Work-Experience")
#         work_base = "div[aria-labelledby='Work-Experience-1-panel']"
#         work = config['step2']['work_experience']

#         await page.fill("div[data-automation-id='formField-jobTitle'] input", work['job_title'])
#         await page.fill("div[data-automation-id='formField-companyName'] input", work['company'])
#         await page.fill("div[data-automation-id='formField-location'] input", work['location'])

#         try:
#             await page.check(f"{work_base} input[name='currentlyWorkHere']")
#         except:
#             print("⚠️ 'Currently work here' checkbox not found or already checked.")

#         await page.fill(f"{work_base} input[data-automation-id='dateSectionMonth-input']", work['start_month'])
#         await page.fill(f"{work_base} input[data-automation-id='dateSectionYear-input']", work['start_year'])
#         await page.locator(f"{work_base} div[data-automation-id='formField-roleDescription'] textarea").fill(work['description'])

#         # Education
#         await click_add_button_if_needed(page, "Education")
#         edu_base = "div[aria-labelledby='Education-1-panel']"
#         edu = config['step2']['education']

#         # await page.locator(f"{edu_base} [data-automation-id='formField-school']").click()
#         # await page.locator(f"{edu_base} [data-automation-id='formField-school'] input").fill(edu['school'])
#         # await page.locator(f"{edu_base} [data-automation-id='formField-school'] input").press("Enter")
        
#         await page.locator(f"{edu_base} [data-automation-id='formField-schoolName']").click()
#         await page.locator(f"{edu_base} [data-automation-id='formField-schoolName'] input").fill(edu['school'])
#         # await page.locator(f"{edu_base} [data-automation-id='formField-schoolName'] input").press("Enter")
#         # await page.get_by_role("option", name=edu['school_option']).click()
#         await page.mouse.click(0, 0)

#         await page.locator(f"{edu_base} [name='degree']").click()
#         # await page.locator(f"{edu_base} [data-automation-id='formField-degree']").click()
#         await page.wait_for_timeout(500)
#         await page.get_by_role("option", name=edu['degree']).click()
#         await page.mouse.click(0, 0)

#         await page.locator(f"{edu_base} [data-automation-id='formField-fieldOfStudy']").click()
#         await page.get_by_role("option", name=edu['field_of_study']).click()
#         await page.locator(f"{edu_base} [data-automation-id='formField-gradeAverage'] input").fill(edu['grade'])

#         # Language
#         # await click_add_button_if_needed(page, "Languages")
#         # lang = config['step2']['language']
#         # try:
#         #     await page.locator('[name="language"]').nth(0).click()
#         #     await page.get_by_role("option", name=lang['language']).click()
#         #     await page.wait_for_timeout(1000)

#         #     for skill in ["Comprehension", "Overall", "Reading", "Speaking", "Writing"]:
#         #         try:
#         #             await page.get_by_label(f"{skill} Select One Required").click()
#         #             await page.get_by_role("option", name=lang['proficiency']).click()
#         #             await page.mouse.click(0, 0)
#         #             await page.wait_for_timeout(1000)
#         #         except Exception as e:
#         #             print(f"⚠️ {skill} dropdown skipped: {e}")
#         #     print("✅ Language section filled.")
#         # except Exception as e:
#         #     print(f"⚠️ Language input failed: {e}")

#         # Resume Upload
#         print("📄 Uploading resume...")
#         try:
#             await page.locator('[data-automation-id="attachments-FileUpload"] input[type="file"]').set_input_files(config['step2']['resume_path'])
#             await page.wait_for_timeout(5000)
#             print("📌 Resume uploaded.")
#         except:
#             print("❌ Resume upload failed.")

#         # Save and Continue
#         await page.click('button[data-automation-id="pageFooterNextButton"]')
#         print("✅ Step 2 completed.")
#         return True

#     except Exception as e:
#         print(f"❌ Step 2 failed: {e}")
#         try:
#             await page.screenshot(path="step2_failed.png")
#         except Exception as ss_err:
#             print(f"⚠️ Screenshot failed: {ss_err}")
#         return False


from playwright.async_api import Page
from utils.parser import CONFIG

# ---------- helpers ----------
async def section_exists(page: Page, section_id: str, idx: int) -> bool:
    return await page.locator(
        f"div[aria-labelledby='{section_id}-{idx}-panel']"
    ).is_visible()

async def click_add(page: Page, section: str) -> None:
    await page.locator(
        f"div[aria-labelledby='{section}-section'] button[data-automation-id='add-button']"
    ).click()
    await page.wait_for_timeout(500)

# ---------- main ----------
async def fill_my_experience(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("\n💼 Step 2: My Experience")

        # -------- remove old cards --------
        for btn in await page.get_by_role("button", name="Delete").all():
            await btn.click()
            await page.wait_for_timeout(300)

        # -------- WORK EXPERIENCE --------
        for idx, we in enumerate(config["step2"]["work_experience"], start=1):
            if not await section_exists(page, "Work-Experience", idx):
                await click_add(page, "Work-Experience")

            base = f"div[aria-labelledby='Work-Experience-{idx}-panel']"
            await page.fill(f"{base} div[data-automation-id='formField-jobTitle'] input", we["job_title"])
            await page.wait_for_timeout(2000)

            await page.fill(f"{base} div[data-automation-id='formField-companyName'] input", we["company"])
            await page.wait_for_timeout(2000)

            await page.fill(f"{base} div[data-automation-id='formField-location'] input", we["location"])
            await page.wait_for_timeout(2000)

            if we.get("currently_work_here", False):
                try:
                    await page.check(f"{base} input[name='currentlyWorkHere']")
                except:
                    pass
            await page.wait_for_timeout(20000)

            await page.fill(f"{base} input[data-automation-id='dateSectionMonth-input']", we["start_month"])
            await page.fill(f"{base} input[data-automation-id='dateSectionYear-input']", we["start_year"])
            await page.wait_for_timeout(20000)

            if not we.get("currently_work_here", False):
                await page.locator(f"{base} input[data-automation-id='dateSectionMonth-input']").nth(1).fill(we.get("end_month", ""))
                await page.locator(f"{base} input[data-automation-id='dateSectionYear-input']").nth(1).fill(we.get("end_year", ""))
                await page.wait_for_timeout(20000)

            await page.locator(
                f"{base} div[data-automation-id='formField-roleDescription'] textarea"
            ).fill(we["description"])
            await page.wait_for_timeout(300)

        # -------- EDUCATION --------
        for idx, edu in enumerate(config["step2"]["education"], start=1):
            if not await section_exists(page, "Education", idx):
                await click_add(page, "Education")

            base = f"div[aria-labelledby='Education-{idx}-panel']"

            await page.locator(f"{base} [data-automation-id='formField-schoolName']").click()
            await page.locator(f"{base} [data-automation-id='formField-schoolName'] input").fill(edu["school"])
            await page.wait_for_timeout(300)

            await page.locator(f"{base} [name='degree']").click()
            await page.get_by_role("option", name=edu["degree"]).click()
            await page.wait_for_timeout(300)

            await page.locator(f"{base} [data-automation-id='formField-fieldOfStudy']").click()
            await page.get_by_role("option", name=edu["field_of_study"]).click()
            await page.wait_for_timeout(300)

            await page.locator(f"{base} [data-automation-id='formField-gradeAverage'] input").fill(edu["grade"])
            await page.wait_for_timeout(300)

        # -------- RESUME --------
        await page.locator(
            '[data-automation-id="attachments-FileUpload"] input[type="file"]'
        ).set_input_files(config["step2"]["resume_path"])
        await page.wait_for_timeout(1000)
        print("📎 Resume uploaded.")

        # -------- NEXT --------
        await page.click('button[data-automation-id="pageFooterNextButton"]')
        print("✅ Step 2 completed.")
        return True

    except Exception as err:
        print(f"❌ Step 2 failed: {err}")
        await page.screenshot(path="step2_failed.png")
        return False
