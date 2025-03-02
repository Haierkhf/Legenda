import logging
import os
import json
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from fastapi import FastAPI, Request

# Загрузка переменных окружения
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("7756038660:AAHgk4D2wRoC45mxg6v5zwMxNtowOyv0JLo")
CRYPTOBOT_API_KEY = os.getenv("347583:AA2FTH9et0kfdviBIOv9RfeDPUYq5HAcbRj")
ADMIN_ID = os.getenv("6402443549")  # ID, куда отправлять информацию о новых ботах

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

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f, indent=4)

pending_payments = {}  # Список ожидающих оплат пользователей

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):  # Исправлено: добавлен JSONDecodeError
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def update_balance(user_id, amount):
    users = load_users()
    if user_id not in users:
        users[user_id] = {"balance": 0}  # Исправлено: создаём пользователя, если его нет
    users[user_id]["balance"] += amount
    save_users(users)

def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        ("🤖 Создать бота", "create_bot"),
        ("ℹ️ Информация", "info"),
        ("💬 Отзывы", "https://t.me/nwf0L9BBCoJYl2Qy"),
        ("👤 Профиль", "profile"),
        ("🔒 Политика конфиденциальности", "privacy")
    ]
    for text, data in buttons:
        markup.add(InlineKeyboardButton(text=text, callback_data=data))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    users = load_users()

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        save_users(users)

    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=main_menu())  # Исправлено: добавлены скобки

def create_bot_menu():
    markup = InlineKeyboardMarkup()
    options = [  # Исправлено: теперь используем options, а не buttons
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
    for text, data in options:  # Исправлено: теперь корректно используется options
        markup.add(InlineKeyboardButton(text=text, callback_data=data))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_callback(call: CallbackQuery):
    bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())
    @bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_type_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    bot_type = call.data

    users = load_users()
    users[user_id] = {"selected_bot_type": bot_type, "state": "waiting_for_name"}
    save_users(users)

    bot.send_message(call.message.chat.id, "Введите название для нового бота:")
    bot.register_next_step_handler(call.message, process_bot_name)

def process_bot_name(message):
    user_id = str(message.from_user.id)
    bot_name = message.text

    users = load_users()
    users[user_id]["bot_name"] = bot_name
    save_users(users)

    price = 22.80  # Цена создания бота
    user_balance = users[user_id].get("balance", 0)

    if user_balance >= price:
        users[user_id]["balance"] -= price
        save_users(users)
        finalize_bot_creation(user_id, message.chat.id)
    else:
        send_payment_link(user_id, message.chat.id, price)

def send_payment_link(user_id, chat_id, price):
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={"asset": "USDT", "currency": "USD", "amount": price},
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )

        if response.ok:
            data = response.json()
            if "result" in data:
                pay_url = data["result"]["pay_url"]
                pending_payments[user_id] = data["result"]["invoice_id"]
                bot.send_message(chat_id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(chat_id, "Ошибка при создании платежа.")
    except Exception as e:
        logging.error(f"Ошибка при создании счета: {e}")
        bot.send_message(chat_id, "Ошибка при обработке платежа.")

def finalize_bot_creation(user_id, chat_id):
    users = load_users()
    bot_type = users[user_id]["selected_bot_type"]
    bot_name = users[user_id]["bot_name"]

    # Отправляем информацию админу
    bot.send_message(ADMIN_ID, f"❗ Новый бот создан!\n👤 Пользователь: {user_id}\n📌 Тип: {bot_type}\n📝 Название: {bot_name}")

    bot.send_message(chat_id, "✅ Ваш бот успешно создан!")
    users[user_id]["state"] = "none"
    save_users(users)
    @app.post("/cryptobot_webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()
    logging.info(f"Webhook received: {data}")

    if "invoice_id" in data and data.get("status") == "paid":
        invoice_id = data["invoice_id"]
        user_id = next((uid for uid, inv_id in pending_payments.items() if inv_id == invoice_id), None)

        if user_id:
            update_balance(user_id, float(data["amount"]))
            finalize_bot_creation(user_id, user_id)  # Завершаем создание бота
            del pending_payments[user_id]
    return {"status": "ok"}
    if __name__ == "__main__":
    logging.info("Бот запущен и готов к работе.")
    bot.polling(none_stop=True)
