from flask import Flask, request, jsonify
import os
import json
import time
import logging
import requests
from dotenv import load_dotenv
from flask_cors import CORS

# Завантаження змінних оточення
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Отримання токена Telegram з оточення
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logging.error("TELEGRAM_TOKEN не задано у змінних оточення!")

# Папка для збереження файлів (опціонально)
DATA_FOLDER = "applications"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def send_system_message(user_id, text):
    """
    Відправляє системне повідомлення (команду) до бота.
    Видалення повідомлення прибране для тестування.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text,
        "disable_notification": True
    }
    try:
        r = requests.post(url, json=payload)
        logging.info("Системне повідомлення відправлено, статус: %s", r.status_code)
    except Exception as e:
        logging.error("Помилка відправлення системного повідомлення: %s", e)

@app.route('/endpoint', methods=['POST'])
def receive_data():
    """
    Ендпоінт для прийому даних від WebApp або API.
    Дані зберігаються у файл і формується команда для бота.
    """
    try:
        data = request.get_json()
        logging.info("Отримано дані: %s", data)
    except Exception as e:
        logging.error("Помилка парсингу JSON: %s", e)
        return jsonify({"status": "error", "error": "Невірний JSON"}), 400

    # Збереження даних у файл (опціонально)
    user_id = data.get("user_id", "unknown")
    filename = f"application_{user_id}_{int(time.time())}.json"
    file_path = os.path.join(DATA_FOLDER, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info("Дані збережено у файл: %s", filename)
    except Exception as e:
        logging.error("Помилка збереження даних у файл: %s", e)

    # Якщо в даних є user_id, формуємо команду для бота
    if data.get("user_id"):
        command_text = "/webapp_data " + json.dumps(data, ensure_ascii=False)
        send_system_message(data.get("user_id"), command_text)
    else:
        logging.error("user_id відсутній у отриманих даних")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # Використовуємо PORT із оточення (Render задає його автоматично; за замовчуванням 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
