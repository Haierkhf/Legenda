import os
import json
import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import requests

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)

# Файл для хранения данных пользователей
USERS_FILE = "users.json"

# Загрузка данных пользователей
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        users = json.load(file)
else:
    users = {}

# Функция сохранения данных пользователей
def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)

# Функция проверки и создания пользователя
def get_user(user_id):
    if str(user_id) not in users:
        users[str(user_id)] = {
            "balance": 0.0,
            "bots_created": 0,
            "referrals": 0,
            "referral_earnings": 0.0
        }
        save_users()
    return users[str(user_id)]
    # Функция создания главного меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🛠 Создать бота"))
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("💬 Отзывы"))
    markup.add(KeyboardButton("ℹ️ Информация"))
    return markup

# Команда /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.chat.id)
    get_user(user_id)  # Проверка и добавление пользователя в базу

    bot.send_message(
        user_id,
        "👋 Добро пожаловать! Этот бот поможет вам создать собственного Telegram-бота.",
        reply_markup=main_menu()
    )
    # Функция обработки кнопки "ℹ️ Информация"
@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_handler(message):
    info_text = (
        "ℹ️ *Информация о боте:*\n\n"
        "Этот бот позволяет создавать различных Telegram-ботов.\n"
        "Вы можете выбрать один из 9 вариантов, ввести необходимые данные,\n"
        "и бот автоматически создаст, задеплоит и отправит вам готовый бот.\n\n"
        "💰 *Как пополнить баланс?*\n"
        "Перейдите в '👤 Профиль' → 'Пополнить баланс' и следуйте инструкциям.\n\n"
        "🔗 *Реферальная система:*\n"
        "Приглашайте друзей и получайте *15%* от их пополнений на свой баланс.\n"
    )
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔙 Назад"))
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown", reply_markup=markup)
    # Функция создания меню профиля
def profile_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💰 Пополнить баланс"), KeyboardButton("💸 Вывести средства"))
    markup.add(KeyboardButton("🔗 Моя реферальная ссылка"))
    markup.add(KeyboardButton("📊 Моя статистика"))
    markup.add(KeyboardButton("🔙 Назад"))
    return markup

# Обработчик кнопки "👤 Профиль"
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_handler(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)

    balance = user_data["balance"]
    referred_users = len(user_data["referrals"])

    profile_text = (
        f"👤 *Ваш профиль:*\n\n"
        f"💰 *Баланс:* {balance:.2f} USDT\n"
        f"🔗 *Рефералов:* {referred_users} чел.\n\n"
        "Вы можете пополнить баланс, вывести средства или получить свою реферальную ссылку."
    )

    bot.send_message(user_id, profile_text, parse_mode="Markdown", reply_markup=profile_menu())
    # Функция создания чека через CryptoBot API
def create_payment_invoice(user_id, amount):
    try:
        response = requests.post(
            f"https://api.cryptobot.com/createInvoice",
            json={
                "asset": "USDT",
                "amount": amount,
                "description": f"Пополнение баланса на {amount} USDT",
                "hidden_message": f"Пользователь {user_id} пополняет баланс",
                "paid_btn_name": "open_bot",
                "paid_btn_url": "https://t.me/your_crypto_bot"
            },
            headers={"Authorization": f"Bearer {CRYPTOBOT_TOKEN}"}
        ).json()

        return response["result"]["pay_url"] if response["ok"] else None
    except Exception as e:
        print(f"Ошибка при создании чека: {e}")
        return None

# Обработчик кнопки "💰 Пополнить баланс"
@bot.message_handler(func=lambda message: message.text == "💰 Пополнить баланс")
def top_up_balance(message):
    bot.send_message(message.chat.id, "Введите сумму USDT, которую хотите пополнить:")

    @bot.message_handler(content_types=["text"])
    def process_top_up_amount(msg):
        try:
            amount = float(msg.text)
            if amount <= 0:
                bot.send_message(msg.chat.id, "❌ Некорректная сумма. Попробуйте еще раз.")
                return
            
            pay_url = create_payment_invoice(msg.chat.id, amount)
            if pay_url:
                bot.send_message(msg.chat.id, f"💰 Оплатите {amount} USDT по ссылке:\n{pay_url}")
            else:
                bot.send_message(msg.chat.id, "❌ Ошибка при создании чека. Попробуйте позже.")
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Введите корректное число.")
            # Обработчик кнопки "💸 Вывести средства"
