from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()  # Завантаження змінних з .env

app = Flask(__name__)
CORS(app)  # Увімкнення CORS для всіх маршрутів

@app.route('/endpoint', methods=['POST'])
def get_data():
    """
    Приймає дані від WebApp або бота.
    Формат JSON (наприклад):
      {
         "user_id": 123456789,
         "pib": "Іванов Іван Іванович",
         "region": "Київська",
         "age": "30",
         "phone": "+380XXXXXXXXX",
         "initial_app": { ... },
         "webapp": { ... }
      }
    """
    data = request.json
    app.logger.info("Отримано дані від WebApp/бота: %s", data)
    # Не надсилаємо повідомлення користувачу – лише повертаємо статус
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
