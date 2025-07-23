"""
Dynamic Job Application Progress Extractor.

This module provides a class to dynamically extract the progress of a job application
from a web page. It is designed to be adaptable to various job application form
structures without relying on hardcoded selectors.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Browser, ElementHandle, Page, async_playwright

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Constants ---
COMPLETED_KEYWORDS = ["complete", "finished", "done", "past"]
ACTIVE_KEYWORDS = ["active", "current", "present", "now"]
PROGRESS_CONTAINER_SELECTORS = [
    '[aria-label*="progress" i]',
    '[aria-label*="step" i]',
    '[class*="progress" i]',
    '[class*="step" i]',
    '[data-automation-id*="progress" i]',
    '[data-testid*="progress" i]',
    'ol[class*="progress" i]',
    'ul[class*="progress" i]',
    'div[class*="stepper" i]',
    'nav[class*="step" i]',
]
STEP_ELEMENT_SELECTORS = [
    "li",
    'div[class*="step"]',
    'div[data-automation-id*="step"]',
    'div[aria-label*="step"]',
    '[class*="step"]',
    'div[class*="item"]',
    'span[class*="step"]',
]


class DynamicJobProgressExtractor:
    """
    Extracts job application progress by dynamically analyzing the page structure.
    """

    def __init__(self) -> None:
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def launch_browser(self, headless: bool = False) -> None:
        """Launches a Playwright browser instance and creates a new page."""
        logging.info(f"Launching browser in {'headless' if headless else 'headed'} mode.")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.page = await self.browser.new_page()

    async def close_browser(self) -> None:
        """Closes the Playwright browser instance."""
        if self.browser:
            logging.info("Closing browser.")
            await self.browser.close()

    async def _find_progress_container(self, page: Page) -> Optional[ElementHandle]:
        """Finds the main container element for the progress steps."""
        logging.debug("Attempting to find progress container.")
        for selector in PROGRESS_CONTAINER_SELECTORS:
            try:
                container = await page.query_selector(selector)
                if container:
                    steps = await container.query_selector_all(
                        'li, div[class*="step"], div[data-automation-id*="step"]'
                    )
                    if len(steps) > 1:
                        logging.info(f"Found progress container with selector: {selector}")
                        return container
            except Exception as e:
                logging.warning(
                    f"Error checking selector '{selector}': {e}"
                )
                continue
        return None

    async def _extract_step_elements(self, container: ElementHandle) -> List[ElementHandle]:
        """Extracts individual step elements from the progress container."""
        logging.debug("Extracting step elements from container.")
        for selector in STEP_ELEMENT_SELECTORS:
            steps = await container.query_selector_all(selector)
            if len(steps) > 1:
                logging.info(f"Found {len(steps)} step elements with selector: {selector}")
                return steps
        return []

    async def _analyze_step_element(
        self, step_element: ElementHandle, index: int
    ) -> Dict[str, Any]:
        """Analyzes a single step element to extract its details."""
        step_info: Dict[str, Any] = {
            "step_number": index + 1,
            "step_name": f"Step {index + 1}",
            "status": "unknown",
        }

        try:
            attributes = await step_element.evaluate(
                "(element) => Object.fromEntries(Array.from(element.attributes, ({name, value}) => [name, value]))"
            )
            text_content = (await step_element.text_content() or "").lower()

            step_info["step_name"] = self._get_step_name(step_element, attributes, text_content, index)
            step_info["status"] = self._get_step_status(attributes, text_content)

        except Exception as e:
            logging.error(f"Failed to analyze step element {index + 1}: {e}")
            step_info["error"] = str(e)

        return step_info

    def _get_step_name(
        self, element: ElementHandle, attributes: Dict[str, str], text: str, index: int
    ) -> str:
        """Determines the name of the step from various sources."""
        # Prefer aria-label or specific attributes
        for attr in ["aria-label", "data-step-name", "title"]:
            if attr in attributes and len(attributes[attr]) > 3:
                return attributes[attr].strip()

        # Use cleaned text content if meaningful
        cleaned_text = re.sub(r"\d+", "", text).strip()
        if len(cleaned_text) > 3:
            return cleaned_text

        return f"Step {index + 1}" # Fallback

    def _get_step_status(self, attributes: Dict[str, str], text: str) -> str:
        """Determines the status (completed, active, unknown) of a step."""
        attr_values = " ".join(attributes.values()).lower()

        if any(keyword in attr_values or keyword in text for keyword in COMPLETED_KEYWORDS):
            return "completed"
        if any(keyword in attr_values or keyword in text for keyword in ACTIVE_KEYWORDS):
            return "active"

        return "unknown"

    async def extract_progress(self, page: Optional[Page] = None) -> Dict[str, Any]:
        """Extracts the entire progress structure from the page."""
        page = page or self.page
        if not page:
            return {"error": "Page object not available."}

        try:
            container = await self._find_progress_container(page)
            if not container:
                return {"error": "Could not find a progress container on the page."}

            step_elements = await self._extract_step_elements(container)
            if not step_elements:
                return {"error": "Could not extract step elements from container."}

            analyzed_steps = await asyncio.gather(
                *[self._analyze_step_element(step, i) for i, step in enumerate(step_elements)]
            )

            # Finalize status: if one is active, unknowns are inactive
            if any(s["status"] == "active" for s in analyzed_steps):
                for step in analyzed_steps:
                    if step["status"] == "unknown":
                        step["status"] = "inactive"

            completed_steps = [s for s in analyzed_steps if s["status"] == "completed"]
            current_step = next((s for s in analyzed_steps if s["status"] == "active"), None)

            return {
                "total_steps": len(analyzed_steps),
                "completed_steps": len(completed_steps),
                "current_step_name": current_step["step_name"] if current_step else "N/A",
                "steps": analyzed_steps,
            }

        except Exception as e:
            logging.critical(f"A critical error occurred during extraction: {e}")
            return {"error": str(e)}

    @staticmethod
    def display_summary(progress_info: Dict[str, Any]) -> None:
        """Prints a formatted summary of the application progress."""
        if "error" in progress_info:
            logging.error(f"Cannot display summary due to error: {progress_info['error']}")
            return

        logging.info("\n--- Job Application Progress ---")
        logging.info(f"Total Steps: {progress_info['total_steps']}")
        logging.info(f"Completed: {progress_info['completed_steps']}")
        logging.info(f"Current Step: {progress_info['current_step_name']}")
        logging.info("---------------------------------")

        for step in progress_info["steps"]:
            icons = {"completed": "✅", "active": "🔄", "inactive": "⏳", "unknown": "❓"}
            status = step.get("status", "unknown")
            logging.info(
                f"{icons[status]} Step {step['step_number']}: {step['step_name']} ({status.upper()})"
            )


async def run_single_extraction(
    url: str, headless: bool = True
) -> Optional[Dict[str, Any]]:
    """Convenience function to launch, extract, and close."""
    extractor = DynamicJobProgressExtractor()
    try:
        await extractor.launch_browser(headless=headless)
        if not extractor.page:
            logging.error("Failed to create a page.")
            return None

        logging.info(f"Navigating to {url}")
        await extractor.page.goto(url, wait_until="networkidle")
        await asyncio.sleep(2)  # Allow for dynamic content to load

        progress_data = await extractor.extract_progress()
        extractor.display_summary(progress_data)
        return progress_data

    except Exception as e:
        logging.critical(f"An error occurred during single extraction run: {e}")
        return {"error": str(e)}
    finally:
        await extractor.close_browser()


async def main() -> None:
    """Main function to demonstrate the extractor's capabilities."""
    test_url = "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite/job/Senior-DevOps-Engineer_JR1997710/apply/applyManually"
    logging.info(f"--- Running Dynamic Job Progress Extractor on: {test_url} ---")

    await run_single_extraction(test_url, headless=True)


if __name__ == "__main__":
    asyncio.run(main())
