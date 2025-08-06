from playwright.async_api import Page
from utils.parser import CONFIG


async def _choose_from_dropdown(page: Page, field_id: str, option_text: str) -> bool:
    """Open a dropdown and pick an option (exact match)."""
    try:
        # Wait for the dropdown to be available
        await page.wait_for_timeout(500)
        
        # Try different selector strategies for the dropdown
        dropdown_selectors = [
            f'[id="{field_id}"]',
            f'[name="{field_id}"]',
            f'[data-automation-id="{field_id}"]',
            # For the specific IDs in your extracted data
            f'[id="personalInfoPerson--{field_id.replace("personalInfoPerson--", "")}"]' if "personalInfoPerson--" not in field_id else f'[id="{field_id}"]'
        ]
        
        dropdown = None
        for selector in dropdown_selectors:
            try:
                dropdown = page.locator(selector)
                if await dropdown.count() > 0:
                    break
            except:
                continue
        
        if dropdown is None or await dropdown.count() == 0:
            print(f"   ⚠️  Could not find dropdown with ID: {field_id}")
            return False
            
        # Click to open dropdown
        await dropdown.click()
        await page.wait_for_timeout(500)
        
        # Select the option
        await page.get_by_role("option", name=option_text, exact=True).click()
        await page.wait_for_timeout(500)
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Error selecting dropdown option: {e}")
        return False


async def _handle_checkbox(page: Page, field_id: str, should_check: bool) -> bool:
    """Handle checkbox fields."""
    try:
        # Try different selector strategies for checkboxes
        checkbox_selectors = [
            f'[id="{field_id}"]',
            f'[name="{field_id}"]',
            f'[data-automation-id="{field_id}"]',
            # Common checkbox patterns
            'input[name="acceptTermsAndAgreements"]',
            'input[data-automation-id="createAccountCheckbox"]'
        ]
        
        checkbox = None
        for selector in checkbox_selectors:
            try:
                checkbox = page.locator(selector)
                if await checkbox.count() > 0:
                    break
            except:
                continue
        
        if checkbox is None or await checkbox.count() == 0:
            print(f"   ⚠️  Could not find checkbox with ID: {field_id}")
            return False
        
        # Check or uncheck based on requirement
        if should_check:
            if not await checkbox.is_checked():
                await checkbox.check()
                print(f"   ✔  Checkbox checked: {field_id}")
        else:
            if await checkbox.is_checked():
                await checkbox.uncheck()
                print(f"   ✔  Checkbox unchecked: {field_id}")
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Error handling checkbox: {e}")
        return False


