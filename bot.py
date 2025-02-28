import logging
import os
import json
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Включаем логирование
logging.basicConfig(level=logging.INFO)

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
        [InlineKeyboardButton(text="💬 Отзывы", url="https://t.me/nWf0L9BBCoJlY2Qy")],
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🔒 Политика конфиденциальности", callback_data="privacy")]
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

# Подменю "Создать бота"
def create_bot_menu():
    buttons = [
        [InlineKeyboardButton(text="📢 Автопостинг", callback_data="create_autoposting_bot")],
        [InlineKeyboardButton(text="💳 Продажа цифровых товаров", callback_data="create_digital_goods_bot")],
        [InlineKeyboardButton(text="📊 Арбитраж криптовалют", callback_data="create_crypto_arbitrage_bot")],
        [InlineKeyboardButton(text="🖼️ Генерация изображений AI", callback_data="create_ai_image_bot")],
        [InlineKeyboardButton(text="📝 Генерация PDF-документов", callback_data="create_pdf_bot")],
        [InlineKeyboardButton(text="🔗 Продажа подписок", callback_data="create_subscriptions_bot")],
        [InlineKeyboardButton(text="🔍 Поиск airdrop'ов", callback_data="create_airdrop_bot")],
        [InlineKeyboardButton(text="🔒 Продажа VPN/прокси", callback_data="create_proxy_bot")],
        [InlineKeyboardButton(text="📅 Бронирование услуг", callback_data="create_booking_bot")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
# Кнопка "Профиль"
@dp.callback_query(lambda c: c.data == "profile")
async def profile_handler(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)

    if user_id not in users:
        users[user_id] = {"balance": 0, "username": callback_query.from_user.username}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)

    balance = users[user_id]["balance"]

    me = await bot.get_me()
    referral_link = f"https://t.me/{me.username}?start={user_id}"

    profile_text = (
        f"**Ваш профиль**\n\n"
        f"👤 Пользователь: {callback_query.from_user.username or 'Без имени'}\n"
        f"💰 Баланс: {balance} USDT\n"
        f"🔗 Ваша реферальная ссылка: [Нажмите здесь]({referral_link})"
    )

    await callback_query.message.answer(profile_text, parse_mode="Markdown")

# Оплата через CryptoBot
@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def pay_handler(callback_query: types.CallbackQuery):
    user_id = str(callback_query.from_user.id)
    amount_usd = 22.80  # Цена услуги

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
    f"Оплатите {amount_usd} USDT, чтобы создать бота.\n[Перейти к оплате]({pay_url})"
        )
        
            parse_mode="Markdown"
# Кнопка "Информация"
@dp.callback_query(lambda c: c.data == "info")
async def info_handler(callback_query: types.CallbackQuery):
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

    await callback_query.message.answer(info_text, parse_mode="Markdown")

# Политика конфиденциальности
@dp.callback_query(lambda c: c.data == "privacy")
async def privacy_handler(callback_query: types.CallbackQuery):
    privacy_text = (
        "🔒 **Политика конфиденциальности**\n\n"
        "1️⃣ Ваши данные (имя, ID) хранятся в зашифрованном виде.\n"
        "2️⃣ Мы не передаём информацию третьим лицам.\n"
        "3️⃣ Все платежи через CryptoBot безопасны.\n"
        "4️⃣ Вы можете удалить свой аккаунт в любое время.\n"
    )

    await callback_query.message.answer(privacy_text, parse_mode="Markdown")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
