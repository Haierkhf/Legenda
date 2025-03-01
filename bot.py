import logging
import os
import telebot
import json
import requests
from fastapi import FastAPI, Request  # Импортируем FastAPI и Request один раз
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Токены
TELEGRAM_BOT_TOKEN = "7756038660:AAHgk4D2wRoC45mxg6v5zwMxNtowOyv0JLo"
CRYPTOBOT_API_KEY = "347583:AAr39UUQRuaxRGshwKo0zFHQnK5n3KMWkzr"
CRYPTOBOT_API_URL = "https://api.cryptobot.com"

try:
    response = requests.get(f"{CRYPTOBOT_API_URL}/{CRYPTOBOT_API_KEY}")
    response.raise_for_status()  # Если статус не OK, вызовет исключение
    logging.info("API криптобота доступен и запрос успешен.")
except requests.exceptions.RequestException as e:
    logging.error(f"Ошибка при подключении к API криптобота: {e}")

# Создаём объект FastAPI
app = FastAPI()

# Создаём бота Telegram
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Файл пользователей
USERS_FILE = "users.json"

# Проверяем, существует ли файл users.json
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Загружаем users.json
try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
except json.JSONDecodeError:
    users = {}

# Временное хранилище платежей
pending_payments = {}

# Создаем эндпоинт для получения webhook (для API)
@app.post("/cryptobot_webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()
    # Логика обработки webhook
    print(data)
    return {"status": "received"}

# Проверка правильности токена бота
try:
    bot.get_me()
    logging.info("Токен правильный, бот успешно подключен.")
except Exception as e:
    logging.error(f"Ошибка при подключении: {e}")
    exit()

# Пример проверки подключения к CryptoBot API
try:
    response = requests.get(f"https://api.cryptobot.com/{CRYPTOBOT_API_KEY}")  # Пример URL для CryptoBot
    if response.status_code == 200:
        logging.info("Подключение к CryptoBot API успешно.")
    else:
        logging.error(f"Ошибка при подключении к CryptoBot API: {response.status_code}")
except requests.exceptions.RequestException as e:
    logging.error(f"Ошибка при подключении к CryptoBot API: {e}")
    exit()

# Запуск бота (если необходимо)
if __name__ == '__main__':
    bot.polling(none_stop=True)

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🤖 Создать бота", callback_data="create_bot"))
    markup.add(InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    markup.add(InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/nWf0L9BBCoJlY2Qy"))
    markup.add(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    markup.add(InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="privacy"))
    return markup
    import telebot
import json
import os
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from dotenv import load_dotenv

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="🤖 Создать бота", callback_data="create_bot"))
    markup.add(InlineKeyboardButton(text="ℹ️ Информация", callback_data="info"))
    markup.add(InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/nWf0L9BBCoJlY2Qy"))
    markup.add(InlineKeyboardButton(text="👤 Профиль", callback_data="profile"))
    markup.add(InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="privacy"))
    return markup

# Команда /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    bot.send_message(message.chat.id, "Привет! Я бот. Выбери действие:", reply_markup=main_menu())

from telebot import TeleBot, types
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

bot = TeleBot('YOUR_BOT_TOKEN')

# Главное меню
def main_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="Создать бота", callback_data="create_bot"))
    markup.add(InlineKeyboardButton(text="Профиль", callback_data="profile"))
    return markup

