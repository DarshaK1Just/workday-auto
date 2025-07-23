"""
Handles the login process for Workday job applications.
Combines best practices from first sample with exact reference patterns from second sample.
"""

import logging
from typing import Any, Dict
from playwright.async_api import Page, TimeoutError

from utils.parser import CONFIG

# --- Constants ---
SIGN_IN_BUTTON = 'button:has-text("Sign In")'
CREATE_ACCOUNT_BUTTON = 'button:has-text("Create Account")'
APPLY_BUTTON = 'button:has-text("Apply")'
APPLY_MANUALLY_BUTTON = 'button:has-text("Apply Manually")'

EMAIL_LABEL = "Email Address"
PASSWORD_LABEL = "Password"
VERIFY_PASSWORD_LABEL = "Verify New Password"
TERMS_CHECKBOX_SELECTOR = '[data-automation-id="createAccountCheckbox"]'
INVALID_CREDENTIALS_SELECTOR = 'div[data-automation-id="errorBanner"]'

# Timeout constants
TIMEOUTS = {
    "page_load": 30000,
    "button_click": 5000,
    "element_wait": 5000,
    "network_idle": 15000
}


async def _navigate_and_load_page(page: Page, config: Dict[str, Any]) -> bool:
    """Navigate to the job URL and handle page loading."""
    logging.info("🔐 Opening job URL …")
    try:
        await page.goto(config["job_url"], timeout=TIMEOUTS["page_load"])
        return True
    except Exception as e:
        logging.error(f"❌ Cannot load job page: {e}")
        return False


async def _click_initial_sign_in(page: Page) -> bool:
    """Click the top-level Sign In button."""
    try:
        logging.info("➡️ Clicking top‑level Sign In …")
        await page.get_by_role("button", name="Sign In").click(timeout=TIMEOUTS["button_click"])
        await page.wait_for_timeout(1000)
        return True
    except TimeoutError:
        logging.error("❌ Top‑level Sign In button not found.")
        return False


async def _perform_existing_account_login(page: Page, config: Dict[str, Any]) -> bool:
    """Handle login for existing accounts."""
    if await page.get_by_role("button", name="Sign In").is_visible():
        logging.info("🔄 Account exists – signing in …")
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_timeout(1000)
        
        try:
            logging.info("🔑 Filling login form …")
            await page.get_by_label(EMAIL_LABEL, exact=True).fill(config["email"])
            await page.wait_for_timeout(1000)
            await page.get_by_label(PASSWORD_LABEL, exact=True).fill(config["password"])
            await page.wait_for_timeout(1000)
            await page.get_by_role("button", name="Sign In", exact=True).click()
            await page.wait_for_timeout(3000)

            # Check for login errors
            if await page.locator("text=Invalid").first.is_visible():
                logging.error("❌ Login rejected – invalid credentials.")
                await page.screenshot(path="login_invalid.png")
                return False

            logging.info("✅ Logged in.")
            return True
        except Exception as e:
            logging.error(f"❌ Sign‑in step failed: {e}")
            await page.screenshot(path="login_failed.png")
            return False
    
    return True  # No existing account login needed


async def _create_new_account(page: Page, config: Dict[str, Any]) -> bool:
    """Handle account creation process."""
    try:
        if await page.get_by_role("button", name="Create Account").is_visible():
            logging.info("🆕 'Create Account' detected – creating new account …")
            await page.get_by_role("button", name="Create Account").click()
            await page.wait_for_timeout(1000)

            # Fill account creation form
            await page.get_by_label(EMAIL_LABEL, exact=True).fill(config["email"])
            await page.wait_for_timeout(1000)
            await page.get_by_label(PASSWORD_LABEL, exact=True).fill(config["password"])
            await page.wait_for_timeout(1000)
            await page.get_by_label(VERIFY_PASSWORD_LABEL, exact=True).fill(config["password"])
            await page.wait_for_timeout(1000)

            # Handle terms checkbox if present
            try:
                checkbox = page.locator(TERMS_CHECKBOX_SELECTOR)
                if not await checkbox.is_checked():
                    await checkbox.check()
                logging.info("✅ Checked 'I Agree' checkbox.")
            except Exception as e:
                logging.warning(f"⚠️ Could not check 'I Agree' checkbox: {e}")

            # Submit account creation
            await page.get_by_role("button", name="Create Account", exact=True).click()
            logging.info("⏳ Waiting for account creation …")
            await page.wait_for_timeout(3000)

            # Handle post-creation sign-in
            return await _handle_post_creation_signin(page, config)
            
    except Exception as e:
        logging.error(f"❌ Account‑creation step failed: {e}")
        await page.screenshot(path="create_account_failed.png")
        return False
    
    return True


