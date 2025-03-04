import os
import json
import logging
import requests
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# === НАСТРОЙКА ЛОГИРОВАНИЯ ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")  # API-ключ от CryptoBot
ADMIN_ID = os.getenv("ADMIN_ID")

if not BOT_TOKEN or not CRYPTO_BOT_TOKEN or not ADMIN_ID:
    logging.error("❌ Ошибка: Не найдены все нужные переменные окружения!")
    raise ValueError("BOT_TOKEN, CRYPTO_BOT_TOKEN или ADMIN_ID отсутствуют!")

ADMIN_ID = int(ADMIN_ID)  # Убеждаемся, что это число
bot = telebot.TeleBot(BOT_TOKEN)

# === ЗАГРУЗКА ПОЛЬЗОВАТЕЛЕЙ ===
USERS_FILE = "users.json"

def load_users():
    """Загрузка пользователей из файла"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning("⚠️ Ошибка чтения users.json. Создаю новый файл.")
                return {}
    return {}

def save_users():
    """Автосохранение users.json при изменении данных"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

users = load_users()

# === ГЛАВНОЕ МЕНЮ ===
def main_menu():
    """Создаёт клавиатуру главного меню"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🤖 Создать бота", callback_data="create_bot"))
    markup.add(InlineKeyboardButton("👤 Профиль", callback_data="profile"))
    markup.add(InlineKeyboardButton("ℹ️ Информация", callback_data="info"))
    markup.add(InlineKeyboardButton("💬 Отзывы", url="https://t.me/nWf0L9BBCoJlY2Qy"))  # Ссылка на отзывы
    return markup

# === ОБРАБОТЧИК /start ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    """Обрабатывает команду /start и отправляет главное меню"""
    user_id = str(message.from_user.id)

    # Если пользователь новый — добавляем в базу
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username, "chat_id": message.chat.id}
        save_users()

    bot.send_message(
        message.chat.id,
        "👋 Привет! Выберите действие:",
        reply_markup=main_menu()
    )

# === ОБРАБОТЧИК КНОПОК ГЛАВНОГО МЕНЮ ===
@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_callback(call):
    """Вывод информации о сервисе"""
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
    bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call):
    """Выводит информацию о профиле пользователя"""
    user_id = str(call.from_user.id)

    if user_id not in users:
        bot.send_message(call.message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    username = users[user_id].get("username", "Не указан")
    balance = users[user_id].get("balance", 0)

    bot.send_message(
        call.message.chat.id,
        f"👤 *Ваш профиль:*\n\n"
        f"🔹 *Имя пользователя:* @{username}\n"
        f"💰 *Баланс:* {balance} USDT",
        parse_mode="Markdown"
    )
# === МЕНЮ ВЫБОРА ТИПА БОТА ===
def create_bot_menu():
    """Создаёт меню выбора типа бота"""
    markup = InlineKeyboardMarkup()
    bot_types = [
        ("📢 Автопостинг", "autopost"),
        ("💳 Продажа товаров", "digital_goods"),
        ("📊 Арбитраж криптовалют", "crypto_arbitrage"),
        ("🖼️ Генерация изображений AI", "ai_images"),
        ("📝 Генерация PDF", "pdf_generator"),
        ("🔗 Продажа подписок", "subscriptions"),
        ("🔍 Поиск airdrop'ов", "airdrop_search"),
        ("🔒 Продажа VPN/прокси", "vpn_proxy"),
        ("📅 Бронирование услуг", "booking"),
        ("🔙 Назад", "main_menu")
    ]
    for name, callback in bot_types:
        markup.add(InlineKeyboardButton(name, callback_data=f"bot_type_{callback}"))
    return markup

# === ОБРАБОТЧИК "СОЗДАТЬ БОТА" ===
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def handle_create_bot(call):
    """Выбор типа бота"""
    bot.send_message(call.message.chat.id, "🔹 Выберите тип бота:", reply_markup=create_bot_menu())

# === ОБРАБОТЧИК ВЫБОРА ТИПА БОТА ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("bot_type_"))
def process_bot_type(call):
    """Сохраняем тип бота и запрашиваем имя"""
    user_id = str(call.from_user.id)
    bot_type = call.data.replace("bot_type_", "")

    users[user_id]["selected_bot_type"] = bot_type
    users[user_id]["state"] = "waiting_for_bot_name"
    save_users()

    bot.send_message(call.message.chat.id, f"Вы выбрали: *{bot_type}*\n\nВведите имя для вашего бота:", parse_mode="Markdown")

# === ОБРАБОТЧИК ВВОДА ИМЕНИ БОТА ===
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("state") == "waiting_for_bot_name")
def process_bot_name(message):
    """Сохраняем имя бота и предлагаем оплату"""
    user_id = str(message.from_user.id)
    bot_name = message.text

    users[user_id]["bot_name"] = bot_name
    users[user_id]["state"] = "waiting_for_payment"
    save_users()

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_payment_{user_id}"))
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment"))

    bot.send_message(
        message.chat.id,
        f"✅ Имя бота сохранено: *{bot_name}*\n\n"
        f"💰 Стоимость создания: *29.99 USDT*.\n\n"
        f"Подтвердите оплату или отмените.",
        reply_markup=markup,
        parse_mode="Markdown"
    )
# === ПРОВЕРКА БАЛАНСА И ОПЛАТА ===
def process_balance_and_payment(user_id, chat_id):
    """Проверяет баланс и отправляет подтверждение или ссылку на оплату"""
    balance = users.get(str(user_id), {}).get("balance", 0)
    bot_price = 29.99  # Стоимость создания бота

    if balance >= bot_price:
        # Если денег хватает, спрашиваем подтверждение
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_payment_{user_id}"))
        markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel_payment"))

        bot.send_message(chat_id, f"💰 У вас есть {balance} USDT.\n"
                                  f"Создание бота стоит {bot_price} USDT.\n\n"
                                  f"Вы действительно хотите оплатить?", reply_markup=markup)
    else:
        # Если денег не хватает, отправляем кнопку для оплаты
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно еще {missing_amount} USDT.")
        send_payment_button(chat_id, missing_amount)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_payment_"))
def confirm_payment(call):
    """Обработчик подтверждения оплаты"""
    user_id = call.data.split("_")[-1]  # Получаем user_id из callback_data
    chat_id = call.message.chat.id

    if str(user_id) in users:
        bot_price = 29.99
        users[str(user_id)]["balance"] -= bot_price  # Списываем деньги
        save_users()

        bot.send_message(chat_id, "✅ Оплата успешно подтверждена! Начинаем создание бота.")
        finalize_bot_creation(user_id, chat_id)
    else:
        bot.send_message(chat_id, "⚠️ Ошибка: пользователь не найден.")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_payment")
def cancel_payment(call):
    """Обработчик отмены оплаты"""
    bot.send_message(call.message.chat.id, "❌ Оплата отменена.")

# === СОЗДАНИЕ ПЛАТЕЖНОГО ЧЕКА ЧЕРЕЗ CRYPTOBOT API ===
def create_invoice(user_id, amount, currency="USDT"):
    """Создание платежного чека через API Crypto Bot"""
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTO_BOT_TOKEN}
    data = {
        "asset": currency,
        "amount": amount,
        "description": f"Оплата создания бота для {user_id}",
        "hidden_message": "Спасибо за оплату!",
        "paid_btn_name": "viewItem",
        "paid_btn_url": "https://t.me/ваш_бот",
        "allow_comments": False,
        "allow_anonymous": False
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()

    if result.get("ok"):
        return result["result"]["pay_url"]  # Возвращаем ссылку на оплату
    else:
        return None

def send_payment_button(chat_id, amount):
    """Функция отправки кнопки для оплаты"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data=f"pay_create_bot_{amount}"))

    bot.send_message(chat_id, "Для оплаты нажмите кнопку ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_create_bot"))
