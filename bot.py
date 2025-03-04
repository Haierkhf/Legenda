import os
import json
import logging
import requests
import telebot
from flask import Flask, request
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CRYPTOBOT_API_KEY = os.environ.get("CRYPTOBOT_API_KEY")
ADMIN_ID = os.environ.get("ADMIN_ID")
CRYPTO_PAY_URL = "https://pay.crypt.bot/api/createInvoice"
CRYPTO_BOT_URL = "https://pay.crypt.bot/"


if not BOT_TOKEN or not CRYPTOBOT_API_KEY or not ADMIN_ID:
    raise ValueError("Ошибка: не найдены необходимые переменные окружения!")

ADMIN_ID = int(ADMIN_ID)
bot = telebot.TeleBot(BOT_TOKEN)

# Файл хранения данных пользователей
USERS_FILE = "users.json"

# Загружаем пользователей из файла (если он существует)
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        users = json.load(file)
else:
    users = {}  # Если файла нет, создаем пустой словарь

def save_users():
    """Функция автоматического сохранения users.json"""
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)

def update_user(user_id, key, value):
    """Функция для обновления данных пользователя и автосохранения"""
    if user_id not in users:
        users[user_id] = {}
    
    users[user_id][key] = value
    save_users()  # Автоматическое сохранение после обновления


users = load_users()
app = Flask(__name__)
# Главное меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        KeyboardButton("🤖 Создать бота"),
        KeyboardButton("ℹ️ Информация"),
        KeyboardButton("💬 Отзывы"),
        KeyboardButton("👤 Профиль")
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

    bot.send_message(
        message.chat.id,
        "Привет! Выберите действие:",
        reply_markup=main_menu()
    )
# Меню выбора типа бота
def create_bot_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    options = [
        "📢 Автопостинг", "💳 Продажа цифровых товаров", "📊 Арбитраж криптовалют",
        "🖼️ Генерация изображений AI", "📝 Генерация PDF-документов",
        "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
        "📅 Бронирование услуг", "🔙 Назад"
    ]
    for text in options:
        markup.add(KeyboardButton(text))
    return markup

# Обработчик кнопки "Создать бота"
@bot.message_handler(func=lambda message: message.text == "🤖 Создать бота")
def handle_create_bot(message):
    bot.send_message(message.chat.id, "Выберите тип бота:", reply_markup=create_bot_menu())

# Обработчик выбора типа бота
@bot.message_handler(func=lambda message: message.text in [
    "📢 Автопостинг", "💳 Продажа цифровых товаров", "📊 Арбитраж криптовалют",
    "🖼️ Генерация изображений AI", "📝 Генерация PDF-документов",
    "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
    "📅 Бронирование услуг"
])
def process_bot_type(message):
    user_id = str(message.from_user.id)
    users[user_id]["selected_bot_type"] = message.text
    users[user_id]["state"] = "waiting_for_bot_name"
    save_users(users)

    bot.send_message(message.chat.id, f"Вы выбрали: {message.text}\n\nВведите имя для вашего бота:")

# Обработчик ввода имени бота
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("state") == "waiting_for_bot_name")
def process_bot_name(message):
    user_id = str(message.from_user.id)
    users[user_id]["bot_name"] = message.text
    users[user_id]["state"] = "waiting_for_payment"
    save_users(users)

    bot.send_message(
        message.chat.id,
        f"✅ Имя бота сохранено: *{message.text}*\n\n"
        "💰 Для продолжения необходимо оплатить создание.\n"
        "Проверяем ваш баланс...",
        parse_mode="Markdown"
    )

    check_user_balance(user_id, message.chat.id)
# Проверка баланса перед созданием бота
def check_user_balance(user_id, chat_id):
    balance = users.get(user_id, {}).get("balance", 0)
    bot_price = 29.99  # Стоимость создания бота

    if balance >= bot_price:
        users[user_id]["balance"] -= bot_price
        save_users(users)
        finalize_bot_creation(user_id, chat_id)
    else:
        missing_amount = bot_price - balance
        bot.send_message(chat_id, f"❗ Недостаточно средств. Нужно еще {missing_amount} USDT.")
        send_payment_link(user_id, chat_id, missing_amount)


