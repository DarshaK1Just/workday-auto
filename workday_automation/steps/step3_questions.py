from playwright.async_api import Page
from utils.parser import CONFIG
from utils.extractor import extract_all_form_fields
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Timeout constants
TIMEOUTS = {
    "short": 1000,      # 1 second
    "medium": 3000,     # 3 seconds  
    "long": 5000,       # 5 seconds
    "dropdown": 2000,   # 2 seconds for dropdown
    "animation": 500    # 0.5 seconds for animations
}

async def fill_input_field(page: Page, field: dict, value: str | bool):
    """Fill a single form field based on its type."""
    field_id = field['id_of_input_component']
    field_label = field.get('label', 'Unknown')
    field_type = field.get('type_of_input', 'unknown')
    
    if not field_id:
        logging.warning(f"⚠️ Skipping field '{field_label}' - no ID found")
        return False
    
    try:
        if field_type == "dropdown-button":
            # Handle dropdown buttons (Yes/No questions)
            button_locator = page.locator(f"button[id='{field_id}']")
            
            # Wait for button to be visible
            await button_locator.wait_for(state="visible", timeout=TIMEOUTS["medium"])
            
            # Click to open dropdown
            await button_locator.click()
            await page.wait_for_timeout(TIMEOUTS["dropdown"])
            
            try:
                # Wait for options to appear
                await page.wait_for_selector('[role="listbox"] [role="option"], [data-automation-id="picklistOption"]', 
                                           timeout=TIMEOUTS["dropdown"])
                
                # Select the option
                option_clicked = False
                option_selectors = [
                    f'[role="option"]:has-text("{str(value)}")',
                    f'[data-automation-id="picklistOption"]:has-text("{str(value)}")',
                    f'[role="option"]:text-is("{str(value)}")',
                    f'li:has-text("{str(value)}")'
                ]
                
                for selector in option_selectors:
                    try:
                        option = page.locator(selector)
                        if await option.count() > 0:
                            await option.click()
                            option_clicked = True
                            logging.info(f"   ✅ Selected '{value}' for '{field_label}'")
                            break
                    except:
                        continue
                
                if not option_clicked:
                    # Try using get_by_role as fallback
                    await page.get_by_role("option", name=str(value)).click()
                    logging.info(f"   ✅ Selected '{value}' for '{field_label}' (fallback method)")
                
            except Exception as option_error:
                logging.warning(f"   ⚠️ Could not select option '{value}' for '{field_label}': {option_error}")
                # Close dropdown by pressing Escape
                await page.keyboard.press("Escape")
                return False
            
            # Close dropdown by clicking away
            await page.mouse.click(0, 0)
            await page.wait_for_timeout(TIMEOUTS["animation"])
            
        elif field_type == "text":
            # Handle text inputs
            locator = page.locator(f"[id='{field_id}']")
            await locator.wait_for(state="visible", timeout=TIMEOUTS["medium"])
            await locator.click()
            await locator.fill(str(value))
            await page.wait_for_timeout(TIMEOUTS["short"])
            
        elif field_type == "textarea":
            # Handle textarea inputs
            locator = page.locator(f"[id='{field_id}']")
            await locator.wait_for(state="visible", timeout=TIMEOUTS["medium"])
            await locator.click()
            await locator.fill(str(value))
            await page.wait_for_timeout(TIMEOUTS["short"])
            
        elif field_type == "checkbox":
            # Handle checkboxes
            locator = page.locator(f"[id='{field_id}']")
            await locator.wait_for(state="visible", timeout=TIMEOUTS["medium"])
            
            if str(value).lower() in ["yes", "true", "1"]:
                await locator.check()
            else:
                await locator.uncheck()
            await page.wait_for_timeout(TIMEOUTS["short"])
            
        elif field_type == "radio":
            # Handle radio buttons
            radio_locator = page.locator(f"input[type='radio'][value='{value}']")
            if await radio_locator.count() == 0:
                # Try finding by associated label
                radio_locator = page.locator(f"input[type='radio']").filter(has_text=str(value))
            
            await radio_locator.wait_for(state="visible", timeout=TIMEOUTS["medium"])
            await radio_locator.click()
            await page.wait_for_timeout(TIMEOUTS["short"])
            
        else:
            logging.warning(f"⚠️ Unknown field type '{field_type}' for field '{field_label}'")
            return False
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to fill field '{field_label}' (ID: {field_id}, Type: {field_type}): {e}")
        return False

