import logging
import os
import json
import requests
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv
from fastapi import FastAPI, Request
import logging
import os

# Создаем папку для логов, если она не существует
if not os.path.exists('logs'):
    os.makedirs('logs')

# Настроим логирование в файл и консоль
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot_log.log'),  # Путь к файлу лога
        logging.StreamHandler()  # Дополнительно выводим логи в консоль
    ]
)
import json

USERS_FILE = 'users.json'  # Укажите путь к файлу пользователей (если в той же директории, то достаточно имени файла)

# Функция для загрузки пользователей из файла
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Если файл не найден или пустой, возвращаем пустой словарь

# Функция для сохранения пользователей в файл
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
        import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# Пример логирования
logging.info("Бот запущен.")

# Далее идет ваш код бота
load_dotenv()

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = "7756038660:AAHgk4D2wRoC45mxg6v5zwMxNtowOyv0JLo"
CRYPTOBOT_API_KEY = "347583:AA2FTH9et0kfdviBIOv9RfeDPUYq5HAcbRj"

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
except json.JSONDecodeError:
    users = {}

pending_payments = {}

app = FastAPI()

def main_menu():
    markup = InlineKeyboardMarkup()
    buttons = [
        ("🤖 Создать бота", "create_bot"),
        ("ℹ️ Информация", "info"),
        ("💬 Отзывы", "https://t.me/nWf0L9BBCoJlY2Qy"),
        ("👤 Профиль", "profile"),
        ("🔒 Политика конфиденциальности", "privacy")
    ]
    for text, data in buttons:
        markup.add(InlineKeyboardButton(text=text, callback_data=data if "http" not in data else None, url=data if "http" in data else None))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
    bot.send_message(message.chat.id, "Привет! Я бот. Выбери действие:", reply_markup=main_menu())

from telebot import types

# Подменю для создания бота
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

# Обработчик кнопки "Создать бота"
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_menu_callback(call: CallbackQuery):
    bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())

# Обработчик выбора типа бота
@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    bot_type = call.data

    bot_type_names = {
        "create_autoposting_bot": "📢 Автопостинг",
        "create_digital_goods_bot": "💳 Продажа цифровых товаров",
        "create_crypto_arbitrage_bot": "📊 Арбитраж криптовалют",
        "create_ai_image_bot": "🖼️ Генерация изображений AI",
        "create_pdf_bot": "📝 Генерация PDF-документов",
        "create_subscriptions_bot": "🔗 Продажа подписок",
        "create_airdrop_bot": "🔍 Поиск airdrop'ов",
        "create_proxy_bot": "🔒 Продажа VPN/прокси",
        "create_booking_bot": "📅 Бронирование услуг"
    }

    if bot_type in bot_type_names:
        # Просим ввести название для нового бота
        bot.send_message(call.message.chat.id, f"Вы выбрали {bot_type_names[bot_type]}.\n\nВведите название для нового бота:")

        # Сохраняем выбранный тип бота
        users[user_id] = {"selected_bot_type": bot_type, "state": "waiting_for_name"}
        
        # Переход в состояние ожидания названия бота
        bot.register_next_step_handler(call.message, ask_bot_name)

