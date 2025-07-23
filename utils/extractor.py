"""
This module provides functions to extract form field data from Workday job application pages.
Combines best practices from the first sample with exact reference patterns from the second sample.

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
DROPDOWN_TRIGGER_SELECTOR = 'button[aria-haspopup="listbox"]'

# --- Timeout Constants ---
TIMEOUTS = {
    "element_wait": 2000,
    "animation_wait": 500,
    "page_wait": 3000
}


async def get_form_field_containers(page: Page) -> List[Locator]:
    """Gets all form field container elements from the page."""
    try:
        return await page.locator(FORM_FIELD_SELECTOR).all()
    except Exception as e:
        logging.error(f"Error getting form field containers: {e}")
        return []


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

    # Define extractors in order of priority
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
    
    try:
        containers = await page.locator(MULTI_SELECT_CONTAINER_SELECTOR).all()
        for idx, container in enumerate(containers):
            try:
                input_id = await container.get_attribute("id")
                
                # Extract label using xpath - following reference pattern
                label_el = container.locator('xpath=ancestor::div[contains(@data-automation-id, "formField")]/label')
                label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
                label = label_text.replace("*", "").strip()
                is_required = '*' in label_text or await container.get_attribute("aria-required") == 'true'
                
                # Get selected values using pill selector
                selected_values = await container.locator(PILL_SELECTOR).all_inner_texts()

                # Extract all available options by clicking dropdown
                all_options = []
                dropdown_button = container.locator(DROPDOWN_BUTTON_SELECTOR)
                if await dropdown_button.count() > 0:
                    await dropdown_button.click()
                    await page.wait_for_selector(PICKLIST_OPTION_SELECTOR, timeout=TIMEOUTS["element_wait"])
                    await page.wait_for_timeout(TIMEOUTS["animation_wait"])  # Wait for animation
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
    except Exception as e:
        logging.error(f"Error extracting multiselect fields: {e}")
    
    return results


async def extract_radio_fields(page: Page) -> List[FormField]:
    """Extracts data from radio button groups."""
    results: List[FormField] = []
    
    try:
        fieldsets = await page.locator("fieldset").all()
        for idx, fieldset in enumerate(fieldsets):
            try:
                # Extract legend label
                label_el = fieldset.locator("legend label")
                label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
                label = label_text.replace("*", "").strip()
                is_required = '*' in label_text or await fieldset.get_attribute("aria-required") == 'true'
                
                # Extract radio options
                radio_items = fieldset.locator('input[type="radio"]')
                options: List[str] = []
                selected_values: List[str] = []
                
                for i in range(await radio_items.count()):
                    radio = radio_items.nth(i)
                    value = await radio.get_attribute("value")
                    input_id = await radio.get_attribute("id")
                    
                    # Get label for radio button - following reference pattern
                    label_for_radio = page.locator(f'label[for="{input_id}"]')
                    label_text = await label_for_radio.inner_text() if await label_for_radio.count() > 0 else value
                    options.append(label_text)
                    
                    # Check if selected - using reference pattern
                    if await radio.get_attribute("checked") == "true":
                        selected_values.append(label_text)

                results.append({
                    "label": label,
                    "id_of_input_component": await fieldset.get_attribute("id"),
                    "required": is_required,
                    "type_of_input": "radio",
                    "options": options,
                    "user_data_select_values": selected_values
                })
            except Exception as e:
                logging.error(f"[Radio #{idx}] Error: {e}")
    except Exception as e:
        logging.error(f"Error extracting radio fields: {e}")
    
    return results


async def extract_button_dropdown_fields(page: Page) -> List[FormField]:
    """Extracts data from dropdown fields that are activated by a button."""
    results: List[FormField] = []
    
    try:
        containers = await get_form_field_containers(page)
        for idx, container in enumerate(containers):
            try:
                # Use reference pattern for button selector
                button = container.locator(DROPDOWN_TRIGGER_SELECTOR)
                if await button.count() == 0:
                    continue
                
                input_id = await button.get_attribute("id")
                # Get selected label - following reference pattern
                selected_label = (await button.inner_text()).strip()
                
                # Extract label
                label_el = container.locator(f'label[for="{input_id}"]')
                label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
                label = label_text.replace("*", "").strip()
                is_required = '*' in label_text or await button.get_attribute("aria-required") == 'true'
                
                # Click to get options
                await button.click()
                await page.wait_for_timeout(TIMEOUTS["animation_wait"])
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
    except Exception as e:
        logging.error(f"Error extracting button dropdown fields: {e}")
    
    return results


async def extract_text_fields(page: Page) -> List[FormField]:
    """Extracts data from text input fields."""
    results: List[FormField] = []
    
    try:
        containers = await get_form_field_containers(page)
        for idx, container in enumerate(containers):
            try:
                input_el = container.locator('input[type="text"]')
                if await input_el.count() == 0:
                    continue
                
                input_id = await input_el.get_attribute("id")
                input_value = await input_el.input_value()
                
                # Extract label
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
    except Exception as e:
        logging.error(f"Error extracting text fields: {e}")
    
    return results


async def extract_checkbox_fields(page: Page) -> List[FormField]:
    """Extracts data from checkbox fields."""
    results: List[FormField] = []
    
    try:
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
                
                # Extract label
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
    except Exception as e:
        logging.error(f"Error extracting checkbox fields: {e}")
    
    return results


async def extract_all_steps_sequentially(page: Page) -> Dict[str, List[FormField]]:
    """
    Extracts all form fields from each step of the application process sequentially.
    
    Args:
        page: The Playwright Page object
        
    Returns:
        Dictionary mapping step names to their form fields
    """
    # Wait for page to stabilize - using reference timeout value
    await page.wait_for_timeout(TIMEOUTS["page_wait"])

    try:
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
                logging.info(f"→ Extracted {len(form_data)} fields from step: {step_name}")
            else:
                all_step_data[step_name] = []

        return all_step_data
    except Exception as e:
        logging.error(f"Error in extract_all_steps_sequentially: {e}")
        return {}


# --- Utility Functions for Enhanced Error Handling ---

async def _safe_get_attribute(element: Locator, attribute: str, default: str = "") -> str:
    """Safely get an attribute from an element with fallback."""
    try:
        value = await element.get_attribute(attribute)
        return value if value is not None else default
    except Exception:
        return default


async def _safe_get_inner_text(element: Locator, default: str = "Unknown") -> str:
    """Safely get inner text from an element with fallback."""
    try:
        if await element.count() > 0:
            return await element.inner_text()
        return default
    except Exception:
        return default


async def _safe_click_and_extract_options(page: Page, button: Locator, option_selector: str) -> List[str]:
    """Safely click a dropdown and extract options with error handling."""
    try:
        await button.click()
        await page.wait_for_timeout(TIMEOUTS["animation_wait"])
        options = await page.locator(option_selector).all_inner_texts()
        await page.keyboard.press("Escape")  # Close dropdown
        return options
    except Exception as e:
        logging.warning(f"Could not extract dropdown options: {e}")
        try:
            await page.keyboard.press("Escape")  # Ensure dropdown is closed
        except:
            pass
        return []
