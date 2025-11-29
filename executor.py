from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import os
import requests
import json

# --- KONFIGURASI ---
base_username = "kalananti_student"  # Username dasar
password_akun = "SandiKuat2025"
email_induk   = "kalanantiacademics@gmail.com" 
jumlah_akun   = 3 
apps_script_url = os.environ.get("APPS_SCRIPT_URL") # Read from GitHub Secrets

# Setup Browser
options = webdriver.ChromeOptions()
options.add_argument("--headless") # Headless for GitHub Actions
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--window-size=1920,1080")

# options.add_experimental_option("detach", True) # Not needed for headless/CI

print("=== MEMULAI BOT PENDAFTARAN SCRATCH (HEADLESS) ===")

try:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
except Exception as e:
    print(f"Error initializing driver: {e}")
    exit(1)

for i in range(1, jumlah_akun + 1):
    # Buat data unik
    username_fix = f"{base_username}{random.randint(100, 999)}" 
    email_fix = email_induk.replace("@", f"+{username_fix}@") 
    
    print(f"\n[{i}/{jumlah_akun}] Mendaftar: {username_fix} | Email: {email_fix}")

    try:
        driver.get("https://scratch.mit.edu/join")
        time.sleep(3) 

        # --- TAHAP 1: Username & Password ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username"))).send_keys(username_fix)
        time.sleep(0.5)
        driver.find_element(By.ID, "password").send_keys(password_akun)
        time.sleep(0.5)
        driver.find_element(By.ID, "passwordConfirm").send_keys(password_akun)
        time.sleep(1)
        
        # Klik Next
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]"))).click()
        time.sleep(1)

        # --- TAHAP 2: Negara (Country) ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "country")))
        country_select = Select(driver.find_element(By.ID, "country"))
        country_select.select_by_visible_text("Indonesia")
        time.sleep(1)
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]"))).click()
        time.sleep(1)

        # --- TAHAP 3: Lahir (Month & Year) ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "birth_month")))
        Select(driver.find_element(By.ID, "birth_month")).select_by_value("1") # Januari
        time.sleep(0.5)
        Select(driver.find_element(By.ID, "birth_year")).select_by_value("2004") # Tahun 2004
        time.sleep(1)
        
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]"))).click()
        time.sleep(1)

        # --- TAHAP 4: Gender ---
        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//span[contains(., 'Prefer not to say')]"))).click()
        except:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//input[@value='female']"))).click()
            
        time.sleep(1)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Next')]"))).click()
        time.sleep(1)

        # --- TAHAP 5: Email ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
        driver.find_element(By.ID, "email").send_keys(email_fix)
        time.sleep(2)
        
        # KLIK CREATE ACCOUNT
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Create Your Account')]"))).click()
        
        print(">>> Klik 'Create Account' dilakukan...")
        
        # --- PENENTUAN CAPTCHA ---
        time.sleep(5)
        
        if "welcome" in driver.current_url or "Welcome" in driver.page_source:
            print(f"✅ SUKSES! Akun {username_fix} berhasil dibuat.")
            
            # Send data to Apps Script
            if apps_script_url:
                try:
                    payload = {
                        "username": username_fix,
                        "password": password_akun
                    }
                    requests.post(apps_script_url, json=payload)
                    print(f"   -> Data sent to Spreadsheet.")
                except Exception as req_e:
                    print(f"   -> Failed to send data to Spreadsheet: {req_e}")
            
            # Logout
            driver.get("https://scratch.mit.edu/accounts/logout/")
            time.sleep(3)
        else:
            print("⚠️ MUNGKIN GAGAL/CAPTCHA MUNCUL. Cek browser.")

    except Exception as e:
        print(f"❌ Error pada {username_fix}: {e}")
        continue

driver.quit()
print("\n=== SELESAI ===")