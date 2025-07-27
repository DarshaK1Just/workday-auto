"""
Updated Step 2 form filler that uses extracted form data structure
to dynamically fill work experience, education, and other sections.
"""

from playwright.async_api import Page
from utils.parser import CONFIG
from utils.extractor import extract_all_form_fields
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def fill_field_by_extracted_data(page: Page, field_data: dict, value: str) -> bool:
    """
    Fill a single field based on extracted field data structure.
    
    Args:
        page: Playwright page object
        field_data: Extracted field information from extractor
        value: Value to fill in the field
    
    Returns:
        bool: Success status
    """
    try:
        field_id = field_data["id_of_input_component"]
        field_type = field_data["type_of_input"]
        field_label = field_data["label"]
        
        logging.info(f"Filling field: {field_label} ({field_type}) with value: {value}")
        
        if field_type == "text":
            await page.fill(f'[id="{field_id}"]', value)
            await page.wait_for_timeout(500)
            
        elif field_type == "textarea":
            await page.fill(f'[id="{field_id}"]', value)
            await page.wait_for_timeout(500)
            
        elif field_type == "checkbox":
            checkbox = page.locator(f'[id="{field_id}"]')
            is_checked = await checkbox.is_checked()
            should_check = value.lower() in ['true', 'yes', '1', 'on']
            
            if should_check and not is_checked:
                await checkbox.check()
            elif not should_check and is_checked:
                await checkbox.uncheck()
            await page.wait_for_timeout(300)
            
        elif field_type == "date":
            # Handle MM/YYYY date format
            if "/" in value:
                month, year = value.split("/")
                # Find month and year inputs within the date field
                date_container = page.locator(f'[id="{field_id}"]')
                month_input = date_container.locator('input[aria-label="Month"]')
                year_input = date_container.locator('input[aria-label="Year"]')
                
                if await month_input.count() > 0:
                    await month_input.fill(month)
                if await year_input.count() > 0:
                    await year_input.fill(year)
                await page.wait_for_timeout(500)
            
        elif field_type in ["dropdown-button", "radio"]:
            # Click the field and select the option
            field_element = page.locator(f'[id="{field_id}"]')
            await field_element.click()
            await page.wait_for_timeout(300)
            
            # Try to find and click the option
            option_selectors = [
                f'[role="option"]:has-text("{value}")',
                f'[data-automation-id="picklistOption"]:has-text("{value}")',
                f'label:has-text("{value}")'
            ]
            
            for selector in option_selectors:
                try:
                    option = page.locator(selector)
                    if await option.count() > 0:
                        await option.click()
                        await page.wait_for_timeout(300)
                        break
                except:
                    continue
            
        elif field_type in ["single-file", "multiple-file"]:
            # Handle file uploads
            file_input = page.locator(f'[id="{field_id}"]')
            if await file_input.count() == 0:
                # Try alternative selector for file input
                file_input = page.locator('input[type="file"]').first
            
            if await file_input.count() > 0:
                await file_input.set_input_files(value)
                await page.wait_for_timeout(1000)
                logging.info(f"File uploaded: {value}")
            
        elif field_type == "multi-select":
            # Handle multi-select fields
            field_element = page.locator(f'[id="{field_id}"]')
            await field_element.click()
            await page.wait_for_timeout(300)
            
            # If value is a list, select multiple options
            values = [value] if isinstance(value, str) else value
            for val in values:
                try:
                    option = page.locator(f'[data-automation-id="promptOption"]:has-text("{val}")')
                    if await option.count() > 0:
                        await option.click()
                        await page.wait_for_timeout(300)
                except:
                    continue
            
            # Click outside to close dropdown
            await page.mouse.click(0, 0)
            
        return True
        
    except Exception as e:
        logging.error(f"Error filling field {field_data.get('label', 'unknown')}: {e}")
        return False

