"""
This module provides functions to extract form field data from Workday job application pages.

It uses Playwright to interact with the page and extract information about various
form fields like text inputs, dropdowns, checkboxes, radio buttons, and multi-select fields.
The extracted data is structured into a consistent format for further processing.
"""

import logging
from typing import Any, Callable, Coroutine, Dict, List, Set, TypedDict

from playwright.async_api import Locator, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Type Definitions ---
class FormField(TypedDict):
    """A dictionary representing a single form field."""
    label: str
    id_of_input_component: str
    required: bool
    type_of_input: str
    options: List[str]
    user_data_select_values: List[str]

# --- Constants for Selectors ---
FORM_FIELD_SELECTOR = '[data-automation-id^="formField-"]'
PROGRESS_BAR_SELECTOR = '[data-automation-id^="progressBar"] li'
MULTI_SELECT_CONTAINER_SELECTOR = '[data-automation-id="multiSelectContainer"]'
DROPDOWN_BUTTON_SELECTOR = '[data-automation-id="dropdownButton"]'
PICKLIST_OPTION_SELECTOR = '[data-automation-id="picklistOption"]'
PILL_SELECTOR = '[data-automation-id="pill"]'
DROPDOWN_TRIGGER_SELECTOR = 'button[data-automation-id="trigger"]'

async def get_form_field_containers(page: Page) -> List[Locator]:
    """Gets all form field container elements from the page."""
    return await page.locator(FORM_FIELD_SELECTOR).all()

async def extract_application_steps(page: Page) -> List[Dict[str, Any]]:
    """Extracts the application steps from the progress bar."""
    steps_data = []
    try:
        progress_items = await page.locator(PROGRESS_BAR_SELECTOR).all()
        for item in progress_items:
            label_el = item.locator('label').nth(1)
            step_name = await label_el.inner_text()
            is_current = await item.get_attribute('data-automation-id') == 'progressBarActiveStep'
            steps_data.append({
                "step_name": step_name.strip(),
                "is_current_step": is_current
            })
    except Exception as e:
        logging.error(f"[Step Extractor] Error: {e}")
    return steps_data

async def extract_all_form_fields(page: Page) -> List[FormField]:
    """Extracts all supported form fields from the current page."""
    all_results: List[FormField] = []
    seen_labels: Set[str] = set()

    extractors: List[Callable[[Page], Coroutine[Any, Any, List[FormField]]]] = [
        extract_multiselect_fields,
        extract_radio_fields,
        extract_button_dropdown_fields,
        extract_text_fields,
        extract_checkbox_fields
    ]

    for extractor in extractors:
        try:
            fields = await extractor(page)
            for field in fields:
                if field["label"] not in seen_labels:
                    all_results.append(field)
                    seen_labels.add(field["label"])
        except Exception as e:
            logging.error(f"Error in extractor {extractor.__name__}: {e}")

    return all_results

async def extract_multiselect_fields(page: Page) -> List[FormField]:
    """Extracts data from multi-select dropdown fields."""
    results: List[FormField] = []
    containers = await page.locator(MULTI_SELECT_CONTAINER_SELECTOR).all()
    for idx, container in enumerate(containers):
        try:
            input_id = await container.get_attribute("id")
            label_el = container.locator('xpath=ancestor::div[contains(@data-automation-id, "formField")]/label')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await container.get_attribute("aria-required") == 'true'
            selected_values = await container.locator(PILL_SELECTOR).all_inner_texts()

            all_options = []
            dropdown_button = container.locator(DROPDOWN_BUTTON_SELECTOR)
            if await dropdown_button.count() > 0:
                await dropdown_button.click()
                await page.wait_for_selector(PICKLIST_OPTION_SELECTOR, timeout=2000)
                await page.wait_for_timeout(500)  # Wait for animation
                all_options = await page.locator(PICKLIST_OPTION_SELECTOR).all_inner_texts()
                await dropdown_button.click()  # Close dropdown

            results.append({
                "label": label,
                "id_of_input_component": input_id,
                "required": is_required,
                "type_of_input": "multi-select",
                "options": all_options,
                "user_data_select_values": selected_values
            })
        except Exception as e:
            logging.error(f"[MultiSelect #{idx}] Error: {e}")
    return results

