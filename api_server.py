#!/usr/bin/env python3
import os
import json
import logging
from flask import Flask, request, jsonify

import telegram
import urllib.parse

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Отримуємо токен для Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN is not set in environments!")
    exit(1)

bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Ендпоінт для отримання даних з WebApp (нова заявка або редагування)
@app.route('/submit_app', methods=['POST'])
def submit_app():
    try:
        data = request.get_json()
        # Очікується формат:
        # {
        #   "chat_id": <telegram chat id>,
        #   "application": {
        #         "ФГ": ...,
        #         "ЄДРПОУ": ...,
        #         "Кількість": ...,
        #         "Коментар": ...,
        #         "Культура": ...,
        #         "Область": ...,
        #         "Район": ...,
        #         "Населений пункт": ...,
        #         "Бажана ціна": ...,
        #         "Тип оплати": ...
        #    },
        #   "edit_index": <optional, якщо редагування>
        # }
        chat_id = data.get("chat_id")
        app_data = data.get("application")
        if not chat_id or not app_data:
            return jsonify({"status": "error", "message": "Неповні дані"}), 400

        # Детальна валідація (наприклад, перевірка числових полів)
        if app_data.get("ЄДРПОУ") and not (app_data["ЄДРПОУ"].isdigit() and len(app_data["ЄДРПОУ"]) == 8):
            return jsonify({"status": "error", "message": "Невірний формат ЄДРПОУ"}), 400
        if app_data.get("Кількість") and not str(app_data["Кількість"]).isdigit():
            return jsonify({"status": "error", "message": "Кількість має бути числом"}), 400
        if app_data.get("Бажана ціна") and not str(app_data["Бажана ціна"]).isdigit():
            return jsonify({"status": "error", "message": "Бажана ціна має бути числом"}), 400

        # Формуємо повідомлення для попереднього перегляду заявки
        text = (
            f"Перевірте заявку:\n\n"
            f"ФГ: {app_data.get('ФГ', '')}\n"
            f"ЄДРПОУ: {app_data.get('ЄДРПОУ', '')}\n"
            f"Кількість: {app_data.get('Кількість', '')}\n"
            f"Коментар: {app_data.get('Коментар', '')}\n"
            f"Культура: {app_data.get('Культура', '')}\n"
            f"Область: {app_data.get('Область', '')}\n"
            f"Район: {app_data.get('Район', '')}\n"
            f"Населений пункт: {app_data.get('Населений пункт', '')}\n"
            f"Бажана ціна: {app_data.get('Бажана ціна', '')}\n"
            f"Тип оплати: {app_data.get('Тип оплати', '')}"
        )

        # Створюємо 3 кнопки: Редагувати, Підтвердити, Скасувати
        keyboard = telegram.InlineKeyboardMarkup([
            [
                telegram.InlineKeyboardButton("Редагувати", callback_data="edit_app"),
                telegram.InlineKeyboardButton("Підтвердити", callback_data="confirm_app"),
                telegram.InlineKeyboardButton("Скасувати", callback_data="cancel_app")
            ]
        ])
        bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)
        # Зберігаємо заявку у файл користувача (<chat_id>.json)
        user_file = f"{chat_id}.json"
        try:
            with open(user_file, "r", encoding="utf-8") as f:
                apps = json.load(f)
        except FileNotFoundError:
            apps = []
        edit_index = data.get("edit_index")
        if edit_index is not None and str(edit_index).isdigit():
            edit_index = int(edit_index)
            if 0 <= edit_index < len(apps):
                # Позначаємо, що заявка була редагована
                app_data["edited"] = True
                apps[edit_index] = app_data
            else:
                apps.append(app_data)
        else:
            apps.append(app_data)
        with open(user_file, "w", encoding="utf-8") as f:
            json.dump(apps, f, ensure_ascii=False, indent=4)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.error(f"Exception in /submit_app: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Запуск сервера на порту (за замовчуванням 5000 або PORT з оточення)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
