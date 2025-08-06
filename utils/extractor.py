"""
Improved form extraction module that properly handles dynamic sections like Work Experience.
Fixed to properly distinguish between radio buttons and dropdown buttons.
"""

import logging
from typing import Any, Callable, Coroutine, Dict, List, Set, TypedDict

from playwright.async_api import Locator, Page

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FormField(TypedDict):
    """A dictionary representing a single form field."""
    label: str
    id_of_input_component: str
    required: bool
    type_of_input: str
    options: List[str]
    user_data_select_values: List[str]
    section_name: str  # Added to track which section this field belongs to

# Constants
FORM_FIELD_SELECTOR = '[data-automation-id^="formField-"]'
MULTI_SELECT_CONTAINER_SELECTOR = '[data-automation-id="multiSelectContainer"]'
DROPDOWN_BUTTON_SELECTOR = '[data-automation-id="dropdownButton"]'
PICKLIST_OPTION_SELECTOR = '[data-automation-id="picklistOption"]'
PILL_SELECTOR = '[data-automation-id="pill"]'
PROMPT_OPTION_SELECTOR = '[data-automation-id="promptOption"]'
ACTIVE_LIST_CONTAINER = '[data-automation-id="activeListContainer"]'
DROPDOWN_TRIGGER_SELECTOR = '[aria-haspopup="listbox"]'

# --- Timeout Constants ---
TIMEOUTS = {
    "element_wait": 2000,
    "animation_wait": 500,
    "page_wait": 3000
}
ADD_BUTTON_SELECTOR = '[data-automation-id="add-button"]'

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
        progress_items = await page.locator('[data-automation-id^="progressBar"] li').all()
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

async def extract_all_form_fields(page: Page, exclude_dynamic_sections: bool = False) -> List[FormField]:
    """
    Extracts all supported form fields from the current page.
    
    Args:
        page: Playwright page object
        exclude_dynamic_sections: If True, skips dynamic section extraction to avoid recursion
    """
    all_results: List[FormField] = []
    seen_labels: Set[str] = set()

    # Define extractors - removed dynamic sections from main flow
    # IMPORTANT: Order matters! Put dropdown_button before radio to catch dropdown buttons first
    base_extractors: List[Callable[[Page], Coroutine[Any, Any, List[FormField]]]] = [
        extract_multiselect_fields,
        extract_button_dropdown_fields,  # MOVED BEFORE radio fields
        extract_radio_fields,            # This will now only catch actual radio buttons
        extract_text_fields,
        extract_checkbox_fields,
        extract_textarea_fields,  # Added for role descriptions
        extract_date_fields,      # Added for start/end dates
        extract_file_upload_fields  # Added for resume/CV uploads
    ]

    # Run base extractors
    for extractor in base_extractors:
        try:
            fields = await extractor(page)
            for field in fields:
                field_key = f"{field['label']}_{field['id_of_input_component']}"
                if field_key not in seen_labels:
                    all_results.append(field)
                    seen_labels.add(field_key)
        except Exception as e:
            logging.error(f"Error in extractor {extractor.__name__}: {e}")

    # Handle dynamic sections separately
    if not exclude_dynamic_sections:
        try:
            dynamic_fields = await extract_dynamic_section_fields(page)
            for field in dynamic_fields:
                field_key = f"{field['label']}_{field['id_of_input_component']}"
                if field_key not in seen_labels:
                    all_results.append(field)
                    seen_labels.add(field_key)
        except Exception as e:
            logging.error(f"Error in dynamic section extraction: {e}")

    return all_results

