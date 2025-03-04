import os
import json
import logging
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CRYPTOBOT_API_KEY = os.environ.get("CRYPTOBOT_API_KEY")
ADMIN_ID = os.environ.get("ADMIN_ID")

if not BOT_TOKEN:
    raise ValueError("Ошибка: BOT_TOKEN не найден!")

if not CRYPTOBOT_API_KEY:
    raise ValueError("Ошибка: CRYPTOBOT_API_KEY не найден!")

if not ADMIN_ID:
    raise ValueError("Ошибка: ADMIN_ID не найден!")

# Преобразование ADMIN_ID в число
ADMIN_ID = int(ADMIN_ID)

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных пользователей
USERS_FILE = "users.json"

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

# Загрузка пользователей из файла
users = load_users()

# Flask сервер для обработки вебхуков
app = Flask(__name__)

# Список ожидающих оплат
pending_payments = {}
# Функция создания главного меню
def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton("🤖 Создать бота", callback_data="create_bot"),
        InlineKeyboardButton("ℹ️ Информация", callback_data="info"),
        InlineKeyboardButton("💬 Отзывы", url="https://t.me/nwf0L9BBCoJYl2Qy"),
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("🔒 Политика конфиденциальности", callback_data="privacy"),
    ]
    markup.add(*buttons)
    return markup

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "username": message.from_user.username,
            "chat_id": message.chat.id
        }
        save_users(users)

    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=main_menu())
# Функция создания меню с типами ботов
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

# Обработчик нажатия на кнопку "Создать бота"
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def handle_create_bot(call):
    bot.send_message(call.message.chat.id, "Выберите тип бота:", reply_markup=create_bot_menu())

# Обработчик выбора типа бота
@bot.callback_query_handler(func=lambda call: call.data.startswith("create_"))
def create_bot_callback(call):
    bot_type = call.data.replace("create_", "")  # Убираем префикс "create_"
    
    bot_type_names = {
        "autoposting_bot": "📢 Автопостинг",
        "digital_goods_bot": "🛍 Продажа цифровых товаров",
        "crypto_arbitrage_bot": "📈 Арбитраж криптовалют",
        "ai_image_bot": "🎨 Генерация AI-изображений",
        "pdf_bot": "📄 Генерация PDF-документов",
        "subscriptions_bot": "🔄 Продажа подписок",
        "airdrop_bot": "🔍 Поиск airdrop'ов",
        "proxy_bot": "🔐 Продажа VPN/прокси",
        "booking_bot": "📅 Бронирование услуг"
    }

    if bot_type not in bot_type_names:
        bot.send_message(call.message.chat.id, "❌ Ошибка: неизвестный тип бота")
        return

    user_id = str(call.from_user.id)

    if user_id not in users:
        users[user_id] = {}

    users[user_id]["selected_bot_type"] = bot_type  # Сохраняем выбранный тип
    users[user_id]["state"] = "waiting_for_bot_name"  # Меняем состояние
    save_users(users)  # Сохраняем в базу

    bot.send_message(call.message.chat.id, f"Вы выбрали: {bot_type_names[bot_type]}. Введите имя бота:")
    bot.register_next_step_handler(call.message, process_bot_name)  # Ждём ввод имени бота
# Функция обработки ввода имени бота
def process_bot_name(message):
    user_id = str(message.from_user.id)
    bot_name = message.text.strip()

    if user_id not in users or "selected_bot_type" not in users[user_id]:
        bot.send_message(message.chat.id, "❌ Ошибка: пожалуйста, начните процесс заново.")
        return

    users[user_id]["bot_name"] = bot_name  # Сохраняем имя бота
    save_users(users)

    bot.send_message(message.chat.id, f"✅ Ваш бот '{bot_name}' зарегистрирован! Проверяем баланс...")
    check_user_balance(user_id, message.chat.id)
    # Обработчик кнопки "👤 Профиль"
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    user_id = str(call.from_user.id)

    if user_id not in users:
        bot.send_message(call.message.chat.id, "❌ Ошибка: ваш профиль не найден. Попробуйте снова.")
        return

    username = users[user_id].get("username", "Не указан")
    balance = users[user_id].get("balance", 0)

    # Экранируем специальные символы Markdown
    username_safe = username.replace("_", "\\_").replace("*", "\\*").replace("[", "\").replace("]", "\")

    profile_text = (f"👤 *Ваш профиль:*\n\n"
                    f"🔹 *Имя пользователя:* @{username_safe}\n"
                    f"💰 *Баланс:* {balance} USDT")

    bot.send_message(call.message.chat.id, profile_text, parse_mode="MarkdownV2")  # Используем MarkdownV2

