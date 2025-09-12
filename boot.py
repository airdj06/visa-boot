#!/usr/bin/env python3
"""
boot.py - automated booking bot (Selenium)

Usage:
  python boot.py            # open with browser window
  python boot.py --headless # run headless (suitable for servers/GitHub Actions)
"""

import argparse
import sys
import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------
# CONFIG / USER DATA
# ---------------------------
USER_DATA = {
    "name": "ZITOUNI Alaeddine",
    "dob": "06/11/2001",       # dd/mm/yyyy
    "phone": "+213540195220",
    "email": "alaztn25@gmail.com",
    "passport": "314552941"
}

URL = "https://konzinfobooking.mfa.gov.hu/"
MAX_WAIT = 30
RETRY_DELAY = 5   # seconds between attempts (increase to be polite)

# ---------------------------
# helper utilities
# ---------------------------
def js_click(driver, el):
    driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", el)
    driver.execute_script("arguments[0].click();", el)

def safe_find_label_input(driver, text, wait):
    """
    Find an input associated with a label with given visible text.
    Returns the input element (or raises).
    """
    # find label with text (case-insensitive)
    labels = driver.find_elements(By.XPATH, f"//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")
    for lab in labels:
        # try `for` attribute
        try:
            for_attr = lab.get_attribute("for")
            if for_attr:
                el = driver.find_element(By.ID, for_attr)
                return el
        except:
            pass
        # otherwise return the next input after label
        try:
            el = lab.find_element(By.XPATH, "./following::input[1]")
            return el
        except:
            pass
    # fallback: search inputs whose placeholder or aria-label contains the text
    inputs = driver.find_elements(By.XPATH, f"//input[contains(translate(@placeholder, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}') or contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text.lower()}')]")
    if inputs:
        return inputs[0]
    raise Exception(f"Input for label containing '{text}' not found")

def find_label_and_click_contains(driver, needle_lower):
    """
    Iterate all <label> elements and click the first that includes needle_lower (already lowercased).
    Returns True if clicked.
    """
    labels = driver.find_elements(By.TAG_NAME, "label")
    for lab in labels:
        txt = (lab.text or "").strip().lower()
        if needle_lower in txt:
            try:
                js_click(driver, lab)
                return True
            except:
                try:
                    lab.click()
                    return True
                except:
                    pass
    return False