async def extract_dynamic_section_fields(page: Page) -> List[FormField]:
    """
    Clicks 'Add' in dynamic sections and extracts nested fields.
    Avoids recursion by calling base extractors directly.
    """
    sectioned_results: List[FormField] = []

    try:
        # Get all section headers
        section_headers = await page.locator("h3[id$='-section']").all()

        for header in section_headers:
            try:
                section_id = await header.get_attribute("id")
                section_title = (await header.inner_text()).strip()
                logging.info(f"[{section_title}] Processing section...")

                if not section_id:
                    continue

                # Find section container
                section_container = page.locator(f'div[role="group"][aria-labelledby="{section_id}"]')
                if await section_container.count() == 0:
                    continue

                # Click Add button if present
                add_button = section_container.locator(ADD_BUTTON_SELECTOR)
                if await add_button.count() > 0:
                    await add_button.click()
                    await page.wait_for_timeout(TIMEOUTS["animation_wait"])

                    # Wait for new fields to appear
                    await page.wait_for_selector(FORM_FIELD_SELECTOR, timeout=5000)

                    # Extract fields specifically from this section
                    section_fields = await extract_section_specific_fields(page, section_container, section_title)
                    sectioned_results.extend(section_fields)
                    
                    logging.info(f"[{section_title}] Extracted {len(section_fields)} fields")

            except Exception as e:
                logging.error(f"[{section_title}] Error: {e}")

    except Exception as e:
        logging.error(f"[extract_dynamic_section_fields] Error: {e}")

    return sectioned_results

async def extract_section_specific_fields(page: Page, section_container: Locator, section_name: str) -> List[FormField]:
    """
    Extract fields specifically from within a section container.
    """
    fields: List[FormField] = []
    
    try:
        # Get form fields within this section
        form_fields = await section_container.locator(FORM_FIELD_SELECTOR).all()
        
        for container in form_fields:
            # Try different field types
            field = None
            
            # Dropdown buttons first (before text inputs)
            dropdown_button = container.locator(DROPDOWN_TRIGGER_SELECTOR)
            if await dropdown_button.count() > 0:
                field = await extract_single_dropdown_button_field(container, dropdown_button)
            
            # Text inputs
            if not field:
                text_input = container.locator('input[type="text"]')
                if await text_input.count() > 0:
                    field = await extract_single_text_field(container, text_input)
            
            # Checkboxes
            if not field:
                checkbox = container.locator('input[type="checkbox"]')
                if await checkbox.count() > 0:
                    field = await extract_single_checkbox_field(container, checkbox)
            
            # Textareas
            if not field:
                textarea = container.locator('textarea')
                if await textarea.count() > 0:
                    field = await extract_single_textarea_field(container, textarea)
            
            # Date fields (complex date pickers)
            if not field:
                date_input = container.locator('input[role="spinbutton"]')
                if await date_input.count() > 0:
                    field = await extract_single_date_field(container)
            
            # File upload fields
            if not field:
                file_upload = container.locator('[data-automation-id="attachments-FileUpload"]')
                if await file_upload.count() > 0:
                    field = await extract_single_file_upload_field(container, file_upload)
            
            if field:
                field["section_name"] = section_name
                fields.append(field)
                
    except Exception as e:
        logging.error(f"Error extracting section fields: {e}")
    
    return fields

async def extract_single_dropdown_button_field(container: Locator, button: Locator) -> FormField:
    """Extract a single dropdown button field."""
    input_id = await button.get_attribute("id")
    if not input_id:
        return None

    # Selected label
    selected_label = (await button.inner_text()).strip()
    if selected_label.lower() in {"select one", "select", ""}:
        selected_label = ""

    # Extract label from fieldset legend or regular label
    fieldset = container.locator('fieldset')
    if await fieldset.count() > 0:
        # For fieldset-based dropdowns (like your HTML example)
        legend_label = fieldset.locator('legend div[data-automation-id="richText"] p')
        if await legend_label.count() > 0:
            label_text = await legend_label.inner_text()
        else:
            legend_label = fieldset.locator('legend label')
            label_text = await legend_label.inner_text() if await legend_label.count() > 0 else "Unknown"
    else:
        # Regular label extraction
        label_el = container.locator(f'label[for="{input_id}"]')
        label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
    
    # Clean label and check if required
    label = label_text.replace("*", "").strip()
    is_required = (
        "*" in label_text
        or (await button.get_attribute("aria-required")) == "true"
        or "Required" in (await button.get_attribute("aria-label") or "")
    )

    return {
        "label": label,
        "id_of_input_component": input_id,
        "required": is_required,
        "type_of_input": "dropdown-button",
        "options": [],  # Will be filled by main extractor
        "user_data_select_values": [selected_label] if selected_label else [],
        "section_name": ""
    }