# Обработчик кнопки "ℹ️ Информация"
@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_callback(call):
    info_text = (
        "ℹ️ *Информация о сервисе:*\n\n"
        "Наш бот предоставляет удобные инструменты для автоматизации "
        "различных процессов, таких как:\n"
        "- Автопостинг\n"
        "- Продажа цифровых товаров\n"
        "- Арбитраж криптовалют\n"
        "- Генерация PDF и изображений AI\n"
        "- Управление подписками\n\n"
        "📌 Выберите нужный вам бот в меню и начните работать прямо сейчас!\n\n"
        "💰 *Как пополнить баланс?*\n"
        "1. Нажмите кнопку 'Создать бота'.\n"
        "2. Выберите нужный тип бота.\n"
        "3. Следуйте инструкции по оплате.\n"
        "4. После успешного платежа ваш баланс обновится автоматически.\n\n"
        "📞 Если у вас возникли вопросы, свяжитесь с поддержкой."
    )
    bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

# Обработчик кнопки "🔒 Политика конфиденциальности"
@bot.callback_query_handler(func=lambda call: call.data == "privacy")
def privacy_callback(call):
    privacy_text = (
        "🔒 *Политика конфиденциальности:*\n\n"
        "Мы уважаем вашу конфиденциальность и гарантируем защиту ваших данных. "
        "Ваши личные данные не передаются третьим лицам и используются только "
        "для улучшения работы бота.\n\n"
        "❗ Используя нашего бота, вы соглашаетесь с данной политикой."
    )
    bot.send_message(call.message.chat.id, privacy_text, parse_mode="Markdown")

# Функция проверки баланса перед созданием бота
def check_user_balance(user_id, chat_id):
    users = user.get(user_id, {})
    balance = users.get("balance", 0)
    bot_price = 22.80  # Цена создания бота в USDT

    if balance >= bot_price:
        users[user_id]["balance"] -= bot_price  # Списываем сумму
        save_users(users)
        finalize_bot_creation(user_id, chat_id)
    else:
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно еще {missing_amount} USDT.")
        send_payment_link(user_id, chat_id, missing_amount)

# Функция создания счета через Crypto Bot API
def create_invoice(user_id, amount):
    data = {
        "asset": "USDT",  # Валюта платежа
        "amount": amount,  # Сумма оплаты
        "description": "Пополнение баланса",
        "hidden_message": "Спасибо за оплату!",  # Сообщение после оплаты
        "paid_btn_name": "openBot",  # Кнопка после оплаты
        "payload": f"user_{user_id}",  # Уникальный идентификатор
        "allow_comments": False,
        "allow_anonymous": False
    }

    headers = {"Crypto-Pay-API-Token": TOKEN}
    response = requests.post(CRYPTO_PAY_URL, json=data, headers=headers)

    if response.status_code == 200:
        invoice_data = response.json()
        return invoice_data["result"]["pay_url"]  # Возвращаем ссылку на оплату
    else:
        print("Ошибка при создании счета:", response.text)  # Логируем ошибку
        return None  # Если ошибка, возвращаем None

# Функция отправки ссылки на оплату
def send_payment_link(user_id, chat_id, amount):
    payment_url = create_invoice(user_id, amount)  # Создаем счет

    if payment_url:
        bot.send_message(
            chat_id,
            f"💳 Для пополнения баланса на {amount} USDT перейдите по ссылке:\n\n"
            f"[Оплатить через CryptoBot]({payment_url})",
            parse_mode="Markdown",
        )
    else:
        bot.send_message(chat_id, "❌ Ошибка при создании платежной ссылки. Попробуйте позже.")

