
import pandas as pd
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from keep_alive import keep_alive
import time
import requests
import traceback
from twilio.rest import Client
from bot import start_bot
from telegram.ext import Application, CommandHandler
import os
import threading
from bot import start_bot
 

TOKEN = os.environ.get("BOT_TOKEN")  # Set this in Render dashboard under Environment
app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Hello from Render!")

app.add_handler(CommandHandler("start", start))

app.run_webhook(
    listen="0.0.0.0",
    port=8080,
    webhook_url=f"https://GEMs-Bot.onrender.com/{TOKEN}"
)

def scrape_attendance(reg_no, password):
    url = "http://mitsims.in/"

    def check_website_status(url):
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False


#
#options = Options()

    options = webdriver.ChromeOptions()
    #options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--log-level=3')

    driver = None
    try:
        if not check_website_status(url):
            return {"error": "Website is down"}

        #service = Service(ChromeDriverManager().install())
        chromedriver_path = shutil.which("chromedriver")
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(2)
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "studentLink"))).click()
        WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "studentForm")))

        form = driver.find_element(By.ID, "studentForm")
        form.find_element(By.ID, "inputStuId").send_keys(reg_no)
        form.find_element(By.ID, "inputPassword").send_keys(password)
        time.sleep(2)
        #form.find_element(By.ID, "studentSubmitButton").click()
        submit_button = form.find_element(By.ID, "studentSubmitButton")

        # Scroll into view
        driver.execute_script("arguments[0].scrollIntoView(true);",
                              submit_button)

        # Now click safely
        submit_button.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR,".x-fieldset.bottom-border.x-fieldset-default")))
        try:
            WebDriverWait(driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.ID, "studentErrorDiv")),
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "x-form-display-field"))))

            try:
                error_div = driver.find_element(By.ID, "studentErrorDiv")
                if error_div.is_displayed():
                    return {"error": "Your Login Credentials are incorrect"}
            except:
                pass

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "x-form-display-field")))

        except Exception:
            return {"error": "Your Login Credentials are incorrect"}

        fields = driver.find_elements(By.CLASS_NAME, "x-form-display-field")
        name = fields[0].text.strip() if fields else "Unknown"

        try:
            roll_number = driver.find_element(
                By.CSS_SELECTOR,
                "#profileUsn .x-form-display-field").text.strip()
        except Exception:
            roll_number = "Not Found"

        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR,
                     ".x-fieldset.bottom-border.x-fieldset-default")))
        except Exception:
            return {
                "name": name,
                "roll_number": roll_number,
                "total_classes": 0,
                "present": 0,
                "absent": 0,
                "percentage": 0,
                "subjects": {}
            }

        attendance_rows = driver.find_elements(
            By.CSS_SELECTOR, ".x-fieldset.bottom-border.x-fieldset-default")
        subjects = {}
        total_present = 0
        total_conducted = 0
        for row in attendance_rows:
            try:
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-field.x-form-item:nth-child(2) .x-form-display-field"))
                )
                subject_code = row.find_element(By.CSS_SELECTOR, "div.x-field.x-form-item:nth-child(2) .x-form-display-field").text.strip()

                # Enhanced scraping for Present
                present_text = ""
                try:
                    present_element = WebDriverWait(row, 10).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.x-field.x-form-item:nth-child(3) .x-form-display-field"))
                    )
                    present_text = present_element.text.strip()
                    if not present_text:
                        time.sleep(1)
                        present_text = present_element.text.strip()
                    if not present_text:
                        present_text = driver.execute_script("return arguments[0].innerText;", present_element).strip()
                    if not present_text:
                        print(f"Warning: Empty present_text for {subject_code}")
                except Exception as e:
                    print(f"Error scraping present for {subject_code}: {e}")
                try:
                    conducted_text = row.find_element(By.CSS_SELECTOR, "div.x-field.x-form-item:nth-child(4) .x-form-display-field").text.strip()
                except Exception as e:
                    conducted_text = "0"
                    print(f"Error scraping conducted for {subject_code}: {e}")

                # Optional raw log for specific subjects
                #if subject_code == "23CSE106" or subject_code == "23CSD602":
                 #   print(f"Raw scraped for {subject_code}: present_text='{present_text}', conducted_text='{conducted_text}'")

                present = int(present_text) if present_text.isdigit() else 0
                conducted = int(conducted_text) if conducted_text.isdigit() else 0
                absent = conducted - present
                percentage = round((present / conducted * 100), 2) if conducted else 0

                subjects[subject_code] = {
                    "present": present,
                    "conducted": conducted,
                    "absent": absent,
                    "percentage": percentage
                }

                total_present += present
                total_conducted += conducted
            except Exception as e:
                print(f"❌ Error scraping row for subject {subject_code}: {e}")
                traceback.print_exc()
                continue

        attendance_data = {
            "name": name,
            "roll_number": roll_number,
            "total_classes": total_conducted,
            "present": total_present,
            "absent": total_conducted - total_present,
            "percentage": round((total_present / total_conducted * 100), 2) if total_conducted else 0,
            "subjects": subjects
            }

        #return attendance_data    
        return create_sms_message(attendance_data)

    except Exception as e:
        traceback.print_exc()
        return {"error": str(e)}

    finally:
        if driver:
            driver.quit()


