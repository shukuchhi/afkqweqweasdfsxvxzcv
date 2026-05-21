import sys
import os
import time
import subprocess
import requests
import secrets
import string
import re
import random
import webbrowser
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Подключаем пути
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.adb_helper import check_adb_devices

# Импортируем обновленные функции
from utils.adb_utils import connect_adb, take_screenshot, tap, adb_input_text, swipe, find_template

class MailTmClient:
    def __init__(self):
        self.base_url = "https://api.mail.tm"
        self.headers = {"Content-Type": "application/json"}
        self.account = None
        self.token = None

    def fetch_domains(self):
        response = requests.get(f"{self.base_url}/domains", headers=self.headers)
        if response.status_code == 200:
            return response.json()["hydra:member"][0]["domain"]
        else:
            raise Exception(f"Ошибка получения доменов: {response.status_code}")

    def generate_username(self):
        letters = string.ascii_lowercase
        username = ''.join(secrets.choice(letters) for _ in range(secrets.randbelow(4) + 5))
        number = ''.join(secrets.choice(string.digits) for _ in range(secrets.randbelow(3) + 2))
        return f"{username}{number}"

    def create_account(self, username=None, password=None):
        domain = self.fetch_domains()
        if not username: username = self.generate_username()
        if not password: password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        email_address = f"{username}@{domain}"
        payload = {"address": email_address, "password": password}
        
        response = requests.post(f"{self.base_url}/accounts", json=payload, headers=self.headers)
        if response.status_code == 201:
            self.account = response.json()
            print(f"Создан email: {email_address}")
            return email_address, password
        else:
            raise Exception(f"Ошибка создания аккаунта: {response.status_code}")

    def get_token(self, email, password):
        payload = {"address": email, "password": password}
        response = requests.post(f"{self.base_url}/token", json=payload, headers=self.headers)
        if response.status_code == 200:
            self.token = response.json()["token"]
            self.headers["Authorization"] = f"Bearer {self.token}"
            print("Токен получен")
        else:
            raise Exception(f"Ошибка токена: {response.status_code}")

    def fetch_messages(self, device, max_attempts=10, delay=5):
        for attempt in range(max_attempts):
            response = requests.get(f"{self.base_url}/messages", headers=self.headers)
            if response.status_code == 200:
                messages = response.json()
                if messages["hydra:member"]:
                    return messages["hydra:member"][0]
                else:
                    print(f"Письма нет, ждем... {attempt + 1}/{max_attempts}")
                    time.sleep(delay)
            else:
                raise Exception(f"Ошибка API писем: {response.status_code}")
        
        print("Письмо не пришло. Пробуем обновить интерфейс игры...")
        reload_captcha = (1232, 324)
        reload_email = (1466, 225)
        
        tap(device, reload_captcha[0], reload_captcha[1])
        time.sleep(1)
        tap(device, reload_captcha[0], reload_captcha[1])
        time.sleep(10)
        tap(device, reload_email[0], reload_email[1])
        time.sleep(3)
        
        raise Exception("Письмо не получено (таймаут).")

    def fetch_message_content(self, message_id):
        response = requests.get(f"{self.base_url}/messages/{message_id}", headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ошибка контента письма: {response.status_code}")

    def extract_verification_link(self, message_content):
        html_content = message_content.get("html", "")
        if isinstance(html_content, list): html_content = "".join(html_content)
        
        match = re.search(r'https://mtacc\.mobilelegends\.com[^"\s<>]+/inemail/activation/[^"\s<>]+', html_content)
        if match: return match.group(0)
        
        match = re.search(r'(https?://[^\s<>"]+)', html_content)
        if match: return match.group(0)
        
        raise Exception("Ссылка не найдена в письме")

def save_to_file(email, email_password):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    file_path = os.path.join(base_dir, "accounts.txt")
    message = f"🌸 Почта: {email} \\n🌸 Пароль на сайте: {email_password}\n"
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(message)
        print("Данные сохранены в accounts.txt")
    except Exception as e:
        print(f"Ошибка сохранения файла: {e}")

def send_telegram_message(email, email_password):
    bot_token = "6364433192:AAFwRvgsSrqXQzLPOyPgFUddqgort9UAPFU"
    chat_id = "1767791884"
    message = f"🌸 Почта: {email} \\n🌸 Пароль на сайте: {email_password}"
    try:
        requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", 
                      params={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
        print("Отправлено в Telegram")
    except:
        print("Ошибка отправки в Telegram")

def close_browser(driver=None):
    try:
        if driver:
            driver.quit()
            print("Браузер закрыт.")
    except Exception as e:
        print(f"Ошибка закрытия браузера: {e}")

def clear_text(device):
    try:
        cmd = f"adb -s {device.serial} shell input keyevent KEYCODE_DEL"
        for _ in range(15):
            subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"Ошибка очистки: {e}")

def solve_captcha(device, captcha_reload):
    print("Решение капчи...")
    api_key = "9000cac40fb9c1d1140727d309e89358"
    
    full_screenshot_path = take_screenshot(device)
    time.sleep(1)

    img = Image.open(full_screenshot_path)
    x, y, w, h = 685, 400, 555, 375
    captcha_area = (x, y, x + w, y + h)
    
    captcha_filename = f"captcha_{device.serial}.png"
    captcha_img = img.crop(captcha_area)
    captcha_img.save(captcha_filename)

    try:
        with open(captcha_filename, "rb") as f:
            response = requests.post("http://2captcha.com/in.php", 
                                     files={"file": f}, 
                                     data={"key": api_key, "method": "post", "coordinatescaptcha": "1"})
        
        if not response.text.startswith("OK|"):
            raise Exception(f"Ошибка отправки капчи: {response.text}")
        
        task_id = response.text.split("|")[1]
        print(f"Капча отправлена ID: {task_id}")
        try: os.remove(captcha_filename)
        except: pass

        for attempt in range(30):
            resp = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={task_id}")
            result = resp.text
            
            if result.startswith("OK|coordinates:"):
                coords_str = result.split("coordinates:")[1]
                for coord_pair in coords_str.split(";"):
                    if not coord_pair: continue
                    cx = int(coord_pair.split(",")[0].split("=")[1])
                    cy = int(coord_pair.split(",")[1].split("=")[1])
                    tap(device, x + cx, y + cy)
                    time.sleep(1)
                return True
                
            elif result == "ERROR_CAPTCHA_UNSOLVABLE":
                tap(device, captcha_reload[0], captcha_reload[1])
                time.sleep(5)
                return False
            time.sleep(5)
    except Exception as e:
        print(f"Сбой капчи: {e}")
        return False
            
    raise Exception("Таймаут решения капчи")

def run(serial=None):
    print(f"Starting Email Verification on {serial}...")

    try:
        device = connect_adb(serial)
    except Exception as e:
        print(f"Critical ADB Error: {e}")
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    templates_dir = os.path.join(base_dir, "templates")
    captcha_slider_check = os.path.join(templates_dir, "1.png")
    password_input_window_template = os.path.join(templates_dir, "password_input_window.png")

    time.sleep(2.5)
    tap(device, 64, 70)
    time.sleep(3)
    tap(device, 1785, 165)
    time.sleep(4)
    tap(device, 167, 700)
    time.sleep(5)

    max_process_attempts = 10
    process_attempt = 0

    while process_attempt < max_process_attempts:
        process_attempt += 1
        print(f"--- Попытка процесса {process_attempt} ---")
        driver = None

        tap(device, 1363, 363)
        time.sleep(3)

        attempt = 0
        found_pass_window = False
        while attempt < 45:
            scr = take_screenshot(device)
            if find_template(scr, password_input_window_template):
                print("Окно ввода почты открыто.")
                found_pass_window = True
                break
            time.sleep(2)
            attempt += 1

        if not found_pass_window:
            print("❌ ОШИБКА: Окно ввода почты не найдено. Пробуем еще раз.")
            continue
            
        mail_client = MailTmClient()
        try:
            email, email_password = mail_client.create_account()
            mail_client.get_token(email, email_password)
        except Exception as e:
            print(f"Ошибка почты: {e}")
            continue

        print(f"Данные: {email} (Пароль сайта: {email_password})")
        time.sleep(2)

        # Ввод данных
        tap(device, 746, 444)
        time.sleep(1)
        adb_input_text(device, "aaa") 
        time.sleep(1)
        clear_text(device)
        tap(device, 100, 100)
        time.sleep(1)
        tap(device, 746, 444)
        time.sleep(1)
        adb_input_text(device, email)
        time.sleep(1)
        tap(device, 100, 100) # Клик вне поля
        time.sleep(3)

        tap(device, 959, 826) # Клик "Далее"

        time.sleep(5)

        captcha_reload = (1215, 422)
        captcha_check_attempt = 0
        found_captcha = False
        
        while captcha_check_attempt < 30:
            scr = take_screenshot(device)
            if find_template(scr, captcha_slider_check):
                print("Капча найдена!")
                found_captcha = True
                break
            print("Ждем капчу...")
            if captcha_check_attempt > 10 and captcha_check_attempt % 5 == 0:
                tap(device, 959, 826) # Повторный клик если не вылезла
            time.sleep(2)
            captcha_check_attempt += 1
            
        if not found_captcha:
            print("Капча не появилась.")
            continue

        solved = False
        for _ in range(5):
            if solve_captcha(device, captcha_reload):
                time.sleep(4)
                scr = take_screenshot(device)
                if not find_template(scr, captcha_slider_check):
                    print("Капча исчезла!")
                    solved = True
                    break
            time.sleep(2)
        
        if not solved:
            print("Не удалось решить капчу. Ресет.")
            continue

        print("Ждем письмо...")
        try:
            message = mail_client.fetch_messages(device=device)
            content = mail_client.fetch_message_content(message["id"])
            link = mail_client.extract_verification_link(content)
            
            print(f"Ссылка: {link}")
            
            try:
                opts = Options()
                opts.add_argument("--new-window")
                driver = webdriver.Chrome(options=opts)
                driver.get(link)
            except:
                webbrowser.open_new(link)
            
            time.sleep(15)
            close_browser(driver)

            time.sleep(2)
            tap(device, 1075, 265) # Подтверждение в игре

            send_telegram_message(email, email_password)
            save_to_file(email, email_password)
            
            print("Успех!")
            return # Выход из функции после успеха

        except Exception as e:
            print(f"Ошибка верификации: {e}")
            close_browser(driver)
            continue

    print("Не удалось верифицировать аккаунт после всех попыток.")

if __name__ == "__main__":
    run()