def send_payment_button(chat_id):
    """Функция отправки кнопки для оплаты"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💳 Оплатить создание бота", callback_data="pay_create_bot"))

    bot.send_message(chat_id, "Для оплаты нажмите кнопку ниже:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "pay_create_bot")
def process_payment(call):
    """Обработчик нажатия на кнопку оплаты"""
    user_id = call.from_user.id

    if user_id not in users:
        bot.send_message(call.message.chat.id, "⚠️ Вы не зарегистрированы в системе.")
        return

    amount = 29.99  # Цена создания бота в USDT
    payment_url = f"https://pay.crypt.bot/?to=ВАШ_КОШЕЛЕК&amount={amount}&currency=USDT"

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🔗 Оплатить", url=payment_url))

    bot.send_message(call.message.chat.id, f"💰 Для оплаты перейдите по ссылке:", reply_markup=markup)
# Завершение создания бота после оплаты
def finalize_bot_creation(user_id, chat_id):
    bot_name = users[user_id].get("bot_name", "Без имени")
    bot_type = users[user_id].get("selected_bot_type", "Неизвестный тип")

    bot.send_message(
        chat_id,
        f"✅ Ваша заявка отправлена разработчику!\n\n"
        f"🔹 *Название бота:* {bot_name}\n"
        f"🔹 *Тип:* {bot_type}\n\n"
        f"⏳ Среднее время создания: *до 72 часов*.\n"
        f"🔔 Вы получите уведомление, когда бот будет готов!",
        parse_mode="Markdown"
    )

    # Уведомление администратору
    bot.send_message(
        ADMIN_ID,
        f"🔔 *Новая заявка на бота!*\n\n"
        f"👤 Пользователь: @{users[user_id].get('username', 'Неизвестно')}\n"
        f"🔹 Название: {bot_name}\n"
        f"🔹 Тип: {bot_type}\n",
        parse_mode="Markdown"
    )

    users[user_id]["state"] = None
    save_users(users)
    # Обработчик профиля
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_callback(message):
    user_id = str(message.from_user.id)

    if user_id not in users:
        bot.send_message(message.chat.id, "❌ Ошибка: ваш профиль не найден.")
        return

    username = users[user_id].get("username", "Не указан")
    balance = users[user_id].get("balance", 0)

    bot.send_message(
        message.chat.id,
        f"👤 *Ваш профиль:*\n\n"
        f"🔹 *Имя пользователя:* @{username}\n"
        f"💰 *Баланс:* {balance} USDT",
        parse_mode="Markdown"
    )

# Обработчик информации
@bot.message_handler(func=lambda message: message.text == "ℹ️ Информация")
def info_callback(message):
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
    bot.send_message(message.chat.id, info_text, parse_mode="Markdown")

# Кнопка "Отзывы" с актуальной ссылкой
@bot.message_handler(func=lambda message: message.text == "💬 Отзывы")
def reviews_callback(message):
    bot.send_message(
        message.chat.id,
        "💬 Вы можете оставить отзыв или прочитать мнения других пользователей здесь:\n\n"
        "👉 [Перейти в группу отзывов](https://t.me/nWf0L9BBCoJlY2Qy)",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    # Обработчик кнопки "Назад" везде, где это требуется
@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_to_main_menu(message):
    bot.send_message(message.chat.id, "🔙 Возвращаемся в главное меню...", reply_markup=main_menu())

# Обработчик кнопки "Назад" из меню выбора бота
@bot.message_handler(func=lambda message: message.text in [
    "📢 Автопостинг", "💳 Продажа цифровых товаров", "📊 Арбитраж криптовалют",
    "🖼️ Генерация изображений AI", "📝 Генерация PDF-документов",
    "🔗 Продажа подписок", "🔍 Поиск airdrop'ов", "🔒 Продажа VPN/прокси",
    "📅 Бронирование услуг"
])
def back_from_bot_type(message):
    bot.send_message(message.chat.id, "🔙 Возвращаемся в меню выбора типа бота...", reply_markup=create_bot_menu())

# Обработчик кнопки "Назад" из этапа ввода имени бота
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("state") == "waiting_for_bot_name")
def back_from_bot_name(message):
    users[str(message.from_user.id)]["state"] = None
    save_users(users)
    bot.send_message(message.chat.id, "🔙 Возвращаемся в меню выбора типа бота...", reply_markup=create_bot_menu())

# Обработчик кнопки "Назад" из этапа оплаты
@bot.message_handler(func=lambda message: users.get(str(message.from_user.id), {}).get("state") == "waiting_for_payment")
def back_from_payment(message):
    users[str(message.from_user.id)]["state"] = None
    save_users(users)
    bot.send_message(message.chat.id, "🔙 Возвращаемся в главное меню...", reply_markup=main_menu())
if __name__ == "__main__":
    print("✅ Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
