#!/usr/bin/env python3
import logging
import os
import json
import asyncio

from aiohttp import web
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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
    creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
    client = gspread.authorize(creds)
    logging.debug("gspread ініціалізовано.")
    return client

def get_worksheets():
    client = init_gspread()
    sheet = client.open_by_key(GOOGLE_SPREADSHEET_ID)
    ws1 = sheet.worksheet(SHEET1_NAME)
    ws2 = sheet.worksheet(SHEET2_NAME)
    return ws1, ws2

async def handle_webapp_data(request: web.Request):
    try:
        data = await request.json()
        user_id = data.get("user_id")
        if not user_id:
            return web.json_response({"status": "error", "error": "user_id missing"})
        if not data or not any(data.values()):
            return web.json_response({"status": "error", "error": "empty data"})
        ws1, _ = get_worksheets()
        new_row = [
            str(user_id),
            data.get("fgh_name", ""),
            data.get("edrpou", ""),
            data.get("quantity", ""),
            data.get("comment", ""),
            data.get("culture", ""),
            data.get("region", ""),
            data.get("district", ""),
            data.get("city", ""),
            "",  # менеджерська ціна
            "",  # статус повідомлення
            data.get("price", ""),
            data.get("paytype", "")
        ]
        ws1.append_row(new_row)
        return web.json_response({"status": "ok"})
    except Exception as e:
        logging.exception(f"API: Помилка: {e}")
        return web.json_response({"status": "error", "error": str(e)})

async def init_app():
    app = web.Application()
    app.add_routes([web.post('/api/webapp_data', handle_webapp_data)])
    return app

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app = loop.run_until_complete(init_app())
    web.run_app(app, port=API_PORT)