async def extract_single_text_field(container: Locator, input_el: Locator) -> FormField:
    """Extract a single text field."""
    input_id = await input_el.get_attribute("id")
    input_value = await input_el.input_value()
    
    # Extract label
    label_el = container.locator(f'label[for="{input_id}"]')
    label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
    label = label_text.replace("*", "").strip()
    is_required = '*' in label_text or await input_el.get_attribute("aria-required") == 'true'
    
    return {
        "label": label,
        "id_of_input_component": input_id,
        "required": is_required,
        "type_of_input": "text",
        "options": [],
        "user_data_select_values": [input_value] if input_value else [],
        "section_name": ""
    }


async def extract_single_file_upload_field(container: Locator, file_upload_el: Locator) -> FormField:
    """Extract a single file upload field."""
    # Get the aria-labelledby attribute to find the label
    label_id = await file_upload_el.get_attribute("aria-labelledby")
    
    # Find the label element
    if label_id:
        label_el = container.locator(f'#{label_id}')
        label_text = await label_el.inner_text() if await label_el.count() > 0 else "File Upload"
    else:
        # Fallback: look for label in container
        label_el = container.locator('label')
        label_text = await label_el.inner_text() if await label_el.count() > 0 else "File Upload"
    
    label = label_text.replace("*", "").strip()
    is_required = "*" in label_text
    
    # Get the file input element
    file_input = file_upload_el.locator('input[type="file"]')
    input_id = await file_input.get_attribute("id") if await file_input.count() > 0 else "unknown"
    
    # Get the select files button ID as backup
    select_button = file_upload_el.locator('[data-automation-id="select-files"]')
    if not input_id and await select_button.count() > 0:
        input_id = await select_button.get_attribute("id")
    
    # Check if multiple files are accepted
    multiple = await file_input.get_attribute("multiple") if await file_input.count() > 0 else None
    upload_type = "multiple-file" if multiple is not None else "single-file"
    
    # Check for existing uploaded files
    uploaded_files = []
    file_items = await file_upload_el.locator('[data-automation-id*="file-item"], .uploaded-file, .file-name').all()
    for file_item in file_items:
        try:
            file_name = await file_item.inner_text()
            if file_name.strip():
                uploaded_files.append(file_name.strip())
        except:
            continue
    
    return {
        "label": label,
        "id_of_input_component": input_id or "unknown",
        "required": is_required,
        "type_of_input": upload_type,
        "options": ["Select file", "Drop file"],
        "user_data_select_values": uploaded_files,
        "section_name": ""
    }

async def extract_single_checkbox_field(container: Locator, input_el: Locator) -> FormField:
    """Extract a single checkbox field."""
    input_id = await input_el.get_attribute("id")
    is_checked = await input_el.is_checked()
    
    # Extract label
    label_el = container.locator(f'label[for="{input_id}"]')
    label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
    label = label_text.replace("*", "").strip()
    is_required = '*' in label_text or await input_el.get_attribute("aria-required") == 'true'
    
    return {
        "label": label,
        "id_of_input_component": input_id,
        "required": is_required,
        "type_of_input": "checkbox",
        "options": ["Yes", "No"],
        "user_data_select_values": ["Yes" if is_checked else "No"],
        "section_name": ""
    }