@bot.message_handler(func=lambda message: message.text == "💸 Вывести средства")
def withdraw_balance(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)

    bot.send_message(message.chat.id, f"💰 Ваш баланс: {user_data['balance']:.2f} USDT\nВведите сумму для вывода:")

    @bot.message_handler(content_types=["text"])
    def process_withdraw(msg):
        try:
            amount = float(msg.text)
            if amount <= 0 or amount > user_data["balance"]:
                bot.send_message(msg.chat.id, "❌ Некорректная сумма для вывода.")
                return
            
            # Здесь добавьте ваш процесс вывода (например, через CryptoBot)
            user_data["balance"] -= amount
            save_user_data()
            bot.send_message(msg.chat.id, f"✅ Запрос на вывод {amount} USDT отправлен. Ожидайте обработки.")
        except ValueError:
            bot.send_message(msg.chat.id, "❌ Введите корректное число.")
            # Обработчик кнопки "🔗 Моя реферальная ссылка"
@bot.message_handler(func=lambda message: message.text == "🔗 Моя реферальная ссылка")
def referral_link(message):
    user_id = str(message.chat.id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
    
    bot.send_message(user_id, f"🔗 Ваша реферальная ссылка:\n{ref_link}\n\n"
                              "Приглашайте друзей и получайте 15% с их пополнений!")
    # Обработчик кнопки "📊 Моя статистика"
@bot.message_handler(func=lambda message: message.text == "📊 Моя статистика")
def user_statistics(message):
    user_id = str(message.chat.id)
    user_data = get_user(user_id)

    stats_text = (
        f"📊 *Ваша статистика:*\n\n"
        f"🔹 *Создано ботов:* {user_data.get('bots_created', 0)}\n"
        f"🔹 *Рефералов:* {len(user_data.get('referrals', []))}\n"
        f"🔹 *Заработано с рефералов:* {user_data.get('earned_from_referrals', 0.0):.2f} USDT\n"
    )

    bot.send_message(user_id, stats_text, parse_mode="Markdown")
    # Функция создания меню выбора типа бота
def bot_selection_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    bot_types = [
        "1️⃣ Автоответчик", "2️⃣ Бот-магазин", "3️⃣ Крипто-бот",
        "4️⃣ Чат-бот", "5️⃣ Бот для подписок", "6️⃣ Личный помощник",
        "7️⃣ Парсер", "8️⃣ Арбитражный бот", "9️⃣ Уникальный бот"
    ]
    for bot_type in bot_types:
        markup.add(KeyboardButton(bot_type))
    markup.add(KeyboardButton("🔙 Назад"))
    return markup

# Обработчик кнопки "🤖 Создать бота"
@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def create_bot_handler(message):
    bot.send_message(message.chat.id, "Выберите тип бота:", reply_markup=bot_selection_menu())
    # Словарь для временного хранения данных пользователя о создаваемом боте
user_bot_data = {}

# Обработчик выбора типа бота
@bot.message_handler(func=lambda message: message.text.startswith(("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣")))
def bot_type_selected(message):
    user_id = message.chat.id
    user_bot_data[user_id] = {"type": message.text}
    
    bot.send_message(user_id, "Введите название вашего бота:")
    
    @bot.message_handler(content_types=["text"])
    def get_bot_name(msg):
        user_bot_data[user_id]["name"] = msg.text
        bot.send_message(user_id, "Теперь введите токен вашего бота (получите в @BotFather):")
        
        @bot.message_handler(content_types=["text"])
        def get_bot_token(msg2):
            user_bot_data[user_id]["token"] = msg2.text
            
            # Дополнительные параметры в зависимости от типа бота
            if user_bot_data[user_id]["type"] in ["3️⃣ Крипто-бот", "5️⃣ Бот для подписок"]:
                bot.send_message(user_id, "Введите токен CryptoBot:")
                @bot.message_handler(content_types=["text"])
                def get_crypto_token(msg3):
                    user_bot_data[user_id]["crypto_token"] = msg3.text
                    request_payment(user_id)
                bot.register_next_step_handler(msg2, get_crypto_token)
            elif user_bot_data[user_id]["type"] in ["6️⃣ Личный помощник"]:
                bot.send_message(user_id, "Введите ID администратора:")
                @bot.message_handler(content_types=["text"])
                def get_admin_id(msg3):
                    user_bot_data[user_id]["admin_id"] = msg3.text
                    request_payment(user_id)
                bot.register_next_step_handler(msg2, get_admin_id)
            else:
                request_payment(user_id)
                # Функция проверки баланса и создания платежа
def request_payment(user_id):
    user_data = get_user(str(user_id))
    
    bot_price = 29.99  # Цена бота в USDT
    if user_data["balance"] < bot_price:
        bot.send_message(user_id, f"❌ У вас недостаточно средств ({user_data['balance']} USDT). Генерируем чек на оплату...")
        
        pay_url = create_payment_invoice(user_id, bot_price)
        if pay_url:
            bot.send_message(user_id, f"💰 Оплатите {bot_price} USDT по ссылке:\n{pay_url}")
        else:
            bot.send_message(user_id, "❌ Ошибка при создании чека. Попробуйте позже.")
    else:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("✅ Подтвердить"), KeyboardButton("❌ Отменить"))
        
        bot.send_message(user_id, f"💰 На вашем балансе {user_data['balance']} USDT. Хотите оплатить создание бота за {bot_price} USDT?", reply_markup=markup)