def find_config_value_for_question(question_text: str, config: dict) -> str:
    """
    Match a question to a config value using keywords and patterns.
    This function dynamically maps questions to config values.
    """
    question_lower = question_text.lower()
    
    # Get step3 config
    step3_config = config.get("step3", {})
    
    # Define question patterns and their corresponding config keys
    question_patterns = {
        # Work authorization patterns
        "authorization": [
            "legally authorized to work", 
            "authorized to work", 
            "work authorization", 
            "legal authorization",
            "work legally",
            "employment authorization"
        ],
        
        # Sponsorship patterns
        "sponsorship": [
            "sponsorship", 
            "visa sponsorship", 
            "require sponsorship", 
            "need sponsorship",
            "extend your current work authorization",
            "continue and/or extend your current work authorization"
        ],
        
        # Age patterns
        "age": [
            "18 years of age", 
            "over 18", 
            "at least 18", 
            "18 or older",
            "age of majority"
        ],
        
        # Background check patterns
        "background_check": [
            "background check", 
            "background investigation", 
            "criminal background",
            "background screening"
        ],
        
        # Drug test patterns
        "drug_test": [
            "drug test", 
            "drug screening", 
            "substance test",
            "pre-employment drug"
        ],
        
        # Relocation patterns
        "relocation": [
            "relocate", 
            "relocation", 
            "willing to relocate",
            "able to relocate"
        ],
        
        # Travel patterns
        "travel": [
            "travel", 
            "willing to travel", 
            "business travel",
            "travel required"
        ],
        
        # Notice period patterns
        "notice_period": [
            "notice period", 
            "how much notice", 
            "notice required",
            "start date"
        ],
        
        # Salary patterns
        "salary": [
            "salary", 
            "compensation", 
            "expected salary",
            "salary expectation"
        ]
    }
    
    # Try to match question to a pattern
    for config_key, patterns in question_patterns.items():
        for pattern in patterns:
            if pattern in question_lower:
                config_value = step3_config.get(config_key)
                if config_value is not None:
                    logging.info(f"🎯 Matched question '{question_text[:50]}...' to config key '{config_key}' with value '{config_value}'")
                    return str(config_value)
    
    # If no pattern matches, try direct key matching with question keywords
    question_words = question_lower.split()
    for word in question_words:
        if len(word) > 3:  # Only consider words longer than 3 characters
            config_value = step3_config.get(word)
            if config_value is not None:
                logging.info(f"🎯 Found direct match for word '{word}' with value '{config_value}'")
                return str(config_value)
    
    # Default fallback values based on question content
    if any(keyword in question_lower for keyword in ["authorized", "legal", "work"]):
        return "Yes"  # Default to Yes for work authorization
    elif any(keyword in question_lower for keyword in ["sponsorship", "visa"]):
        return "No"   # Default to No for sponsorship
    elif any(keyword in question_lower for keyword in ["18", "age"]):
        return "Yes"  # Default to Yes for age questions
    elif any(keyword in question_lower for keyword in ["background", "drug", "test"]):
        return "Yes"  # Default to Yes for background/drug test consent
    
    logging.warning(f"⚠️ No matching config found for question: '{question_text}'. Using default 'Yes'")
    return "Yes"  # Safe default