async def extract_single_textarea_field(container: Locator, textarea_el: Locator) -> FormField:
    """Extract a single textarea field."""
    input_id = await textarea_el.get_attribute("id")
    input_value = await textarea_el.input_value()
    
    # Extract label
    label_el = container.locator(f'label[for="{input_id}"]')
    label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
    label = label_text.replace("*", "").strip()
    is_required = '*' in label_text or await textarea_el.get_attribute("aria-required") == 'true'
    
    return {
        "label": label,
        "id_of_input_component": input_id,
        "required": is_required,
        "type_of_input": "textarea",
        "options": [],
        "user_data_select_values": [input_value] if input_value else [],
        "section_name": ""
    }

async def extract_single_date_field(container: Locator) -> FormField:
    """Extract a single date field (MM/YYYY format)."""
    # Look for the fieldset containing the date inputs
    fieldset = container.locator('fieldset')
    if await fieldset.count() == 0:
        return None
    
    # Get label from legend
    legend_label = fieldset.locator('legend label')
    label_text = await legend_label.inner_text() if await legend_label.count() > 0 else "Date"
    label = label_text.replace("*", "").strip()
    is_required = '*' in label_text
    
    # Get the date wrapper ID
    date_wrapper = fieldset.locator('[data-automation-id="dateInputWrapper"]')
    wrapper_id = await date_wrapper.get_attribute("id") if await date_wrapper.count() > 0 else "unknown"
    
    # Get current values
    month_input = fieldset.locator('input[aria-label="Month"]')
    year_input = fieldset.locator('input[aria-label="Year"]')
    
    month_value = await month_input.input_value() if await month_input.count() > 0 else ""
    year_value = await year_input.input_value() if await year_input.count() > 0 else ""
    
    current_value = f"{month_value}/{year_value}" if month_value and year_value else ""
    
    return {
        "label": label,
        "id_of_input_component": wrapper_id,
        "required": is_required,
        "type_of_input": "date",
        "options": [],
        "user_data_select_values": [current_value] if current_value else [],
        "section_name": ""
    }

# Implement the missing base extractors
async def extract_textarea_fields(page: Page) -> List[FormField]:
    """Extract textarea fields."""
    results: List[FormField] = []
    
    try:
        containers = await page.locator(FORM_FIELD_SELECTOR).all()
        for container in containers:
            textarea = container.locator('textarea')
            if await textarea.count() > 0:
                field = await extract_single_textarea_field(container, textarea)
                if field:
                    field["section_name"] = "main"
                    results.append(field)
    except Exception as e:
        logging.error(f"Error extracting textarea fields: {e}")
    
    return results


async def extract_file_upload_fields(page: Page) -> List[FormField]:
    """Extract file upload fields (like Resume/CV uploads)."""
    results: List[FormField] = []
    
    try:
        # Look for file upload containers
        file_upload_containers = await page.locator('[data-automation-id="attachments-FileUpload"]').all()
        
        for idx, container in enumerate(file_upload_containers):
            try:
                # Get the aria-labelledby attribute to find the label
                label_id = await container.get_attribute("aria-labelledby")
                
                # Find the label element
                if label_id:
                    label_el = page.locator(f'#{label_id}')
                    label_text = await label_el.inner_text() if await label_el.count() > 0 else "File Upload"
                else:
                    # Fallback: look for label in parent container
                    parent_container = container.locator('xpath=ancestor::div[contains(@data-automation-id, "formField")]')
                    label_el = parent_container.locator('label')
                    label_text = await label_el.inner_text() if await label_el.count() > 0 else "File Upload"
                
                label = label_text.replace("*", "").strip()
                is_required = "*" in label_text
                
                # Get the file input element
                file_input = container.locator('input[type="file"]')
                input_id = await file_input.get_attribute("id") if await file_input.count() > 0 else f"file-upload-{idx}"
                
                # Get the select files button ID as backup
                select_button = container.locator('[data-automation-id="select-files"]')
                if not input_id and await select_button.count() > 0:
                    input_id = await select_button.get_attribute("id")
                
                # Check if multiple files are accepted
                multiple = await file_input.get_attribute("multiple") if await file_input.count() > 0 else None
                upload_type = "multiple-file" if multiple is not None else "single-file"
                
                # Check for existing uploaded files (if any)
                uploaded_files = []
                # Look for uploaded file indicators - this might need adjustment based on actual DOM
                file_items = await container.locator('[data-automation-id*="file-item"], .uploaded-file, .file-name').all()
                for file_item in file_items:
                    try:
                        file_name = await file_item.inner_text()
                        if file_name.strip():
                            uploaded_files.append(file_name.strip())
                    except:
                        continue
                
                results.append({
                    "label": label,
                    "id_of_input_component": input_id or f"file-upload-{idx}",
                    "required": is_required,
                    "type_of_input": upload_type,
                    "options": ["Select file", "Drop file"],  # Available actions
                    "user_data_select_values": uploaded_files,  # Currently uploaded files
                    "section_name": "main"
                })
                
            except Exception as e:
                logging.error(f"[File Upload #{idx}] Error: {e}")
                continue
                
    except Exception as e:
        logging.error(f"Error extracting file upload fields: {e}")
    
    return results


