import asyncio
import os
import socket
import struct
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from ftplib import FTP

# ================= НАЛАШТУВАННЯ БОТА =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TG_ID = 5596041220  # Ваш особистий Telegram ID

# Реквізити для гравців
CARD_NUMBER = "4149 4999 1111 2222"  # Вкажіть вашу карту
CARD_HOLDER = "Ярослав В."
# =====================================================

# ================= НАЛАШТУВАННЯ СЕРВЕРА CS 1.6 =======
FTP_HOST = "IP_АДРЕСА_ХОСТИНГУ"      
FTP_USER = "ЛОГІН_FTP"
FTP_PASS = "ПАРОЛЬ_FTP"
FTP_FILE_PATH = "/cstrike/addons/amxmodx/config/users.ini" 

RCON_HOST = "IP_СЕРВЕРА_ГРИ"         
RCON_PORT = 27015                    
RCON_PASS = "RCON_ПАРОЛЬ_СЕРВЕРА"

# Прапори доступу (флаги) для кожної привілегії
FLAGS_CONFIG = {
    "vip": "t",                        
    "admin": "abcdef",                 
    "sponsor": "abcdefghijklmnopqrst"  
}
# =====================================================

# Легка функція відправки RCON-команди для GoldSource (CS 1.6) без сторонніх бібліотек
def send_cs_rcon(host, port, rcon_password, command):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3.0)
        # Стандартний пакет запиту для серверів CS 1.6
        req = b'\xFF\xFF\xFF\xFFrcon ' + rcon_password.encode('utf-8') + b' ' + command.encode('utf-8') + b'\n'
        s.sendto(req, (host, int(port)))
        data, _ = s.recvfrom(4096)
        s.close()
        return data.decode('utf-8', errors='ignore')
    except Exception as e:
        return f"Помилка RCON: {str(e)}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 1. Реагуємо на команду /start (Показуємо ЛИШЕ ОДНУ кнопку)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = [
        [types.InlineKeyboardButton(text="🛒 Купити привілегію", callback_data="open_shop")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    
    welcome_text = (
        "👋 **Вітаємо в магазині нашого сервера CS 1.6!**\n\n"
        "Натисніть на кнопку нижче, щоб переглянути доступні привілегії 👇"
    )
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="Markdown")

# 2. Людина натиснула "Купити привілегію" -> відкриваємо список товарів
@dp.callback_query(F.data == "open_shop")
async def open_shop(callback: types.CallbackQuery):
    kb = [
        [types.InlineKeyboardButton(text="💎 VIP (200 грн / 30 днів)", callback_data="buy_vip")],
        [types.InlineKeyboardButton(text="🛡️ Адмін (400 грн / 30 днів)", callback_data="buy_admin")],
        [types.InlineKeyboardButton(text="👑 Спонсор (800 грн / 30 днів)", callback_data="buy_sponsor")]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    shop_text = "📋 **Оберіть привілегію, яку бажаєте придбати:**"
    await callback.message.edit_text(shop_text, reply_markup=keyboard, parse_mode="Markdown")
    await callback.answer()

# 3. Вивід реквізитів та інструкції
@dp.callback_query(F.data.startswith("buy_"))
async def process_buy_button(callback: types.CallbackQuery):
    priv_type = callback.data.split("_")[1]
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
        f"Оплатіть точну суму на картку. Після цього надішліть сюди (в особисті повідомлення боту) інформацію у такому форматі:\n\n"
        f"1. Скріншот чека про оплату 📸\n"
        f"2. Ваш Нік у грі 🎮\n"
        f"3. Ваш SteamID 🆔 (наприклад, `STEAM_0:0:12345678`)"
    )
    await callback.message.answer(response_text, parse_mode="Markdown")
    await callback.answer()

# 4. ТАЄМНА КОМАНДА ВИДАЧІ ДЛЯ ВАС (Працює тільки для вашого ADMIN_TG_ID)
@dp.message(F.chat.type == "private", F.from_user.id == ADMIN_TG_ID, Command("give"))
async def grant_privilege_command(message: types.Message):
    try:
        args = message.text.split(maxsplit=3)
        if len(args) < 3:
            await message.answer("❌ Формат команди: `/give [vip/admin/sponsor] [SteamID] [Нік]`", parse_mode="Markdown")
            return
            
        priv_type = args[1].lower()
        steam_id = args[2]
        nickname = args[3] if len(args) > 3 else "Гравець"
        
        if priv_type not in FLAGS_CONFIG:
            await message.answer("❌ Невірний тип! Доступно: vip, admin, sponsor")
            return
            
        flags = FLAGS_CONFIG[priv_type]
        new_entry = f'\n; Додано ботом для {nickname}\n"{steam_id}" "" "{flags}" "ce"'
        
        # 1. Підключаємося по FTP та оновлюємо users.ini
        with FTP(FTP_HOST) as ftp:
            ftp.login(user=FTP_USER, passwd=FTP_PASS)
            lines = []
            ftp.retrlines(f'RETR {FTP_FILE_PATH}', lines.append)
            file_content = "\n".join(lines)
            
            updated_content = file_content + new_entry
            
            with open("temp_users.ini", "w", encoding="utf-8") as temp_file:
                temp_file.write(updated_content)
                
            with open("temp_users.ini", "rb") as temp_file:
                ftp.storbinary(f'STOR {FTP_FILE_PATH}', temp_file)
                
        # 2. Оновлюємо список адмінів у грі через нашу легку RCON функцію
        send_cs_rcon(RCON_HOST, RCON_PORT, RCON_PASS, "amx_reloadadmins")
            
        await message.answer(f"✅ Успішно! Гравцю *{nickname}* ({steam_id}) видано привілегію **{priv_type}**.\nСервер оновлено через RCON.", parse_mode="Markdown")
        
    except Exception as e:
        await message.answer(f"❌ Помилка: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