# Обработчик ввода названия бота
def ask_bot_name(message):
    user_id = str(message.from_user.id)
    bot_name = message.text

    # Проверяем, что пользователь зарегистрирован в системе
    if user_id in users and users[user_id].get("state") == "waiting_for_name":
        # Сохраняем введенное название бота
        users[user_id]["bot_name"] = bot_name
        selected_bot_type = users[user_id]["selected_bot_type"]

        # Получаем название типа бота
        bot_type_names = {
            "create_autoposting_bot": "📢 Автопостинг",
            "create_digital_goods_bot": "💳 Продажа цифровых товаров",
            "create_crypto_arbitrage_bot": "📊 Арбитраж криптовалют",
            "create_ai_image_bot": "🖼️ Генерация изображений AI",
            "create_pdf_bot": "📝 Генерация PDF-документов",
            "create_subscriptions_bot": "🔗 Продажа подписок",
            "create_airdrop_bot": "🔍 Поиск airdrop'ов",
            "create_proxy_bot": "🔒 Продажа VPN/прокси",
            "create_booking_bot": "📅 Бронирование услуг"
        }

        bot_type_name = bot_type_names.get(selected_bot_type, "Неизвестный тип")

        # Подтверждаем создание бота
        bot.send_message(message.chat.id, f"Вы успешно создали бота для типа: {bot_type_name}!\n\nНазвание вашего бота: {bot_name}")

        # Сброс состояния
        users[user_id]["state"] = "none"
        users[user_id].pop("selected_bot_type", None)

        # Можно добавить дальнейшую логику по созданию бота, например, создание аккаунта или базы данных для нового бота.
    else:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте снова.")

        # обработчик кнопки для создания бота и проверки баланса
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()  # Загружаем пользователей

    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Проверка наличия средств
        if user_balance >= payment_amount:
            # Уменьшаем баланс пользователя
            new_balance = user_balance - payment_amount
            users[user_id]["balance"] = new_balance
            save_users(users)

            # Отправляем пользователю сообщение о успешной оплате
# Обработчик кнопки "Создать бота"
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()  # Загружаем пользователей

    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Проверка наличия средств
        if user_balance >= payment_amount:
            # Уменьшаем баланс пользователя
            new_balance = user_balance - payment_amount
            users[user_id]["balance"] = new_balance
            save_users(users)

            # Отправляем пользователю сообщение о успешной оплате
            bot.send_message(call.message.chat.id, f"✅ Оплата прошла успешно! Новый баланс: {new_balance} USDT.")
            bot.send_message(call.message.chat.id, "Ваш бот успешно создан!")
            
            # Логика создания бота...
            bot.send_message(call.message.chat.id, "Теперь выберите тип бота для создания:")
            bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())
            
        else:
            # Если средств недостаточно, отправляем чек на оплату
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств для создания бота. Пожалуйста, оплатите {payment_amount} USDT.")
            
            # Отправляем кнопку для оплаты
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data="pay_create_bot"))
            bot.send_message(call.message.chat.id, "Для оплаты нажмите кнопку ниже:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")

# обработчик кнопки "Оплатить создание бота"
@bot.callback_query_handler(func=lambda call: call.data == "pay_create_bot")
def pay_create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()  # Загружаем пользователей

    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Проверка наличия средств
        if user_balance >= payment_amount:
            # Уменьшаем баланс пользователя
            new_balance = user_balance - payment_amount
            users[user_id]["balance"] = new_balance
            save_users(users)

            # Отправляем пользователю сообщение о успешной оплате
            bot.send_message(call.message.chat.id, f"✅ Оплата прошла успешно! Новый баланс: {new_balance} USDT.")
            bot.send_message(call.message.chat.id, "Ваш бот успешно создан!")

            # Логика создания бота...
            bot.send_message(call.message.chat.id, "Теперь выберите тип бота для создания:")
            bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())

        else:
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств для создания бота. Баланс: {user_balance} USDT. Необходимая сумма: {payment_amount} USDT.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")

# Обработчик выбора типа бота
@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    bot_type = call.data

    bot_type_names = {
        "create_autoposting_bot": "📢 Автопостинг",
        "create_digital_goods_bot": "💳 Продажа цифровых товаров",
        "create_crypto_arbitrage_bot": "📊 Арбитраж криптовалют",
        "create_ai_image_bot": "🖼️ Генерация изображений AI",
        "create_pdf_bot": "📝 Генерация PDF-документов",
        "create_subscriptions_bot": "🔗 Продажа подписок",
        "create_airdrop_bot": "🔍 Поиск airdrop'ов",
        "create_proxy_bot": "🔒 Продажа VPN/прокси",
        "create_booking_bot": "📅 Бронирование услуг"
    }

    if bot_type in bot_type_names:
