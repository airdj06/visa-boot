#!/usr/bin/env python3
import time
import random
import argparse
import sys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

# ---------------------------
# Parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", help="Run Chrome in headless (stealth) mode")
args = parser.parse_args()

# ---------------------------
# Your personal information
# ---------------------------
USER_DATA = {
    "name": "ZITOUNI Alaeddine",
    "dob": "06/11/2001",       # dd/mm/yyyy
    "phone": "+213540195220",
    "email": "alaztn25@gmail.com",
    "passport": "314552941"
}

# ---------------------------
# Human-like helpers
# ---------------------------
def human_sleep(base=0.25, var=0.12):
    """Small randomized pause."""
    t = max(0.01, random.gauss(base, var))
    time.sleep(t)

def human_type(elem, text, delay_mean=0.08, delay_sigma=0.03, clear_first=True):
    """Type text into element character-by-character with tiny random delays."""
    try:
        if clear_first:
            elem.clear()
            human_sleep(0.08, 0.04)
    except Exception:
        pass

    for ch in text:
        try:
            elem.send_keys(ch)
        except Exception:
            try:
                elem.click()
                elem.send_keys(ch)
            except Exception:
                pass
        time.sleep(max(0, random.gauss(delay_mean, delay_sigma)))
    human_sleep(0.12, 0.06)

def human_move_and_click(driver, elem, pre_pause=(0.4,0.2), post_pause=(0.6,0.25), jitter=6):
    """
    Move mouse to element with small jitter then click using ActionChains.
    Falls back to element.click() or JS click if ActionChains fails.
    """
    try:
        # scroll into view first
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", elem)
        except Exception:
            pass

        # slight pause before moving
        time.sleep(max(0, random.gauss(pre_pause[0], pre_pause[1])))

        actions = ActionChains(driver)
        # move to element then tiny offset
        actions.move_to_element(elem)
        offset_x = random.randint(-jitter, jitter)
        offset_y = random.randint(-jitter, jitter)
        actions.move_by_offset(offset_x, offset_y)
        # small human-like pause before click
        actions.pause(max(0.05, random.random() * 0.2))
        actions.click()
        actions.perform()

        time.sleep(max(0, random.gauss(post_pause[0], post_pause[1])))
        return True
    except Exception as e:
        # fallback strategies
        try:
            elem.click()
            human_sleep(0.2, 0.08)
            return True
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", elem)
                human_sleep(0.2, 0.08)
                return True
            except Exception as final_e:
                print("[ERROR] Click failed (all strategies):", final_e)
                return False

def text_contains_any(driver, substrings):
    """Case-insensitive search of page text for any of the substrings list."""
    try:
        body = driver.find_element(By.TAG_NAME, "body").text.lower()
        for s in substrings:
            if s.lower() in body:
                return True
    except Exception:
        pass
    return False

# ---------------------------
# Start browser (undetected if headless requested)
# ---------------------------
print("[INFO] Starting browser...")
driver = None
try:
    if args.headless:
        # use undetected_chromedriver for headless/stealth runs
        try:
            import undetected_chromedriver as uc
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            # Keep window size consistent (some anti-bot checks look for tiny sizes)
            options.add_argument("--window-size=1920,1080")
            driver = uc.Chrome(options=options, headless=True)
        except Exception as e:
            print("[WARN] undetected_chromedriver not available or failed to start:", e)
            print("[WARN] Falling back to regular selenium Chrome (may be detected).")
            raise
    # if not headless or fallback needed, use regular selenium + webdriver_manager
    if driver is None:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        options = webdriver.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # do NOT set headless here for human-like testing; headless may be passed in arg
        if args.headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("--window-size=1920,1080")
        # reduce chrome noise
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
except Exception as e:
    print("[ERROR] Could not start Chrome driver:", e)
    sys.exit(1)

driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 30)
actions = ActionChains(driver)