# ---------------------------
# booking attempt routine
# ---------------------------
def try_booking(driver, wait):
    print("[STEP 1] Selecting consulate: Algeria - Algiers...")
    try:
        # open select location modal
        select_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select location') or contains(., 'Select Location')]")))
        js_click(driver, select_btn)
        print("[INFO] Opened consulate selection modal.")
        # choose Algiers
        # try to click the label that contains 'Algeria - Algiers' (case-insensitive)
        clicked = find_label_and_click_contains(driver, "algeria - algiers")
        if not clicked:
            # fallback to label contains 'algeria'
            clicked = find_label_and_click_contains(driver, "algeria")
        if not clicked:
            raise Exception("Could not find label for 'Algeria - Algiers'")
        print("[INFO] Selected: Algeria - Algiers")

        # Close modal if a close button exists
        try:
            close_btn = driver.find_element(By.XPATH, "//button[contains(@class,'close') or contains(., '×') or contains(., 'Close')]")
            js_click(driver, close_btn)
            print("[INFO] Closed consulate selection modal.")
        except:
            print("[INFO] No Close button found, continuing...")

    except Exception as e:
        print("[ERROR] Could not select consulate:", e)
        return False

    # STEP 2: select visa type C
    print("[STEP 2] Selecting Visa Type C...")
    try:
        app_type_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select type of application') or contains(., 'Select type')]")))
        js_click(driver, app_type_btn)
        print("[INFO] Opened application type selection modal.")
        time.sleep(1)

        # Find a label that mentions "type c" (case-insensitive) and click its associated checkbox
        labels = driver.find_elements(By.TAG_NAME, "label")
        found = False
        for lab in labels:
            txt = (lab.text or "").strip().lower()
            if "type c" in txt or "type c)" in txt or "short term visa" in txt and "type c" in txt:
                try:
                    # prefer to click input if present (the checkbox)
                    for_attr = lab.get_attribute("for")
                    if for_attr:
                        chk = driver.find_element(By.ID, for_attr)
                        js_click(driver, chk)
                    else:
                        js_click(driver, lab)
                    found = True
                    break
                except:
                    pass
        if not found:
            # fallback: search inputs whose id pattern looks like a guid (checkboxes)
            try:
                # try clicking by known id from HTML snippet
                sample_id = "b1c126d3-b6f4-4396-9bde-8eef45c7f451"
                chk = driver.find_element(By.ID, sample_id)
                js_click(driver, chk)
                found = True
            except:
                pass
        if not found:
            raise Exception("Could not find a checkbox/label for Visa Type C")
        print("[INFO] Visa Type C checkbox selected.")

        # Save button in modal
        save_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Save') or contains(., 'SAVE') or contains(@class,'btn-success')]")))
        js_click(driver, save_btn)
        print("[INFO] Saved Visa Type C selection.")

    except Exception as e:
        print("[WARNING] Could not select Visa Type C:", e)
        return False

    # STEP 3: fill personal info
    print("[STEP 3] Filling personal details...")
    try:
        # Name
        name_input = safe_find_label_input(driver, "name", wait)
        name_input.clear()
        name_input.send_keys(USER_DATA["name"])
        print("[INFO] Name filled.")

        # Date of Birth - duet date picker input usually has id 'birthDate' / class 'duet-date__input'
        try:
            dob_input = driver.find_element(By.ID, "birthDate")
        except:
            dob_input = driver.find_element(By.XPATH, "//input[contains(@class,'duet-date__input') or contains(@placeholder,'e.g.')]")
        dob_input.clear()
        dob_input.send_keys(USER_DATA["dob"])
        # trigger change events if needed
        driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles:true})); arguments[0].dispatchEvent(new Event('change', {bubbles:true}));", dob_input)
        print("[INFO] Date of Birth filled.")

        # Phone
        phone_input = safe_find_label_input(driver, "phone number", wait)
        phone_input.clear()
        phone_input.send_keys(USER_DATA["phone"])
        print("[INFO] Phone number filled.")

        # Email
        email_input = safe_find_label_input(driver, "email address", wait)
        email_input.clear()
        email_input.send_keys(USER_DATA["email"])
        print("[INFO] Email filled.")

        # Re-enter email (dynamic id) - find by label text
        email2_input = safe_find_label_input(driver, "re-enter the email address", wait)
        email2_input.clear()
        email2_input.send_keys(USER_DATA["email"])
        print("[INFO] Re-entered Email filled.")

        # Passport number (label "Passport number")
        passport_input = safe_find_label_input(driver, "passport number", wait)
        passport_input.clear()
        passport_input.send_keys(USER_DATA["passport"])
        # remove focus so button won't wait for typing
        driver.execute_script("arguments[0].blur()", passport_input)
        print("[INFO] Passport number filled and focus removed.")

        # consent checkboxes - use labels if present
        try:
            lab_ack = driver.find_element(By.XPATH, "//label[contains(., 'I have read') or contains(., 'acknowledged') or contains(., 'read and acknowledged')]")
            js_click(driver, lab_ack)
            print("[INFO] Acknowledgement checkbox checked.")
        except:
            try:
                chk = driver.find_element(By.ID, "slabel13")
                js_click(driver, chk)
                print("[INFO] Acknowledgement checkbox checked.")
            except:
                print("[WARNING] Acknowledgement checkbox not found.")

        try:
            lab_consent = driver.find_element(By.XPATH, "//label[contains(., 'consent') and contains(., 'personal data') or contains(., 'processing of my personal data')]")
            js_click(driver, lab_consent)
            print("[INFO] Consent checkbox checked.")
        except:
            try:
                chk2 = driver.find_element(By.ID, "label13")
                js_click(driver, chk2)
                print("[INFO] Consent checkbox checked.")
            except:
                print("[WARNING] Consent checkbox not found.")

        time.sleep(0.8)

        # Click Select date
        select_date_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Select date') or contains(.,'Select date »') or contains(., 'Select date »')]")))
        js_click(driver, select_date_btn)
        print("[INFO] Clicked 'Select date' button.")

        # small wait to let modal appear if there is a "no appointments" message
        time.sleep(2)

        # detect "no appointments available" modal or message
        noapp_candidates = driver.find_elements(By.XPATH, "//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'no appointments available') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'there are currently no appointments')]")
        if noapp_candidates:
            print("[INFO] No appointments available modal detected.")
            # press OK
            try:
                ok_btn = driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'ok') or contains(., 'OK »') or contains(., 'OK')]")
                js_click(driver, ok_btn)
            except:
                print("[WARNING] Could not find OK button to close 'no appointments' modal.")
            return False
        else:
            # not found: assume success (or next page opened)
            print("[SUCCESS] Appointment page opened — possible slots available.")
            return True

    except Exception as e:
        print("[ERROR] Could not fill form:", str(e))
        traceback.print_exc()
        return False

# ---------------------------
# Main
# ---------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run Chrome headless (suitable for servers)")
    args = parser.parse_args()

    # Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # avoid some automation flags (standard)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36")

    if args.headless:
        # modern headless mode; if your chromedriver/chrome is older, try "--headless"
        options.add_argument("--headless=new")

    print("[INFO] Starting browser...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, MAX_WAIT)

    print("[INFO] Opening", URL)
    driver.get(URL)
    time.sleep(2)

    # close cookie popup if present
    try:
        cookie_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Accept') or contains(., 'OK') or contains(., 'Accept all')]")))
        js_click(driver, cookie_btn)
        print("[INFO] Cookie popup closed.")
    except Exception:
        print("[INFO] No cookie popup found.")

    try:
        # loop until success
        attempt = 0
        while True:
            attempt += 1
            print(f"[INFO] Attempt #{attempt} ...")
            ok = try_booking(driver, wait)
            if ok:
                print("[SUCCESS] Booking flow reached appointment page. Stopping loop.")
                break
            print(f"[INFO] No appointment found, will wait {RETRY_DELAY}s then refresh and try again.")
            time.sleep(RETRY_DELAY)
            driver.refresh()
            # small delay before next attempt
            time.sleep(2)
    except KeyboardInterrupt:
        print("[INFO] Interrupted by user.")
    finally:
        print("[INFO] Done. Leaving browser open for manual inspection (if not headless).")
        # If you want the script to close the browser on finish, uncomment:
        # driver.quit()

if __name__ == "__main__":
    main()
