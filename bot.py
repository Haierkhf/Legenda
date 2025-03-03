import os
import logging
import json
import requests
import telebot
from telebot import types
from telebot.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

users = {}  # Глобальный словарь пользователей

def handle_user(user_id):
    if user_id not in users:
        users[user_id] = {"selected_bot_type": None, "state": "ожидание"}
    
app = Flask(__name__)

# Загружаем переменные окружения
TELEGRAM_BOT_TOKEN = os.environ.get("BOT_TOKEN")
CRYPTOBOT_API_KEY = os.environ.get("CRYPTOBOT_API_KEY")
ADMIN_ID = os.environ.get("ADMIN_ID")

# Выводим переменные окружения в логи для проверки
print("BOT_TOKEN:", TELEGRAM_BOT_TOKEN if TELEGRAM_BOT_TOKEN else "НЕ НАЙДЕН!")
print("CRYPTOBOT_API_KEY:", CRYPTOBOT_API_KEY if CRYPTOBOT_API_KEY else "НЕ НАЙДЕН!")
print("ADMIN_ID:", ADMIN_ID if ADMIN_ID else "НЕ НАЙДЕН!")

# Проверяем, загружены ли переменные окружения
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Ошибка: BOT_TOKEN пустой!")

if not CRYPTOBOT_API_KEY:
    raise ValueError("Ошибка: CRYPTOBOT_API_KEY не найден! Проверь переменные окружения.")

if not ADMIN_ID:
    raise ValueError("Ошибка: ADMIN_ID не найден! Проверь переменные окружения.")

# Инициализируем бота
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Создание папки для логов
os.makedirs('logs', exist_ok=True)

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
    markup = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton("🤖 Создать бота", callback_data="create_bot"),
        types.InlineKeyboardButton("ℹ Информация", callback_data="info"),
        types.InlineKeyboardButton("💬 Отзывы", url="https://t.me/nwf0L9BBCoJYl2Qy"),
        types.InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        types.InlineKeyboardButton("🔒 Политика конфиденциальности", callback_data="privacy"),
    ]
    markup.add(*buttons)
    return markup


@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = message.from_user.id
    users = load_users()  # Функция для загрузки пользователей из файла

    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "username": message.from_user.username,
            "chat_id": message.chat.id
        }
    else:
        users[user_id]["chat_id"] = message.chat.id  # Обновляем chat_id

    save_users(users)  # Функция для сохранения пользователей в файл

    bot.send_message(
    message.chat.id,
    "Привет! Выберите действие:",
    reply_markup=main_menu()
)
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def handle_profile(call):
    user_id = call.message.chat.id  # Используем call.message

    try:
        users = load_users()

        if user_id in users:
            username = escape_markdown(users[user_id].get("username", "Не указан"))
            balance = users[user_id].get("balance", 0)

            # Генерируем реферальную ссылку
            bot_info = bot.get_me()
            bot_username = bot_info.username
            ref_link = f"https://t.me/{bot_username}?start={user_id}"

            response = (
                f"👤 *Ваш профиль:*\n\n"
                f"🔹 *Имя пользователя:* @{username}\n"
                f"💰 *Баланс:* {balance} USDT\n\n"
                f"🔗 *Ваша реферальная ссылка:*\n{ref_link}"
            )
        else:
            response = "⚠️ Вы не зарегистрированы в системе."

        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке вашего профиля.")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте позже.")
        print(f"Ошибка в handle_profile: {e}")
        
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "create_bot":
        bot.send_message(call.message.chat.id, "Вы выбрали создать бота!")
    elif call.data == "info":
        bot.send_message(call.message.chat.id, "Здесь будет информация.")
    elif call.data == "profile":
        bot.send_message(call.message.chat.id, "Ваш профиль.")
    elif call.data == "privacy":
        bot.send_message(call.message.chat.id, "Политика конфиденциальности.")
        
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("create_"))
def create_bot_type_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    bot_type = call.data

    users = load_users()
    if user_id not in users:
        users[user_id] = {}  # Создаём пользователя, если его нет
    users[user_id].update({"selected_bot_type": bot_type, "state": "waiting_for_bot_name"})
    save_users(users)

    # Эти строки должны быть внутри функции!
    bot.send_message(call.message.chat.id, "Введите название для нового бота")
    bot.register_next_step_handler(call.message, process_bot_name)
    
# <-- Пустая строка перед новой функцией!

def send_payment_link(user_id, chat_id, amount):
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={"asset": "USDT", "currency": "USD", "amount": amount},
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )

        data = response.json()
        
        if "result" in data:
            pay_url = data["result"]["pay_url"]
            bot.send_message(chat_id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(chat_id, "Ошибка: не удалось создать ссылку на оплату.")

    except Exception as e:
        print(f"Ошибка при создании платежа: {e}")
        bot.send_message(chat_id, "Произошла ошибка при обработке платежа.")

def process_bot_name(message):
    user_id = str(message.from_user.id)
    bot_name = message.text

    users = load_users()
    if user_id not in users:
        users[user_id] = {"balance": 0}  # Исправлено: создаём пользователя, если его нет

    users[user_id]["bot_name"] = bot_name
    save_users(users)

    price = 22.80  # Цена создания бота

    user_balance = users[user_id].get("balance", 0)  # Получаем баланс

    if user_balance >= price:
        users[user_id]["balance"] -= price  # Вычитаем стоимость бота
        save_users(users)
        finalize_bot_creation(user_id, message.chat.id)  # Завершаем создание бота
    else:
        send_payment_link(user_id, message.chat.id, price)  # Отправляем ссылку на оплату
    

def finalize_bot_creation(user_id, chat_id):
    users = load_users()

    bot_type = users[user_id].get("selected_bot_type", "Неизвестный бот")
    bot_name = users[user_id].get("bot_name", "Без названия")

    bot.send_message(ADMIN_ID, f"❗ Новый бот создан!\n👤 Пользователь: {user_id}\n📌 Тип: {bot_type}\n📝 Название: {bot_name}")
    bot.send_message(chat_id, "✅ Ваш бот успешно создан!")
    users[user_id]["state"] = "none"
    save_users(users)

# <-- Вынес декоратор `@app.post` из функции!
from flask import Flask, request

app = Flask(__name__)

@app.post("/cryptobot_webhook")
def cryptobot_webhook():
    data = request.json
    print("Получены данные от CryptoBot:", data)
    return "OK", 200

    if "invoice_id" in data and data.get("status") == "paid":
        invoice_id = data["invoice_id"]
        user_id = next((uid for uid, inv_id in pending_payments.items() if inv_id == invoice_id), None)

        if user_id:
            update_balance(user_id, float(data["amount"]))
            finalize_bot_creation(user_id, users[user_id]["chat_id"])
            del pending_payments[user_id]
    return {"status": "ok"}
    
if __name__ == "__main__":
    logging.info("Бот запущен и готов к работе.")
    bot.delete_webhook()
    bot.polling(none_stop=True)
