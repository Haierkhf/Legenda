import os
import json
import logging
import telebot
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CRYPTOBOT_API_KEY = os.environ.get("CRYPTOBOT_API_KEY")
ADMIN_ID = os.environ.get("ADMIN_ID")
CRYPTO_PAY_URL = "https://pay.crypt.bot/api/createInvoice"

if not BOT_TOKEN or not CRYPTOBOT_API_KEY or not ADMIN_ID:
    raise ValueError("Ошибка: не найдены необходимые переменные окружения!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

USERS_FILE = "users.json"

# Функции загрузки и сохранения пользователей
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_users()

app = Flask(__name__)

# Функция создания главного меню (клавиатура под строкой ввода)
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("🤖 Создать бота"),
        KeyboardButton("ℹ️ Информация"),
        KeyboardButton("💬 Отзывы"),
        KeyboardButton("👤 Профиль")
    ]
    markup.add(*buttons)
    return markup

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username, "chat_id": message.chat.id}
        save_users(users)

    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=main_menu())

# Функция создания меню с типами ботов
def create_bot_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    options = [
        "📢 Автопостинг", "💳 Продажа цифровых товаров", "📊 Арбитраж криптовалют",
        "🖼️ Генерация изображений AI", "📝 Генерация PDF-документов",
        "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
        "📅 Бронирование услуг", "🔙 Назад"
    ]
    for text in options:
        markup.add(KeyboardButton(text))
    return markup

# Обработчик кнопок меню
@bot.message_handler(func=lambda message: message.text in ["🤖 Создать бота", "🔙 Назад"])
def handle_create_bot(message):
    bot.send_message(message.chat.id, "Выберите тип бота:", reply_markup=create_bot_menu())

# Обработчик информации
@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_callback(message):
    info_text = (
        "ℹ️ *Информация о сервисе:*\n\n"
        "Наш бот предоставляет удобные инструменты для автоматизации:\n"
        "- Автопостинг\n"
        "- Продажа цифровых товаров\n"
        "- Арбитраж криптовалют\n"
        "- Генерация PDF и изображений AI\n"
        "- Управление подписками\n\n"
        "💰 *Как пополнить баланс?*\n"
        "1. Нажмите кнопку 'Создать бота'.\n"
        "2. Выберите нужный тип бота.\n"
        "3. Следуйте инструкции по оплате.\n"
        "4. После успешного платежа ваш баланс обновится автоматически.\n\n"
        "🔒 *Политика конфиденциальности:*\n"
        "Мы уважаем вашу конфиденциальность и гарантируем защиту ваших данных."
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

# Обработчик профиля
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_callback(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    username = users[user_id].get("username", "Не указан")
    balance = users[user_id].get("balance", 0)
    bot.send_message(message.chat.id, f"👤 Ваш профиль:\n\n🔹 Имя пользователя: @{username}\n💰 Баланс: {balance} USDT")

# Функция проверки баланса перед созданием бота
def check_user_balance(user_id, chat_id):
    balance = users.get(user_id, {}).get("balance", 0)
    bot_price = 22.80

    if balance >= bot_price:
        users[user_id]["balance"] -= bot_price
        save_users(users)
        finalize_bot_creation(user_id, chat_id)
    else:
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно еще {missing_amount} USDT.")
        send_payment_link(user_id, chat_id, missing_amount)

# Функция создания счета через Crypto Bot API
def create_invoice(user_id, amount):
    data = {
        "asset": "USDT",
        "amount": amount,
        "description": "Пополнение баланса",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "openBot",
        "payload": f"user_{user_id}",
        "allow_comments": False,
        "allow_anonymous": False
    }

    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
    response = requests.post(CRYPTO_PAY_URL, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()["result"]["pay_url"]
    else:
        print("Ошибка создания платежа:", response.text)
        return None

# Функция отправки ссылки на оплату
def send_payment_link(user_id, chat_id, amount):
    payment_url = create_invoice(user_id, amount)

    if payment_url:
        bot.send_message(chat_id, f"💳 Пополнение баланса: [Оплатить через CryptoBot]({payment_url})", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ Ошибка создания платежа. Попробуйте позже.")

# Функция уведомления админа о покупке
def finalize_bot_creation(user_id, chat_id):
    bot.send_message(ADMIN_ID, f"🔔 Новый заказ!\n👤 Пользователь: @{users[user_id].get('username', 'Неизвестно')}")
    bot.send_message(chat_id, "✅ Бот успешно куплен и будет создан!")

if __name__ == "__main__":
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