# Обработчик кнопки "Создать бота"
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()  # Загружаем пользователей

    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Проверка наличия средств
        if user_balance >= payment_amount:
            # Уменьшаем баланс пользователя
            new_balance = user_balance - payment_amount
            users[user_id]["balance"] = new_balance
            save_users(users)

            # Отправляем пользователю сообщение о успешной оплате
            bot.send_message(call.message.chat.id, f"✅ Оплата прошла успешно! Новый баланс: {new_balance} USDT.")
            bot.send_message(call.message.chat.id, "Теперь выберите тип бота для создания:")

            # Логика выбора типа бота
            bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())
            
        else:
            # Если средств недостаточно, отправляем чек на оплату
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств для создания бота. Пожалуйста, оплатите {payment_amount} USDT.")
            
            # Отправляем кнопку для оплаты
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data="pay_create_bot"))
            bot.send_message(call.message.chat.id, "Для оплаты нажмите кнопку ниже:", reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")

# Обработчик кнопки "Оплатить создание бота"
@bot.callback_query_handler(func=lambda call: call.data == "pay_create_bot")
def pay_create_bot_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users = load_users()  # Загружаем пользователей

    if user_id in users:
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Проверка наличия средств
        if user_balance >= payment_amount:
            # Уменьшаем баланс пользователя
            new_balance = user_balance - payment_amount
            users[user_id]["balance"] = new_balance
            save_users(users)

            # Отправляем пользователю сообщение о успешной оплате
            bot.send_message(call.message.chat.id, f"✅ Оплата прошла успешно! Новый баланс: {new_balance} USDT.")
            bot.send_message(call.message.chat.id, "Теперь выберите тип бота для создания:")

            # Логика выбора типа бота
            bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())

        else:
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств для создания бота. Баланс: {user_balance} USDT. Необходимая сумма: {payment_amount} USDT.")
    else:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")

# Обработчик выбора типа бота
@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_type_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    bot_type = call.data

    bot_type_names = {
        "create_autoposting_bot": "📢 Автопостинг",
        "create_digital_goods_bot": "💳 Продажа цифровых товаров",
        "create_crypto_arbitrage_bot": "📊 Арбитраж криптовалют",
        "create_ai_image_bot": "🖼️ Генерация изображений AI",
        "create_pdf_bot": "📝 Генерация PDF-документов",
        "create_subscriptions_bot": "🔗 Продажа подписок",
        "create_airdrop_bot": "🔍 Поиск airdrop'ов",
        "create_proxy_bot": "🔒 Продажа VPN/прокси",
        "create_booking_bot": "📅 Бронирование услуг"
    }

    if bot_type in bot_type_names:
        # Перед тем как предложить ввести название, проверяем баланс
        user_balance = users[user_id].get("balance", 0)
        payment_amount = 22.80  # Стоимость создания бота

        # Если баланс достаточен, разрешаем вводить название
        if user_balance >= payment_amount:
            # Сохраняем выбранный тип бота
            users[user_id] = {"selected_bot_type": bot_type, "state": "waiting_for_name"}
            bot.send_message(call.message.chat.id, f"Вы выбрали {bot_type_names[bot_type]}.\n\nВведите название для нового бота:")

            # Переход в состояние ожидания названия бота
            bot.register_next_step_handler(call.message, ask_bot_name)
        else:
            # Если средств недостаточно, отправляем чек на оплату
            bot.send_message(call.message.chat.id, f"❌ У вас недостаточно средств для создания бота. Пожалуйста, оплатите {payment_amount} USDT.")
            
            # Отправляем кнопку для оплаты
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data="pay_create_bot"))
            bot.send_message(call.message.chat.id, "Для оплаты нажмите кнопку ниже:", reply_markup=markup)