async def fill_dynamic_section(page: Page, section_name: str, section_data: list, config_data: list) -> bool:
    """
    Fill a dynamic section (Work Experience, Education) with multiple entries.
    
    Args:
        page: Playwright page object
        section_name: Name of the section (e.g., "Work Experience")
        section_data: Extracted field data for this section
        config_data: Configuration data to fill
    
    Returns:
        bool: Success status
    """
    try:
        logging.info(f"Filling dynamic section: {section_name}")
        
        # First, delete any existing entries
        delete_buttons = await page.locator('button:has-text("Delete")').all()
        for btn in delete_buttons:
            try:
                await btn.click()
                await page.wait_for_timeout(300)
            except:
                continue
        
        # Add entries based on config data
        for entry_idx, entry_config in enumerate(config_data):
            logging.info(f"Adding {section_name} entry {entry_idx + 1}")
            
            # Click "Add Another" or "Add" button for this section
            section_id = section_name.replace(" ", "-") + "-section"
            add_button = page.locator(f'div[aria-labelledby="{section_id}"] [data-automation-id="add-button"]')
            
            if await add_button.count() > 0:
                await add_button.click()
                await page.wait_for_timeout(500)
                
                # Wait for form fields to appear
                await page.wait_for_selector('[data-automation-id^="formField-"]', timeout=5000)
                
                # Re-extract fields to get the new form structure
                current_fields = await extract_all_form_fields(page, exclude_dynamic_sections=True)
                
                # Fill fields for this entry
                await fill_section_entry(page, current_fields, entry_config, section_name)
        
        return True
        
    except Exception as e:
        logging.error(f"Error filling dynamic section {section_name}: {e}")
        return False

async def fill_section_entry(page: Page, fields: list, entry_config: dict, section_name: str) -> bool:
    """
    Fill a single entry in a dynamic section.
    
    Args:
        page: Playwright page object
        fields: Current form fields
        entry_config: Configuration for this entry
        section_name: Name of the section
    
    Returns:
        bool: Success status
    """
    try:
        # Create field mapping based on common patterns
        field_mappings = {
            # Work Experience mappings
            "Job Title": "job_title",
            "Company": "company", 
            "Location": "location",
            "I currently work here": "currently_work_here",
            "From": "start_date",
            "To": "end_date", 
            "Role Description": "description",
            
            # Education mappings
            "School Name": "school",
            "School": "school",  # Alternative label
            "Degree": "degree",
            "Field of Study": "field_of_study",
            "Grade Average": "grade",
            "Grade": "grade",  # Alternative label
            
            # Resume mappings
            "Upload a file": "resume_path",
            "Upload a file (5MB max)": "resume_path"
        }
        
        for field in fields:
            field_label = field["label"]
            config_key = field_mappings.get(field_label)
            
            if config_key and config_key in entry_config:
                config_value = entry_config[config_key]
                
                # Handle special cases
                if config_key in ["start_date", "end_date"]:
                    # Combine month and year for date fields
                    if config_key == "start_date":
                        month = entry_config.get("start_month", "")
                        year = entry_config.get("start_year", "")
                        config_value = f"{month}/{year}" if month and year else ""
                    elif config_key == "end_date" and not entry_config.get("currently_work_here", False):
                        month = entry_config.get("end_month", "")
                        year = entry_config.get("end_year", "")
                        config_value = f"{month}/{year}" if month and year else ""
                    else:
                        continue  # Skip end date if currently working
                
                elif config_key == "currently_work_here":
                    config_value = str(config_value).lower()
                
                elif config_key == "school":
                    # For school fields, prefer school_option if available (for dropdown matching)
                    if "school_option" in entry_config and field["type_of_input"] in ["dropdown-button", "multi-select"]:
                        config_value = entry_config["school_option"]
                    else:
                        config_value = entry_config["school"]
                
                # Fill the field
                if config_value:
                    success = await fill_field_by_extracted_data(page, field, str(config_value))
                    if success:
                        logging.info(f"✅ Filled {field_label}: {config_value}")
                    else:
                        logging.warning(f"⚠️ Failed to fill {field_label}: {config_value}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error filling section entry: {e}")
        return False

