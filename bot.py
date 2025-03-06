import os
import json
import telebot
from telebot import types
from dotenv import load_dotenv
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import requests
import subprocess
import time  # Добавлен import time
import logging
import shutil
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

print("BOT_TOKEN:", BOT_TOKEN)
print("CRYPTO_BOT_TOKEN:", CRYPTO_BOT_TOKEN)
print("ADMIN_ID:", ADMIN_ID)

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных пользователей
USERS_FILE = "users.json"

# Функция загрузки данных пользователей
def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Функция сохранения данных пользователей
def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# Функция логирования действий
def log_action(user_id, action):
    users = load_users()  # Загружаем пользователей
    user_id_str = str(user_id)  # Преобразуем ID в строку

    if user_id_str not in users:
        users[user_id_str] = {"balance": 0, "actions": []}  # Создаем запись

    users[user_id_str]["actions"].append(action)  # Добавляем действие
    save_users(users)  # Сохраняем изменения
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    log_action(user_id, "запустил бота")

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = ["👤 Профиль", "🤖 Создать бота", "⭐ Отзывы", "ℹ️ Информация"]
    markup.add(*[KeyboardButton(btn) for btn in buttons])

    bot.send_message(user_id, "👋 Добро пожаловать! Выберите действие:", reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile(message):
    user_id = message.chat.id
    users = load_users()
    user_data = users.get(str(user_id), {"balance": 0, "actions": []})
    
    balance = user_data["balance"]
    actions = "\n".join(user_data["actions"][-5:]) or "Нет действий"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 Пополнить", callback_data="deposit"))
    markup.add(InlineKeyboardButton("💸 Вывести", callback_data="withdraw"))
    markup.add(InlineKeyboardButton("📊 Статистика", callback_data="stats"))
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(user_id, f"💰 Баланс: {balance}$\n📜 Последние действия:\n{actions}", reply_markup=markup)
    
@bot.callback_query_handler(func=lambda call: call.data == "deposit")
def deposit(call):
    bot.send_message(call.message.chat.id, "Введите сумму для пополнения (мин. 1$):")
    bot.register_next_step_handler(call.message, process_deposit)

def process_deposit(message):
    user_id = message.chat.id
    try:
        amount = float(message.text)
        if amount < 1:
            bot.send_message(user_id, "❌ Минимальная сумма пополнения 1$. Попробуйте снова.")
            return

        payment_link = f"https://t.me/CryptoBot?start=pay_{amount}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Оплатить", url=payment_link))
        
        bot.send_message(user_id, f"💵 Перейдите по ссылке и оплатите {amount}$", reply_markup=markup)

    except ValueError:
        bot.send_message(user_id, "❌ Введите корректное число.")
        
@bot.callback_query_handler(func=lambda call: call.data == "withdraw")
def withdraw(call):
    bot.send_message(call.message.chat.id, "Введите сумму для вывода (мин. 10$):")
    bot.register_next_step_handler(call.message, process_withdraw)

def process_withdraw(message):
    user_id = message.chat.id
    try:
        amount = float(message.text)
        users = load_users()
        balance = users.get(str(user_id), {}).get("balance", 0)

        if amount < 10:
            bot.send_message(user_id, "❌ Минимальная сумма вывода 10$.")
            return
        
        if amount > balance:
            bot.send_message(user_id, "❌ Недостаточно средств на балансе.")
            return

        users[str(user_id)]["balance"] -= amount
        save_users(users)
        
        bot.send_message(user_id, "✅ Ваша заявка на вывод принята. Деньги поступят в течение 48 часов.")
        bot.send_message(ADMIN_ID, f"🚨 Пользователь {user_id} запросил вывод {amount}$.")

    except ValueError:
        bot.send_message(user_id, "❌ Введите корректное число.")
        
@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_handler(message):
    text = ("ℹ️ В этом разделе вы найдете все ответы на ваши вопросы:\n\n"
            "🔹 *Профиль* - здесь можно пополнить баланс, вывести деньги, "
            "посмотреть статистику и получить реферальную ссылку.\n"
            "🔹 *Создать бота* - выберите тип бота, оплатите создание, "
            "и бот сам создаст и запустит его для вас!\n"
            "🔹 *Отзывы* - здесь можно посмотреть отзывы о нашем сервисе.\n"
            "🔹 *Как пополнить баланс?* - нажмите 'Пополнить' в профиле, "
            "введите сумму, и получите ссылку на оплату через CryptoBot.\n"
            "🔹 *Что такое реферальная система?* - пригласите друзей, "
            "и получайте 15% с их пополнений на ваш баланс!\n\n"
            "🔹 *Какие токены нужны?*:\n"
            "   - *BOT_TOKEN* (получается в @BotFather) – для работы бота.\n"
            "   - *CRYPTOBOT_TOKEN* (в @CryptoBot) – для платежей.\n"
            "   - *ADMIN_ID* (узнать в @userinfobot) – ID владельца бота.")

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())
    
@bot.message_handler(func=lambda message: message.text == "⭐ Отзывы")
def reviews(message):
    bot.send_message(message.chat.id, "⭐ Посмотреть отзывы: [Отзывы](https://t.me/nWf0L9BBCoJlY2Qy)", parse_mode="Markdown")
    # Обработчик кнопки "🤖 Создать бота"
import json
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

bot = telebot.TeleBot("ВАШ_BOT_TOKEN")
BOT_PRICE = 29.99

