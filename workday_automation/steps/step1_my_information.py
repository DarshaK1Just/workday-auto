# from playwright.async_api import Page
# from utils.parser import CONFIG
# async def fill_my_information(page: Page, config: dict = CONFIG) -> bool:
#     try:
#         print("📄 Step 1: My Information")

#         # --- How Did You Hear About Us ---
#         try:
#             print("📬 Selecting multiple sources in 'How Did You Hear About Us?'")
#             source_container = page.locator('[data-automation-id="multiselectInputContainer"]').nth(0)
#             await source_container.click()
#             await page.wait_for_timeout(2000)

#             options = config['step1']['hear_about_us']
#             for option in options:
#                 try:
#                     await page.get_by_role("option", name=option).click()
#                     await page.wait_for_timeout(2000)
#                 except:
#                     print(f"⚠️ Option '{option}' not found")

#             await page.mouse.click(0, 0)  # Dismiss dropdown
#         except Exception as e:
#             print(f"⚠️ Dropdown 'How Did You Hear About Us?' failed: {e}")

#         # --- Previous GM Employment ---
#         try:
#             await page.get_by_role("radio", name="No").click()
#             await page.wait_for_timeout(2000)
#         except:
#             print("⚠️ Could not select 'No' for GM employment")

#         # --- Legal Name ---
#         try:
#             await page.fill('#name--legalName--firstName', config['step1']['first_name'])
#             await page.wait_for_timeout(2000)
#             await page.fill('#name--legalName--lastName', config['step1']['last_name'])
#             await page.wait_for_timeout(2000)
#         except:
#             print("⚠️ Could not fill legal name")

#         # --- Address Information ---
#         try:
#             await page.locator('[data-automation-id="formField-addressLine1"] input').fill(config['step1']['address_line1'])
#             await page.wait_for_timeout(2000)
#             await page.locator('[data-automation-id="formField-city"] input').fill(config['step1']['city'])
#             await page.wait_for_timeout(2000)

#             await page.locator('[name="countryRegion"]').click()
#             await page.get_by_role("option", name=config['step1']['state']).click()
#             await page.mouse.click(0, 0)
#             await page.wait_for_timeout(2000)

#             await page.locator('[data-automation-id="formField-postalCode"] input').fill(config['step1']['postal_code'])
#             await page.wait_for_timeout(2000)
            
#             # For GAP only            
#             # await page.locator('[data-automation-id="formField-regionSubdivision1"] input').fill(config['step1']['country'])
#             # await page.wait_for_timeout(2000)
#         except:
#             print("⚠️ Could not fill address fields")

#         # --- Phone Information ---
#         try:
#             await page.locator('[name="phoneType"]').click()
#             await page.wait_for_timeout(2000)
#             await page.get_by_role("option", name=config['step1']['phone_type'], exact=True).click()
#             await page.mouse.click(0, 0)
#             await page.wait_for_timeout(2000)
#             await page.locator('[name="phoneNumber"]').fill(config['step1']['phone_number'])
#         except:
#             print("⚠️ Could not fill phone info")

#         # --- Save and Continue ---
#         try:
#             await page.click('button[data-automation-id="pageFooterNextButton"]')
#             print("✅ Clicked 'Save and Continue'.")
#             print("✅ Step 1 completed.")
#             return True
#         except:
#             print("❌ Could not click Save and Continue.")
#             return False

#     except Exception as e:
#         print(f"❌ Step 1 failed: {e}")
#         try:
#             await page.screenshot(path="step1_failed.png")
#         except Exception as ss_err:
#             print(f"⚠️ Screenshot failed: {ss_err}")
#         return False


# from playwright.async_api import Page
# from utils.parser import CONFIG
# from utils.extractor import extract_all_form_fields