def process_payment(call):
    """Обработчик нажатия на кнопку оплаты"""
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if str(user_id) not in users:
        bot.send_message(chat_id, "⚠️ Вы не зарегистрированы в системе.")
        return

    amount = float(call.data.split("_")[-1])  # Получаем сумму из callback_data
    invoice_url = create_invoice(user_id, amount)

    if invoice_url:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔗 Оплатить", url=invoice_url))

        bot.send_message(chat_id, "💰 Для оплаты перейдите по ссылке:", reply_markup=markup)
    else:
        bot.send_message(chat_id, "⚠️ Ошибка при создании платежного чека. Попробуйте позже.")
# === ВЕБХУК ДЛЯ ОБРАБОТКИ ПЛАТЕЖЕЙ CRYPTOBOT ===
from flask import Flask, request

app = Flask(__name__)

@app.route("/cryptobot_webhook", methods=["POST"])
def cryptobot_webhook():
    """Обрабатывает входящие платежи от CryptoBot"""
    data = request.json

    if not data or "invoice_id" not in data or "status" not in data:
        return {"status": "error", "message": "Неверные данные"}

    user_id = str(data.get("payload"))  # ID пользователя
    amount = float(data.get("amount", 0))

    if user_id in users and data["status"] == "paid":
        users[user_id]["balance"] += amount
        save_users()

        bot.send_message(users[user_id]["chat_id"], f"✅ Оплата {amount} USDT получена, ваш баланс пополнен!")
        bot.send_message(ADMIN_ID, f"💰 Новый платеж от @{users[user_id].get('username', 'Неизвестно')} на сумму {amount} USDT")

        # Если пользователь ждал оплату, проверяем баланс снова
        if users[user_id].get("state") == "waiting_for_payment":
            process_balance_and_payment(user_id, users[user_id]["chat_id"])

    return {"status": "ok"}
import time

def start_bot():
    """Запуск бота с защитой от крашей"""
    while True:
        try:
            print("✅ Бот запущен и готов к работе!")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)  # Перезапуск через 5 секунд в случае ошибки

if __name__ == "__main__":
    if os.getenv("USE_WEBHOOK"):  
        # Если используется вебхук, запускаем Flask-сервер
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    else:
        # Иначе запускаем бота в режиме polling
        start_bot()
