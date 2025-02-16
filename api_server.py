from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS
import requests
import logging

load_dotenv()  # Завантаження змінних оточення

app = Flask(__name__)
CORS(app)  # Дозволяємо CORS

# Налаштування логування (вже налаштовано глобально)
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

def send_silent_message(user_id, text):
    """Відправляє повідомлення користувачу і одразу його видаляє, щоб користувач не бачив системних повідомлень."""
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": text,
        "disable_notification": True
    }
    try:
        response = requests.post(send_url, json=payload)
        app.logger.info("Повідомлення відправлено, статус: %s", response.status_code)
        result = response.json()
        if result.get("ok"):
            message_id = result["result"]["message_id"]
            # Видаляємо повідомлення через 1 секунду
            delete_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteMessage"
            delete_payload = {"chat_id": user_id, "message_id": message_id}
            # Можна додати затримку, якщо потрібно
            requests.post(delete_url, json=delete_payload)
            app.logger.info("Повідомлення видалено для user_id=%s", user_id)
    except Exception as e:
        app.logger.error("Помилка відправлення/видалення повідомлення: %s", e)

@app.route('/endpoint', methods=['POST'])
def receive_data():
    data = request.get_json()
    app.logger.info("Отримано дані: %s", data)
    
    user_id = data.get("user_id")
    if user_id:
        # Формуємо текст повідомлення (це системне повідомлення, яке користувач не побачить)
        text = (
            "Дані з WebApp отримано:\n"
            f"Культура: {data.get('culture')}\n"
            f"Область: {data.get('region')}\n"
            f"Район: {data.get('district')}\n"
            f"Населений пункт: {data.get('city')}"
        )
        send_silent_message(user_id, text)
    
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