# LABEL_TO_CONFIG_KEY = {
#     "How Did You Hear About Us?": "hear_about_us",
#     "Have you previously worked for NVIDIA as an employee or contractor?": "previous_worker",
#     # "Have you ever worked for Gap Inc as a full time, part time, seasonal or contract worker? If you are an internal applicant, please apply through the company portal on Workday via the Jobs Hub.": "previous_worker",
#     "First Name": "first_name",
#     "Last Name": "last_name",
#     "Address Line 1": "address_line1",
#     "City": "city",
#     "State": "state",
#     "Postal Code": "postal_code",
#     "Country Phone Code": "country",
#     "County": "county",
#     "Phone Device Type": "phone_type", 
#     "Phone Number": "phone_number",
#     "Phone Extension": "phone_extension",
#     "I have a preferred name": "preferred_name",
#     # "Have you previously been employed by GM?": "gm_employment",
# }

# async def fill_my_information(page: Page, config: dict) -> bool:
#     try:
#         print("📄 Step 1: My Information")
#         form_fields = await extract_all_form_fields(page)

#         for field in form_fields:
#             label = field["label"]
#             field_type = field["type_of_input"]
#             input_id = field["id_of_input_component"]
#             config_key = LABEL_TO_CONFIG_KEY.get(label)

#             if not config_key:
#                 # Skip silently if label is "Unknown"
#                 if label == "Unknown":
#                     continue
#                 print(f"⚠️ No config mapping for label: '{label}'")
#                 continue

#             user_value = config['step1'].get(config_key)
#             if user_value is None:
#                 print(f"⚠️ No user value for: '{label}' (key: {config_key})")
#                 continue

#             try:
#                 selector = f'[id="{input_id}"]'

#                 # --- Text Field ---
#                 if field_type == "text":
#                     field_el = page.locator(selector)
#                     await field_el.click()
#                     await page.wait_for_timeout(300)
#                     await field_el.fill(user_value)

#                 # --- Radio Button ---
#                 elif field_type == "radio":
#                     await page.get_by_role("radio", name=user_value, exact=True).click()

#                 # --- Checkbox ---
#                 elif field_type == "checkbox":
#                     checkbox = page.locator(selector)
#                     is_checked = await checkbox.is_checked()
#                     should_check = str(user_value).lower() == "yes"
#                     if should_check != is_checked:
#                         await checkbox.click()

#                 # --- Dropdown ---
#                 elif field_type == "dropdown-button":
#                     await page.locator(selector).click()
#                     await page.wait_for_timeout(300)

#                     option = page.get_by_role("option", name=user_value)
#                     try:
#                         await option.click(timeout=3000)
#                     except:
#                         # Skip fallback message for specific labels like "Country"
#                         if label != "Country":
#                             print(f"⚠️ Retrying with fallback for dropdown: {label}")
#                         fallback = page.locator("div[role='option']").filter(has_text=user_value.split()[0])
#                         await fallback.first.click()

#                     await page.mouse.click(0, 0)

#                 # --- Multi-select ---
#                 elif field_type == "multi-select":
#                     if not isinstance(user_value, list):
#                         print(f"⚠️ Expected list for multi-select '{label}', got: {user_value}")
#                         continue

#                     try:
#                         print(f"📬 Selecting multiple options for '{label}'")
#                         container = page.locator(selector)
#                         input_box = container.locator("input")

#                         await input_box.click()

#                         for val in user_value:
#                             try:
#                                 await page.get_by_role("option", name=val).click()
#                                 await page.wait_for_timeout(500)
#                             except:
#                                 await page.locator(f'div[role="option"] >> text="{val}"').first.click()
#                                 print(f"✅ Selected fallback option: {val}")

#                         await page.mouse.click(0, 0)

#                     except Exception as e:
#                         print(f"⚠️ Multi-select field '{label}' failed: {e}")

#             except Exception as fill_err:
#                 print(f"❌ Failed to fill field '{label}' ({field_type}): {fill_err}")

#         # --- Save and Continue ---
#         try:
#             await page.click('button[data-automation-id="pageFooterNextButton"]')
#             print("✅ Clicked 'Save and Continue'. Step 1 complete.")
#             return True
#         except Exception as e:
#             print(f"❌ Could not click 'Save and Continue': {e}")
#             return False

#     except Exception as e:
#         print(f"❌ Step 1 failed: {e}")
#         try:
#             await page.screenshot(path="step1_failed.png")
#         except Exception as ss_err:
#             print(f"⚠️ Screenshot failed: {ss_err}")
#         return False


