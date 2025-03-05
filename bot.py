import telebot
import json
import os
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Загрузка переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

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
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {"balance": 0, "actions": []}
    users[str(user_id)]["actions"].append(action)
    save_users(users)
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
def info(message):
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
            "   - BOT_TOKEN (получается в @BotFather) – для работы бота.\n"
            "   - CRYPTOBOT_TOKEN (в @CryptoBot) – для платежей.\n"
            "   - ADMIN_ID (узнать в @userinfobot) – ID владельца бота.")

    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    @bot.message_handler(func=lambda message: message.text == "⭐ Отзывы")
def reviews(message):
    bot.send_message(message.chat.id, "⭐ Посмотреть отзывы: [Отзывы](https://t.me/nWf0L9BBCoJlY2Qy)", parse_mode="Markdown")
    # Обработчик кнопки "🤖 Создать бота"
@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def create_bot_handler(message):
    markup = InlineKeyboardMarkup()
    bot_types = [
        "🛍 Магазин-бот", "💰 Крипто-бот", "📢 Инфо-бот", 
        "🤝 Реферальный бот", "📊 Статистика-бот", "🎫 Бот для билетов", 
        "📝 Форма-бот", "🎮 Игровой бот", "🔐 Авторизационный бот"
    ]
    
    for bot_type in bot_types:
        markup.add(InlineKeyboardButton(bot_type, callback_data=f"select_{bot_type}"))
    
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

    bot.send_message(
        message.chat.id,
        "Выберите тип бота, которого хотите создать 👇",
        reply_markup=markup
    )
    @bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def create_bot(message):
    user_id = message.chat.id
    log_action(user_id, "открыл меню создания бота")

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
    user_id = message.chat.id
    bot_type = message.text

    users = load_users()
    users[str(user_id)]["selected_bot"] = {"type": bot_type}
    save_users(users)

    bot.send_message(user_id, "Введите название вашего бота:")
    bot.register_next_step_handler(message, ask_bot_tokens)
    def ask_bot_tokens(message):
    user_id = message.chat.id
    bot_name = message.text

    users = load_users()
    users[str(user_id)]["selected_bot"]["name"] = bot_name
    save_users(users)

    bot_type = users[str(user_id)]["selected_bot"]["type"]

    bot.send_message(user_id, "Отправьте BOT_TOKEN (получите в @BotFather):")
    bot.register_next_step_handler(message, lambda msg: save_bot_token(msg, "bot_token"))

def save_bot_token(message, key):
    user_id = message.chat.id
    users = load_users()
    users[str(user_id)]["selected_bot"][key] = message.text
    save_users(users)

    if users[str(user_id)]["selected_bot"]["type"] != "📢 Информационный бот":
        bot.send_message(user_id, "Отправьте CRYPTOBOT_TOKEN (получите в @CryptoBot):")
        bot.register_next_step_handler(message, lambda msg: save_bot_token(msg, "crypto_token"))
    else:
        bot.send_message(user_id, "Отправьте ваш ADMIN_ID (узнать в @userinfobot):")
        bot.register_next_step_handler(message, lambda msg: save_bot_token(msg, "admin_id"))
        def check_balance_before_payment(message):
    user_id = message.chat.id
    users = load_users()
    balance = users[str(user_id)]["balance"]

    price = 29.99
    if balance < price:
        payment_link = f"https://t.me/CryptoBot?start=pay_{price}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("💳 Оплатить", url=payment_link))
        markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))

        bot.send_message(user_id, f"❌ Недостаточно средств. Вам нужно {price}$. Пополните баланс:", reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_payment"))
        markup.add(InlineKeyboardButton("❌ Отменить", callback_data="back_main"))

        bot.send_message(user_id, f"💵 С вашего баланса будет списано {price}$. Подтвердите оплату:", reply_markup=markup)
        @bot.callback_query_handler(func=lambda call: call.data == "confirm_payment")
def process_payment(call):
    user_id = call.message.chat.id
    users = load_users()
    
    price = 29.99
    users[str(user_id)]["balance"] -= price
    save_users(users)

    bot.send_message(user_id, "✅ Оплата успешна! Начинаю создание бота...")
    create_and_deploy_bot(user_id)
    import subprocess

def create_and_deploy_bot(user_id):
    users = load_users()
    bot_data = users[str(user_id)]["selected_bot"]

    bot_code = f"""
import telebot
BOT_TOKEN = "{bot_data['bot_token']}"
bot = telebot.TeleBot(BOT_TOKEN)

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
    import time

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
        @bot.message_handler(commands=['restart_all'])
def restart_all_bots(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.send_message(message.chat.id, "🔄 Перезапускаем все боты...")
        for file in os.listdir():
            if file.startswith("bot_") and file.endswith(".py"):
                subprocess.run(["pkill", "-f", file])  # Останавливаем процесс
                subprocess.Popen(["python3", file])  # Запускаем заново
        bot.send_message(message.chat.id, "✅ Все боты перезапущены!")
    else:
        bot.send_message(message.chat.id, "❌ У вас нет доступа к этой команде.")
        
