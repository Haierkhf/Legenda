import logging
import os
import json
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = "7756038660:AAHgk4D2wRoC45mxg6v5zwMxNtowOyv0JLo"
CRYPTOBOT_API_KEY = "347583:AAr39UUQRuaxRGshwKo0zFHQnK5n3KMWkzr"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
except json.JSONDecodeError:
    users = {}

pending_payments = {}

app = FastAPI()

def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        ("🤖 Создать бота", "create_bot"),
        ("ℹ️ Информация", "info"),
        ("💬 Отзывы", "https://t.me/nWf0L9BBCoJlY2Qy"),
        ("👤 Профиль", "profile"),
        ("🔒 Политика конфиденциальности", "privacy")
    ]
    for text, data in buttons:
        markup.add(InlineKeyboardButton(text=text, callback_data=data if "http" not in data else None, url=data if "http" in data else None))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
    bot.send_message(message.chat.id, "Привет! Я бот. Выбери действие:", reply_markup=main_menu())

def create_bot_menu():
    markup = InlineKeyboardMarkup()
    options = [
        ("📢 Автопостинг", "create_autoposting_bot"),
        ("💳 Продажа цифровых товаров", "create_digital_goods_bot"),
        ("📊 Арбитраж криптовалют", "create_crypto_arbitrage_bot"),
        ("🖼️ Генерация изображений AI", "create_ai_image_bot"),
        ("📝 Генерация PDF-документов", "create_pdf_bot"),
        ("🔗 Продажа подписок", "create_subscriptions_bot"),
        ("🔍 Поиск airdrop'ов", "create_airdrop_bot"),
        ("🔒 Продажа VPN/прокси", "create_proxy_bot"),
        ("📅 Бронирование услуг", "create_booking_bot"),
        ("🔙 Назад", "main_menu")
    ]
    for text, data in options:
        markup.add(InlineKeyboardButton(text=text, callback_data=data))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_menu_callback(call: CallbackQuery):
    bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_callback(call: CallbackQuery):
    responses = {
        "create_autoposting_bot": "Вы выбрали бот для автопостинга.",
        "create_digital_goods_bot": "Вы выбрали бот для продажи цифровых товаров.",
        "create_crypto_arbitrage_bot": "Вы выбрали бот для арбитража криптовалют.",
        "create_ai_image_bot": "Вы выбрали бот для генерации изображений AI.",
        "create_pdf_bot": "Вы выбрали бот для генерации PDF-документов.",
        "create_subscriptions_bot": "Вы выбрали бот для продажи подписок.",
        "create_airdrop_bot": "Вы выбрали бот для поиска airdrop'ов.",
        "create_proxy_bot": "Вы выбрали бот для продажи VPN/прокси.",
        "create_booking_bot": "Вы выбрали бот для бронирования услуг.",
        "main_menu": "Возвращаемся в главное меню."
    }
    response = responses.get(call.data, "Неизвестный выбор.")
    bot.answer_callback_query(call.id, response)
    if call.data == "main_menu":
        bot.edit_message_text("Главное меню", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    else:
        bot.send_message(call.message.chat.id, response)

@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_handler(call: CallbackQuery):
    info_text = (
        "ℹ️ **Информация о боте**\n\n"
        "🚀 **Функции:**\n"
        "🤖 *Создать бота* – выберите шаблон бота и оплатите создание.\n"
        "👤 *Профиль* – показывает ваш баланс и реферальную ссылку.\n"
        "💰 *Пополнить баланс* – оплата через CryptoBot.\n"
        "💬 *Отзывы* – читайте и оставляйте отзывы.\n\n"
        "📩 Если у вас есть вопросы — пишите в поддержку!"
    )
    bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "privacy")
def privacy_handler(call: CallbackQuery):
    privacy_text = (
        "🔒 **Политика конфиденциальности**\n\n"
        "1️⃣ Ваши данные (имя, ID) хранятся в зашифрованном виде.\n"
        "2️⃣ Мы не передаём информацию третьим лицам.\n"
        "3️⃣ Все платежи через CryptoBot безопасны.\n"
        "4️⃣ Вы можете удалить свой аккаунт в любое время.\n"
    )
    bot.send_message(call.message.chat.id, privacy_text, parse_mode="Markdown")

@app.post("/cryptobot_webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()
    logging.info(f"Webhook received: {data}")

    if "invoice_id" in data and data.get("status") == "paid":
        invoice_id = data["invoice_id"]
        user_id = next((uid for uid, inv_id in pending_payments.items() if inv_id == invoice_id), None)

        if user_id:
            users[user_id]["balance"] += float(data["amount"])
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)
            del pending_payments[user_id]
            bot.send_message(user_id, f"✅ Оплата {data['amount']} USDT получена! Ваш баланс обновлён.")
        else:
            logging.warning("Платеж получен, но пользователь не найден.")
    return {"status": "ok"}

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def pay_handler(call: CallbackQuery):
    user_id = str(call.from_user.id)
    amount_usd = 22.80
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={"asset": "USDT", "currency": "USD", "amount": amount_usd},
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )
        if response.ok:
            data = response.json()
            if "result" in data:
                pay_url = data["result"]["pay_url"]
                pending_payments[user_id] = data["result"]["invoice_id"]
                bot.send_message(call.message.chat.id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(call.message.chat.id, "Ошибка при создании платежа.")
    except Exception as e:
        logging.error(f"Ошибка при создании счета: {e}")
        bot.send_message(call.message.chat.id, "Ошибка при обработке платежа.")

if __name__ == "__main__":
    bot.polling(none_stop=True)