# Функция проверки баланса перед созданием бота
def check_user_balance(user_id, chat_id):
    user = users.get(user_id, {})
    balance = user.get("balance", 0)
    bot_price = 22.80  # Цена создания бота в USDT

    if balance >= bot_price:
        users[user_id]["balance"] -= bot_price  # Списываем сумму
        save_users(users)
        finalize_bot_creation(user_id, chat_id)
    else:
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно еще {missing_amount} USDT.")
        send_payment_link(user_id, chat_id, missing_amount)

# Функция создания счета через Crypto Bot API
def create_invoice(user_id, amount):
    data = {
        "asset": "USDT",  # Валюта платежа (можно заменить на BTC, TON и др.)
        "amount": amount,  # Сумма оплаты
        "description": "Пополнение баланса",
        "hidden_message": "Спасибо за оплату!",  # Сообщение после оплаты
        "paid_btn_name": "openBot",  # Кнопка после оплаты
        "payload": f"user_{user_id}",  # Уникальный ID юзера
        "allow_comments": False,
        "allow_anonymous": False
    }

    headers = {"Crypto-Pay-API-Token": TOKEN}
    response = requests.post(CRYPTO_PAY_URL, json=data, headers=headers)

    if response.status_code == 200:
        invoice = response.json()
        return invoice["result"]["invoice_url"]  # Возвращаем реальную ссылку на оплату
    else:
        print("Ошибка создания платежа:", response.json())  # Выводим ошибку в консоль
        return None  # Если ошибка, возвращаем None

# Функция отправки ссылки на оплату
def send_payment_link(user_id, chat_id, amount):
    payment_url = create_invoice(user_id, amount)

    if payment_url:
        bot.send_message(
            chat_id,
            f"💳 Для пополнения баланса на {amount} USDT перейдите по ссылке:\n\n"
            f"[Оплатить через CryptoBot]({payment_url})",
            parse_mode="Markdown",
        )
    else:
        bot.send_message(chat_id, "❌ Ошибка создания платежа. Попробуйте позже.")
    # Вебхук для обработки платежей CryptoBot
@app.route("/cryptobot_webhook", methods=["POST"])
def cryptobot_webhook():
    data = request.json
    print(f"Получены данные от CryptoBot: {data}")

    if not data or "invoice_id" not in data or "status" not in data:
        return {"status": "error", "message": "Неверные данные"}

    invoice_id = data["invoice_id"]
    status = data["status"]

    # Проверяем, есть ли этот инвойс в ожидающих платежах
    user_id = next((uid for uid, inv_id in pending_payments.items() if inv_id == invoice_id), None)

    if user_id and status == "paid":
        amount = float(data.get("amount", 0))
        update_balance(user_id, amount)
        bot.send_message(users[user_id]["chat_id"], f"✅ Оплата {amount} USDT получена, баланс пополнен!")
        del pending_payments[user_id]  # Удаляем из списка ожидания

    return {"status": "ok"}
    # Функция завершения создания бота после успешной оплаты
def finalize_bot_creation(user_id, chat_id):
    if user_id not in users or "selected_bot_type" not in users[user_id]:
        bot.send_message(chat_id, "❌ Ошибка: не найден выбранный тип бота.")
        return

    bot_type = users[user_id]["selected_bot_type"]
    bot_name = users[user_id].get("bot_name", "Без имени")

    bot.send_message(
        chat_id,
        f"✅ Ваша заявка отправлена разработчику!\n\n"
        f"🔹 *Название бота:* {bot_name}\n"
        f"🔹 *Тип:* {bot_type}\n\n"
        f"⏳ Среднее время создания: *72 часа*.\n"
        f"🔔 Вы получите уведомление, когда бот будет готов!",
        parse_mode="Markdown",
    )

    # Уведомление администратору
    bot.send_message(
        ADMIN_ID,
        f"🔔 *Новая заявка на бота!*\n\n"
        f"👤 Пользователь: @{users[user_id].get('username', 'Неизвестный')}\n"
        f"🔹 Название: {bot_name}\n"
        f"🔹 Тип: {bot_type}\n",
        parse_mode="Markdown",
    )

    # Очистка состояния
    users[user_id]["state"] = None
    save_users(users)
if __name__ == "__main__":
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
