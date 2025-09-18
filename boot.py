# boot.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import argparse
import sys
import random

# ---------------------------
# Parse arguments
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
parser.add_argument("--max-minutes", type=int, default=20, help="How many minutes to keep trying on the same VM (default: 20)")
parser.add_argument("--attempt-delay", type=float, default=5.0, help="Seconds to wait between attempts (default: 5)")
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
# Start browser
# ---------------------------
print("[INFO] Starting browser...")
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")      # reduce Chrome noise
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-software-rasterizer")

if args.headless:
    options.add_argument("--headless=new")  # new headless mode
    options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_window_size(1920, 1080)
wait = WebDriverWait(driver, 30)

driver.get("https://konzinfobooking.mfa.gov.hu/")

# ---------------------------
# Function: complete one booking attempt (keeps original prints & sleeps)
# Returns:
#   0 -> success (appointment page opened)
#   1 -> retryable failure (no appointment / captcha / other)
#   2 -> IP blocked (explicit)
# ---------------------------
def try_booking_once():
    try:
        # STEP 0: Check if IP is blocked
        try:
            blocked_msg = driver.find_element(By.XPATH, "//h3[contains(text(),'Your IP') and contains(text(),'blocked')]")
            if blocked_msg:
                print("[ERROR] Your IP is blocked. Stopping attempt.")
                return 2  # signal IP blocked
        except Exception:
            pass

        # STEP 1: Select Consulate (Algiers)
        print("[STEP 1] Selecting consulate: Algeria - Algiers...")
        try:
            time.sleep(2)
            select_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select location')]"))
            )
            time.sleep(3)
            driver.execute_script("arguments[0].click();", select_btn)
            print("[INFO] Opened consulate selection modal.")

            algiers_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//label[contains(text(),'Algeria - Algiers')]"))
            )
            driver.execute_script("arguments[0].click();", algiers_option)
            print("[INFO] Selected: Algeria - Algiers")

            try:
                close_btn = driver.find_element(By.XPATH, "//button[contains(text(),'Close') or contains(text(),'×')]")
                driver.execute_script("arguments[0].click();", close_btn)
                print("[INFO] Closed consulate selection modal.")
            except Exception:
                print("[INFO] No Close button found, continuing...")

        except Exception as e:
            print("[ERROR] Could not select consulate:", e)
            return 1

        time.sleep(2)
        # STEP 2: Select Visa Type C
        print("[STEP 2] Selecting Visa Type C...")
        try:
            app_type_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select type of application')]"))
            )
            driver.execute_script("arguments[0].click();", app_type_btn)
            print("[INFO] Opened application type selection modal.")

            visa_c_checkbox = wait.until(
                EC.element_to_be_clickable((By.ID, "b1c126d3-b6f4-4396-9bde-8eef45c7f451"))
            )
            driver.execute_script("arguments[0].click();", visa_c_checkbox)
            print("[INFO] Visa Type C checkbox selected.")

            save_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Save')]"))
            )
            driver.execute_script("arguments[0].click();", save_btn)
            print("[INFO] Saved Visa Type C selection.")

        except Exception as e:
            print("[WARNING] Could not select Visa Type C:", e)
            return 1

        time.sleep(2)
        # STEP 3: Fill Personal Information
        print("[STEP 3] Filling personal details...")
        try:
            name_input = wait.until(EC.presence_of_element_located((By.ID, "label4")))
            name_input.clear()
            name_input.send_keys(USER_DATA["name"])

            time.sleep(1)
            dob_input = wait.until(EC.presence_of_element_located((By.ID, "birthDate")))
            dob_input.clear()
            dob_input.send_keys(USER_DATA["dob"])

            phone_input = wait.until(EC.presence_of_element_located((By.ID, "label9")))
            phone_input.clear()
            phone_input.send_keys(USER_DATA["phone"])

            email_input = wait.until(EC.presence_of_element_located((By.ID, "label10")))
            email_input.clear()
            email_input.send_keys(USER_DATA["email"])

            email2_input = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//label[contains(text(),'Re-enter the email address')]/following::input[1]")
                )
            )
            email2_input.clear()
            email2_input.send_keys(USER_DATA["email"])

            passport_input = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//label[contains(text(),'Passport number')]/following::input[1]")
                )
            )
            passport_input.clear()
            passport_input.send_keys(USER_DATA["passport"])
            driver.execute_script("arguments[0].blur();", passport_input)

            consent1 = wait.until(EC.element_to_be_clickable((By.ID, "slabel13")))
            driver.execute_script("arguments[0].click();", consent1)

            consent2 = wait.until(EC.element_to_be_clickable((By.ID, "label13")))
            driver.execute_script("arguments[0].click();", consent2)

            time.sleep(3)
            select_date_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Select date')]"))
            )
            driver.execute_script("arguments[0].click();", select_date_btn)
            print("[INFO] Clicked 'Select date' button.")

            time.sleep(10)
            try:
                # Detect if "Select a date" step is active (blue circle)
                active_step = driver.find_element(By.XPATH, "//a[@id='idopontvalasztas-tab' and contains(@class,'active')]")
                if active_step:
                    print("[SUCCESS] Appointment page opened! 🚀")
                    # Keep the browser open a bit so you can act manually if needed (same behavior as before)
                    time.sleep(50)
                    return 0
            except Exception:
                pass

            # Check if "no appointments" modal appeared
            try:
                no_app_modal = driver.find_element(By.XPATH, "//div[contains(text(),'no appointments available')]")
                print("[INFO] No appointments available. Restarting...")
                try:
                    ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'OK')]")
                    driver.execute_script("arguments[0].click();", ok_btn)
                except Exception:
                    pass
                return 1
            except Exception:
                pass

            try:
                captcha_modal = driver.find_element(By.XPATH, "//div[contains(text(),'hCaptcha has to be checked')]")
                print("[INFO] hCaptcha detected. Refreshing and retrying...")
                try:
                    ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'OK')]")
                    driver.execute_script("arguments[0].click();", ok_btn)
                except Exception:
                    pass
                return 1

            except Exception:
                print("[WARNING] Could not detect appointment modal, but step 'Select a date' not active either.")
                return 1

        except Exception as e:
            print("[ERROR] Could not fill form:", e)
            return 1

    except Exception as outer_e:
        print("[CRITICAL] Unexpected error in attempt:", outer_e)
        return 1