async def extract_radio_fields(page: Page) -> List[FormField]:
    """Extracts data from radio button groups."""
    results: List[FormField] = []
    fieldsets = await page.locator("fieldset").all()
    for idx, fieldset in enumerate(fieldsets):
        try:
            label_el = fieldset.locator("legend label")
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await fieldset.get_attribute("aria-required") == 'true'
            radio_items = fieldset.locator('input[type="radio"]')
            options: List[str] = []
            selected_values: List[str] = []
            for i in range(await radio_items.count()):
                radio = radio_items.nth(i)
                input_id = await radio.get_attribute("id")
                label_for_radio = page.locator(f'label[for="{input_id}"]')
                option_label = await label_for_radio.inner_text()
                options.append(option_label.strip())
                if await radio.is_checked():
                    selected_values.append(option_label.strip())

            results.append({
                "label": label,
                "id_of_input_component": await fieldset.get_attribute("id"),
                "required": is_required,
                "type_of_input": "radio",
                "options": options,
                "user_data_select_values": selected_values
            })
        except Exception as e:
            logging.error(f"[Radio Field #{idx}] Error: {e}")
    return results

async def extract_button_dropdown_fields(page: Page) -> List[FormField]:
    """Extracts data from dropdown fields that are activated by a button."""
    results: List[FormField] = []
    containers = await get_form_field_containers(page)
    for idx, container in enumerate(containers):
        try:
            button = container.locator(DROPDOWN_TRIGGER_SELECTOR)
            if await button.count() == 0:
                continue
            input_id = await button.get_attribute("id")
            selected_label = await button.locator('span').first.inner_text()
            label_el = container.locator(f'label[for="{input_id}"]')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await button.get_attribute("aria-required") == 'true'
            await button.click()
            await page.wait_for_timeout(500)  # Wait for animation
            options = await page.locator('[role="listbox"] [role="option"], [data-automation-id="picklistOption"]').all_inner_texts()
            await page.keyboard.press("Escape")
            results.append({
                "label": label,
                "id_of_input_component": input_id,
                "required": is_required,
                "type_of_input": "dropdown-button",
                "options": options,
                "user_data_select_values": [selected_label] if selected_label else []
            })
        except Exception as e:
            logging.error(f"[Dropdown Button #{idx}] Error: {e}")
    return results

async def extract_text_fields(page: Page) -> List[FormField]:
    """Extracts data from text input fields."""
    results: List[FormField] = []
    containers = await get_form_field_containers(page)
    for idx, container in enumerate(containers):
        try:
            input_el = container.locator('input[type="text"]')
            if await input_el.count() == 0:
                continue
            input_id = await input_el.get_attribute("id")
            input_value = await input_el.input_value()
            label_el = container.locator(f'label[for="{input_id}"]')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await input_el.get_attribute("aria-required") == 'true'
            results.append({
                "label": label,
                "id_of_input_component": input_id,
                "required": is_required,
                "type_of_input": "text",
                "options": [],
                "user_data_select_values": [input_value]
            })
        except Exception as e:
            logging.error(f"[Text Field #{idx}] Error: {e}")
    return results

async def extract_checkbox_fields(page: Page) -> List[FormField]:
    """Extracts data from checkbox fields."""
    results: List[FormField] = []
    containers = await get_form_field_containers(page)
    for idx, container in enumerate(containers):
        try:
            input_el = container.locator('input[type="checkbox"]')
            if await input_el.count() == 0:
                continue
            input_id = await input_el.get_attribute("id")
            input_name = await input_el.get_attribute("name")
            is_checked = await input_el.is_checked()
            aria_required = await input_el.get_attribute("aria-required")
            label_el = container.locator(f'label[for="{input_id}"]')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or aria_required == 'true'
            results.append({
                "label": label,
                "id_of_input_component": input_id or input_name,
                "required": is_required,
                "type_of_input": "checkbox",
                "options": ["Yes", "No"],
                "user_data_select_values": ["Yes" if is_checked else "No"]
            })
        except Exception as e:
            logging.error(f"[Checkbox #{idx}] Error: {e}")
    return results

async def extract_all_steps_sequentially(page: Page) -> Dict[str, List[FormField]]:
    """Extracts all form fields from each step of the application process sequentially."""
    # NOTE: This timeout is a 'magic sleep' and might be unreliable.
    # It's better to wait for a specific element or network condition if possible.
    await page.wait_for_timeout(3000)

    steps = await extract_application_steps(page)
    all_step_data: Dict[str, List[FormField]] = {}

    for step in steps:
        step_name = step["step_name"]
        is_current = step["is_current_step"]
        logging.info(f"[STEP] Found: {step_name} | Current: {is_current}")

        if is_current:
            logging.info(f"→ Extracting data for current step: {step_name}")
            form_data = await extract_all_form_fields(page)
            all_step_data[step_name] = form_data
        else:
            all_step_data[step_name] = []

    return all_step_data
