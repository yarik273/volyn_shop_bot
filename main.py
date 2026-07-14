import telebot
import os
import threading
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================= НАЛАШТУВАННЯ БОТА =================
BOT_TOKEN = os.getenv("MY_NEW_SECRET_TOKEN")  # Наша безпечна змінна
TARGET_THREAD_ID = 693  # Ваш ID гілки

# Реквізити для гравців (ВКАЖІТЬ ВАШІ РЕАЛЬНІ ДАНІ)
CARD_NUMBER = "4149439024408951"
CARD_HOLDER = "Ярослав Володимирович."           
# =====================================================

bot = telebot.TeleBot(BOT_TOKEN)

# 1. Реагуємо на команду /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    current_thread_id = message.message_thread_id
    if message.chat.type in ['group', 'supergroup'] and current_thread_id != TARGET_THREAD_ID:
        return

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🛒 Купити привілегію", callback_data="open_shop"))
    
    welcome_text = (
        "👋 **Вітаємо в магазині нашого сервера CS 1.6!**\n\n"
        "Натисніть на кнопку нижче, щоб переглянути доступні привілегії 👇"
    )
    bot.send_message(
        chat_id=message.chat.id, 
        text=welcome_text, 
        reply_markup=keyboard, 
        parse_mode="Markdown",
        message_thread_id=current_thread_id
    )

# 2. Обробка кнопки "Купити привілегію"
@bot.callback_query_handler(func=lambda call: call.data == "open_shop")
def open_shop(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="💎 VIP (200 грн / 30 днів)", callback_data="buy_vip"),
        types.InlineKeyboardButton(text="🛡️ Admin (400 грн / 30 днів)", callback_data="buy_admin"),
        types.InlineKeyboardButton(text="👑 Спонсор (800 грн / 30 днів)", callback_data="buy_sponsor"),
        types.InlineKeyboardButton(text="👕 Модель гравця (100 грн / 30 днів)", callback_data="buy_model"),
        types.InlineKeyboardButton(text="💰 5000 бонусів (100 грн)", callback_data="buy_bonuses")
    )
    shop_text = "📋 **Оберіть привілегію або товар, який бажаєте придбати:**"
    
    bot.edit_message_text(
        text=shop_text, 
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        reply_markup=keyboard, 
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# 3. Вивід картки та інструкції замовлення
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy_button(call):
    # Отримуємо точний тип послуги після знаку підкреслення
    priv_type = call.data.split("_")[1]
    
    # Списки цін та назв, куди ми додали нові товари
    prices = {
        "vip": "200 грн", 
        "admin": "400 грн", 
        "sponsor": "800 грн",
        "model": "100 грн",
        "bonuses": "100 грн"
    }
    
    names = {
        "vip": "💎 VIP-статус (30 днів)", 
        "admin": "🛡️ Права Адміна (30 днів)", 
        "sponsor": "👑 Спонсор сервера (30 днів)",
        "model": "👕 Унікальна модель гравця (30 днів)",
        "bonuses": "💰 Пакет 5000 бонусів"
    }
    
    response_text = (
        f"📋 **Ви обрали:** {names[priv_type]}\n"
        f"💰 **Сума до сплати:** {prices[priv_type]}\n\n"
        f"💳 **Реквізити для оплати:**\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 **Отримувач:** {CARD_HOLDER}\n\n"
        f"⚠️ **Важлива інструкція:**\n"
        f"Оплатіть точну суму на картку. Після цього надішліть сюди інформацію у такому форматі:\n\n"
        f"1. Скріншот чека про оплату 📸\n"
        f"2. Ваш Нік 🎮\n"
        f"3. Ваш SteamID 🆔 (наприклад, `STEAM_0:0:12345678`)"
    )
    
    bot.edit_message_text(
        text=response_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# === ВЕБ-СЕРВЕР ДЛЯ RENDER ===
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        return

def run_health_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()
    print("Магазин привілегій успішно запущено!")
    
    bot.remove_webhook()
    bot.polling(none_stop=True, interval=2, timeout=15)
    
