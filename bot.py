import os
import json
import re
import logging
import time
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request

# === Настройка логирования ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# === Загрузка переменных окружения ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTO_BOT_TOKEN = os.getenv("CRYPTO_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

print(f"BOT_TOKEN: {BOT_TOKEN}")
print(f"CRYPTO_BOT_TOKEN: {CRYPTO_BOT_TOKEN}")
print(f"ADMIN_ID: {ADMIN_ID}")


if not BOT_TOKEN or not CRYPTO_BOT_TOKEN or not ADMIN_ID:
    logging.error("❌ Ошибка: Не найдены все нужные переменные окружения!")
    raise ValueError("BOT_TOKEN, CRYPTO_BOT_TOKEN или ADMIN_ID отсутствуют!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# === Файл для хранения пользователей ===
USERS_FILE = "users.json"
# === Функция загрузки пользователей ===
def load_users():
    """Загружает пользователей из файла users.json"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logging.warning("⚠ Ошибка чтения users.json. Создан новый файл.")
                return {}
    return {}

# === Функция сохранения пользователей ===
def save_users():
    """Сохраняет данные пользователей в users.json"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# === Функция обновления данных пользователя ===
def update_user(user_id, key, value):
    """Обновляет данные пользователя и сразу сохраняет"""
    if user_id not in users:
        users[user_id] = {}
    
    users[user_id][key] = value
    save_users()

# === Загружаем пользователей при запуске ===
users = load_users()
# === Функция создания клавиатуры главного меню ===
def main_menu():
    """Создаёт клавиатуру главного меню"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🤖 Создать бота"))
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("ℹ️ Информация"))
    markup.add(KeyboardButton("💬 Отзывы"))
    return markup

# === Обработчик команды /start ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    """Обрабатывает команду /start и отправляет главное меню"""
    user_id = str(message.from_user.id)

    # Если пользователь новый — добавляем в базу
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "username": message.from_user.username,
            "chat_id": message.chat.id
        }
        save_users()

    bot.send_message(
        message.chat.id,
        "👋 Привет! Выберите действие:",
        reply_markup=main_menu()
    )

# === Обработчик кнопки "Информация" ===
@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_callback(message):
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
        "4. После успешного платежа ваш баланс пополнится автоматически.\n\n"
        "🔒 *Политика конфиденциальности:*\n"
        "Мы уважаем вашу конфиденциальность и гарантируем защиту ваших данных."
    )
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

# Функция экранирования Markdown
def escape_markdown(text):
    return re.sub(r'([_*[\]()~`>#+-=|{}.!])', r'\\\1', text)

# Обработчик кнопки "Профиль"
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_callback(message):
    """Выводит информацию о профиле пользователя"""
    user_id = str(message.from_user.id)

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    username = users[user_id].get("username")
    if not username:
        username = "Не указан"
    username = escape_markdown(username)  # Экранируем спецсимволы

    balance = users[user_id].get("balance", 0)

    bot.send_message(
        message.chat.id,
        f"👤 *Ваш профиль:*\n\n"
        f"🔹 *Имя пользователя:* @{username}\n"
        f"💰 *Баланс:* {balance} USDT",
        parse_mode="MarkdownV2"
    )

bot.polling()
    
# === Обработчик кнопки "Отзывы" ===
@bot.message_handler(func=lambda message: message.text == "💬 Отзывы")
def reviews_callback(message):
    """Отправляет ссылку на канал с отзывами"""
    bot.send_message(
        message.chat.id,
        "💬 Вы можете оставить отзыв или прочитать мнения других пользователей здесь:\n\n"
        "👉 [Перейти в группу отзывов](https://t.me/nWf0L9BBCoJlY2Qy)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    # === Функция клавиатуры для выбора типа бота ===
def create_bot_menu():
    """Создаёт меню выбора типа бота"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    bot_types = [
        "📢 Автопостинг", "💳 Продажа товаров", "📊 Арбитраж криптовалют",
        "🖼️ Генерация изображений AI", "📝 Генерация PDF",
        "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
        "📅 Бронирование услуг", "🔙 Назад"
    ]
    for name in bot_types:
        markup.add(KeyboardButton(name))
    return markup

# === Обработчик кнопки "Создать бота" ===
@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def handle_create_bot(message):
    """Запускает процесс выбора типа бота"""
    bot.send_message(message.chat.id, "🔹 Выберите тип бота:", reply_markup=create_bot_menu())

# === Обработчик выбора типа бота ===
@bot.message_handler(func=lambda message: message.text in [
    "📢 Автопостинг", "💳 Продажа товаров", "📊 Арбитраж криптовалют",
    "🖼️ Генерация изображений AI", "📝 Генерация PDF",
    "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
    "📅 Бронирование услуг"
])
def process_bot_type(message):
    """Сохраняем тип бота и запрашиваем имя"""
    user_id = str(message.from_user.id)

    users[user_id]["selected_bot_type"] = message.text
    users[user_id]["state"] = "waiting_for_bot_name"
    save_users()

    bot.send_message(message.chat.id, f"Вы выбрали: *{message.text}*\n\nВведите имя для вашего бота:", parse_mode="Markdown")

