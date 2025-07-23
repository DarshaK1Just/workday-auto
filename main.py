"""
Main entry point for the Workday Auto application.

This script orchestrates the entire process of logging into Workday, 
navigating through the application steps, and submitting the form.
"""

import asyncio
import logging
import json
from typing import Callable, Awaitable, Tuple

from playwright.async_api import async_playwright, Page

from workday_automation.login_handler import login_to_workday
from workday_automation.steps.step1_my_information import fill_my_information
from workday_automation.steps.step2_experience import fill_my_experience
from workday_automation.steps.step3_questions import fill_application_questions
from workday_automation.steps.step4_disclosures import fill_voluntary_disclosures
from workday_automation.steps.step5_self_identify import fill_self_identify
from workday_automation.steps.step6_review_submit import submit_review
from utils.extractor import extract_all_steps_sequentially
from utils.parser import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("workday_auto_apply.log"),
        logging.StreamHandler()
    ]
)


async def run_step(step_fn: Callable[[Page], Awaitable[bool]], page: Page, step_name: str) -> bool:
    """
    Runs a single step of the application process, with logging and error handling.

    Args:
        step_fn: The async function for the step to be executed.
        page: The Playwright Page object.
        step_name: The name of the step for logging purposes.

    Returns:
        True if the step was successful, False otherwise.
    """
    logging.info(f"--- Starting: {step_name} ---")
    try:
        if await step_fn(page, CONFIG):
            logging.info(f"--- Completed: {step_name} ---")
            return True
        else:
            logging.error(f"--- Failed: {step_name} ---")
            return False
    except Exception as e:
        logging.critical(f"An unexpected exception occurred in {step_name}: {e}", exc_info=True)
        await page.screenshot(path=f"{step_name.replace(' ', '_').lower()}_exception.png")
        return False


async def main():
    """Main function to run the entire Workday application process."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=CONFIG.get('headless', True))
        context = await browser.new_context()
        page = await context.new_page()

        try:
            if not await login_to_workday(page, CONFIG):
                logging.critical("Login failed. Exiting automation.")
                return
            
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(5000)
            
            print("[INFO] Starting full application form extraction...")
            all_step_data = await extract_all_steps_sequentially(page)
            
            print("[SUCCESS] Form data extracted:")
            print(json.dumps(all_step_data, indent=2))
            
            with open("extracted_form_data.json", "w", encoding="utf-8") as f:
                json.dump(all_step_data, f, indent=2, ensure_ascii=False)

            # steps: list[Tuple[str, Callable[[Page], Awaitable[bool]]]] = [
            #     ("Step 1: My Information", fill_my_information),
            #     ("Step 2: My Experience", fill_my_experience),
            #     ("Step 3: Application Questions", fill_application_questions),
            #     ("Step 4: Voluntary Disclosures", fill_voluntary_disclosures),
            #     ("Step 5: Self Identification", fill_self_identify),
            #     ("Step 6: Review & Submit", submit_review)
            # ]

            # for name, function in steps:
            #     if not await run_step(function, page, name):
            #         logging.error(f"Stopping process due to failure in {name}.")
            #         return

            logging.info("🎉🎉🎉 Job application process completed successfully! 🎉🎉🎉")

        finally:
            await browser.close()
            logging.info("Browser closed.")


if __name__ == "__main__":
    asyncio.run(main())