import telebot
import os
import threading
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================= НАЛАШТУВАННЯ БОТА =================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 👇 ВАШ РЕАЛЬНИЙ ID ГІЛКИ З ПОСИЛАННЯ 👇
TARGET_THREAD_ID = 693  

# Реквізити для гравців
CARD_NUMBER = "4149439024408951"  # Вкажіть вашу карту
CARD_HOLDER = "Ярослав Володимирович."           # Ваше ім'я
# =====================================================

bot = telebot.TeleBot(BOT_TOKEN)

# 1. Реагуємо на команду /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    current_thread_id = message.message_thread_id
    
    # Якщо пишуть у групі, але НЕ в тій гілці — ігноруємо.
    # В особистих повідомленнях chat.type буде 'private', тому ця умова пропуститься!
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
        message_thread_id=current_thread_id  # Автоматично підлаштується (в приватних буде None)
    )

# 2. Обробка кнопки "Купити привілегію"
@bot.callback_query_handler(func=lambda call: call.data == "open_shop")
def open_shop(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="💎 VIP (200 грн / 30 днів)", callback_data="buy_vip"),
        types.InlineKeyboardButton(text="🛡️ Admin (400 грн / 30 днів)", callback_data="buy_admin"),
        types.InlineKeyboardButton(text="👑 Спонсор (800 грн / 30 днів)", callback_data="buy_sponsor")
    )
    shop_text = "📋 **Оберіть привілегію, яку бажаєте придбати:**"
    bot.edit_message_text(shop_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# 3. Вивід картки та інструкції
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy_button(call):
    # Виправлено: додано індекс, щоб правильно отримувати тип послуги (vip, admin, sponsor)
    priv_type = call.data.split("_")[1]
    prices = {"vip": "200 грн", "admin": "400 грн", "sponsor": "800 грн"}
    names = {"vip": "💎 VIP-статус", "admin": "🛡️ Права Адміна", "sponsor": "👑 Спонсор сервера"}
    
    response_text = (
        f"📋 **Ви обрали:** {names[priv_type]}\n"
        f"⏳ **Термін дії:** 30 днів\n"
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
    bot.send_message(call.message.chat.id, response_text, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# === ВЕБ-СЕРВЕР ДЛЯ СТАБІЛЬНОЇ РОБОТИ НА RENDER ===
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
    
    # Решение против ошибки 409 на Render:
    try:
        print("Вибиваємо старі завислі процеси...")
        bot.log_out()  # Принудительно закрывает старые сессии в Telegram
    except Exception as e:
        print(f"Запис log_out пропущено або вже очищено: {e}")
        
    bot.remove_webhook() 
    bot.infinity_polling(skip_pending=True)
    
    
