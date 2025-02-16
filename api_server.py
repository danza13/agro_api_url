from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS  # імпорт flask-cors

load_dotenv()  # Завантаження змінних з .env

app = Flask(__name__)
CORS(app)  # Увімкнення CORS для всіх маршрутів

# Отримуємо токен бота для відправки повідомлень (якщо потрібно)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
BOT_SENDMESSAGE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

@app.route('/endpoint', methods=['POST'])
def get_data():
    """
    Цей маршрут приймає дані від WebApp після натискання кнопки "Підтвердити".
    Дані очікуються у форматі JSON, наприклад:
      {
         "user_id": 123456789,
         "culture": "Пшениця",
         "region": "Київська",
         "district": "Білоцерківський",
         "city": "Біла Церква"
      }
    """
    data = request.json
    print("Отримано дані від WebApp:", data)

    # Для демонстрації: надсилаємо повідомлення користувачеві через Telegram Bot API
    user_id = data.get("user_id")
    if user_id and TELEGRAM_TOKEN:
        text_msg = "Дані з WebApp отримано:\n"
        for key, value in data.items():
            text_msg += f"{key}: {value}\n"
        try:
            resp = requests.post(
                BOT_SENDMESSAGE_URL,
                json={"chat_id": user_id, "text": text_msg},
                timeout=10
            )
            print("Відповідь від Telegram:", resp.status_code, resp.text)
        except Exception as e:
            print("Помилка надсилання повідомлення:", e)

    # Повертаємо статус "ok"
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
