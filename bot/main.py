
import os
import json
import hmac
import hashlib
import time
import secrets
import html

import requests

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from bot.config import BOT_TOKEN, ADMIN_ID

app = FastAPI(title="LEVIN Shop API")

# Разрешаем запросы от Mini App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Проверка данных Telegram Mini App
def verify_telegram_data(init_data: str):
    if not init_data:
        raise HTTPException(401, "Telegram authorization required")

    from urllib.parse import parse_qsl

    parsed = dict(parse_qsl(init_data))

    received_hash = parsed.pop("hash", None)

    if not received_hash:
        raise HTTPException(401, "Invalid Telegram data")

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        BOT_TOKEN.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(401, "Telegram data verification failed")

    auth_date = int(parsed.get("auth_date", 0))

    if time.time() - auth_date > 86400:
        raise HTTPException(401, "Telegram session expired")

    return json.loads(parsed["user"])


# Структура товара в заказе
class OrderItem(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=150)
    price: int = Field(gt=0)
    quantity: int = Field(gt=0, le=100)


# Структура заказа
class Order(BaseModel):
    initData: str
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=5, max_length=20)
    street: str = Field(min_length=3, max_length=150)
    apartment: str = Field(default="", max_length=20)
    floor: str = Field(default="", max_length=10)
    entrance: str = Field(default="", max_length=10)
    contact_method: str
    comment: str = Field(default="", max_length=500)
    items: list[OrderItem]


# Проверка работы сервера
@app.get("/health")
def health():
    return {"status": "ok", "shop": "LEVIN"}


# Приём заказа
@app.post("/api/orders")
def create_order(order: Order):

    # Проверяем Telegram-пользователя
    user = verify_telegram_data(order.initData)

    if not order.items:
        raise HTTPException(400, "Cart is empty")

    if order.contact_method not in ["Звонок", "WhatsApp"]:
        raise HTTPException(400, "Invalid contact method")

    # Формируем заказ
    order_number = secrets.token_hex(4).upper()

    total = sum(
        item.price * item.quantity
        for item in order.items
    )

    products_text = "\n".join(
        f"• {html.escape(item.name)} × {item.quantity} — "
        f"{item.price * item.quantity:,} ₸".replace(",", " ")
        for item in order.items
    )

    address_parts = [
        order.street,
        f"кв. {order.apartment}" if order.apartment else "",
        f"этаж {order.floor}" if order.floor else "",
        f"подъезд {order.entrance}" if order.entrance else ""
    ]

    address = ", ".join(part for part in address_parts if part)

    message = (
        "🎄 <b>LEVIN — НОВЫЙ ЗАКАЗ</b>\n\n"
        f"🧾 <b>Заказ №{order_number}</b>\n\n"
        f"👤 <b>Покупатель:</b> {html.escape(order.name)}\n"
        f"📞 <b>Телефон:</b> {html.escape(order.phone)}\n"
        f"📍 <b>Адрес:</b> {html.escape(address)}\n"
        f"💬 <b>Связь:</b> {html.escape(order.contact_method)}\n\n"
        f"🛍 <b>ТОВАРЫ:</b>\n{products_text}\n\n"
        f"💰 <b>ИТОГО: {total:,} ₸</b>\n\n"
        f"📝 <b>Комментарий:</b> "
        f"{html.escape(order.comment or 'Нет')}\n\n"
        f"Telegram ID покупателя: {user.get('id')}"
    )

    # Отправляем сообщение администратору
    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": ADMIN_ID,
            "text": message,
            "parse_mode": "HTML"
        },
        timeout=15
    )

    if not response.ok:
        raise HTTPException(502, "Could not send order to administrator")

    return {
        "success": True,
        "order_number": order_number,
        "total": total,
        "message": "Ваш заказ отправлен!"
    }