async def fill_application_questions(page: Page, config: dict = CONFIG) -> bool:
    """
    Dynamically fill all application questions found on the page.
    """
    try:
        print("\n❓ Step 3: Application Questions")
        
        # Wait for page to stabilize
        await page.wait_for_timeout(TIMEOUTS["medium"])
        
        # Extract all form fields from the current page
        all_form_data = await extract_all_form_fields(page)
        
        # Filter for Application Questions section
        application_questions = []
        for field in all_form_data:
            # Check if this field belongs to Application Questions section
            section_name = field.get("section_name", "")
            if (section_name == "Application Questions" or 
                section_name == "main" or 
                "questionnaire" in field.get("id_of_input_component", "").lower()):
                
                # Skip fields without proper labels or IDs
                if (field.get("label") and 
                    field.get("label") != "Unknown" and 
                    field.get("id_of_input_component")):
                    application_questions.append(field)
        
        if not application_questions:
            logging.warning("⚠️ No application questions found on this page")
            return True
        
        logging.info(f"📋 Found {len(application_questions)} application questions to fill")
        
        # Fill each question
        filled_count = 0
        for i, field in enumerate(application_questions, 1):
            question_text = field.get("label", "")
            field_id = field.get("id_of_input_component", "")
            field_type = field.get("type_of_input", "")
            is_required = field.get("required", False)
            
            print(f"\n📝 Question {i}: {question_text}")
            print(f"   Type: {field_type} | Required: {is_required} | ID: {field_id}")
            
            # Find the appropriate config value for this question
            config_value = find_config_value_for_question(question_text, config)
            
            print(f"   📌 Using value: '{config_value}'")
            
            # Fill the field
            success = await fill_input_field(page, field, config_value)
            if success:
                filled_count += 1
                print(f"   ✅ Successfully filled")
            else:
                print(f"   ❌ Failed to fill")
                
                # If it's a required field and we failed, this could be problematic
                if is_required:
                    logging.error(f"❌ Failed to fill required field: {question_text}")
            
            # Small delay between fields
            await page.wait_for_timeout(TIMEOUTS["short"])
        
        print(f"\n📊 Summary: Successfully filled {filled_count}/{len(application_questions)} questions")
        
        # Wait before proceeding
        await page.wait_for_timeout(TIMEOUTS["medium"])
        
        # Click Next/Continue button
        print("➡️ Clicking Next button...")
        try:
            # Try different button selectors
            next_button_selectors = [
                'button[data-automation-id="pageFooterNextButton"]',
                'button[data-automation-id="continueButton"]',
                'button:has-text("Next")',
                'button:has-text("Continue")',
                'button[type="submit"]'
            ]
            
            clicked = False
            for selector in next_button_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0 and await button.is_visible():
                        await button.click()
                        clicked = True
                        logging.info(f"✅ Clicked next button using selector: {selector}")
                        break
                except:
                    continue
            
            if not clicked:
                logging.warning("⚠️ Could not find Next/Continue button")
                return False
            
            await page.wait_for_timeout(TIMEOUTS["medium"])
            print("✅ Step 3 completed successfully.")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to click Next button: {e}")
            return False
    
    except Exception as err:
        logging.error(f"❌ Step 3 failed: {err}")
        try:
            await page.screenshot(path="step3_failed.png")
        except Exception as ss_err:
            logging.error(f"⚠️ Screenshot failed: {ss_err}")
        return False

# Alternative simplified version if you prefer direct mapping
async def fill_application_questions_simple(page: Page, config: dict = CONFIG) -> bool:
    """
    Simplified version that directly maps common questions to config values.
    """
    try:
        print("\n❓ Step 3: Application Questions (Simple Mode)")
        
        # Wait for page to stabilize
        await page.wait_for_timeout(TIMEOUTS["medium"])
        
        # Extract form fields
        all_form_data = await extract_all_form_fields(page)
        
        # Get step3 config
        step3_config = config.get("step3", {})
        
        # Direct question mapping
        question_mappings = {
            "Are you legally authorized to work": step3_config.get("authorization", "Yes"),
            "Will you require sponsorship": step3_config.get("sponsorship", "No"),
            "Are you 18 years of age": step3_config.get("age", "Yes"),
            "background check": step3_config.get("background_check", "Yes"),
            "drug test": step3_config.get("drug_test", "Yes"),
            "willing to relocate": step3_config.get("relocation", "No"),
            "willing to travel": step3_config.get("travel", "Yes")
        }
        
        filled_count = 0
        for field in all_form_data:
            if (field.get("section_name") in ["Application Questions", "main"] and 
                field.get("label") and 
                field.get("label") != "Unknown" and
                field.get("id_of_input_component")):
                
                question = field.get("label", "")
                
                # Find matching config value
                config_value = None
                for key_phrase, value in question_mappings.items():
                    if key_phrase.lower() in question.lower():
                        config_value = value
                        break
                
                if config_value:
                    print(f"📝 Filling: {question[:60]}... = {config_value}")
                    success = await fill_input_field(page, field, config_value)
                    if success:
                        filled_count += 1
        
        print(f"✅ Filled {filled_count} questions")
        
        # Click Next
        next_button = page.locator('button[data-automation-id="pageFooterNextButton"]')
        await next_button.click()
        await page.wait_for_timeout(TIMEOUTS["medium"])
        
        return True
        
    except Exception as err:
        logging.error(f"❌ Step 3 (Simple) failed: {err}")
        return False
