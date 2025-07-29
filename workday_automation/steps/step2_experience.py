
from playwright.async_api import Page
from utils.parser import CONFIG
from utils.extractor import extract_all_form_fields
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Helper to fill based on type
async def fill_input_field(page: Page, field: dict, value: str | bool | list):
    selector = f"[id='{field['id_of_input_component']}']"

    try:
        if field["type_of_input"] == "text":
            await page.fill(selector, value)
        elif field["type_of_input"] == "textarea":
            await page.locator(selector).fill(value)
        elif field["type_of_input"] == "checkbox":
            if str(value).lower() in ["yes", "true", "1"]:
                await page.check(selector)
            else:
                await page.uncheck(selector)
        elif field["type_of_input"] == "date":
            await page.fill(selector, value)
        elif field["type_of_input"] == "multi-select":
            # Skipped: handled separately
            pass
        elif field["type_of_input"] == "multiple-file":
            await page.set_input_files(selector, value)
        else:
            logging.warning(f"Unknown input type: {field['type_of_input']} for {field['label']}")
    except Exception as e:
        logging.warning(f"Failed to fill field '{field['label']}': {e}")


async def fill_my_experience(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("\n💼 Step 2: My Experience")

        form_fields = await extract_all_form_fields(page)
        await page.wait_for_timeout(2000)

        # --- WORK EXPERIENCE ---
        for i, we in enumerate(config["step2"].get("work_experience", [])):
            for field in form_fields:
                if field["section_name"] == "Work Experience" and f"workExperience-{i + 1}--" in (field["id_of_input_component"] or ""):
                    if "jobTitle" in field["id_of_input_component"]:
                        await fill_input_field(page, field, we["job_title"])
                    elif "companyName" in field["id_of_input_component"]:
                        await fill_input_field(page, field, we["company"])
                    elif "location" in field["id_of_input_component"]:
                        await fill_input_field(page, field, we["location"])
                    elif "currentlyWorkHere" in field["id_of_input_component"]:
                        await fill_input_field(page, field, we.get("currently_work_here", False))
                    elif "startDate" in field["id_of_input_component"]:
                        await fill_input_field(page, field, f"{we['start_month']}/{we['start_year']}")
                    elif "endDate" in field["id_of_input_component"]:
                        if not we.get("currently_work_here", False):
                            await fill_input_field(page, field, f"{we['end_month']}/{we['end_year']}")
                    elif "roleDescription" in field["id_of_input_component"]:
                        await fill_input_field(page, field, we["description"])
        await page.wait_for_timeout(2000)

        # --- EDUCATION ---
        for i, edu in enumerate(config["step2"].get("education", [])):
            for field in form_fields:
                if field["section_name"] == "Education" and f"education-{i + 1}--" in (field["id_of_input_component"] or ""):
                    if "schoolName" in field["id_of_input_component"]:
                        await fill_input_field(page, field, edu["school_option"])
                    elif "degree" in field["id_of_input_component"]:
                        await fill_input_field(page, field, edu["degree"])
                    elif "fieldOfStudy" in field["id_of_input_component"]:
                        await fill_input_field(page, field, edu["field_of_study"])
                    elif "gradeAverage" in field["id_of_input_component"]:
                        await fill_input_field(page, field, edu["grade"])
                    elif "firstYearAttended" in field["id_of_input_component"]:
                        await fill_input_field(page, field, "2020")
                    elif "lastYearAttended" in field["id_of_input_component"]:
                        await fill_input_field(page, field, "2024")
        await page.wait_for_timeout(2000)

        # --- CERTIFICATIONS (optional) ---
        for field in form_fields:
            if field["section_name"] == "Certifications":
                # Add your logic here when certification data is added in YAML
                pass

        # --- LANGUAGE ---
        lang_data = config["step2"].get("language")
        if lang_data:
            for field in form_fields:
                if field["section_name"] == "Languages":
                    if "language" in field["id_of_input_component"]:
                        await fill_input_field(page, field, lang_data.get("language", ""))
                    elif "overall" in field["id_of_input_component"].lower():
                        await fill_input_field(page, field, lang_data.get("proficiency", ""))
        await page.wait_for_timeout(2000)

        # --- RESUME UPLOAD ---
        for field in form_fields:
            if field["type_of_input"] == "multiple-file" and "attachments" in field["id_of_input_component"]:
                await fill_input_field(page, field, config["step2"]["resume_path"])
                print("📌 Resume uploaded.")
        await page.wait_for_timeout(2000)

        # --- WEBSITES, SKILLS, LINKEDIN (optional) ---
        # You can add logic when available in YAML

        # Next button
        await page.click('button[data-automation-id="pageFooterNextButton"]')
        print("✅ Step 2 completed.")
        return True

    except Exception as err:
        print(f"❌ Step 2 failed: {err}")
        await page.screenshot(path="step2_failed.png")
        return False
