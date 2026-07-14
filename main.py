import asyncio
import os  # Ця бібліотека потрібна, щоб читати дані з Render
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

# ================= НАЛАШТУВАННЯ БОТА =================
# Бот автоматично візьме токен із налаштувань Render (змінна BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Реквізити для гравців (картку ви можете вписати сюди або теж приховати)
CARD_NUMBER = "4149 4999 1111 2222"  # Вкажіть вашу карту
CARD_HOLDER = "Ярослав В."           # Ваше ім'я
# =====================================================

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
        "Натисніть на кнопку ниже, щоб переглянути доступні привілегії 👇"
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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
  