async def extract_all_steps_sequentially(page: Page) -> Dict[str, List[FormField]]:
    """
    Extracts all form fields from each step of the application process sequentially.
    
    Args:
        page: The Playwright Page object
        
    Returns:
        Dictionary mapping step names to their form fields
    """
    # Wait for page to stabilize
    await page.wait_for_timeout(3000)  # 3 second wait for page stability

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

async def extract_date_fields(page: Page) -> List[FormField]:
    """Extract date fields."""
    results: List[FormField] = []
    
    try:
        containers = await page.locator(FORM_FIELD_SELECTOR).all()
        for container in containers:
            date_input = container.locator('input[role="spinbutton"]')
            if await date_input.count() > 0:
                field = await extract_single_date_field(container)
                if field:
                    field["section_name"] = "main"
                    results.append(field)
    except Exception as e:
        logging.error(f"Error extracting date fields: {e}")
    
    return results

async def extract_multiselect_fields(page: Page) -> List[FormField]:
    """Extracts all multi-select fields from the current form page."""
    results: List[FormField] = []

    try:
        containers = await page.locator(MULTI_SELECT_CONTAINER_SELECTOR).all()
        if not containers:
            logging.warning("⚠️ No multi-select containers found.")
            return results

        for idx, container in enumerate(containers):
            try:
                input_id = await container.get_attribute("id")

                # Extract label using xpath
                label_el = container.locator('xpath=ancestor::div[contains(@data-automation-id, "formField")]/label')
                label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
                label = label_text.replace("*", "").strip()
                is_required = '*' in label_text or await container.get_attribute("aria-required") == 'true'

                # Get selected values
                selected_values = await container.locator(PILL_SELECTOR).all_inner_texts()

                # Extract available options
                all_options = []
                dropdown_button = container.locator(DROPDOWN_BUTTON_SELECTOR)
                if await dropdown_button.count() > 0:
                    await dropdown_button.click()
                    await page.wait_for_selector(PICKLIST_OPTION_SELECTOR, timeout=TIMEOUTS["element_wait"])
                    await page.wait_for_timeout(TIMEOUTS["animation_wait"])
                    all_options = await page.locator(PICKLIST_OPTION_SELECTOR).all_inner_texts()
                    await dropdown_button.click()  # Close dropdown

                results.append({
                    "label": label,
                    "id_of_input_component": input_id,
                    "required": is_required,
                    "type_of_input": "multi-select",
                    "options": all_options,
                    "user_data_select_values": selected_values,
                    "section_name": "main"
                })
            except Exception as e:
                logging.error(f"[MultiSelect #{idx}] Error: {e}")
    except Exception as e:
        logging.error(f"❌ Error extracting multiselect fields: {e}")

    return results