from playwright.async_api import Page
from utils.parser import CONFIG
from utils.extractor import extract_all_form_fields

LABEL_TO_CONFIG_KEY = {
    "How Did You Hear About Us?": "hear_about_us",
    "Have you previously worked for NVIDIA as an employee or contractor?": "previous_worker",
    "Have you previously been employed by GM?": "gm_employment",
    "First Name": "first_name",
    "Last Name": "last_name",
    "Address Line 1": "address_line1",
    "City": "city",
    "State": "state",
    "Postal Code": "postal_code",
    "Country": "country",
    "County": "county",
    "Country Phone Code": "country",  # same value reused
    "Phone Device Type": "phone_type", 
    "Phone Number": "phone_number",
    "Phone Extension": "phone_extension",
    "I have a preferred name": "preferred_name",
}

async def fill_my_information(page: Page, config: dict = CONFIG) -> bool:
    try:
        print("📄 Step 1: My Information")
        form_fields = await extract_all_form_fields(page)

        for field in form_fields:
            label = field["label"]
            field_type = field["type_of_input"]
            input_id = field["id_of_input_component"]
            config_key = LABEL_TO_CONFIG_KEY.get(label)

            if label == "Unknown" or not input_id:
                continue

            if not config_key:
                print(f"⚠️ No config mapping for label: '{label}'")
                continue

            user_value = config['step1'].get(config_key)
            if user_value is None:
                print(f"⚠️ No user value for: '{label}' (key: {config_key})")
                continue

            try:
                selector = f'[id="{input_id}"]'

                # --- Text Field ---
                if field_type == "text":
                    field_el = page.locator(selector)
                    await field_el.click()
                    await page.wait_for_timeout(300)
                    await field_el.fill(user_value)

                # --- Radio Button ---
                elif field_type == "radio":
                    await page.get_by_role("radio", name=user_value, exact=True).click()

                # --- Checkbox ---
                elif field_type == "checkbox":
                    checkbox = page.locator(selector)
                    is_checked = await checkbox.is_checked()
                    should_check = str(user_value).lower() in ["yes", "true", "1"]
                    if should_check != is_checked:
                        await checkbox.click()

                # --- Dropdown ---
                elif field_type == "dropdown-button":
                    await page.locator(selector).click()
                    await page.wait_for_timeout(300)

                    try:
                        await page.get_by_role("option", name=user_value, exact=True).click(timeout=3000)
                    except:
                        print(f"⚠️ Retrying with fallback for dropdown: {label}")
                        fallback = page.locator(f'div[role="option"]:has-text("{user_value}")')
                        await fallback.first.click(timeout=3000)

                    await page.mouse.click(0, 0)

                # --- Multi-select ---
                elif field_type == "multi-select":
                    if not isinstance(user_value, list):
                        print(f"⚠️ Expected list for multi-select '{label}', got: {user_value}")
                        continue

                    try:
                        print(f"📬 Selecting multiple options for '{label}'")
                        container = page.locator(selector)
                        input_box = container.locator("input")

                        await input_box.click()

                        for val in user_value:
                            try:
                                await page.get_by_role("option", name=val).click()
                                await page.wait_for_timeout(500)
                            except:
                                await page.locator(f'div[role="option"] >> text="{val}"').first.click()
                                print(f"✅ Selected fallback option: {val}")

                        await page.mouse.click(0, 0)

                    except Exception as e:
                        print(f"⚠️ Multi-select field '{label}' failed: {e}")

            except Exception as fill_err:
                print(f"❌ Failed to fill field '{label}' ({field_type}): {fill_err}")

        # --- Save and Continue ---
        try:
            await page.click('button[data-automation-id="pageFooterNextButton"]')
            print("✅ Clicked 'Save and Continue'. Step 1 complete.")
            return True
        except Exception as e:
            print(f"❌ Could not click 'Save and Continue': {e}")
            return False

    except Exception as e:
        print(f"❌ Step 1 failed: {e}")
        try:
            await page.screenshot(path="step1_failed.png")
        except Exception as ss_err:
            print(f"⚠️ Screenshot failed: {ss_err}")
        return False
