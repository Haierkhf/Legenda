import logging
import os
import json
import requests
import threading
import telebot
from telebot.formatting import escape_markdown
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from flask import Flask, request

# Настроим логирование в файл и консоль
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot_log.log"),
        logging.StreamHandler()
    ]
)

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
app = Flask(__name__)

# Файл пользователей
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

# Создаем файл users.json, если его нет
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Подгружаем пользователей в память
users = load_users()
# Функция для создания главного меню
def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        InlineKeyboardButton("🤖 Создать бота", callback_data="create_bot"),
        InlineKeyboardButton("ℹ Информация", callback_data="info"),
        InlineKeyboardButton("💬 Отзывы", url="https://t.me/nwf0L9BBCoJYl2Qy"),
        InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        InlineKeyboardButton("🔒 Политика конфиденциальности", callback_data="privacy"),
    ]
    markup.add(*buttons)
    return markup

# Функция получения состояния пользователя
def get_user_state(user_id):
    return users.get(str(user_id), {}).get("state", "idle")

# Обработчик команды /start (автоматическая регистрация)
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)  # Приводим ID пользователя к строке
    users = load_users()  # Загружаем список пользователей

    # Если пользователь зашел впервые – регистрируем его
    if user_id not in users:
        users[user_id] = {
            "balance": 0,
            "username": message.from_user.username or "Не указан",
            "chat_id": message.chat.id
        }
        save_users(users)  # Сохраняем обновленные данные

        # Логируем нового пользователя
        logging.info(f"Новый пользователь зарегистрирован: {user_id} (@{message.from_user.username})")

    bot.send_message(
        message.chat.id,
        "Привет! Добро пожаловать в бота! Выберите действие:",
        reply_markup=main_menu()
    )
from telebot.formatting import escape_markdown  # Импорт для защиты Markdown в сообщениях

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "create_bot":
        show_create_bot_menu(call.message.chat.id)  # Запускаем процесс создания бота
    
    elif call.data == "info":
        show_info(call.message.chat.id)  # Вызываем функцию с подробной информацией
    
    elif call.data == "profile":
        handle_profile(call)  # Вызываем функцию профиля
    
    elif call.data == "privacy":
        show_privacy_policy(call.message.chat.id)  # Вызываем политику конфиденциальности

# Функция для отображения профиля пользователя
def handle_profile(call):
    user_id = str(call.from_user.id)  # Приводим ID к строке
    users = load_users()  # Загружаем базу пользователей

    try:
        if user_id in users:
            username = escape_markdown(users[user_id].get("username", "Не указан"))
            balance = users[user_id].get("balance", 0)

            # Генерируем реферальную ссылку
            bot_info = bot.get_me()
            bot_username = bot_info.username or "бот"
            ref_link = f"https://t.me/{bot_username}?start={user_id}"

            response = (
                f"👤 *Ваш профиль:*\n\n"
                f"🔹 *Имя пользователя:* @{username}\n"
                f"💰 *Баланс:* {balance} USDT\n\n"
                f"🔗 *Ваша реферальная ссылка:*\n{escape_markdown(ref_link)}"
            )
        else:
            response = "⚠️ Вы не зарегистрированы в системе."

        bot.answer_callback_query(call.id)  # Подтверждаем нажатие кнопки
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Ошибка в handle_profile для {user_id}: {e}")
        bot.answer_callback_query(call.id, "⚠️ Ошибка при обработке профиля.")
        bot.send_message(call.message.chat.id, "🚨 Произошла ошибка. Попробуйте позже.")

