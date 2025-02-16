from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()  # Завантаження змінних оточення

app = Flask(__name__)
CORS(app)  # Дозволяємо CORS, якщо потрібно

@app.route('/endpoint', methods=['POST'])
def receive_data():
    data = request.get_json()
    app.logger.info("Отримано дані: %s", data)
    # Додаткове опрацювання даних, наприклад, відправка повідомлення ботом або збереження
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
