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
from utils.extractor import extract_all_form_fields
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Helper to fill based on type using locator
async def fill_input_field(page: Page, field: dict, value: str | bool | list):
    field_id = field['id_of_input_component']
    
    try:
        if field["type_of_input"] == "text":
            locator = page.locator(f"[id='{field_id}']")
            await locator.click()
            await locator.fill(str(value))
            
        elif field["type_of_input"] == "textarea":
            locator = page.locator(f"[id='{field_id}']")
            await locator.click()
            await locator.fill(str(value))
            
        elif field["type_of_input"] == "checkbox":
            locator = page.locator(f"[id='{field_id}']")
            if str(value).lower() in ["yes", "true", "1"]:
                await locator.check()
            else:
                await locator.uncheck()
                
        elif field["type_of_input"] == "select" or field["type_of_input"] == "dropdown":
            # Handle dropdown buttons (like degree, language dropdowns)
            button_locator = page.locator(f"button[id='{field_id}']")
            await button_locator.click()
            await page.wait_for_timeout(500)
            try:
                await page.get_by_role("option", name=str(value)).click()
            except:
                # Try alternative selection method
                await page.locator(f"[role='option']:has-text('{value}')").click()
            await page.mouse.click(0, 0)  # Click away to close dropdown
            
        elif field["type_of_input"] == "multi-select" or "multiSelectContainer" in field.get("html_content", ""):
            # Handle multi-select fields like skills, school, field of study
            input_locator = page.locator(f"input[id='{field_id}']")
            await input_locator.click()
            
            if isinstance(value, list):
                for item in value:
                    await input_locator.fill(str(item))
                    await page.wait_for_timeout(1000)
                    try:
                        # Try to select from dropdown if available
                        await page.get_by_role("option", name=str(item)).click()
                    except:
                        # If no dropdown, press Enter to add the item
                        await page.keyboard.press("Enter")
            else:
                await input_locator.fill(str(value))
                await page.wait_for_timeout(1000)
                try:
                    await page.get_by_role("option", name=str(value)).click()
                except:
                    await page.keyboard.press("Enter")
            
            await page.mouse.click(0, 0)  # Click away
            
        elif field["type_of_input"] == "date":
            # Extract month/year/day from the value (e.g., "06/2023" or "06/15/2023")
            date_parts = str(value).split("/")
            month = date_parts[0] if len(date_parts) >= 2 else None
            year = date_parts[1] if len(date_parts) >= 2 else None
            day = date_parts[1] if len(date_parts) == 3 else None

            try:
                # Fill Month
                await page.fill(f"input[id='{field_id}-dateSectionMonth-input']", month)

                # Fill Year
                await page.fill(f"input[id='{field_id}-dateSectionYear-input']", year)

                # Optional: Fill Day if present
                if len(date_parts) == 3:
                    await page.fill(f"input[id='{field_id}-dateSectionDay-input']", day)
            except Exception as e:
                logging.warning(f"⚠️ Date input failed for field '{field['label']}' with id '{field_id}': {e}")
 
        elif field["type_of_input"] == "multiple-file" or "FileUpload" in field.get("html_content", ""):
            # Handle file uploads
            try:
                # Try different file input selectors
                file_selectors = [
                    f'[data-automation-id="{field_id}"] input[type="file"]',
                    f'input[data-automation-id="file-upload-input-ref"]',
                    f'[id="{field_id}"] input[type="file"]'
                ]
                
                for selector in file_selectors:
                    file_input = page.locator(selector)
                    if await file_input.is_visible():
                        await file_input.set_input_files(value)
                        break
                else:
                    # Try clicking the select files button first
                    select_button = page.locator(f'button[data-automation-id="select-files"]')
                    if await select_button.is_visible():
                        await select_button.click()
                        await page.wait_for_timeout(500)
                        file_input = page.locator('input[type="file"]').last
                        await file_input.set_input_files(value)
            except Exception as e:
                logging.warning(f"File upload failed for {field_id}: {e}")
                
        else:
            logging.warning(f"Unknown input type: {field['type_of_input']} for {field['label']}")
            
    except Exception as e:
        logging.warning(f"Failed to fill field '{field['label']}' (ID: {field_id}): {e}")