async def _handle_post_creation_signin(page: Page, config: Dict[str, Any]) -> bool:
    """Handle sign-in after account creation."""
    # After creation, Workday normally returns to a "Already have an account? Sign In" link
    if await page.get_by_role("button", name="Sign In").is_visible():
        logging.info("🔄 Account created – returning to Sign In …")
        await page.get_by_role("button", name="Sign In").click()
        await page.wait_for_timeout(1000)
        
        # Normal sign-in after account creation
        try:
            logging.info("🔑 Filling login form …")
            await page.get_by_label(EMAIL_LABEL, exact=True).fill(config["email"])
            await page.wait_for_timeout(1000)
            await page.get_by_label(PASSWORD_LABEL, exact=True).fill(config["password"])
            await page.wait_for_timeout(1000)
            await page.get_by_role("button", name="Sign In", exact=True).click()
            await page.wait_for_timeout(3000)

            # Quick sanity check
            if await page.locator("text=Invalid").first.is_visible():
                logging.error("❌ Login rejected – invalid credentials.")
                await page.screenshot(path="login_invalid.png")
                return False

            logging.info("✅ Logged in.")
            return True
        except Exception as e:
            logging.error(f"❌ Sign‑in step failed: {e}")
            await page.screenshot(path="login_failed.png")
            return False
    
    return True


async def _navigate_to_application_form(page: Page) -> bool:
    """Navigate to the job application form by clicking Apply buttons."""
    try:
        logging.info("➡️ Clicking 'Apply' …")
        await page.get_by_role("button", name="Apply").click(timeout=TIMEOUTS["button_click"])
        await page.wait_for_timeout(1000)

        logging.info("📝 Clicking 'Apply Manually' …")
        await page.get_by_role("button", name="Apply Manually").click(timeout=TIMEOUTS["button_click"])
        await page.wait_for_timeout(1500)
        
        return True
    except TimeoutError as e:
        logging.error(f"⚠️ Apply buttons missing: {e}")
        await page.screenshot(path="apply_click_error.png")
        return False


async def login_to_workday(page: Page, config: Dict[str, Any] = CONFIG) -> bool:
    """
    Orchestrates the login process for a Workday job application.
    Combines best practices with exact reference patterns.

    Args:
        page: The Playwright Page object.
        config: A dictionary containing configuration like URL, email, and password.

    Returns:
        True if the entire login and navigation process is successful, False otherwise.
    """
    
    # Step 1: Navigate to job page
    if not await _navigate_and_load_page(page, config):
        return False

    # Step 2: Click initial Sign In button
    if not await _click_initial_sign_in(page):
        return False

    # Step 3: Handle existing account login
    if not await _perform_existing_account_login(page, config):
        return False

    # Step 4: Handle account creation if needed
    if not await _create_new_account(page, config):
        return False

    # Step 5: Navigate to application form
    if not await _navigate_to_application_form(page):
        return False

    logging.info("🎉 Successfully navigated to the manual application page.")
    return True


# --- Alternative implementation using original first sample patterns (commented for reference) ---
"""
async def _navigate_and_sign_in_alternative(page: Page, config: Dict[str, Any]) -> bool:
    # Alternative implementation using locator patterns from first sample
    logging.info(f"Navigating to job URL: {config['job_url']}")
    try:
        await page.goto(config["job_url"], wait_until="networkidle", timeout=45000)
    except TimeoutError:
        logging.error("Timeout while loading the job page.")
        return False

    try:
        logging.info("Clicking top-level 'Sign In' button.")
        await page.locator(SIGN_IN_BUTTON).first.click(timeout=10000)
    except TimeoutError:
        logging.warning("Top-level 'Sign In' button not found or timed out. Assuming already on login page.")

    # Check for email field to confirm we are on login page
    try:
        await page.get_by_label(EMAIL_LABEL, exact=True).wait_for(timeout=5000)
    except TimeoutError:
        logging.error("Could not find the email field on the login page.")
        return False

    logging.info("Filling login form.")
    await page.get_by_label(EMAIL_LABEL, exact=True).fill(config["email"])
    await page.get_by_label(PASSWORD_LABEL, exact=True).fill(config["password"])
    await page.locator(SIGN_IN_BUTTON).last.click()

    try:
        await page.wait_for_load_state("networkidle", timeout=15000)
    except TimeoutError:
        logging.warning("Timeout waiting for network idle after login. Continuing...")

    if await page.locator(INVALID_CREDENTIALS_SELECTOR).is_visible():
        logging.error("Login failed: Invalid credentials.")
        await page.screenshot(path="login_failed.png")
        return False

    logging.info("Login successful.")
    return True
"""