# === Обработчик ввода имени бота ===
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("state") == "waiting_for_bot_name")
def process_bot_name(message):
    """Сохраняем имя бота и предлагаем оплату"""
    user_id = str(message.from_user.id)
    users[user_id]["bot_name"] = message.text
    users[user_id]["state"] = "waiting_for_payment"
    save_users()

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("✅ Подтвердить оплату"), KeyboardButton("❌ Отмена"))

    bot.send_message(
        message.chat.id,
        f"✅ Имя бота сохранено: *{message.text}*\n\n"
        f"💰 Стоимость создания: *29.99 USDT*.\n\n"
        f"Подтвердите оплату или отмените.",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    # === Проверка баланса перед оплатой ===
def check_balance_and_ask_payment(user_id, chat_id):
    """Проверяет баланс пользователя и предлагает оплату"""
    balance = users.get(user_id, {}).get("balance", 0)
    bot_price = 29.99  # Цена создания бота

    if balance >= bot_price:
        # Если хватает денег, спрашиваем, хочет ли он оплатить из баланса
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("✅ Оплатить с баланса"), KeyboardButton("❌ Отмена"))

        bot.send_message(chat_id, f"💰 У вас есть {balance} USDT. Хотите оплатить создание бота за {bot_price} USDT?", reply_markup=markup)
    else:
        # Если не хватает, отправляем ссылку на оплату
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно ещё {missing_amount} USDT.")
        send_payment_link(user_id, chat_id, missing_amount)

# === Обработчик оплаты с баланса ===
@bot.message_handler(func=lambda message: message.text in ["✅ Оплатить с баланса", "❌ Отмена"])
def process_payment_choice(message):
    """Обрабатывает выбор оплаты"""
    user_id = str(message.from_user.id)
    chat_id = message.chat.id

    if message.text == "✅ Оплатить с баланса":
        bot_price = 29.99

        if users[user_id]["balance"] >= bot_price:
            users[user_id]["balance"] -= bot_price
            save_users()

            bot.send_message(chat_id, "✅ Оплата успешна! Ваш бот создаётся...")
            finalize_bot_creation(user_id, chat_id)
        else:
            bot.send_message(chat_id, "❗ Ошибка: Недостаточно средств.")
    else:
        bot.send_message(chat_id, "🚫 Оплата отменена.")

# === Генерация чека через CryptoBot API ===
def create_invoice(user_id, amount, currency="USDT"):
    """Создаёт чек для оплаты через CryptoBot"""
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
        "allow_anonymous": False,
        "payload": user_id  # Передаём user_id для обработки платежа
    }
    
    response = requests.post(url, json=data, headers=headers)
    result = response.json()

    if result.get("ok"):
        return result["result"]["pay_url"]  # Возвращаем ссылку на оплату
    else:
        logging.error(f"❌ Ошибка при создании чека: {result}")
        return None

# === Функция отправки ссылки на оплату ===
def send_payment_link(user_id, chat_id, amount):
    """Генерирует и отправляет ссылку на оплату"""
    invoice_url = create_invoice(user_id, amount)

    if invoice_url:
        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("💳 Оплатить"))

        bot.send_message(
            chat_id,
            f"💰 Для оплаты {amount} USDT перейдите по ссылке:\n\n[🔗 Оплатить]({invoice_url})",
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        bot.send_message(chat_id, "❌ Ошибка: не удалось создать чек для оплаты. Попробуйте позже.")
        # === Вебхук для обработки платежей от CryptoBot ===
app = Flask(__name__)

@app.route("/cryptobot_webhook", methods=["POST"])
def cryptobot_webhook():
    """Обрабатывает входящие платежи от CryptoBot"""
    data = request.json

    if not data or "invoice_id" not in data or "status" not in data:
        return {"status": "error", "message": "Неверные данные"}

    user_id = str(data.get("payload", ""))  # ID пользователя из payload

    if not user_id or user_id not in users:
        return {"status": "error", "message": "Пользователь не найден"}

    amount = float(data.get("amount", 0))

    if data["status"] == "paid":
        users[user_id]["balance"] += amount
        save_users()

        bot.send_message(users[user_id]["chat_id"], f"✅ Оплата {amount} USDT получена, ваш баланс пополнен!")
        bot.send_message(ADMIN_ID, f"💰 Новый платеж от @{users[user_id].get('username', 'Неизвестно')} на сумму {amount} USDT")

        # Если пользователь ждал оплату, проверяем баланс снова
        if users[user_id].get("state") == "waiting_for_payment":
            check_balance_and_ask_payment(user_id, users[user_id]["chat_id"])

    return {"status": "ok"}
    import time

def start_bot():
    """Запуск бота с защитой от крашей"""
    while True:
        try:
            print("✅ Бот запущен и работает!")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"❌ Ошибка: {e}")
            time.sleep(5)  # Перезапуск через 5 секунд в случае ошибки

if __name__ == "__main__":
    if os.getenv("USE_WEBHOOK"):  
        # Если используется вебхук, запускаем Flask-сервер
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    else:
        # Иначе запускаем бота в режиме polling
        start_bot()
