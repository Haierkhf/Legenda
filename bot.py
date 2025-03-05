import os
import json
import logging
import threading
import time
import subprocess
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
    # Функция безопасного запуска основного бота
def start_bot():
    while True:
        try:
            logging.info("✅ Основной бот запущен.")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logging.error(f"Ошибка в основном боте: {traceback.format_exc()}")
            time.sleep(5)  # Ждем перед повторным запуском
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

# Профильное меню
def profile_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔙 Назад"))
    return kb

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    args = message.get_args()
    register_user(user_id)

    if args.startswith("ref_"):
        referrer_id = args.replace("ref_", "")
        if referrer_id != user_id and referrer_id in users and users[user_id]["referrer"] is None:
            users[user_id]["referrer"] = referrer_id
            users[referrer_id]["referrals"] += 1
            save_users()

    await message.answer("👋 Привет! Выберите действие:", reply_markup=main_menu())

# Профиль пользователя
@dp.message_handler(lambda message: message.text == "👤 Профиль")
async def profile_handler(message: types.Message):
    user_id = str(message.from_user.id)
    register_user(user_id)

    data = users[user_id]
    ref_link = get_ref_link(user_id)

    text = (f"👤 *Ваш профиль:*\n"
            f"💰 Баланс: {data['balance']} USDT\n"
            f"🤖 Создано ботов: {data['bots_created']}\n"
            f"👥 Рефералы: {data['referrals']}\n"
            f"💵 Заработано с рефералов: {data['ref_earnings']} USDT\n\n"
            f"🔗 *Ваша реферальная ссылка:*\n`{ref_link}`")

    await message.answer(text, reply_markup=profile_menu(), parse_mode="Markdown")

# Пополнение баланса через CryptoBot
@dp.message_handler(lambda message: message.text == "💰 Пополнить баланс")
async def top_up_balance(message: types.Message):
    user_id = str(message.from_user.id)
    invoice = create_cryptobot_invoice(user_id, 10)  # Минимальная сумма 1 USDT
    if invoice:
        await message.answer(f"💳 Для пополнения нажмите:\n{invoice}")
    else:
        await message.answer("❌ Ошибка при создании платежа.")

def create_cryptobot_invoice(user_id, amount):
    url = f"https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    data = {
        "asset": "USDT", "amount": amount, "description": "Пополнение баланса",
        "hidden_message": user_id, "allow_comments": False, "allow_anonymous": False
    }

    try:
        response = requests.post(url, json=data, headers=headers).json()
        return response.get("result", {}).get("pay_url")
    except:
        return None

# Проверка платежей (автоначисление)
async def check_payments():
    url = f"https://pay.crypt.bot/api/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}

    try:
        response = requests.get(url, headers=headers).json()
        for invoice in response["result"]:
            if invoice["status"] == "paid":
                user_id = invoice["hidden_message"]
                amount = float(invoice["amount"])
                
                if user_id in users:
                    users[user_id]["balance"] += amount
                    referrer_id = users[user_id]["referrer"]
                    
                    if referrer_id:
                        bonus = round(amount * 0.15, 2)
                        users[referrer_id]["balance"] += bonus
                        users[referrer_id]["ref_earnings"] += bonus
                        await bot.send_message(referrer_id, f"🎉 Вам начислено {bonus} USDT за реферала!")

                    save_users()
    except:
        pass
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
        try:
            # Загрузка данных о ботах из файла, если user_bot_data не является глобальной переменной
            with open("users.json", "r") as file:
                user_bot_data = json.load(file)

            for user_id, bot_data in user_bot_data.items():
                bot_filename = f"user_bot_{user_id}.py"

                # Проверяем, запущен ли бот
                result = subprocess.run(["pgrep", "-af", "python"], capture_output=True, text=True)

                if bot_filename not in result.stdout:
                    logging.warning(f"⚠️ Бот {bot_data['name']} ({user_id}) не запущен. Перезапускаем...")

                    # Перезапуск бота через Supervisor
                    subprocess.run(["supervisorctl", "restart", f"user_bot_{user_id}"])

            time.sleep(60)  # Проверяем ботов каждую минуту

        except Exception as e:
            logging.error(f"Ошибка в auto_restart_bots: {traceback.format_exc()}")

# Запуск потока для отслеживания ботов
restart_thread = threading.Thread(target=auto_restart_bots, daemon=True)
restart_thread.start()
def main():
    # Запуск основного бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()

    # Запуск функции авто-ребута ботов
    restart_thread = threading.Thread(target=auto_restart_bots, daemon=True)
    restart_thread.start()

    bot_thread.join()  # Ожидание завершения основного бота

if __name__ == "__main__":
    main()