async def fill_my_experience(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("\n💼 Step 2: My Experience")
        
        # Extract all form fields only once
        form_fields = await extract_all_form_fields(page)

        # --- WORK EXPERIENCE ---
        work_experiences = config["step2"].get("work_experience", [])
        for i, we in enumerate(work_experiences):
            print(f"📝 Filling work experience {i + 1}")
            for field in form_fields:
                field_id = field.get("id_of_input_component", "")
                if field["section_name"] == "Work Experience" and f"workExperience-" in field_id:
                    if "jobTitle" in field_id:
                        await fill_input_field(page, field, we["job_title"])
                    elif "companyName" in field_id:
                        await fill_input_field(page, field, we["company"])
                    elif "location" in field_id:
                        await fill_input_field(page, field, we["location"])
                    elif "currentlyWorkHere" in field_id:
                        await fill_input_field(page, field, we.get("currently_work_here", False))
                    elif "startDate" in field_id:
                        await fill_input_field(page, field, f"{we['start_month']}/{we['start_year']}")
                    elif "endDate" in field_id:
                        if not we.get("currently_work_here", False):
                            await fill_input_field(page, field, f"{we['end_month']}/{we['end_year']}")
                    elif "roleDescription" in field_id:
                        await fill_input_field(page, field, we["description"])
        await page.wait_for_timeout(2000)

        # --- EDUCATION ---
        education_entries = config["step2"].get("education", [])

        for i, edu in enumerate(education_entries):
            print(f"🎓 Filling education {i + 1}")
            
            for field in form_fields:
                field_id = field.get("id_of_input_component")
                section = field.get("section_name", "")
                
                if not field_id or section != "Education" or not field_id.startswith("education-"):
                    continue

                if "school" in field_id:
                    school_value = edu.get("school_option", edu.get("school", ""))
                    await fill_multiselect_field(page, field, school_value)

                elif "degree" in field_id:
                    await fill_input_field(page, field, edu.get("degree", ""))

                elif "fieldOfStudy" in field_id:
                    await fill_input_field(page, field, edu.get("field_of_study", ""))

                elif "gradeAverage" in field_id:
                    await fill_input_field(page, field, edu.get("grade", ""))

                elif "firstYearAttended" in field_id:
                    await fill_input_field(page, field, edu.get("start_year", "2020"))

                elif "lastYearAttended" in field_id:
                    await fill_input_field(page, field, edu.get("end_year", "2024"))

        await page.wait_for_timeout(1000)


        # --- CERTIFICATIONS ---
        certs = config["step2"].get("certifications", [])
        for i, cert in enumerate(certs):
            print(f"🏆 Filling certification {i + 1}")
            for field in form_fields:
                field_id = field.get("id_of_input_component", "")
                if field["section_name"] == "Certifications" and f"certification-" in field_id:
                    if "certification" in field_id and "certificationNumber" not in field_id:
                        await fill_input_field(page, field, cert.get("name", cert.get("certification", "")))
                    elif "certificationNumber" in field_id:
                        await fill_input_field(page, field, cert.get("number", cert.get("certificationNumber", "")))
                    elif "issuedDate" in field_id:
                        issued_date = cert.get("issued_date", cert.get("issuedDate", "01/01/2023"))
                        await fill_input_field(page, field, issued_date)
                    elif "expirationDate" in field_id:
                        exp_date = cert.get("expiration_date", cert.get("expirationDate", "01/01/2025"))
                        await fill_input_field(page, field, exp_date)
                    elif "attachments" in field_id:
                        cert_file = cert.get("file_path", cert.get("attachments"))
                        if cert_file:
                            await fill_input_field(page, field, cert_file)
        await page.wait_for_timeout(2000)

        # --- LANGUAGES ---
        langs = config["step2"].get("languages", [])
        for i, lang in enumerate(langs):
            print(f"🌐 Filling language {i + 1}")
            for field in form_fields:
                field_id = field.get("id_of_input_component", "")
                if field["section_name"] == "Languages" and f"language-" in field_id:
                    if field_id.endswith("--language"):
                        await fill_input_field(page, field, lang["language"])
                    elif "native" in field_id:
                        await fill_input_field(page, field, lang.get("native", False))
                    elif any(skill in field["label"].lower() for skill in ["comprehension", "overall", "reading", "speaking", "writing"]):
                        await fill_input_field(page, field, lang["proficiency"])
        await page.wait_for_timeout(2000)

        # --- SKILLS ---
        print("🔧 Filling skills...")
        skills = config["step2"].get("skills", [])
        for field in form_fields:
            field_id = field.get("id_of_input_component", "")
            if field["section_name"] == "Skills" or "skills" in field_id:
                await fill_input_field(page, field, skills)
        await page.wait_for_timeout(2000)

        # --- RESUME UPLOAD ---
        print("📄 Uploading resume...")
        resume_uploaded = False
        for field in form_fields:
            field_id = field.get("id_of_input_component", "")
            if ("attachments" in field_id or "FileUpload" in field.get("html_content", "")) and not resume_uploaded:
                resume_path = config["step2"].get("resume_path")
                if resume_path:
                    try:
                        await fill_input_field(page, field, resume_path)
                        print("📌 Resume uploaded.")
                        resume_uploaded = True
                        await page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"❌ Resume upload failed: {e}")
        await page.wait_for_timeout(2000)

        # --- WEBSITES ---
        print("🌐 Filling websites...")
        websites = config["step2"].get("websites", [])
        for i, website in enumerate(websites):
            for field in form_fields:
                field_id = field.get("id_of_input_component", "")
                if field["section_name"] == "Websites" and f"webAddress-" in field_id:
                    if "url" in field_id:
                        await fill_input_field(page, field, website["url"])
        await page.wait_for_timeout(2000)

        # --- LINKEDIN ---
        print("💼 Filling LinkedIn...")
        linkedin_url = config["step2"].get("linkedin", "")
        if linkedin_url:
            for field in form_fields:
                if "linkedin" in field["label"].lower() or "linkedin" in field.get("id_of_input_component", ""):
                    await fill_input_field(page, field, linkedin_url)
        await page.wait_for_timeout(2000)

        # --- CLICK NEXT ---
        print("➡️ Clicking Next button...")
        next_button = page.locator('button[data-automation-id="pageFooterNextButton"]')
        await next_button.click()
        print("✅ Step 2 completed.")


    except Exception as err:
        print(f"❌ Step 2 failed: {err}")
        try:
            await page.screenshot(path="step2_failed.png")
        except Exception as ss_err:
            print(f"⚠️ Screenshot failed: {ss_err}")
        return False
