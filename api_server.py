from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS  # Імпорт Flask-CORS

load_dotenv()  # Завантаження змінних з .env

app = Flask(__name__)
CORS(app)  # Увімкнення CORS для всіх маршрутів

@app.route('/endpoint', methods=['POST'])
def get_data():
    """
    Цей маршрут приймає дані від WebApp після натискання кнопки "Підтвердити".
    Очікується, що дані будуть у форматі JSON, наприклад:
      {
         "user_id": 123456789,
         "culture": "Пшениця",
         "region": "Київська",
         "district": "Білоцерківський",
         "city": "Біла Церква"
      }
    """
    data = request.json
    # Логування отриманих даних (системне повідомлення – не надсилаємо користувачу)
    app.logger.info("Отримано дані від WebApp: %s", data)
    
    # Не надсилаємо повідомлення користувачу; лише повертаємо статус
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
