import asyncio
import json
from playwright.async_api import async_playwright
from workday_automation.steps.step1_my_information import fill_my_information
from workday_automation.steps.step2_experience import fill_my_experience
from workday_automation.steps.step3_questions import fill_application_questions
from workday_automation.steps.step4_disclosures import fill_voluntary_disclosures
from workday_automation.steps.step5_self_identify import fill_self_identify
from workday_automation.steps.step6_review_submit import submit_review
from utils.extractor import extract_all_steps_sequentially

from workday_automation import login_handler
from utils.parser import CONFIG

async def run_step(step_fn, page, step_name: str) -> bool:
    print(f"➡️ Starting: {step_name}")
    try:
        result = await step_fn(page, CONFIG)
        if result:
            print(f"✅ Completed: {step_name}\n")
        else:
            print(f"❌ Failed: {step_name}")
        return result
    except Exception as e:
        print(f"💥 Exception in {step_name}: {e}")
        await page.screenshot(path=f"{step_name.replace(' ', '_').lower()}_exception.png")
        return False


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=CONFIG['headless'])
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Attempting to log in to Workday...")
        login_success = await login_handler.login_to_workday(page, CONFIG)

        if not login_success:
            print("❌ Login failed. Exiting.")
            await browser.close()
            return

        print("✅ Logged in. Proceeding with application...\n")
        
        # extractor = WorkdayFormExtractor(headless=False)
        # form_data = await extractor.run(job_url)
        # print("form_data",json.dumps(form_data, indent=2))
        
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        
        print("[INFO] Starting full application form extraction...")
        all_step_data = await extract_all_steps_sequentially(page)
        
        print("[SUCCESS] Form data extracted:")
        print(json.dumps(all_step_data, indent=2))
        
        with open("extracted_form_data.json", "w", encoding="utf-8") as f:
            json.dump(all_step_data, f, indent=2, ensure_ascii=False)
        

        # Ordered steps with descriptions and handlers
        # steps = [
        #     ("Step 1: My Information", fill_my_information),
        #     ("Step 2: My Experience", fill_my_experience),
        #     ("Step 3: Application Questions", fill_application_questions),
        #     ("Step 4: Voluntary Disclosures", fill_voluntary_disclosures),
        #     # ("Step 5: Self Identification", fill_self_identify), 
        #     ("Step 6: Review & Submit", submit_review)
        # ]

        # for step_name, step_fn in steps:
        #     if not await run_step(step_fn, page, step_name):
        #         print(f"🛑 Stopping process after failure in {step_name}")
        #         await browser.close()
        #         return

        print("🎉 Job application completed successfully!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
