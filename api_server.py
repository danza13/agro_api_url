from flask import Flask, request, jsonify
import os
import json
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import logging
import time

load_dotenv()  # Завантаження змінних оточення

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Опціонально: зберігання даних у файл
DATA_FOLDER = "applications"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def send_system_message(user_id, text):
    """Відправляє системне повідомлення (команду) до бота та видаляє його після 2 секунд."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text,
        "disable_notification": True
    }
    try:
        r = requests.post(url, json=payload)
        app.logger.info("Системне повідомлення відправлено, статус: %s", r.status_code)
        result = r.json()
        if result.get("ok"):
            message_id = result["result"]["message_id"]
            # Затримка 2 секунди, щоб повідомлення точно отрималося
            time.sleep(2)
            delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            delete_payload = {"chat_id": user_id, "message_id": message_id}
            dr = requests.post(delete_url, json=delete_payload)
            app.logger.info("Системне повідомлення видалено, статус: %s", dr.status_code)
    except Exception as e:
        app.logger.error("Помилка відправлення/видалення системного повідомлення: %s", e)

@app.route('/endpoint', methods=['POST'])
def receive_data():
    data = request.get_json()
    app.logger.info("Отримано дані: %s", data)
    
    # Опціонально: зберігаємо дані у файл
    user_id = data.get("user_id", "unknown")
    filename = f"application_{user_id}_{int(time.time())}.json"
    file_path = os.path.join(DATA_FOLDER, filename)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        app.logger.info("Дані збережено у файл: %s", filename)
    except Exception as e:
        app.logger.error("Помилка збереження даних у файл: %s", e)
    
    # Якщо є user_id, формуємо команду з JSON-даними
    if data.get("user_id"):
        command_text = "/webapp_data " + json.dumps(data)
        send_system_message(data.get("user_id"), command_text)
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