# Обработчик подтверждения оплаты
@bot.message_handler(func=lambda message: message.text in ["✅ Подтвердить", "❌ Отменить"])
def confirm_payment(message):
    user_id = message.chat.id
    if message.text == "✅ Подтвердить":
        user_data = get_user(str(user_id))
        bot_price = 29.99
        user_data["balance"] -= bot_price
        save_user_data()
        
        bot.send_message(user_id, "✅ Оплата прошла успешно! Начинаем создание бота...")
        deploy_bot(user_id)
    else:
        bot.send_message(user_id, "❌ Оплата отменена. Возвращаемся в главное меню.")
        # Функция деплоя бота пользователя
def deploy_bot(user_id):
    user_data = user_bot_data.get(user_id)
    
    if not user_data:
        bot.send_message(user_id, "❌ Ошибка: данные о боте не найдены.")
        return
    
    bot_code = f"""
import telebot

bot = telebot.TeleBot("{user_data['token']}")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Это ваш бот {user_data['name']}.")

bot.polling(none_stop=True)
    """
    
    bot_filename = f"user_bot_{user_id}.py"
    with open(bot_filename, "w") as bot_file:
        bot_file.write(bot_code)
    
    bot.send_document(user_id, open(bot_filename, "rb"), caption="Ваш бот успешно создан! Запустите его на сервере.")
    
    # Запуск бота через Supervisor/systemd
    subprocess.run(["supervisorctl", "restart", f"user_bot_{user_id}"])
    
    bot.send_message(user_id, f"✅ Ваш бот {user_data['name']} запущен и работает!")
    # Функция автоматического перезапуска бота после сбоя
def auto_restart_bots():
    while True:
        for user_id, bot_data in user_bot_data.items():
            bot_filename = f"user_bot_{user_id}.py"
            result = subprocess.run(["pgrep", "-f", bot_filename], capture_output=True, text=True)
            if not result.stdout:
                bot.send_message(user_id, f"⚠ Ваш бот {bot_data['name']} был остановлен и перезапускается...")
                subprocess.run(["supervisorctl", "restart", f"user_bot_{user_id}"])
        time.sleep(60)

# Запуск потока для отслеживания ботов
restart_thread = threading.Thread(target=auto_restart_bots, daemon=True)
restart_thread.start()