# Обработчик ввода названия бота
def ask_bot_name(message):
    user_id = str(message.from_user.id)
    bot_name = message.text

    if user_id in users and users[user_id].get("state") == "waiting_for_name":
        # Сохраняем введенное название бота
        users[user_id]["bot_name"] = bot_name
        selected_bot_type = users[user_id]["selected_bot_type"]

        # Получаем название типа бота
        bot_type_names = {
            "create_autoposting_bot": "📢 Автопостинг",
            "create_digital_goods_bot": "💳 Продажа цифровых товаров",
            "create_crypto_arbitrage_bot": "📊 Арбитраж криптовалют",
            "create_ai_image_bot": "🖼️ Генерация изображений AI",
            "create_pdf_bot": "📝 Генерация PDF-документов",
            "create_subscriptions_bot": "🔗 Продажа подписок",
            "create_airdrop_bot": "🔍 Поиск airdrop'ов",
            "create_proxy_bot": "🔒 Продажа VPN/прокси",
            "create_booking_bot": "📅 Бронирование услуг"
        }

        bot_type_name = bot_type_names.get(selected_bot_type, "Неизвестный тип")

        # Подтверждаем создание бота
        bot.send_message(message.chat.id, f"Вы успешно создали бота для типа: {bot_type_name}!\n\nНазвание вашего бота: {bot_name}")

        # Сброс состояния
        users[user_id]["state"] = "none"
        users[user_id].pop("selected_bot_type", None)

        # Можно добавить дальнейшую логику по созданию бота, например, создание аккаунта или базы данных для нового бота.
    else:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка. Попробуйте снова.")
# Функция для экранирования символов Markdown
def escape_markdown(text):
    return text.replace("*", "\\*").replace("_", "\\_").replace("[", "\").replace("]", "\").replace("(", "\").replace(")", "\").replace("~", "\\~").replace("`", "\\`")

# Обработчик кнопки "Профиль"
@bot.callback_query_handler(func=lambda call: call.data == "profile")
def profile_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)

    try:
        users = load_users()  # Загружаем пользователей из файла

        if user_id in users:
            username = escape_markdown(users[user_id].get("username", "Не указан"))
            balance = users[user_id].get("balance", 0)

            # Генерируем реферальную ссылку
            ref_link = escape_markdown(f"https://t.me/{bot.get_me().username}?start={user_id}")

            response = (f"👤 *Ваш профиль:*\n\n"
                       f"🔹 *Имя пользователя:* @{username}\n"
                       f"💰 *Баланс:* {balance} USDT\n\n"
                       f"🔗 *Ваша реферальная ссылка:*\n{ref_link}")
        else:
            response = "⚠️ Вы не зарегистрированы в системе."

        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Ошибка при обработке профиля для пользователя {user_id}: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка при обработке вашего профиля.")
        bot.send_message(call.message.chat.id, "Произошла ошибка. Попробуйте позже.")

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Путь к файлу с пользователями
USERS_FILE = "users.json"

# Функция для загрузки пользователей из файла
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Файл users.json не найден.")
        return {}  # Если файл не найден, возвращаем пустой словарь
    except json.JSONDecodeError:
        logger.error("Ошибка при разборе JSON в файле users.json.")
        return {}  # Если JSON невалиден, возвращаем пустой словарь
    except Exception as e:
        logger.error(f"Неизвестная ошибка при загрузке файла users.json: {e}")
        return {}  # В случае других ошибок, также возвращаем пустой словарь
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_handler(call: CallbackQuery):
    info_text = (
        "ℹ️ **Информация о боте**\n\n"
        "🚀 **Функции:**\n"
        "🤖 *Создать бота* – выберите шаблон бота и оплатите создание.\n"
        "👤 *Профиль* – показывает ваш баланс и реферальную ссылку.\n"
        "💰 *Пополнить баланс* – оплата через CryptoBot.\n"
        "💬 *Отзывы* – читайте и оставляйте отзывы.\n\n"
        "📩 Если у вас есть вопросы — пишите в поддержку!"
    )
    bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "privacy")
