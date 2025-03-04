import os
import json
import logging
import requests
import telebot
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# === Логирование ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# === Загрузка переменных ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
BOT_PRICE = 29.99  # Стоимость создания бота (USDT)

if not BOT_TOKEN or not CRYPTO_BOT_TOKEN or not ADMIN_ID:
    raise ValueError("❌ Ошибка: не найдены необходимые переменные окружения!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# === Файл пользователей ===
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning("⚠ Ошибка чтения users.json. Создан новый файл.")
                return {}
    return {}

def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_users()

# === Главное меню ===
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🤖 Создать бота"))
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("ℹ️ Информация"))
    return markup

@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username, "bots": []}
        save_users()
    
    logging.info(f"👤 Новый пользователь: {message.from_user.username} (ID: {user_id})")

    bot.send_message(message.chat.id, "👋 Привет! Выберите действие:", reply_markup=main_menu())

# === Логирование всех данных пользователей ===
def log_user_action(user_id, action, data=None):
    user_data = users.get(user_id, {})
    username = user_data.get("username", "Неизвестный")
    log_message = f"📌 Действие: {action} | Пользователь: {username} (ID: {user_id})"
    if data:
        log_message += f" | Данные: {data}"
    
    logging.info(log_message)

# === Обновленный профиль ===
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_callback(message):
    user_id = str(message.from_user.id)
    
    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    username = users[user_id].get("username", "Не указан")
    balance = users[user_id].get("balance", 0)
    bots = users[user_id].get("bots", [])

    bot_list = "\n".join([f"🤖 {bot['name']} – @{bot['username']}" for bot in bots]) if bots else "🚫 Нет созданных ботов"

    bot.send_message(
        message.chat.id,
        f"👤 *Ваш профиль:*\n\n"
        f"🔹 *Имя пользователя:* @{username}\n"
        f"💰 *Баланс:* {balance} USDT\n"
        f"📜 *Ваши боты:*\n{bot_list}",
        parse_mode="Markdown"
    )

    log_user_action(user_id, "Просмотр профиля")

# === Обновленный механизм проверки баланса и оплаты ===
@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def handle_create_bot(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    balance = users[user_id].get("balance", 0)

    if balance < BOT_PRICE:
        payment_url = f"https://t.me/CryptoBot?start=PAYMENT_LINK"
        bot.send_message(
            message.chat.id,
            f"❌ *Недостаточно средств!*\n\n"
            f"Создание бота стоит *{BOT_PRICE} USDT*, а на вашем балансе *{balance} USDT*.\n"
            f"👉 [Пополнить баланс]({payment_url})",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        log_user_action(user_id, "Недостаточно средств", {"Баланс": balance})
        return

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("✅ Подтвердить"), KeyboardButton("❌ Отменить"))
    
    bot.send_message(
        message.chat.id,
        f"⚠️ *Вы уверены, что хотите создать бота за {BOT_PRICE} USDT?*",
        reply_markup=markup,
        parse_mode="Markdown"
    )

    users[user_id]["step"] = "confirm_payment"
    save_users()
    log_user_action(user_id, "Запрос на оплату")

@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("step") == "confirm_payment")
def confirm_payment(message):
    user_id = str(message.from_user.id)

    if message.text == "❌ Отменить":
        users[user_id]["step"] = None
        save_users()
        bot.send_message(message.chat.id, "🚫 Действие отменено.", reply_markup=main_menu())
        log_user_action(user_id, "Отмена создания бота")
        return

    if message.text == "✅ Подтвердить":
        users[user_id]["balance"] -= BOT_PRICE
        users[user_id]["step"] = "choose_bot"
        save_users()

        bot.send_message(message.chat.id, "✅ Оплата прошла успешно! Выберите тип бота:", reply_markup=get_bot_catalog())
        log_user_action(user_id, "Оплата подтверждена", {"Баланс после оплаты": users[user_id]["balance"]})
        return

    bot.send_message(message.chat.id, "❌ Ошибка: выберите '✅ Подтвердить' или '❌ Отменить'.")
    
# === Логирование ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("deploy.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

BASE_DIR = "user_bots"  # Папка для хранения всех ботов
SUPERVISOR_CONF_DIR = "/etc/supervisor/conf.d"  # Директория конфигов Supervisor
USERS_FILE = "users.json"

def load_users():
    """Загружает пользователей из users.json"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning("⚠ Ошибка чтения users.json. Создан новый файл.")
                return {}
    return {}

def save_users(users):
    """Сохраняет данные пользователей"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_users()

# === Шаблон кода для нового бота ===
TEMPLATE_CODE = """import telebot

BOT_TOKEN = "{bot_token}"
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🤖 Привет! Я твой новый бот!")

bot.polling(none_stop=True)
"""

def create_and_run_bot(user_id, bot_data):
    """Создаёт и запускает нового бота"""
    bot_dir = os.path.join(BASE_DIR, f"user_{user_id}_bot")
    
    if not os.path.exists(bot_dir):
        os.makedirs(bot_dir)

    bot_file_path = os.path.join(bot_dir, "bot.py")

    with open(bot_file_path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE_CODE.format(bot_token=bot_data["bot_token"]))

    logging.info(f"✅ Бот создан: {bot_file_path}")

    # Настройка Supervisor для автозапуска бота
    supervisor_conf_path = os.path.join(SUPERVISOR_CONF_DIR, f"user_{user_id}_bot.conf")
    supervisor_config = f"""[program:user_{user_id}_bot]
command=python3 {bot_file_path}
autostart=true
autorestart=true
stderr_logfile={bot_dir}/error.log
stdout_logfile={bot_dir}/output.log
"""

    with open(supervisor_conf_path, "w", encoding="utf-8") as f:
        f.write(supervisor_config)

    # Перезапускаем Supervisor, чтобы он подхватил новый конфиг
    subprocess.run("supervisorctl reread", shell=True, check=True)
    subprocess.run("supervisorctl update", shell=True, check=True)
    subprocess.run(f"supervisorctl start user_{user_id}_bot", shell=True, check=True)

    logging.info(f"🚀 Бот для user_{user_id} запущен через Supervisor!")

    # Сохранение информации о запущенном боте
    users[user_id]["bots"].append({
        "name": bot_data["bot_name"],
        "username": get_bot_username(bot_data["bot_token"]),
        "path": bot_file_path
    })
    save_users(users)

def get_bot_username(bot_token):
    """Получает username бота"""
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    response = requests.get(url).json()
    return response["result"]["username"] if response.get("ok") else "unknown_bot"