def load_users():
    try:
        with open("users.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def create_bot(message):
    user_id = str(message.chat.id)
    users = load_users()
    if user_id not in users:
        users[user_id] = {"balance": 0, "actions": [], "selected_bot": {}}
    save_users(users)

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    bot_types = [
        "📢 Информационный бот", "🛒 Бот-магазин", "🎫 Бот для билетов",
        "💰 Донат-бот", "📩 Бот-рассыльщик", "⚙️ Поддержка клиентов",
        "🔄 Обменный бот", "📊 Бот-аналитик", "🎮 Игровой бот"
    ]
    for bt in bot_types:
        markup.add(KeyboardButton(bt))
    markup.add(KeyboardButton("🔙 Назад"))

    bot.send_message(user_id, "Выберите тип бота:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in [
    "📢 Информационный бот", "🛒 Бот-магазин", "🎫 Бот для билетов",
    "💰 Донат-бот", "📩 Бот-рассыльщик", "⚙️ Поддержка клиентов",
    "🔄 Обменный бот", "📊 Бот-аналитик", "🎮 Игровой бот"
])
def ask_bot_name(message):
    user_id = str(message.chat.id)
    bot_type = message.text

    users = load_users()
    users[user_id]["selected_bot"]["type"] = bot_type
    save_users(users)

    bot.send_message(user_id, "Введите название вашего бота:")
    bot.register_next_step_handler(message, ask_bot_token)

def ask_bot_token(message):
    user_id = str(message.chat.id)
    bot_name = message.text

    users = load_users()
    users[user_id]["selected_bot"]["name"] = bot_name
    save_users(users)

    bot.send_message(user_id, "Отправьте BOT_TOKEN (получите в @BotFather):")
    bot.register_next_step_handler(message, save_bot_token, "bot_token")

def save_bot_token(message, key):
    user_id = str(message.chat.id)
    users = load_users()
    users[user_id]["selected_bot"][key] = message.text
    save_users(users)

    if users[user_id]["selected_bot"]["type"] != "📢 Информационный бот":
        bot.send_message(user_id, "Отправьте CRYPTOBOT_TOKEN (получите в @CryptoBot):")
        bot.register_next_step_handler(message, save_bot_token, "crypto_token")
    else:
        bot.send_message(user_id, "Отправьте ваш ADMIN_ID (узнать в @userinfobot):")
        bot.register_next_step_handler(message, save_bot_token, "admin_id")

@bot.message_handler(func=lambda message: message.text == "💵 Проверить баланс")
def check_balance_before_payment(message):
    user_id = str(message.chat.id)
    users = load_users()
    balance = users[user_id]["balance"]

    if balance < BOT_PRICE:
        payment_link = f"https://t.me/CryptoBot?start=pay_{BOT_PRICE}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Оплатить", url=payment_link))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

        bot.send_message(
            user_id,
            f"❌ Недостаточно средств. Вам нужно {BOT_PRICE}$. Пополните баланс:",
            reply_markup=markup
        )
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_payment"))
        markup.add(InlineKeyboardButton("❌ Отменить", callback_data="back_main"))

        bot.send_message(
            user_id,
            f"💵 С вашего баланса будет списано {BOT_PRICE}$. Подтвердите оплату:",
            reply_markup=markup
        )

@bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def process_payment(call):
    user_id = str(call.message.chat.id)
    users = load_users()

    users[user_id]["balance"] -= BOT_PRICE
    users[user_id]["actions"].append(f"Оплатил {BOT_PRICE}$ за создание бота")
    save_users(users)

    bot.send_message(user_id, "✅ Оплата успешна! Начинаю создание бота...")
    create_and_deploy_bot(user_id)

def create_and_deploy_bot(user_id):
    users = load_users()
    bot_data = users[str(user_id)]["selected_bot"]

    bot_code = f"""
import telebot

BOT_TOKEN = "{bot_data['bot_token']}"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я {bot_data['name']}.")

bot.polling()
"""

    with open(f"{bot_data['name']}.py", "w", encoding="utf-8") as f:
        f.write(bot_code)

    bot.send_message(user_id, f"✅ Ваш бот *{bot_data['name']}* создан и сохранен!")
    
bot.polling()

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Это {bot_data['name']}.")

bot.polling(none_stop=True)
"""

    filename = f"bot_{user_id}.py"
    with open(filename, "w") as f:
        f.write(bot_code)

    # Запуск бота
    subprocess.Popen(["python3", filename])

    # Отправка пользователю файла с кодом и ссылки на бота
    bot.send_document(user_id, open(filename, "rb"))
    bot.send_message(user_id, f"✅ Ваш бот создан и запущен! \n🔗 Ссылка: t.me/{bot_data['name']}")

def monitor_bots():
    while True:
        for file in os.listdir():
            if file.startswith("bot_") and file.endswith(".py"):
                process = subprocess.run(["pgrep", "-f", file], capture_output=True, text=True)
                if not process.stdout.strip():
                    subprocess.Popen(["python3", file])
        time.sleep(60)

import threading
threading.Thread(target=monitor_bots, daemon=True).start()
import time
import os
import subprocess
import threading

def restart_bots():
    while True:
        for file in os.listdir():
            if file.startswith("bot_") and file.endswith(".py"):
                process = subprocess.run(["pgrep", "-f", file], capture_output=True, text=True)
                if not process.stdout.strip():
                    print(f"⚠️ Бот {file} упал! Перезапускаем...")
                    subprocess.Popen(["python3", file])
        time.sleep(30)  # Проверяем каждые 30 секунд

# Запускаем мониторинг в отдельном потоке
threading.Thread(target=restart_bots, daemon=True).start()
def update_bot(user_id):
    filename = f"bot_{user_id}.py"
    if os.path.exists(filename):
        subprocess.run(["pkill", "-f", filename])  # Останавливаем старый процесс
        subprocess.Popen(["python3", filename])  # Запускаем новый
        bot.send_message(user_id, "✅ Ваш бот был успешно обновлен!")
    else:
        bot.send_message(user_id, "❌ Ошибка: Бот не найден.")
if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)
