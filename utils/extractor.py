async def get_form_field_containers(page):
    return await page.locator('[data-automation-id^="formField-"]').all()


async def extract_application_steps(page):
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
        print(f"[Step Extractor] Error: {e}")
    return steps_data


async def extract_all_form_fields(page):
    all_results = []
    seen_labels = set()

    extractors = [
        extract_multiselect_fields,
        extract_radio_fields,
        extract_button_dropdown_fields,
        extract_text_fields,
        extract_checkbox_fields
    ]

    for extractor in extractors:
        fields = await extractor(page)
        for field in fields:
            if field["label"] not in seen_labels:
                all_results.append(field)
                seen_labels.add(field["label"])

    return all_results



async def extract_multiselect_fields(page):
    results = []
    containers = await page.locator('[data-automation-id="multiSelectContainer"]').all()
    for idx, container in enumerate(containers):
        try:
            input_id = await container.get_attribute("id")
            label_el = container.locator('xpath=ancestor::div[contains(@data-automation-id, "formField")]/label')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await container.get_attribute("aria-required") == 'true'
            selected_values = await container.locator('[data-automation-id="pill"]').all_inner_texts()

            all_options = []
            dropdown_button = container.locator('[data-automation-id="dropdownButton"]')
            if await dropdown_button.count() > 0:
                await dropdown_button.click()
                await page.wait_for_selector('[data-automation-id="picklistOption"]', timeout=2000)
                await page.wait_for_timeout(500)
                all_options = await page.locator('[data-automation-id="picklistOption"]').all_inner_texts()
                await dropdown_button.click()

            results.append({
                "label": label,
                "id_of_input_component": input_id,
                "required": is_required,
                "type_of_input": "multi-select",
                "options": all_options,
                "user_data_select_values": selected_values
            })
        except Exception as e:
            print(f"[MultiSelect #{idx}] Error: {e}")
    return results


async def extract_radio_fields(page):
    results = []
    fieldsets = await page.locator("fieldset").all()
    for idx, fieldset in enumerate(fieldsets):
        try:
            label_el = fieldset.locator("legend label")
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await fieldset.get_attribute("aria-required") == 'true'
            radio_items = fieldset.locator('input[type="radio"]')
            options = []
            selected_values = []
            for i in range(await radio_items.count()):
                radio = radio_items.nth(i)
                value = await radio.get_attribute("value")
                input_id = await radio.get_attribute("id")
                label_for_radio = page.locator(f'label[for="{input_id}"]')
                label_text = await label_for_radio.inner_text() if await label_for_radio.count() > 0 else value
                options.append(label_text)
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
            print(f"[Radio #{idx}] Error: {e}")
    return results


async def extract_button_dropdown_fields(page):
    results = []
    containers = await get_form_field_containers(page)
    for idx, container in enumerate(containers):
        try:
            button = container.locator('button[aria-haspopup="listbox"]')
            if await button.count() == 0:
                continue
            input_id = await button.get_attribute("id")
            selected_label = (await button.inner_text()).strip()
            label_el = container.locator(f'label[for="{input_id}"]')
            label_text = await label_el.inner_text() if await label_el.count() > 0 else "Unknown"
            label = label_text.replace("*", "").strip()
            is_required = '*' in label_text or await button.get_attribute("aria-required") == 'true'
            await button.click()
            await page.wait_for_timeout(500)
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
            print(f"[Dropdown Button #{idx}] Error: {e}")
    return results


async def extract_text_fields(page):
    results = []
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
            print(f"[Text Field #{idx}] Error: {e}")
    return results


async def extract_checkbox_fields(page):
    results = []
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
            print(f"[Checkbox #{idx}] Error: {e}")
    return results


async def extract_all_steps_sequentially(page):
    await page.wait_for_timeout(3000)
    steps = await extract_application_steps(page)
    all_step_data = {}

    for step in steps:
        step_name = step["step_name"]
        is_current = step["is_current_step"]
        print(f"[STEP] Found: {step_name} | Current: {is_current}")

        if is_current:
            print(f"→ Extracting data for current step: {step_name}")
            form_data = await extract_all_form_fields(page)
            all_step_data[step_name] = form_data
        else:
            all_step_data[step_name] = []

    return all_step_data

