from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import argparse

# ---------------------------
# Parse arguments (so we can run --headless on GitHub Actions)
# ---------------------------
parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
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

if args.headless:
    options.add_argument("--headless=new")  # new headless mode
    options.add_argument("--disable-gpu")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.set_window_size(1920, 1080)
driver.get("https://konzinfobooking.mfa.gov.hu/")

wait = WebDriverWait(driver, 30)

# ---------------------------
# Function: complete booking attempt
# ---------------------------
def try_booking():
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
        except:
            print("[INFO] No Close button found, continuing...")

    except Exception as e:
        print("[ERROR] Could not select consulate:", e)
        return False
        
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
        return False
        
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

        time.sleep(5)
        try:
            # Detect if "Select a date" step is active (blue circle)
            active_step = driver.find_element(By.XPATH, "//a[@id='idopontvalasztas-tab' and contains(@class,'active')]")
            if active_step:
                print("[SUCCESS] Appointment page opened! 🚀")
                return True
        except:
            # If not found, assume no appointments (modal will appear)
            try:
                no_app_modal = driver.find_element(By.XPATH, "//div[contains(text(),'no appointments available')]")
                print("[INFO] No appointments available. Restarting...")
                ok_btn = driver.find_element(By.XPATH, "//button[contains(text(),'OK')]")
                driver.execute_script("arguments[0].click();", ok_btn)
            except:
                print("[WARNING] Could not detect appointment modal, but step 2 not active either.")
            return False

    except Exception as e:
        print("[ERROR] Could not fill form:", e)
        return False

# ---------------------------
# Loop until success
# ---------------------------
while True:
    success = try_booking()
    if success:
        break
    else:
        time.sleep(5)
        driver.refresh()
        print("[INFO] Page refreshed, retrying...")



