import telebot
import os
import threading
import time
from telebot import types
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================= НАЛАШТУВАННЯ БОТА =================
BOT_TOKEN = os.getenv("MY_NEW_SECRET_TOKEN")  # Наша нова безпечна змінна
TARGET_THREAD_ID = 693  # Ваш ID гілки

# Реквізити для гравців
CARD_NUMBER = "4149 4999 1122"  # Вкажіть вашу реальну карту
CARD_HOLDER = "Ярослав В."           # Ваше ім'я
# =====================================================

bot = telebot.TeleBot(BOT_TOKEN)

# Функція автовидалення повідомлень
def auto_delete_message(chat_id, message_id, delay_seconds=30):  # ⏱️ ТИМЧАСОВО 30 СЕКУНД ДЛЯ ТЕСТУ!
    time.sleep(delay_seconds)
    try:
        bot.delete_message(chat_id, message_id)
        print(f"DEBUG: Повідомлення {message_id} успішно видалено за таймером.")
    except Exception as e:
        print(f"DEBUG: Не вдалося видалити повідомлення: {e}")

# 1. Реагуємо на команду /start (Кнопка залишається в гілці назавжди)
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
        types.InlineKeyboardButton(text="👑 Спонсор (800 грн / 30 днів)", callback_data="buy_sponsor")
    )
    shop_text = "📋 **Оберіть привілегію, яку бажаєте придбати:**"
    
    if call.message.chat.type in ['group', 'supergroup']:
        sent_msg = bot.send_message(
            chat_id=call.message.chat.id,
            text=shop_text,
            reply_markup=keyboard,
            parse_mode="Markdown",
            message_thread_id=call.message.message_thread_id
        )
        # Запускаємо таймер видалення меню вибору
        threading.Thread(target=auto_delete_message, args=(call.message.chat.id, sent_msg.message_id, 30), daemon=True).start()
    else:
        bot.edit_message_text(shop_text, call.message.chat.id, call.message.message_id, reply_markup=keyboard, parse_mode="Markdown")
        
    bot.answer_callback_query(call.id)

# 3. Вивід картки та інструкції (ТУТ ВСЕ ВИПРАВЛЕНО)
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_buy_button(call):
    # ✅ ВИПРАВЛЕНО: додано індекс [1], тепер воно чітко розпізнає vip, admin чи sponsor
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
        f"3. Ваш SteamID 🆔"
    )
    
    # Надсилаємо реквізити в чат групи або в приват
    sent_info = bot.send_message(
        chat_id=call.message.chat.id, 
        text=response_text, 
        parse_mode="Markdown",
        message_thread_id=call.message.message_thread_id if call.message.chat.type in ['group', 'supergroup'] else None
    )
    
    if call.message.chat.type in ['group', 'supergroup']:
        # Видаляємо проміжне меню вибору товару, щоб воно не висіло
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
            
        # Запускаємо таймер видалення для самого повідомлення з реквізитами картки
        threading.Thread(target=auto_delete_message, args=(call.message.chat.id, sent_info.message_id, 30), daemon=True).start()
        
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
    
