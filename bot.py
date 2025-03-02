import logging
import os
import json
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from fastapi import FastAPI, Request

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CRYPTOBOT_API_KEY = os.getenv("CRYPTOBOT_API_KEY")

# Проверяем наличие токенов
if not TELEGRAM_BOT_TOKEN or not CRYPTOBOT_API_KEY:
    raise ValueError("Необходимо указать TELEGRAM_BOT_TOKEN и CRYPTOBOT_API_KEY в .env файле!")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
app = FastAPI()

# Создание папки для логов
os.makedirs('logs', exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot_log.log"),
        logging.StreamHandler()
    ]
)

# Файл пользователей
USERS_FILE = "users.json"

# Инициализация users.json, если его нет
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)
        # Функция загрузки пользователей
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Функция сохранения пользователей
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# Функция обновления баланса пользователя
def update_balance(user_id, amount):
    users = load_users()
    if user_id in users:
        users[user_id]["balance"] += amount
        save_users(users)
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
    users = load_users()

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        save_users(users)

    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=main_menu())
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
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()
    
    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80

        if user_balance >= payment_amount:
            users[user_id]["balance"] -= payment_amount
            save_users(users)

            bot.send_message(call.message.chat.id, f"✅ Оплата прошла успешно! Новый баланс: {users[user_id]['balance']} USDT.")
            bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())
        else:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data="pay_create_bot"))
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств. Пополните баланс.", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")
        @bot.callback_query_handler(func=lambda call: call.data == "pay_create_bot")
def pay_create_bot_callback(call: CallbackQuery):
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
                bot.send_message(call.message.chat.id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(call.message.chat.id, "Ошибка при создании платежа.")
    except Exception as e:
        logging.error(f"Ошибка при создании счета: {e}")
        bot.send_message(call.message.chat.id, "Ошибка при обработке платежа.")
        @bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()

    if user_id in users:
        username = users[user_id].get("username", "Не указан")
        balance = users[user_id].get("balance", 0)
        response = f"👤 Ваш профиль:\n🔹 Имя пользователя: @{username}\n💰 Баланс: {balance} USDT"
    else:
        response = "⚠️ Вы не зарегистрированы в системе."

    bot.send_message(call.message.chat.id, response)

if __name__ == "__main__":
    logging.info("Бот запущен.")
    bot.polling(none_stop=True)
    