# ---------------------------
# Main booking function
# ---------------------------
def try_booking():
    # quick check: did the page block us by IP text somewhere?
    try:
        if text_contains_any(driver, ["your ip", "blocked", "blocked by the server", "access denied"]):
            print("[ERROR] Your IP appears blocked. Stopping script.")
            return True  # stop main loop
    except Exception:
        pass

    # open homepage (ensure fresh)
    try:
        driver.get("https://konzinfobooking.mfa.gov.hu/")
        human_sleep(1.2, 0.4)
    except Exception as e:
        print("[ERROR] Could not open site:", e)
        return False

    # STEP 1: Select Consulate (Algiers)
    print("[STEP 1] Selecting consulate: Algeria - Algiers...")
    try:
        human_sleep(1.0, 0.4)
        select_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select location') or contains(.,'Select location')]"))
        )
        if not human_move_and_click(driver, select_btn):
            print("[ERROR] Could not click Select location button.")
            return False
        print("[INFO] Opened consulate selection modal.")

        human_sleep(0.6, 0.2)
        algiers_option = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'Algeria - Algiers') or contains(.,'Algeria - Algiers')]"))
        )
        if not human_move_and_click(driver, algiers_option):
            print("[ERROR] Could not click Algeria - Algiers option.")
            return False
        print("[INFO] Selected: Algeria - Algiers")

        # try to close modal if close button exists
        human_sleep(0.6, 0.2)
        try:
            close_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Close') or contains(text(),'×') or contains(.,'Close')]")
            human_move_and_click(driver, close_btn)
            print("[INFO] Closed consulate selection modal.")
        except Exception:
            print("[INFO] No Close button found, continuing...")

    except Exception as e:
        print("[ERROR] Could not select consulate:", e)
        return False

    human_sleep(1.2, 0.5)

    # STEP 2: Select Visa Type D
    print("[STEP 2] Selecting Visa Type D...")
    try:
        app_type_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select type of application') or contains(.,'Select type of application')]"))
        )
        human_move_and_click(driver, app_type_btn)
        print("[INFO] Opened application type selection modal.")
        human_sleep(1.4, 0.5)

        visa_d_label = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'Visa application (long term; residence permit -D)') or contains(.,'Visa application (long term; residence permit -D)')]"))
        )
        human_move_and_click(driver, visa_d_label)
        print("[INFO] Visa Type D checkbox selected.")
        human_sleep(0.8, 0.35)

        save_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Save') or contains(.,'Save')]"))
        )
        human_move_and_click(driver, save_btn)
        print("[INFO] Saved Visa Type D selection.")

    except Exception as e:
        print("[WARNING] Could not select Visa Type D:", e)
        return False

    human_sleep(1.0, 0.5)

    # STEP 3: Fill Personal Information
    print("[STEP 3] Filling personal details...")
    try:
        # Name
        name_input = wait.until(EC.presence_of_element_located((By.ID, "label4")))
        human_type(name_input, USER_DATA["name"])

        human_sleep(0.6, 0.2)
        # DOB
        dob_input = wait.until(EC.presence_of_element_located((By.ID, "birthDate")))
        human_type(dob_input, USER_DATA["dob"])

        human_sleep(0.6, 0.2)
        # Phone
        phone_input = wait.until(EC.presence_of_element_located((By.ID, "label9")))
        human_type(phone_input, USER_DATA["phone"])

        human_sleep(0.6, 0.2)
        # Email
        email_input = wait.until(EC.presence_of_element_located((By.ID, "label10")))
        human_type(email_input, USER_DATA["email"])

        human_sleep(0.6, 0.2)
        # Re-enter email
        email2_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Re-enter the email address')]/following::input[1]"))
        )
        human_type(email2_input, USER_DATA["email"])

        human_sleep(0.6, 0.2)
        # Passport
        passport_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Passport number')]/following::input[1]"))
        )
        human_type(passport_input, USER_DATA["passport"])
        # blur to trigger any client-side events
        try:
            driver.execute_script("arguments[0].blur();", passport_input)
        except Exception:
            pass

        human_sleep(0.6, 0.3)
        # Consents
        consent1 = wait.until(EC.element_to_be_clickable((By.ID, "slabel13")))
        human_move_and_click(driver, consent1)
        human_sleep(0.4, 0.15)

        consent2 = wait.until(EC.element_to_be_clickable((By.ID, "label13")))
        human_move_and_click(driver, consent2)

        human_sleep(1.0, 0.5)
        # Select date button
        select_date_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select date') or contains(.,'Select date')]"))
        )
        human_move_and_click(driver, select_date_btn)
        print("[INFO] Clicked 'Select date' button.")

        # STEP 4: Check result
        human_sleep(6.0, 2.0)  # wait a bit for the appointment area to load

        # Detect success: appointment step active
        try:
            active_step = driver.find_element(By.XPATH, "//a[@id='idopontvalasztas-tab' and contains(@class,'active')]")
            if active_step:
                print("[SUCCESS] Appointment page opened! 🚀")
                # keep browser open a little so you can inspect manually if not headless
                time.sleep(50)
                return True
        except Exception:
            pass

        # Check for common modals/messages
        if text_contains_any(driver, ["no appointments", "no appointment", "no slots", "no dates available"]):
            print("[INFO] No appointments available. Restarting...")
            try:
                ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'OK') or contains(.,'OK')]")
                human_move_and_click(driver, ok_btn)
            except Exception:
                pass
            return False

        if text_contains_any(driver, ["hcaptcha", "hcaptcha has to be checked", "please verify", "captcha"]):
            print("[INFO] Captcha detected. Manual intervention required.")
            try:
                ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'OK') or contains(.,'OK')]")
                human_move_and_click(driver, ok_btn)
            except Exception:
                pass
            return False

        # if none of the above, we likely got blocked or unexpected state
        if text_contains_any(driver, ["your ip", "blocked", "access denied"]):
            print("[ERROR] Your IP is blocked. Stopping script.")
            return True

        print("[WARNING] Could not detect appointment modal, but step 2 not active either.")
        return False

    except Exception as e:
        print("[ERROR] Could not fill form:", e)
        return False

# ---------------------------
# Loop until success (with randomized backoff)
# ---------------------------
try:
    while True:
        success = try_booking()
        if success:
            break
        else:
            # randomized wait between retries (240-420 seconds -> 4 to 7 minutes)
            wait_time = random.uniform(240, 420)
            print(f"[INFO] No success. Sleeping {wait_time/60:.2f} minutes before retry...")
            time.sleep(wait_time)
            try:
                driver.refresh()
            except Exception:
                pass
except KeyboardInterrupt:
    print("[INFO] Interrupted by user.")
finally:
    try:
        driver.quit()
    except Exception:
        pass
