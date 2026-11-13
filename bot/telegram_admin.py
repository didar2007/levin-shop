
import threading
import time

import telebot
from telebot import types

from bot.config import BOT_TOKEN, ADMIN_ID
from bot.database import (
    init_db,
    save_user,
    get_all_users,
    get_users_count
)


# =====================================
# BOT SETTINGS
# =====================================

bot = telebot.TeleBot(BOT_TOKEN)

broadcast_mode = False

SHOP_URL = "https://didar2007.github.io/levin-shop/"
ADMIN_URL = "https://t.me/toxicalien21"


def is_admin(message):
    return message.from_user.id == ADMIN_ID


# =====================================
# START COMMAND
# =====================================

@bot.message_handler(commands=["start"])
def start_command(message):
    user = message.from_user

    save_user(
        user.id,
        user.first_name or "",
        user.username or ""
    )

    # Постоянная нижняя клавиатура
    bottom_keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        is_persistent=True,
        row_width=2
    )

    bottom_keyboard.add(
        types.KeyboardButton(
            text="🛍 Открыть каталог"
        ),
        types.KeyboardButton(
            text="💬 Связаться с нами"
        )
    )

    # Кнопки приветственного сообщения
    inline_keyboard = types.InlineKeyboardMarkup(
        row_width=1
    )

    inline_keyboard.add(
        types.InlineKeyboardButton(
            text="🛍 Открыть каталог",
            web_app=types.WebAppInfo(url=SHOP_URL)
        ),
        types.InlineKeyboardButton(
            text="💬 Связаться с администратором",
            url=ADMIN_URL
        )
    )

    bot.send_message(
        message.chat.id,
        "🎄 Добро пожаловать в LEVIN!\n\n"
        "Товары для уюта и праздничного настроения.\n\n"
        "Выбирай товары в каталоге или свяжись с нами, "
        "если нужна помощь.",
        reply_markup=inline_keyboard
    )

    bot.send_message(
        message.chat.id,
        "Каталог всегда доступен по кнопке внизу 👇",
        reply_markup=bottom_keyboard
    )


# =====================================
# OPEN CATALOG
# =====================================

@bot.message_handler(
    func=lambda message: message.text == "🛍 Открыть каталог"
)
def open_catalog(message):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            text="🛍 Открыть каталог",
            web_app=types.WebAppInfo(url=SHOP_URL)
        )
    )

    bot.send_message(
        message.chat.id,
        "🎄 Открой каталог LEVIN:",
        reply_markup=keyboard
    )


# =====================================
# CONTACT ADMIN
# =====================================

@bot.message_handler(
    func=lambda message: message.text == "💬 Связаться с нами"
)
def contact_admin(message):
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            text="💬 Написать администратору",
            url=ADMIN_URL
        )
    )

    bot.send_message(
        message.chat.id,
        "Если у тебя есть вопросы, напиши нам:",
        reply_markup=keyboard
    )


# =====================================
# ADMIN PANEL
# =====================================

@bot.message_handler(commands=["admin"])
def admin_command(message):
    if not is_admin(message):
        return

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        is_persistent=True
    )

    # Каталог через сообщение с inline-кнопкой
    keyboard.add(
        types.KeyboardButton(
            text="🛍 Открыть каталог"
        )
    )

    keyboard.add(
        types.KeyboardButton("📢 Рассылка"),
        types.KeyboardButton("👥 Количество клиентов")
    )

    bot.send_message(
        message.chat.id,
        "🎄 LEVIN — Панель администратора",
        reply_markup=keyboard
    )


# =====================================
# CANCEL BROADCAST
# =====================================

@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    global broadcast_mode

    if not is_admin(message):
        return

    broadcast_mode = False

    bot.send_message(
        message.chat.id,
        "Рассылка отменена."
    )


# =====================================
# CLIENT COUNT
# =====================================

@bot.message_handler(
    func=lambda message: message.text == "👥 Количество клиентов"
)
def clients_count(message):
    if not is_admin(message):
        return

    count = get_users_count()

    bot.send_message(
        message.chat.id,
        f"👥 Всего пользователей: {count}"
    )


# =====================================
# START BROADCAST
# =====================================

@bot.message_handler(
    func=lambda message: message.text == "📢 Рассылка"
)
def start_broadcast(message):
    global broadcast_mode

    if not is_admin(message):
        return

    broadcast_mode = True

    bot.send_message(
        message.chat.id,
        "📢 Отправь сообщение или фотографию для рассылки.\n\n"
        "После отправки рассылка начнётся автоматически.\n"
        "Для отмены отправь /cancel."
    )


# =====================================
# BROADCAST MESSAGE
# =====================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "animation",
        "audio",
        "voice",
        "video_note",
        "sticker"
    ]
)
def broadcast_message(message):
    global broadcast_mode

    if not is_admin(message) or not broadcast_mode:
        return

    broadcast_mode = False

    users = get_all_users()

    sent = 0
    failed = 0

    bot.send_message(
        ADMIN_ID,
        f"🚀 Начинаю рассылку.\n"
        f"Получателей: {len(users)}"
    )

    for (user_id,) in users:
        if user_id == ADMIN_ID:
            continue

        try:
            bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            sent += 1
            time.sleep(0.05)

        except Exception:
            failed += 1

    bot.send_message(
        ADMIN_ID,
        "✅ Рассылка завершена!\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не удалось отправить: {failed}"
    )


# =====================================
# START BOT
# =====================================

def start_bot():
    init_db()

    thread = threading.Thread(
        target=bot.infinity_polling,
        kwargs={"skip_pending": True},
        daemon=True
    )

    thread.start()
