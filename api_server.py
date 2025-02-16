from flask import Flask, request, jsonify
import os
import json
import time
import logging
import requests
from dotenv import load_dotenv
from flask_cors import CORS
import asyncio

# Завантаження змінних оточення
load_dotenv()

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logging.error("TELEGRAM_TOKEN не задано у змінних оточення!")

DATA_FOLDER = "applications"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Цю функцію залишаємо, якщо потрібно відправляти повідомлення (але ми її більше не використовуємо)
def send_system_message(user_id, text):
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

# Функція для прямої обробки даних від API. 
# Вона має бути викликана асинхронно.
async def process_webapp_data_direct(user_id, data):
    # Тут ми симулюємо створення прев'ю заявки та відправлення повідомлення через бота.
    # Якщо бот і API працюють в одному процесі, то можна отримати доступ до функцій бота.
    # Наприклад, використовуючи метод send_message із aiogram.
    from your_bot_module import bot  # Припустимо, що ваш бот імпортується з іншого модуля
    preview_text = (
        "<b>Перевірте заявку:</b>\n\n" +
        f"ФГ: {data.get('fgh_name', '')}\n" +
        f"ЄДРПОУ: {data.get('edrpou', '')}\n" +
        f"Кількість: {data.get('quantity', '')}\n" +
        f"Коментар: {data.get('comment', '')}\n" +
        f"Культура: {data.get('culture', '')}\n" +
        f"Область: {data.get('region', '')}\n" +
        f"Район: {data.get('district', '')}\n" +
        f"Населений пункт: {data.get('city', '')}\n" +
        f"Бажана ціна: {data.get('price', '')}\n" +
        f"Тип оплати: {data.get('paytype', '')}\n"
    )
    # Надсилаємо повідомлення користувачу через бота
    await bot.send_message(user_id, preview_text)
    logging.info(f"Пряма обробка даних завершена для user_id={user_id}")

@app.route('/endpoint', methods=['POST'])
def receive_data():
    """
    Ендпоінт для прийому даних від WebApp або API.
    Дані зберігаються у файл і безпосередньо обробляються через process_webapp_data_direct.
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

    if data.get("user_id"):
        # Виклик асинхронної функції process_webapp_data_direct
        # Якщо API та бот працюють в одному процесі, ми можемо використати asyncio.create_task або run_coroutine_threadsafe.
        asyncio.create_task(process_webapp_data_direct(data.get("user_id"), data))
    else:
        logging.error("user_id відсутній у отриманих даних")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