# Функция с подробной информацией о боте (Теперь включает инструкцию по пополнению)
def show_info(chat_id):
    text = (
        "ℹ *Информация о боте*\n\n"
        "Этот бот позволяет создавать автоматизированные сервисы, управлять подписками, "
        "продавать цифровые товары и многое другое.\n\n"
        "📌 *Основные функции:*\n"
        "- Создание Telegram-ботов для автоматизации\n"
        "- Подключение платежей через CryptoBot\n"
        "- Удобная система управления подписками\n"
        "- Бронирование услуг через Telegram\n"
        "- Генерация PDF и AI-изображений\n\n"
        "💰 *Как пополнить баланс?*\n"
        "Для пополнения баланса используем *CryptoBot*. Вот пошаговая инструкция:\n\n"
        "1️⃣ Откройте [CryptoBot](https://t.me/CryptoBot)\n"
        "2️⃣ Перейдите в раздел 'Пополнение' и выберите криптовалюту (например, USDT)\n"
        "3️⃣ Отправьте криптовалюту на указанный адрес\n"
        "4️⃣ После пополнения вернитесь в нашего бота и нажмите 'Проверить баланс'\n\n"
        "⚠️ *Важно:* Переводите средства точно на указанный адрес. Ошибочные переводы невозможно вернуть!"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

# Функция с политикой конфиденциальности
def show_privacy_policy(chat_id):
    text = (
        "🔒 *Политика конфиденциальности*\n\n"
        "1️⃣ Мы не храним ваши личные данные, кроме ID и имени пользователя Telegram.\n"
        "2️⃣ Все платежи обрабатываются через *CryptoBot*, и мы не имеем доступа к вашим средствам.\n"
        "3️⃣ Мы не передаем ваши данные третьим лицам.\n"
        "4️⃣ Вы можете удалить свою информацию, написав в поддержку.\n\n"
        "📌 Используя этого бота, вы соглашаетесь с данной политикой."
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")
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

@bot.callback_query_handler(func=lambda call: call.data == "create_b")
def create_bot_type_callback(call: CallbackQuery):
    bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id)
@bot.callback_query_handler(func=lambda call: call.data.startswith("create_"))
def create_bot_callback(call):

    bot_type = call.data.replace("create_", "")  # Получаем тип бота
    print(f"bot_type после обработки: {bot_type}")  # Проверяем, что получили

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

    print(f"Возможные ключи: {bot_type_names.keys()}")  # Выводим ключи для сверки

    user_id = str(call.from_user.id)  # ID пользователя в строковом формате

    if bot_type in bot_type_names:
        users[user_id]["selected_bot_type"] = bot_type  # Сохраняем выбранный тип
        users[user_id]["state"] = "waiting_for_bot_name"  # Меняем состояние
        save_users(users)  # Сохраняем в базу

        bot.send_message(call.message.chat.id, f"Вы выбрали: {bot_type_names[bot_type]}")
    else:
        bot.send_message(call.message.chat.id, "❌ Ошибка: неизвестный тип бота")
    # Сохраняем имя бота
    users[user_id]["bot_name"] = bot_name
    users[user_id]["state"] = "waiting_for_payment"  # Меняем состояние на ожидание оплаты
    save_users(users)

    bot.send_message(
        message.chat.id, 
        f"✅ Имя бота сохранено: *{bot_name}*\n\n"
        "💰 Для продолжения необходимо оплатить создание.\n"
        "Проверяем ваш баланс...",
        parse_mode="Markdown"
    )
    
    # Проверяем баланс
    check_user_balance(user_id, message.chat.id)
    # Функция проверки баланса пользователя перед оплатой
def check_user_balance(user_id, chat_id):
    user = users.get(user_id, {})
    balance = user.get("balance", 0)
    bot_price = 10  # Стоимость создания бота (можно вынести в переменную)

    if balance >= bot_price:
        # Если денег хватает, списываем сумму и создаем заявку
        users[user_id]["balance"] -= bot_price
        save_users(users)
        complete_bot_creation(user_id, chat_id)
    else:
        # Если денег не хватает, отправляем ссылку на оплату
        send_payment_link(user_id, chat_id, bot_price - balance)

# Функция отправки ссылки на оплату через CryptoBot
def send_payment_link(user_id, chat_id, amount_due):
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={"asset": "USDT", "currency": "USD", "amount": amount_due},
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )
        data = response.json()

        if "result" in data:
            pay_url = data["result"]["pay_url"]
            pending_payments[user_id] = data["result"]  # Сохраняем платеж
            bot.send_message(
                chat_id, 
                f"💰 Для завершения заявки оплатите {amount_due} USDT.\n\n"
                f"🔗 Оплатите по ссылке: {pay_url}",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(chat_id, "❌ Ошибка: не удалось создать ссылку на оплату.")

    except Exception as e:
        logging.error(f"Ошибка при создании платежа: {e}")
        bot.send_message(chat_id, "🚨 Ошибка при обработке платежа. Попробуйте позже.")

# Функция завершения заявки на создание бота
def complete_bot_creation(user_id, chat_id):
    bot_type = users[user_id].get("selected_bot_type", "Неизвестный тип")
    bot_name = users[user_id].get("bot_name", "Без названия")

    # Логируем успешное оформление заявки
    logging.info(f"📩 Заявка на создание бота: {bot_name} ({bot_type}) от пользователя {user_id}")

    bot.send_message(
        chat_id,
        f"✅ *Ваша заявка отправлена разработчику!*\n\n"
        f"🔧 Ваш бот *{bot_name}* ({bot_type}) находится в разработке.\n"
        f"⏳ Среднее время создания — *до 72 часов*.\n"
        f"📢 Как только бот будет готов, вы получите уведомление!",
        parse_mode="Markdown"
    )

    # Сбрасываем состояние пользователя
    users[user_id]["state"] = "idle"
    save_users(users)
    # Список ожидаемых платежей
pending_payments = {}

# Вебхук для приема уведомлений о платежах от CryptoBot
@app.route(f"/{CRYPTOBOT_API_KEY}", methods=["POST"])
def cryptobot_webhook():
    try:
        data = request.get_json()  # Получаем данные из запроса
        if not data or "invoice_id" not in data:
            return "Некорректный запрос", 400

        invoice_id = data["invoice_id"]
        user_id = None

        # Ищем платеж среди ожидаемых
        for uid, payment in pending_payments.items():
            if payment["invoice_id"] == invoice_id:
                user_id = uid
                break

        if not user_id:
            return "Платеж не найден", 404

        # Проверяем статус оплаты
        if data.get("status") == "paid":
            amount = float(data["amount"])
            users[user_id]["balance"] += amount
            save_users(users)

            # Удаляем платеж из списка ожидаемых
            del pending_payments[user_id]

            bot.send_message(
                users[user_id]["chat_id"],
                f"✅ Ваш платеж на *{amount} USDT* успешно зачислен!\n"
                "Вы можете продолжить создание бота.",
                parse_mode="Markdown"
            )

            # Если пользователь был на этапе оплаты – проверяем баланс
            if users[user_id].get("state") == "waiting_for_payment":
                check_user_balance(user_id, users[user_id]["chat_id"])

        return "OK", 200

    except Exception as e:
        logging.error(f"Ошибка в вебхуке CryptoBot: {e}")
        return "Ошибка сервера", 500

# Функция запуска Flask-сервера
def start_flask():
    app.run(host="0.0.0.0", port=5000)
    import threading  # Для одновременного запуска бота и Flask

# Функция для запуска Telegram-бота
def start_telegram_bot():
    logging.info("✅ Бот запущен и работает!")
    bot.polling(none_stop=True)

# Запускаем Telegram-бот и Flask одновременно
if __name__ == "__main__":
    telegram_thread = threading.Thread(target=start_telegram_bot)
    flask_thread = threading.Thread(target=start_flask)

    telegram_thread.start()
    flask_thread.start()
