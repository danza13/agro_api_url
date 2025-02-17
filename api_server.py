#!/usr/bin/env python3
import requests
import json
import os

# Вкажіть URL API (переконайтеся, що порт співпадає з API_PORT, встановленим у bot.py)
API_URL = os.getenv("API_URL", "http://localhost:8080/api/webapp_data")

# Тестові дані
payload = {
    "user_id": 1124775269,
    "fgh_name": "Тест ФГ",
    "edrpou": "00000000",
    "region": "Тестова область",
    "district": "Тестовий район",
    "city": "Тестове місто",
    "culture": "Пшениця",
    "quantity": "100",
    "price": "200",
    "paytype": "Гривня: БН з ПДВ",
    "comment": "тестовий коментар"
}

headers = {"Content-Type": "application/json"}

response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
print("Статус:", response.status_code)
print("Відповідь:", response.json())
