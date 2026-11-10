
import threading
import time

import telebot
from telebot import types

from bot.config import BOT_TOKEN, ADMIN_ID
from bot.database import init_db, save_user, get_all_users, get_users_count


bot = telebot.TeleBot(BOT_TOKEN)

broadcast_mode = False


def is_admin(message):
    return message.from_user.id == ADMIN_ID


@bot.message_handler(commands=["start"])
def start_command(message):
    user = message.from_user

    save_user(
        user.id,
        user.first_name or "",
        user.username or ""
    )

    bot.send_message(
        message.chat.id,
        "🎄 Добро пожаловать в LEVIN!\n\n"
        "Открой каталог и выбери товары для своего дома."
    )


@bot.message_handler(commands=["admin"])
def admin_command(message):
    if not is_admin(message):
        return

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
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


@bot.message_handler(commands=["cancel"])
def cancel_command(message):
    global broadcast_mode

    if not is_admin(message):
        return

    broadcast_mode = False

    bot.send_message(
        message.chat.id,
        "Рассылка отменена.",
        reply_markup=types.ReplyKeyboardRemove()
    )


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
        f"🚀 Начинаю рассылку.\nПолучателей: {len(users)}"
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


def start_bot():
    init_db()

    thread = threading.Thread(
        target=bot.infinity_polling,
        kwargs={"skip_pending": True},
        daemon=True
    )

    thread.start()
