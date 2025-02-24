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

# Словник перекладів для додаткових полів
translation_dict = {
    "natura": "Натура",
    "bilok": "Білок",
    "kleikovina": "Клейковина",
    "smitteva": "Сміттєва домішка",
    "vologhist": "Вологість",
    "sazhkov": "Сажкові зерна",
    "natura_ya": "Натура",
    "vologhist_ya": "Вологість",
    "smitteva_ya": "Сміттєва домішка",
    "vologhist_k": "Вологість",
    "zernovadomishka": "Зернова домішка",
    "poshkodjeni": "Пошкоджені зерна",
    "smitteva_k": "Сміттєва домішка",
    "zipsovani": "Зіпсовані зерна",
    "olijnist_na_suhu": "Олійність на суху",
    "vologhist_son": "Вологість",
    "smitteva_son": "Сміттєва домішка",
    "kislotne": "Кислотне число",
    "olijnist_na_siru": "Олійність на сиру",
    "vologhist_ripak": "Вологість",
    "glukozinolati": "Глюкозінолати",
    "smitteva_ripak": "Сміттєва домішка",
    "bilok_na_siru": "Білок на сиру",
    "vologhist_soya": "Вологість",
    "smitteva_soya": "Сміттєва домішка",
    "olijna_domishka": "Олійна домішка",
    "ambrizia": "Амброзія"
}

API_PORT = int(os.getenv("API_PORT", "8080"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")

def format_preview(data: dict) -> str:
    """
    Форматує дані заявки у зрозумілий текстовий вигляд.
    """
    lines = []
    lines.append("<b>Перевірте заявку:</b>")
    lines.append(f"ФГ: {data.get('fgh_name', '')}")
    lines.append(f"ЄДРПОУ: {data.get('edrpou', '')}")
    lines.append(f"Область: {data.get('region', '')}")
    lines.append(f"Район: {data.get('district', '')}")
    lines.append(f"Місто: {data.get('city', '')}")
    lines.append(f"Група: {data.get('group', '')}")
    lines.append(f"Культура: {data.get('culture', '')}")
    extra = data.get("extra_fields", {})
    if extra:
        lines.append("Додаткові параметри:")
        for key, value in extra.items():
            translated = translation_dict.get(key, key.capitalize())
            lines.append(f"{translated}: {value}")
    lines.append(f"Кількість: {data.get('quantity', '')} т")
    lines.append(f"Ціна: {data.get('price', '')}")
    lines.append(f"Валюта: {data.get('currency', '')}")
    lines.append(f"Форма оплати: {data.get('payment_form', '')}")
    return "\n".join(lines)

async def notify_user(user_id, data: dict):
    """
    Надсилає повідомлення через Telegram Bot API з відформатованим текстом заявки 
    та reply keyboard з кнопками "Підтвердити", "Редагувати", "Скасувати".
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    message_text = format_preview(data)
    reply_markup = {
        "keyboard": [
            [
                {"text": "Підтвердити"},
                {"text": "Редагувати"},
                {"text": "Скасувати"}
            ]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": True
    }
    payload = {
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": "HTML",
        "reply_markup": reply_markup
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            result = await resp.json()
            return result

async def handle_webapp_data(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return web.json_response({"status": "error", "error": "user_id missing"})
        if not data or not any(data.values()):
            return web.json_response({"status": "error", "error": "empty data"})
        
        logging.info(f"API отримав дані для user_id={user_id}: {json.dumps(data, ensure_ascii=False)}")
        
        # Надсилаємо повідомлення з preview заявки (reply keyboard) користувачу.
        notify_result = await notify_user(user_id, data)
        logging.info(f"Сповіщення боту: {notify_result}")
        
        return web.json_response({"status": "preview"})
    except Exception as e:
        logging.exception(f"API: Помилка: {e}")
        return web.json_response({"status": "error", "error": str(e)})

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
