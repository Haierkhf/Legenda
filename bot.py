import os
import json
import logging
import threading
import time
import subprocess
import requests
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv



# Загрузка токенов из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # Укажите свой Telegram ID в переменных окружения

bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения данных пользователей
USERS_FILE = "users.json"


# Функция загрузки данных пользователей
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# Функция сохранения данных пользователей
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4, ensure_ascii=False)


users = load_users()


# Функция проверки инициализации пользователя
def check_user(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {"balance": 0, "actions": []}
        save_users(users)


# Функция создания главного меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("👤 Профиль"), KeyboardButton("🤖 Создать бота"))
    markup.add(KeyboardButton("ℹ️ Информация"), KeyboardButton("⭐ Отзывы"))
    return markup


# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start_handler(message):
    user_id = message.chat.id
    check_user(user_id)
    bot.send_message(
        user_id,
        "👋 Привет! Выберите действие:",
        reply_markup=main_menu(),
    )


# Обработчик кнопки "👤 Профиль"
@bot.message_handler(func=lambda message: message.text == "👤 Профиль")
def profile_handler(message):
    user_id = str(message.chat.id)
    check_user(user_id)
    user_data = users[user_id]
    balance = user_data["balance"]
    actions = "\n".join(user_data["actions"][-5:]) or "Нет действий"

    text = f"👤 Ваш профиль:\n💰 Баланс: {balance}$\n📜 Последние действия:\n{actions}"

    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("💵 Вывести средства"))
    markup.add(KeyboardButton("📊 Статистика"), KeyboardButton("🔙 Назад"))
    
    bot.send_message(user_id, text, reply_markup=markup)


# Обработчик кнопки "💵 Вывести средства"
@bot.message_handler(func=lambda message: message.text == "💵 Вывести средства")
def withdraw_handler(message):
    user_id = str(message.chat.id)
    check_user(user_id)

    bot.send_message(user_id, "Введите сумму для вывода (минимум 10$):")
    bot.register_next_step_handler(message, process_withdraw)


# Функция обработки суммы вывода
def process_withdraw(message):
    user_id = str(message.chat.id)
    check_user(user_id)

    try:
        amount = float(message.text)
        if amount < 10:
            bot.send_message(user_id, "❌ Минимальная сумма вывода — 10$")
            return
        
        users[user_id]["actions"].append(f"Запросил вывод {amount}$")
        save_users(users)

        # Отправка владельцу бота
        admin_message = f"🔔 Запрос на вывод!\n👤 Пользователь: {user_id}\n💰 Сумма: {amount}$\n⏳ Обработка до 48 часов."
        bot.send_message(ADMIN_ID, admin_message)

        bot.send_message(user_id, "✅ Ваш запрос на вывод отправлен. Ожидайте в течение 48 часов.")
    
    except ValueError:
        bot.send_message(user_id, "❌ Ошибка! Введите корректную сумму.")


# Запуск бота
bot.polling(none_stop=True)
