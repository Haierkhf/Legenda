import logging
import os
import json
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Дополнительное логирование сообщений пользователей в отдельный файл
user_logger = logging.getLogger("user_messages")
user_logger.setLevel(logging.INFO)
user_handler = logging.FileHandler("user_messages.log", encoding="utf-8")
user_handler.setFormatter(logging.Formatter("%(asctime)s - [%(user_id)s] %(username)s: %(message)s"))
user_logger.addHandler(user_handler)

# Токены
TELEGRAM_BOT_TOKEN = "7756038660:AAHgk4D2wRoC45mxg6v5zwMxNtowOyv0JLo"
CRYPTOBOT_API_KEY = "347583:AAr39UUQRuaxRGshwKo0zFHQnK5n3KMWkzr"

# Создаём бота и диспетчер
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

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

# Главное меню
def main_menu():
    buttons = [
        [InlineKeyboardButton(text="🤖 Создать бота", callback_data="create_bot")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info")],
        [InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/nwfOL9BBC0J1Y2Q")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Команда /start
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    
    if user_id not in users:
        users[user_id] = {"balance": 0, "username": message.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    await message.answer("Привет! Я бот. Выбери действие:", reply_markup=main_menu())

# Кнопка "Создать Бота"
@dp.callback_query(lambda c: c.data == "create_bot")
async def create_bot(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    amount_usd = 22.80

    response = requests.post(
        "https://pay.crypt.bot/api/createInvoice",
        json={"asset": "USDT", "currency": "USD", "amount": amount_usd, "description": "Оплата бота"},
        headers={"Crypto-Pay-API-Token": CRYPTOBOT_API_KEY}
    )

    if response.ok:
        pay_url = response.json()["result"]["pay_url"]
        invoice_id = response.json()["result"]["invoice_id"]
        pending_payments[user_id] = invoice_id

        await callback_query.message.answer(
            f"Оплатите {amount_usd} USDT, чтобы создать бота.\n[Перейти к оплате]({pay_url})",
            parse_mode="Markdown"
        )
    else:
        await callback_query.message.answer("Ошибка при создании платежа. Попробуйте позже.")

# Кнопка "Профиль"
@dp.callback_query(lambda c: c.data == "profile")
async def profile_handler(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": callback_query.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    balance = users[user_id]["balance"]

    profile_text = (
        f"**Ваш профиль**\n\n"
        f"👤 Пользователь: {callback_query.from_user.username or 'Без имени'}\n"
        f"💰 Баланс: {balance} USDT\n"
        f"🔗 Ваша реферальная ссылка: [Нажмите здесь](https://t.me/{bot.username}?start={user_id})"
    )

    await callback_query.message.answer(profile_text, parse_mode="Markdown")

# Кнопка "Информация"
@dp.callback_query(lambda c: c.data == "info")
async def info_handler(callback_query: types.CallbackQuery):
    info_text = (
        "ℹ️ **Информация о боте**\n\n"
        "Этот бот помогает вам создать собственного Telegram-бота.\n\n"
        "🚀 **Функции:**\n"
        "🤖 *Создать бота* – запрашивает у вас название и описание бота после оплаты.\n"
        "👤 *Профиль* – показывает ваш баланс и реферальную ссылку.\n"
        "💰 *Пополнить баланс* – оплатите через CryptoBot.\n\n"
        "📩 Если у вас есть вопросы — пишите в поддержку!"
    )

    await callback_query.message.answer(info_text, parse_mode="Markdown")

# Логирование сообщений только у пользователей, которые оплатили
@dp.message()
async def log_user_messages(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or "Без имени"
    
    # Проверяем, оплатил ли пользователь
    if users.get(user_id, {}).get("balance", 0) > 0:
        log_data = {
            "user_id": user_id,
            "username": username,
            "message": message.text
        }
        user_logger.info(log_data)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
