#!/usr/bin/env python3
import logging
import os
import json
import asyncio

from aiohttp import web
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import aiohttp_cors

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Завантаження конфігурації Google Sheets. Якщо файлу config.py немає – створюємо його за замовчуванням.
try:
    from config import CONFIG
except ImportError:
    default_config_content = '''# config.py
# Конфігурація для визначення, в яких стовпчиках Google Sheets зберігаються дані заявки
CONFIG = {
    "fgh_name_column": "A",    # Назва ФГ
    "edrpou_column": "B",        # ЄДРПОУ
    "region_column": "C",        # Область
    "district_column": "D",      # Район
    "city_column": "E",          # Місто
    "group_column": "F",         # Група
    "culture_column": "G",       # Культура
    "quantity_column": "H",      # Кількість (тонни)
    "price_column": "I",         # Бажана ціна
    "currency_column": "J",      # Валюта
    "payment_form_column": "K",  # Форма оплати
    "extra_fields_column": "L",  # Додаткові параметри (JSON)
    "row_start": 13              # Початковий рядок для запису
}
'''
    with open("config.py", "w", encoding="utf-8") as f:
        f.write(default_config_content)
    from config import CONFIG

GOOGLE_SPREADSHEET_ID = os.getenv("GOOGLE_SPREADSHEET_ID", "")
SHEET1_NAME = os.getenv("SHEET1_NAME", "Лист1")
SHEET2_NAME = os.getenv("SHEET2_NAME", "Лист2")
API_PORT = int(os.getenv("API_PORT", "8080"))

def init_gspread():
    logging.debug("Ініціалізація gspread...")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Читаємо вміст сервісного акаунта з environment
    service_account_json = os.getenv("SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        raise Exception("SERVICE_ACCOUNT_JSON environment variable is not set")
    creds_info = json.loads(service_account_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    logging.debug("gspread ініціалізовано.")
    return gspread.authorize(creds)

def get_worksheets():
    client = init_gspread()
    sheet = client.open_by_key(GOOGLE_SPREADSHEET_ID)
    ws1 = sheet.worksheet(SHEET1_NAME)
    ws2 = sheet.worksheet(SHEET2_NAME)
    return ws1, ws2

def get_next_free_row(ws, start_col_letter, row_start):
    sheet_row = row_start
    end_col_letter = CONFIG.get("payment_form_column")
    while True:
        cell_range = ws.range(f"{start_col_letter}{sheet_row}:{end_col_letter}{sheet_row}")
        if all((cell.value is None or cell.value.strip() == "") for cell in cell_range):
            break
        sheet_row += 1
    return sheet_row

async def handle_webapp_data(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return web.json_response({"status": "error", "error": "user_id missing"})
        if not data or not any(data.values()):
            return web.json_response({"status": "error", "error": "empty data"})
        
        logging.info(f"API отримав дані для user_id={user_id}: {json.dumps(data, ensure_ascii=False)}")
        
        # Запис даних у Google Sheets
        ws1, _ = get_worksheets()
        fields_order = [
            "fgh_name", "edrpou", "region", "district", "city",
            "group", "culture", "quantity", "price", "currency", "payment_form"
        ]
        from gspread.utils import a1_to_rowcol
        row_start = int(CONFIG.get("row_start", 13))
        sheet_row = get_next_free_row(ws1, CONFIG["fgh_name_column"], row_start)
        for field in fields_order:
            key = f"{field}_column"
            col_letter = CONFIG.get(key)
            if not col_letter:
                continue
            _, col_number = a1_to_rowcol(f"{col_letter}1")
            value = data.get(field, "")
            ws1.update_cell(sheet_row, col_number, value)
        extra_fields_col = CONFIG.get("extra_fields_column")
        if extra_fields_col:
            _, col_number = a1_to_rowcol(f"{extra_fields_col}1")
            extra_fields = data.get("extra_fields", {})
            ws1.update_cell(sheet_row, col_number, json.dumps(extra_fields, ensure_ascii=False))
        return web.json_response({"status": "ok"})
    except Exception as e:
        logging.exception(f"API: Помилка: {e}")
        return web.json_response({"status": "error", "error": str(e)})

async def init_app():
    app = web.Application()
    app.router.add_post('/api/webapp_data', handle_webapp_data)
    
    # Налаштування CORS
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