async def extract_radio_fields(page: Page) -> List[FormField]:
    """Extracts data from ACTUAL radio button groups (not dropdown buttons)."""
    results: List[FormField] = []

    try:
        fieldsets = await page.locator("fieldset").all()
        for idx, fieldset in enumerate(fieldsets):
            try:
                # IMPORTANT: Skip fieldsets that contain dropdown buttons
                dropdown_button = fieldset.locator(DROPDOWN_TRIGGER_SELECTOR)
                if await dropdown_button.count() > 0:
                    logging.info(f"[Radio #{idx}] Skipping fieldset with dropdown button")
                    continue
                
                # Only process fieldsets with actual radio buttons
                radio_inputs = fieldset.locator('input[type="radio"]')
                if await radio_inputs.count() == 0:
                    continue

                # Get label from <legend><label>
                label_el = fieldset.locator("legend label")
                label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
                label = label_text.replace("*", "").strip()
                is_required = '*' in label_text or await fieldset.get_attribute("aria-required") == 'true'

                # Extract input container ID
                input_container = fieldset.locator("div[aria-labelledby]")
                input_id = await input_container.get_attribute("id")
                input_id = input_id or await input_container.get_attribute("data-fkit-id") or "unknown"

                # Extract radio options
                options: List[str] = []
                selected_values: List[str] = []

                for i in range(await radio_inputs.count()):
                    radio = radio_inputs.nth(i)
                    value = await radio.get_attribute("value")
                    radio_id = await radio.get_attribute("id")

                    label_for_radio = page.locator(f'label[for="{radio_id}"]')
                    option_text = await label_for_radio.inner_text() if await label_for_radio.count() > 0 else value
                    options.append(option_text)

                    # Check if selected
                    if await radio.get_attribute("checked") == "true" or await radio.get_attribute("aria-checked") == "true":
                        selected_values.append(option_text)

                results.append({
                    "label": label,
                    "id_of_input_component": input_id,
                    "required": is_required,
                    "type_of_input": "radio",
                    "options": options,
                    "user_data_select_values": selected_values,
                    "section_name": "main"
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
        containers = await page.locator(FORM_FIELD_SELECTOR).all()
        for idx, container in enumerate(containers):
            try:
                button = container.locator(DROPDOWN_TRIGGER_SELECTOR)
                if await button.count() == 0:
                    continue

                # Use the helper function to extract the field
                field = await extract_single_dropdown_button_field(container, button)
                if not field:
                    continue

                # Extract dropdown options by clicking
                try:
                    await button.click()
                    await page.wait_for_timeout(TIMEOUTS["animation_wait"])
                    option_locator = page.locator('[role="listbox"] [role="option"], [data-automation-id="picklistOption"]')
                    await option_locator.first.wait_for(timeout=TIMEOUTS["element_wait"])
                    options = await option_locator.all_inner_texts()
                    await page.keyboard.press("Escape")
                    field["options"] = [opt.strip() for opt in options if opt.strip()]
                except Exception as e:
                    logging.warning(f"[Dropdown Button #{idx}] Could not extract options: {e}")
                    field["options"] = []

                field["section_name"] = "main"
                results.append(field)
                
            except Exception as e:
                logging.error(f"[Dropdown Button #{idx}] Error: {e}")
    except Exception as e:
        logging.error(f"❌ Error extracting button dropdown fields: {e}")

    return results


async def extract_text_fields(page: Page) -> List[FormField]:
    """Extracts data from text input fields."""
    results: List[FormField] = []    

    try:
        containers = await page.locator(FORM_FIELD_SELECTOR).all()
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
                    "user_data_select_values": [input_value] if input_value else [],
                    "section_name": "main"
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
        containers = await page.locator(FORM_FIELD_SELECTOR).all()
        for idx, container in enumerate(containers):
            try:
                input_el = container.locator('input[type="checkbox"]')
                if await input_el.count() == 0:
                    continue
                
                field = await extract_single_checkbox_field(container, input_el)
                if field:
                    field["section_name"] = "main"
                    results.append(field)
            except Exception as e:
                logging.error(f"[Checkbox #{idx}] Error: {e}")
    except Exception as e:
        logging.error(f"Error extracting checkbox fields: {e}")
    
    return results