async def fill_voluntary_disclosures(page: Page, config: dict = CONFIG, extracted_form_data: dict = None) -> bool:
    """
    Dynamic Step 4: Voluntary Disclosures.
    Works with extracted form data to dynamically fill any fields present.
    """
    try:
        print("🛂  Step 4 – Voluntary Disclosures (Dynamic)")

        # Get step4 config data
        step4_config = config.get("step4", {})
        if not step4_config:
            print("⚠️  No step4 config found; attempting to continue...")
            await page.click('button[data-automation-id="pageFooterNextButton"]')
            return True

        # If we have extracted form data, use it to guide filling
        if extracted_form_data and "Voluntary Disclosures" in extracted_form_data:
            voluntary_fields = extracted_form_data["Voluntary Disclosures"]
            
            for field in voluntary_fields:
                field_label = field.get("label", "")
                field_id = field.get("id_of_input_component")
                field_type = field.get("type_of_input", "")
                field_options = field.get("options", [])
                is_required = field.get("required", False)
                
                if not field_id:
                    print(f"   ⚠️  Skipping field '{field_label}' - no ID found")
                    continue
                
                print(f"🔄  Processing field: {field_label} (ID: {field_id}, Type: {field_type})")
                
                # Handle different field types
                if field_type == "dropdown-button":
                    # Map config values to form fields
                    config_value = None
                    
                    # Primary Nationality
                    if "nationality" in field_id.lower() or "nationality" in field_label.lower():
                        config_value = step4_config.get("nationality")
                    
                    # Gender
                    elif "gender" in field_id.lower() or "gender" in field_label.lower():
                        config_value = step4_config.get("gender")
                    
                    # Ethnicity (if present)
                    elif "ethnicity" in field_id.lower() or "ethnicity" in field_label.lower():
                        config_value = step4_config.get("ethnicity")
                    
                    # Veteran Status (if present)
                    elif "veteran" in field_id.lower() or "veteran" in field_label.lower():
                        config_value = step4_config.get("veteran_status")
                    
                    if config_value and config_value in field_options:
                        print(f"   🎯  Selecting '{config_value}' for {field_label}")
                        success = await _choose_from_dropdown(page, field_id, config_value)
                        if success:
                            print(f"   ✔  {field_label} → {config_value}")
                        else:
                            print(f"   ❌  Failed to select {field_label}")
                    else:
                        print(f"   ⚠️  No matching config value for {field_label}")
                        if config_value:
                            print(f"        Config value '{config_value}' not in options: {field_options[:5]}...")
                
                elif field_type == "checkbox":
                    # Handle consent/terms checkboxes
                    if "terms" in field_label.lower() or "consent" in field_label.lower() or "agree" in field_label.lower():
                        should_check = step4_config.get("consent", False)
                        print(f"   ☑️  Processing consent checkbox: {should_check}")
                        success = await _handle_checkbox(page, field_id, should_check)
                        if success:
                            print(f"   ✔  Consent checkbox processed")
                        else:
                            print(f"   ❌  Failed to process consent checkbox")
                
                # Add small delay between fields
                await page.wait_for_timeout(300)
        
        else:
            # Fallback to original hardcoded approach if no extracted data
            print("📋  Using fallback hardcoded approach...")
            
            # Nationality
            if step4_config.get("nationality"):
                try:
                    print("🌍  Selecting nationality...")
                    nationality_dropdown = page.locator('[id="personalInfoPerson--nationality"]')
                    await _choose_from_dropdown(page, "personalInfoPerson--nationality", step4_config["nationality"])
                    print(f"   ✔  Nationality → {step4_config['nationality']}")
                except Exception as e:
                    print(f"   ⚠️  Nationality selection failed: {e}")
            
            # Gender
            if step4_config.get("gender"):
                try:
                    print("🚻  Selecting gender...")
                    await _choose_from_dropdown(page, "personalInfoPerson--gender", step4_config["gender"])
                    print(f"   ✔  Gender → {step4_config['gender']}")
                except Exception as e:
                    print(f"   ⚠️  Gender selection failed: {e}")
            
            # Consent checkbox
            if step4_config.get("consent"):
                try:
                    print("☑️  Processing consent...")
                    await _handle_checkbox(page, "termsAndConditions--acceptTermsAndAgreements", True)
                    print("   ✔  Consent processed")
                except Exception as e:
                    print(f"   ⚠️  Consent processing failed: {e}")

        # Wait a moment before proceeding
        await page.wait_for_timeout(1000)
        
        # Click Next/Save and Continue button
        try:
            next_button_selectors = [
                'button[data-automation-id="pageFooterNextButton"]',
                'button[data-automation-id="continueButton"]',
                'button:has-text("Save and Continue")',
                'button:has-text("Continue")',
                'button:has-text("Next")'
            ]
            
            button_clicked = False
            for selector in next_button_selectors:
                try:
                    button = page.locator(selector)
                    if await button.count() > 0:
                        await button.click()
                        button_clicked = True
                        print("   ✔  Clicked continue button")
                        break
                except:
                    continue
            
            if not button_clicked:
                print("   ⚠️  Could not find continue button, trying generic approach...")
                await page.keyboard.press("Tab")
                await page.keyboard.press("Enter")
            
        except Exception as e:
            print(f"   ⚠️  Error clicking continue button: {e}")
        
        print("✅  Step 4 completed successfully")
        return True

    except Exception as top_err:
        print(f"❌  Step 4 FAILED: {top_err}")
        try:
            await page.screenshot(path="step4_failed.png")
            print("📸  Screenshot saved: step4_failed.png")
        except Exception:
            pass
        return False


# Alternative wrapper function that accepts extracted form data
async def fill_voluntary_disclosures_dynamic(page: Page, extracted_form_data: dict, config: dict = CONFIG) -> bool:
    """
    Wrapper function that explicitly accepts extracted form data.
    """
    return await fill_voluntary_disclosures(page, config, extracted_form_data)
