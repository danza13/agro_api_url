#!/usr/bin/env python3
import logging
import os
import json
import asyncio

from aiohttp import web
from dotenv import load_dotenv
import aiohttp
import aiohttp_cors
import asyncpg  # бібліотека для роботи з PostgreSQL

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

# Змінні середовища
API_PORT = int(os.getenv("API_PORT", "8080"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL")  # Повинен виглядати приблизно так:
# postgresql://agro_sql_user:Lh8qJtn1EK6b8oAsffEqz8LFvLFKdgZx@dpg-cuupoai3esus73ac3lt0-a.oregon-postgres.render.com/agro_sql

# Функція для форматування тексту попереднього перегляду заявки
def format_preview(data: dict) -> str:
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

# Функція для надсилання повідомлення користувачу через Telegram Bot API
async def notify_user(user_id, data: dict):
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

# --- Інтеграція з PostgreSQL через asyncpg ---

db_pool = None

async def init_db_pool():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        # Створюємо таблицю, якщо її ще немає
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS fsm_state (
                user_id BIGINT PRIMARY KEY,
                state TEXT NOT NULL,
                data JSONB NOT NULL,
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
    logging.info("Пул з'єднань з PostgreSQL ініціалізовано.")

async def save_fsm_state(user_id: int, state: str, data: dict):
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO fsm_state(user_id, state, data)
            VALUES($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET state = EXCLUDED.state, data = EXCLUDED.data, updated_at = NOW()
        """, user_id, state, json.dumps(data))

async def get_fsm_state(user_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT state, data FROM fsm_state WHERE user_id = $1", user_id)
        return row

# --- API-ендпоінт для обробки даних WebApp ---
async def handle_webapp_data(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return web.json_response({"status": "error", "error": "user_id missing"})
        if not data or not any(data.values()):
            return web.json_response({"status": "error", "error": "empty data"})
        
        logging.info(f"API отримав дані для user_id={user_id}: {json.dumps(data, ensure_ascii=False)}")
        
        # Надсилаємо повідомлення з попереднім переглядом заявки користувачу
        notify_result = await notify_user(user_id, data)
        logging.info(f"Сповіщення боту: {notify_result}")
        
        # Зберігаємо стан (FSM) для цього користувача з позначкою "confirm_application"
        await save_fsm_state(int(user_id), "confirm_application", data)
        
        return web.json_response({"status": "preview"})
    except Exception as e:
        logging.exception(f"API: Помилка: {e}")
        return web.json_response({"status": "error", "error": str(e)})

async def init_app():
    await init_db_pool()
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