async def fill_my_experience(page: Page, config: dict = CONFIG) -> bool:
    """
    Main function to fill Step 2: My Experience using extracted form data.
    
    Args:
        page: Playwright page object
        config: Configuration dictionary with step2 data structure
    
    Returns:
        bool: Success status
    """
    try:
        logging.info("💼 Step 2: My Experience - Starting form fill")
        
        # Wait for page to load
        await page.wait_for_timeout(2000)
        
        # Get step2 configuration data
        step2_config = config.get("step2", {})
        if not step2_config:
            logging.error("No step2 configuration found in config")
            return False
        
        # Extract all form fields first
        all_fields = await extract_all_form_fields(page)
        logging.info(f"Extracted {len(all_fields)} form fields")
        
        # Group fields by section
        sections = {}
        for field in all_fields:
            section = field.get("section_name", "main")
            if section not in sections:
                sections[section] = []
            sections[section].append(field)
        
        # Fill Work Experience (multiple entries)
        work_experience_data = step2_config.get("work_experience", [])
        if work_experience_data:
            logging.info(f"Filling {len(work_experience_data)} work experience entries")
            await fill_dynamic_section(
                page, 
                "Work Experience", 
                sections.get("Work Experience", []),
                work_experience_data
            )
        
        # Fill Education (multiple entries)
        education_data = step2_config.get("education", [])
        if education_data:
            logging.info(f"Filling {len(education_data)} education entries")
            await fill_dynamic_section(
                page,
                "Education",
                sections.get("Education", []), 
                education_data
            )
        
        # Fill Resume Upload (main section fields)
        resume_path = step2_config.get("resume_path")
        if resume_path:
            logging.info(f"Uploading resume: {resume_path}")
            main_fields = sections.get("main", [])
            for field in main_fields:
                if field["type_of_input"] in ["single-file", "multiple-file"]:
                    await fill_field_by_extracted_data(page, field, resume_path)
                    break  # Only upload to first file field found
        
        # Fill Language section if present
        language_data = step2_config.get("language", {})
        if language_data:
            logging.info("Filling language information")
            main_fields = sections.get("main", [])
            
            # Handle language selection
            language_name = language_data.get("language", "")
            proficiency_level = language_data.get("proficiency", "")
            
            for field in main_fields:
                field_label_lower = field["label"].lower()
                
                # Language field
                if "language" in field_label_lower and "proficiency" not in field_label_lower:
                    if field["type_of_input"] in ["dropdown-button", "multi-select", "radio"]:
                        await fill_field_by_extracted_data(page, field, language_name)
                
                # Proficiency fields (might be multiple for different skills)
                elif "proficiency" in field_label_lower or any(skill in field_label_lower 
                    for skill in ["comprehension", "overall", "reading", "speaking", "writing"]):
                    if field["type_of_input"] in ["dropdown-button", "radio"]:
                        await fill_field_by_extracted_data(page, field, proficiency_level)
        
        # Wait a bit before clicking next
        await page.wait_for_timeout(1000)
        
        # Click Next/Continue button
        try:
            next_button = page.locator('button[data-automation-id="pageFooterNextButton"]')
            if await next_button.count() > 0:
                await next_button.click()
                await page.wait_for_timeout(2000)  # Wait for navigation
                logging.info("✅ Step 2 completed - clicked Next button")
            else:
                # Try alternative selectors for next button
                alt_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Continue")',
                    'button[type="submit"]',
                    '.css-button:has-text("Next")'
                ]
                
                for selector in alt_selectors:
                    try:
                        alt_button = page.locator(selector)
                        if await alt_button.count() > 0:
                            await alt_button.click()
                            await page.wait_for_timeout(2000)
                            logging.info(f"✅ Step 2 completed - clicked Next button using {selector}")
                            break
                    except:
                        continue
                else:
                    logging.warning("Next button not found with any selector")
        except Exception as e:
            logging.error(f"Error clicking Next button: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Step 2 failed: {e}")
        try:
            await page.screenshot(path="step2_failed.png")
            logging.info("Screenshot saved: step2_failed.png")
        except Exception as ss_err:
            logging.error(f"⚠️ Screenshot failed: {ss_err}")
        return False

# Helper function for compatibility with existing code
async def section_exists(page: Page, section_id: str, idx: int) -> bool:
    """Check if a dynamic section entry exists."""
    return await page.locator(f"div[aria-labelledby='{section_id}-{idx}-panel']").is_visible()

async def click_add(page: Page, section: str) -> None:
    """Click the Add button for a dynamic section."""
    await page.locator(f"div[aria-labelledby='{section}-section'] button[data-automation-id='add-button']").click()
    await page.wait_for_timeout(500)
