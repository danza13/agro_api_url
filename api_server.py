#!/usr/bin/env python3
import logging
import os
import json
import asyncio

from aiohttp import web
from dotenv import load_dotenv
import aiohttp
import aiohttp_cors

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Завантаження конфігурації (якщо потрібна)
try:
    from config import CONFIG
except ImportError:
    default_config_content = '''# config.py
CONFIG = {
    "fgh_name_column": "A",
    "edrpou_column": "B",
    "region_column": "C",
    "district_column": "D",
    "city_column": "E",
    "group_column": "F",
    "culture_column": "G",
    "quantity_column": "H",
    "price_column": "I",
    "currency_column": "J",
    "payment_form_column": "K",
    "extra_fields_column": "L",
    "row_start": 13
}
'''
    with open("config.py", "w", encoding="utf-8") as f:
        f.write(default_config_content)
    from config import CONFIG

API_PORT = int(os.getenv("API_PORT", "8080"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Функція для надсилання повідомлення користувачу через Telegram Bot API
async def notify_user(user_id, data):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = f"Отримано заявку:\n{data}"
    payload = {
        "chat_id": user_id,
        "text": message_text
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result

# Основна функція-обробник запиту з WebApp
async def handle_webapp_data(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return web.json_response({"status": "error", "error": "user_id missing"})
        if not data or not any(data.values()):
            return web.json_response({"status": "error", "error": "empty data"})
        
        logging.info(f"API отримав дані для user_id={user_id}: {json.dumps(data, ensure_ascii=False)}")
        
        # Надсилання сповіщення через Telegram Bot API
        notify_result = await notify_user(user_id, json.dumps(data, ensure_ascii=False))
        logging.info(f"Сповіщення боту: {notify_result}")
        
        # Повертаємо статус preview
        return web.json_response({"status": "preview"})
    except Exception as e:
        logging.exception(f"API: Помилка: {e}")
        return web.json_response({"status": "error", "error": str(e)})

# Ініціалізація додатку та налаштування CORS
async def init_app():
    app = web.Application()
    app.router.add_post('/api/webapp_data', handle_webapp_data)
    
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS"]
        )
    })
    for route in list(app.router.routes()):
        cors.add(route)
    
    return app

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=API_PORT)
