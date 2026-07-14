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

# База даних цін та назв для зручного розрахунку
PRICES = {
    "vip": {"30": "200 грн", "60": "380 грн", "90": "550 грн"},  # Виправлено можливу опечатку 350->530, або замініть на свою
    "admin": {"30": "400 грн", "60": "780 грн", "90": "1100 грн"},
    "sponsor": {"30": "800 грн", "60": "1550 грн", "90": "2200 грн"},
    "model": "100 грн",
    "bonuses": "100 грн"
}

NAMES = {
    "vip": "💎 VIP-статус",
    "admin": "🛡️ Права Адміна",
    "sponsor": "👑 Спонсор сервера",
    "model": "👕 Унікальна модель гравця (30 днів)",
    "bonuses": "💰 Пакет 5000 бонусів"
}

# 1. Реагуємо на команду /start
@bot.message_handler(commands=['start'])
def cmd_start(message):
    current_thread_id = message.message_thread_id
    if message.chat.type in ['group', 'supergroup'] and current_thread_id != TARGET_THREAD_ID:
        return

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="🛒 Відкрити Магазин", callback_data="open_shop"))
    
    welcome_text = (
        "👋 **Вітаємо в магазині нашого сервера CS 1.6!**\n\n"
        "Натисніть на кнопку нижче, щоб переглянути доступні товари та привілегії 👇"
    )
    bot.send_message(
        chat_id=message.chat.id, 
        text=welcome_text, 
        reply_markup=keyboard, 
        parse_mode="Markdown",
        message_thread_id=current_thread_id
    )

# 2. Головне меню магазину
@bot.callback_query_handler(func=lambda call: call.data == "open_shop")
def open_shop(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text="💎 VIP-статус", callback_data="select_vip"),
        types.InlineKeyboardButton(text="🛡️ Права Адміна", callback_data="select_admin"),
        types.InlineKeyboardButton(text="👑 Спонсор сервера", callback_data="select_sponsor"),
        types.InlineKeyboardButton(text="👕 Модель гравця (100 грн)", callback_data="buy_model_30"),
        types.InlineKeyboardButton(text="💰 5000 бонусів (100 грн)", callback_data="buy_bonuses_0")
    )
    shop_text = "📋 **Оберіть категорію, яка вас цікавить:**"
    
    bot.edit_message_text(text=shop_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# 3. Меню вибору днів для привілегій
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def select_days(call):
    priv = call.data.split("_")[1]
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(text=f"⏱️ 30 днів ({PRICES[priv]['30']})", callback_data=f"buy_{priv}_30"),
        types.InlineKeyboardButton(text=f"⏱️ 60 днів ({PRICES[priv]['60']})", callback_data=f"buy_{priv}_60"),
        types.InlineKeyboardButton(text=f"⏱️ 90 днів ({PRICES[priv]['90']})", callback_data=f"buy_{priv}_90"),
        types.InlineKeyboardButton(text="⬅️ Назад до магазину", callback_data="open_shop")
    )
    
    text = f"⏳ **Оберіть термін дії для {NAMES[priv]}:**"
    bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# 4. Фінальний вивід реквізитів
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy(call):
    # Отримуємо дані з callback типу: buy_vip_30 або buy_model_30
    _, priv_type, days = call.data.split("_")
    
    # Визначаємо ціну та опис залежно від типу товару
    if priv_type in ["vip", "admin", "sponsor"]:
        price = PRICES[priv_type][days]
        item_name = f"{NAMES[priv_type]} на {days} днів"
    else:
        price = PRICES[priv_type]
        item_name = NAMES[priv_type]
        
    response_text = (
        f"📋 **Ви обрали:** {item_name}\n"
        f"💰 **Сума до сплати:** {price}\n\n"
        f"💳 **Реквізити для оплати:**\n"
        f"`{CARD_NUMBER}`\n"
        f"👤 **Отримувач:** {CARD_HOLDER}\n\n"
        f"⚠️ **Важлива інструкція:**\n"
        f"Оплатіть точну суму на картку. Після цього надішліть сюди інформацію у такому форматі:\n\n"
        f"1. Скріншот чека про оплату 📸\n"
        f"2. Ваш Нік 🎮\n"
        f"3. Ваш SteamID 🆔 (наприклад, `STEAM_0:0:12345678`)"
    )
    
    # Додаємо кнопку повернення назад на випадок, якщо гравець передумав
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="⬅️ Назад до магазину", callback_data="open_shop"))
    
    bot.edit_message_text(
        text=response_text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        reply_markup=keyboard,
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