# ---------------------------
# Loop until success, IP block, or max time reached
# ---------------------------
start_ts = time.time()
max_seconds = args.max_minutes * 60
print(f"[INFO] Starting booking loop (will keep trying on this VM for up to {args.max_minutes} minutes)...")

try:
    while True:
        elapsed = time.time() - start_ts
        if elapsed > max_seconds:
            print(f"[INFO] Reached max runtime on this VM ({args.max_minutes} minutes). Exiting so workflow can use next VM.")
            driver.quit()
            sys.exit(1)   # retryable: move to next VM

        code = try_booking_once()

        if code == 0:
            print("[INFO] SUCCESS — appointment page reached. Exiting with success.")
            try:
                driver.quit()
            except:
                pass
            sys.exit(0)
        elif code == 2:
            print("[ERROR] IP blocked detected on this VM. Exiting so workflow can rotate to next VM.")
            try:
                driver.quit()
            except:
                pass
            sys.exit(2)
        else:
            # retryable failure (no appointments / captcha)
            # restore original style: sleep then refresh and try again on same VM
            sleep_time = args.attempt_delay + random.uniform(0, 2)
            print(f"[INFO] Attempt finished with no appointment. Sleeping {sleep_time:.1f}s then refreshing and retrying on same VM...")
            time.sleep(sleep_time)
            try:
                driver.refresh()
            except Exception as e:
                print("[WARNING] refresh failed:", e)
            print("[INFO] Page refreshed, next attempt will start.")
            # continue loop on same VM

except KeyboardInterrupt:
    print("[INFO] Interrupted by user.")
    try:
        driver.quit()
    except:
        pass
    sys.exit(1)