def send_sms_via_twilio(body):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(body=body,
                                     from_=TWILIO_PHONE,
                                     to=TO_PHONE)
    print("✅ SMS Sent Successfully! SID:", message.sid)


 

def create_sms_message(data):
    name = data["name"]
    roll_number = data["roll_number"]
    total_classes = data["total_classes"]
    total_present = data["present"]
    total_absent = data["absent"]
    overall_percentage = data["percentage"]
    subjects = data["subjects"]

    
    if overall_percentage >= 85:
        color_emoji = "🟢"
    elif overall_percentage >= 70:
        color_emoji = "🔵"
    elif overall_percentage >= 59:
        color_emoji = "🟠"
    else:
        color_emoji = "🔴"


    message_text = f"📊 {name}'s Attendance:\n"
    message_text += f"Roll Number: {roll_number}\n"
    message_text += f"Total Classes: {total_classes}\n"
    message_text += f"Present: {total_present}\n"
    message_text += f"Absent: {total_absent}\n"
    
    message_text += f"Overall %: {overall_percentage}%{color_emoji}\n\n"

    # Subject-wise attendance
    message_text += "📚 Subject-wise Attendance:\n"
    message_text += f"{'Subject':<15} {'P':<4} {'C':<3} {'A':<3} {'%':<7}\n"
    message_text += "-" * 30 + "\n"
    #message_text += f"| {'Subject':<12} | {'P':>3} | {'C':>3} | {'A':>3} | {'%':>6} |\n"
    #message_text += "|" + "-"*14 + "|" + "-"*5 + "|" + "-"*5 + "|" + "-"*5 + "|" + "-"*8 + "|\n"
    c=0
    for subject, details in subjects.items():
        present = details["present"]
        conducted = details["conducted"]
        absent = details["absent"]
        percentage = details["percentage"]
       # message_text += f"| {subject:<12} | {present:>3} | {conducted:>3} | {absent:>3} | {percentage:>6.2f}% |\n"

        message_text += f"{subject:<12} {present:<3} {conducted:<3} {absent:<3} {percentage:<5.2f}%\n"
        #message_text += f"| {subject:.<12} | {present:>3} | {conducted:>3} | {absent:>3} | {percentage:>6.2f}% |\n"
        c+=1
        if c%5==0:
            message_text += "\n"

    message_text+='\n'
    if overall_percentage >= 85:
        message_text+= "🎉 Great job! Keep it up!"
    elif overall_percentage >= 70:
        message_text+="👍 Good, but can be better!"
    elif overall_percentage >= 59:
        message_text+= "🟠 Warning: Attendance low!"
    else:
        message_text+="🔴 🚨 Critical! Attend classes!"
    message_text += "\n- From MITS"
    
    return message_text
def scrape_overall_attendance(username, password):
    attendance_data = scrape_attendance(username, password)
    return create_overall_message(attendance_data)

def scrape_subjectwise_attendance(username, password):
    attendance_data = scrape_attendance(username, password)
    return create_subjectwise_message(attendance_data)



def create_overall_message(data):
    name = data["name"]
    roll_number = data["roll_number"]
    total_classes = data["total_classes"]
    total_present = data["present"]
    total_absent = data["absent"]
    overall_percentage = data["percentage"]

    if overall_percentage >= 85:
        color_emoji = "🟢"
    elif overall_percentage >= 70:
        color_emoji = "🔵"
    elif overall_percentage >= 59:
        color_emoji = "🟠"
    else:
        color_emoji = "🔴"

    message_text = f"📊 {name}'s Attendance:\n"
    message_text += f"Roll Number: {roll_number}\n"
    message_text += f"Total Classes: {total_classes}\n"
    message_text += f"Present: {total_present}\n"
    message_text += f"Absent: {total_absent}\n"
    message_text += f"Overall %: {overall_percentage}%{color_emoji}\n"
    message_text += "\n🎉 Great job! Keep it up!\n- From MITS"
    return message_text.strip()


def create_subjectwise_message(data):
    subjects = data["subjects"]
    message_text = "📚 Subject-wise Attendance:\n"
    message_text += f"{'Subject':<15} {'P':<4} {'C':<3} {'A':<3} {'%':<7}\n"
    message_text += "-" * 30 + "\n"

    c = 0
    for subject, details in subjects.items():
        present = details["present"]
        conducted = details["conducted"]
        absent = details["absent"]
        percentage = details["percentage"]

        message_text += f"{subject:<12} {present:<3} {conducted:<3} {absent:<3} {percentage:<5.2f}%\n"

        c += 1
        if c % 5 == 0:
            message_text += "\n"

    message_text += "\n🎉 Great job! Keep it up!\n- From MITS"
    return message_text.strip()


if __name__ == "__main__":
    keep_alive()
    start_bot()
    
    #sms_body = create_sms_message(attendance_data)
    #send_sms_via_twilio(sms_body)
    
'''if __name__ == "__main__":
    attendance_data = scrape_attendance('23691A3288', 'Nanda@2006')
    if "error" not in attendance_data:
        sms_body = create_sms_message(attendance_data)
        send_sms_via_twilio(sms_body)
    else:
        print(f"Error: {attendance_data['error']}")
'''