# Подменю для создания бота
def create_bot_menu():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(text="📢 Автопостинг", callback_data="create_autoposting_bot"))
    markup.add(InlineKeyboardButton(text="💳 Продажа цифровых товаров", callback_data="create_digital_goods_bot"))
    markup.add(InlineKeyboardButton(text="📊 Арбитраж криптовалют", callback_data="create_crypto_arbitrage_bot"))
    markup.add(InlineKeyboardButton(text="🖼️ Генерация изображений AI", callback_data="create_ai_image_bot"))
    markup.add(InlineKeyboardButton(text="📝 Генерация PDF-документов", callback_data="create_pdf_bot"))
    markup.add(InlineKeyboardButton(text="🔗 Продажа подписок", callback_data="create_subscriptions_bot"))
    markup.add(InlineKeyboardButton(text="🔍 Поиск airdrop'ов", callback_data="create_airdrop_bot"))
    markup.add(InlineKeyboardButton(text="🔒 Продажа VPN/прокси", callback_data="create_proxy_bot"))
    markup.add(InlineKeyboardButton(text="📅 Бронирование услуг", callback_data="create_booking_bot"))
    markup.add(InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu"))
    return markup

# Обработчик нажатия кнопок в главном меню
@bot.callback_query_handler(func=lambda call: call.data == "create_bot")
def create_bot_menu_callback(call: CallbackQuery):
    bot.edit_message_text("Выберите тип бота для создания:", call.message.chat.id, call.message.message_id, reply_markup=create_bot_menu())

# Обработчик нажатия кнопок в подменю "Создать бота"
@bot.callback_query_handler(func=lambda call: call.data.startswith('create_'))
def create_bot_callback(call: CallbackQuery):
    data = call.data
    response = ""

    if data == "create_autoposting_bot":
        response = "Вы выбрали бот для автопостинга."
    elif data == "create_digital_goods_bot":
        response = "Вы выбрали бот для продажи цифровых товаров."
    elif data == "create_crypto_arbitrage_bot":
        response = "Вы выбрали бот для арбитража криптовалют."
    elif data == "create_ai_image_bot":
        response = "Вы выбрали бот для генерации изображений AI."
    elif data == "create_pdf_bot":
        response = "Вы выбрали бот для генерации PDF-документов."
    elif data == "create_subscriptions_bot":
        response = "Вы выбрали бот для продажи подписок."
    elif data == "create_airdrop_bot":
        response = "Вы выбрали бот для поиска airdrop'ов."
    elif data == "create_proxy_bot":
        response = "Вы выбрали бот для продажи VPN/прокси."
    elif data == "create_booking_bot":
        response = "Вы выбрали бот для бронирования услуг."
    elif data == "main_menu":
        response = "Возвращаемся в главное меню."
        bot.edit_message_text("Главное меню", call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    bot.answer_callback_query(call.id, response)
    bot.send_message(call.message.chat.id, response)  # Отправить текст с результатом выбора
# Временное хранилище платежей
pending_payments = {}

# Инициализация FastAPI
app = FastAPI()

# Обработчик платежей через CryptoBot
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def pay_handler(call: CallbackQuery):
    user_id = str(call.from_user.id)
    amount_usd = 22.80  # Цена

    try:
        response = requests.post(
            "https://pay.crypt.bot/api/createInvoice",
            json={
                "asset": "USDT",
                "currency": "USD",
                "amount": amount_usd
            },
            headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY},
        )

        if response.ok:
            data = response.json()
            if "result" in data:
                pay_url = data["result"]["pay_url"]
                invoice_id = data["result"]["invoice_id"]

                # Сохраняем ID платежа
                pending_payments[user_id] = invoice_id

                bot.send_message(call.message.chat.id, f"Оплатите по ссылке: {pay_url}")
        else:
            bot.send_message(call.message.chat.id, "Ошибка при создании платежа.")
            logging.error(f"Ошибка CryptoBot: {response.text}")

    except Exception as e:
        bot.send_message(call.message.chat.id, "Ошибка при обработке платежа.")
        logging.error(f"Ошибка при создании счета: {e}")

# Webhook для обработки уведомлений от CryptoBot
@app.post("/cryptobot_webhook")
async def cryptobot_webhook(request: Request):
    data = await request.json()
    logging.info(f"Webhook received: {data}")  # Логируем данные

    if "invoice_id" in data and "status" in data and data["status"] == "paid":
        invoice_id = data["invoice_id"]

        # Найти пользователя, оплатившего инвойс
        user_id = None
        for uid, inv_id in pending_payments.items():
            if inv_id == invoice_id:
                user_id = uid
                break  # Выходим из цикла, если нашли совпадение

        if user_id:
            logging.info(f"Оплата получена от пользователя: {user_id}")

            # Добавляем сумму к балансу пользователя
            users[user_id]["balance"] += float(data["amount"])

            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=4)

            # Удаляем инвойс из списка ожидания
            del pending_payments[user_id]

            # Отправляем сообщение пользователю
            bot.send_message(user_id, f"✅ Оплата {data['amount']} USDT получена! Ваш баланс обновлён.")
        else:
            logging.warning("Платеж получен, но пользователь не найден.")
    return {"status": "ok"}

# Главное меню
def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🤖 Создать бота", callback_data="create_bot")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
        [InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/nWf0L9BBCoJlY2Qy")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="privacy")]
    ]
    return InlineKeyboardMarkup(buttons)

# Команда /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    bot.send_message(message.chat.id, "Привет! Я бот. Выбери действие:", reply_markup=main_menu())

# Кнопка "Информация"
@bot.callback_query_handler(func=lambda call: call.data == "info")
def info_handler(call: CallbackQuery):
    info_text = (
        "ℹ️ **Информация о боте**\n\n"
        "Этот бот помогает вам создать собственного Telegram-бота.\n\n"
        "🚀 **Функции:**\n"
        "🤖 *Создать бота* – выберите шаблон бота и оплатите создание.\n"
        "👤 *Профиль* – показывает ваш баланс и реферальную ссылку.\n"
        "💰 *Пополнить баланс* – оплата через CryptoBot.\n"
        "💬 *Отзывы* – читайте и оставляйте отзывы.\n\n"
        "📩 Если у вас есть вопросы — пишите в поддержку!"
    )

    bot.send_message(call.message.chat.id, info_text, parse_mode="Markdown")

# Кнопка "Политика конфиденциальности"
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

# Запуск бота
if __name__ == "__main__":
    logging.info("Запуск бота...")
    bot.polling(none_stop=True)
    
