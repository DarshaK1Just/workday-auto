# 💼 AutoJob.ai – Workday Job Application Automation

This project automates the process of applying to jobs on Workday-powered career portals using Python + Playwright. It dynamically extracts and fills multi-step forms (like NVIDIA, Deloitte, etc.) and submits applications programmatically.

---

## 🚀 Features

- ✅ **Automated Login** (optional MFA/SSO)
- ✅ **"Apply Manually" Workflow**
- ✅ **Multi-step Form Navigation:**
  - My Information
  - My Experience
  - Application Questions
  - Voluntary Disclosures
  - Self Identify
  - Review & Submit
- ✅ **Dynamic Form Extraction:**
  - Labels, input types, options, required flags
  - Text fields, checkboxes, dropdowns, radio buttons, multiselect
- ✅ **Autofill via YAML Configuration**
- ✅ **Headless / Debug Mode Support**
- ✅ **Modular Step-wise Automation**

---

## 🧠 How It Works

1. Launches the job URL
2. Clicks `Apply`, then selects `Apply Manually`
3. Iteratively:
   - Extracts the current form page
   - Matches extracted fields with `form_config.yaml`
   - Autofills and submits
4. Completes the job application automatically

---

## 🛠️ Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
python -m playwright install
```

### 2. Create Your `form_config.yaml`

```yaml
step1:
  first_name: "John"
  last_name: "Doe"
  email: "john.doe@example.com"

step2:
  resume_path: "./resume.pdf"
  experience: "5 years"

step4:
  nationality: "India"
  gender: "Male"
  consent: true
```

### 3. Run the Application Bot

```bash
python -m scripts.run_auto_apply
```

---

Output:

```json
[
  { "label": "Email Address", "type": "text", "id": "input-4" },
  { "label": "Password", "type": "password", "id": "input-5" },
  { "label": "Verify New Password", "type": "password", "id": "input-6" },
  { "label": "I agree", "type": "checkbox", "id": "input-8" }
]
```

---

## 📌 Notes

- Headless mode is enabled by default but can be disabled for debugging.
- Resume upload, radio group selection, and custom widgets are handled dynamically.
- Reusable across companies with different Workday layouts.

---
