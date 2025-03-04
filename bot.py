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


def create_invoice(user_id, amount, currency="USDT"):
    """Создание платежного чека через API Crypto Bot"""
    url = f"{CRYPTO_BOT_API_URL}/createInvoice"
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