def privacy_handler(call: CallbackQuery):
    privacy_text = (
        "🔒 **Политика конфиденциальности**\n\n"
        "1️⃣ Ваши данные (имя, ID) хранятся в зашифрованном виде.\n"
        "2️⃣ Мы не передаём информацию третьим лицам.\n"
        "3️⃣ Все платежи через CryptoBot безопасны.\n"
        "4️⃣ Вы можете удалить свой аккаунт в любое время.\n"
    )
    bot.send_message(call.message.chat.id, privacy_text, parse_mode="Markdown")

@app.post("/cryptobot_webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()
    logging.info(f"Webhook received: {data}")

    if "invoice_id" in data and data.get("status") == "paid":
        invoice_id = data["invoice_id"]
        user_id = next((uid for uid, inv_id in pending_payments.items() if inv_id == invoice_id), None)

        if user_id:
            users[user_id]["balance"] += float(data["amount"])
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)
            del pending_payments[user_id]
            bot.send_message(user_id, f"✅ Оплата {data['amount']} USDT получена! Ваш баланс обновлён.")
        else:
            logging.warning("Платеж получен, но пользователь не найден.")
    return {"status": "ok"}

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def pay_handler(call: CallbackQuery):
    user_id = str(call.from_user.id)
    amount_usd = 22.80
    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={"asset": "USDT", "currency": "USD", "amount": amount_usd},
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )
        if response.ok:
            data = response.json()
            if "result" in data:
                pay_url = data["result"]["pay_url"]
                pending_payments[user_id] = data["result"]["invoice_id"]
                bot.send_message(call.message.chat.id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(call.message.chat.id, "Ошибка при создании платежа.")
    except Exception as e:
        logging.error(f"Ошибка при создании счета: {e}")
        bot.send_message(call.message.chat.id, "Ошибка при обработке платежа.")
        import json
import logging

# Путь к файлу с пользователями
USERS_FILE = "users.json"
# Ваш уникальный ID (например, из Telegram)
MY_USER_ID = "6402443549"  # Замените на свой ID

# Функция для загрузки пользователей из файла
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}  # Если файл не найден или пустой, возвращаем пустой словарь

# Функция для сохранения пользователей в файл
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# Функция для изменения баланса только для себя
def change_balance_for_myself(new_balance):
    users = load_users()

    if MY_USER_ID in users:
        users[MY_USER_ID]["balance"] = new_balance
        save_users(users)
        print(f"Баланс изменен для пользователя {MY_USER_ID}: {new_balance} USDT")  # Исправил на USDT
    else:
        print("Пользователь не найден.")

# Например, когда нужно обновить баланс (например, в команде /start или после обработки запроса)
@bot.message_handler(commands=['start'])
def start(message):
    # Пример: сразу после старта мы хотим установить баланс для себя
    new_balance = 500.0  # Устанавливаем новый баланс
    change_balance_for_myself(new_balance)

    bot.send_message(message.chat.id, "Привет! Я бот. Баланс обновлен.")
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)  # Уровень логирования — DEBUG (можно настроить на INFO, ERROR, etc.)
logger = logging.getLogger(__name__)

USERS_FILE = "users.json"

# Функция для загрузки пользователей из файла
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Ошибка при загрузке users.json: {e}")  # Логируем ошибку
        return {}  # Если файл не найден или пустой, возвращаем пустой словарь

# Функция для сохранения пользователей в файл
def save_users(users):
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка при сохранении users.json: {e}")  # Логируем ошибку
# Запуск бота
logging.info("Бот запущен. Ожидание сообщений...")
bot.polling(none_stop=True)

if __name__ == "__main__":
    bot.polling(none_stop=True)
