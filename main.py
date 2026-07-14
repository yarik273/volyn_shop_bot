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
CARD_HOLDER = "Шеремета Ярослав Володимирович."           
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
жим ШІ
Усі
Зображення
Новини
Відео
Короткі відео
Вебсторінки
Книги
Фінанси

7 сайтів
Боти в Telegram-каналах використовуються для автоматизації публікацій, збору аналітики, модерації коментарів та спілкування з аудиторією. 

Partnerkin
 +1
 Щоб бот міг виконувати свої функції (наприклад, публікувати пости або керувати коментарями), його обов'язково потрібно додати в адміністратори каналу.
Нижче наведено покрокову інструкцію, як додати будь-якого бота до каналу, а також добірку найкращих інструментів для різних завдань.
Як додати бота в Telegram-канал та налаштувати його
Знайдіть бота: Введіть у пошуку месенджера точне ім'я бота через символ @ (наприклад, @TGStat_Bot). 

Sber Developer
Перейдіть до налаштувань каналу: Відкрийте свій канал, натисніть на його назву (або на три крапки) та виберіть «Управління каналом» (Manage Channel). 

Sber Developer
Призначте адміністратором: Перейдіть у розділ «Адміністратори» → «Додати адміністратора». 

Sber Developer
Знайдіть та додайте бота: Вставте нікнейм бота у рядок пошуку, виберіть його та надайте необхідні права (наприклад, «Публікація дописів» або «Редагування дописів»). 
Активуйте бота: Перейдіть у чат із самим ботом та виконайте його стартові команди (зазвичай це /start або додання каналу через внутрішнє меню бота). 

Unisender
 +1
Популярні боти за категоріями
📝 Автовідкладення та оформлення контенту
@ControllerBot — класичний безкоштовний сервіс для створення відкладених постів, додавання кнопок реакцій, посилань та перегляду базової статистики. 

Unisender
@NotepostBot — сучасний бот для автопостингу з можливістю налаштування розкладів, інтеграції з канбан-дошками та розширеним редактором тексту. 

Unisender
@AximoBot — зручний інструмент для автоматичного імпорту та пересилання нових постів чи відео з інших платформ (YouTube, TikTok, RSS-стрічки) прямо у ваш канал. 
📊 Статистика та аналітика
@TGStat_Bot — офіційний бот відомої платформи аналітики, який миттєво надсилає детальні звіти щодо охоплень, підписників та залученості будь-якого відкритого каналу.
@telemetrmebot — інструмент аналізу каналів від сервісу Telemetr, що допомагає відстежувати динаміку аудиторії та перевіряти інші канали на предмет накрутки перед купівлею реклами. 

ChatPlace
🛡️ Модерація та захист від спаму
@ChatKeeperBot або @Shieldy — частіше використовуються у прив'язаних до каналу чатах-обговореннях; вони автоматично видаляють спам, матюки, посилання та ставлять капчу для нових користувачів.
@TGAlertsBot — моніторить згадки назви вашого каналу або брендів за заданими ключовими словами по всьому Telegram. 
⚙️ Корисні утиліти
@voicybot — автоматично перетворює будь-які голосові повідомлення чи аудіофайли, надіслані у чат, у друкований текст.
@Stickers — офіційний бот від розробників Telegram для створення та завантаження власних брендованих стикерпаків. 
Як створити власного персонального бота?
Якщо вам потрібен унікальний робот під індивідуальні завдання, його можна створити самостійно:
Запустіть головного бота месенджера — @BotFather.
Надішліть команду /newbot, вкажіть назву та унікальне системне ім'я (username), яке закінчується на bot.
Скопіюйте отриманий API-токен.
Підключіть цей токен до No-Code конструкторів (наприклад, Manybot, PuzzleBot) або використовуйте мови програмування (Python, Node.js), щоб прописати логіку роботи. 

Unisender
 +2
Яке саме конкретне завдання ви хочете вирішити за допомогою бота (наприклад, налаштувати відкладений постинг, приймати заявки чи видаляти спам в обговореннях)? Розкажіть, і я підкажу найкращий інструмент або алгоритм налаштування!
Відповіді ШІ можуть містити помилки. Докладніше





Цей скриншот показує сповіщення від системи моніторингу (наприклад, Uptime Robot або подібного сервісу) про те, що ваш Telegram-бот, розміщений на платформі Render (onrender.com), наразі не працює.
Система зафіксувала помилку HTTP 501 – Не реалізовано (Not Implemented).
Що означає помилка HTTP 501?
Помилка 501 означає, що вебсервер Render, на якому запущено вашого бота, отримав мережевий запит (наприклад, вебхук від Telegram або перевірку від моніторингу), але серверний код вашого бота або конфігурація сервера не підтримують метод цього запиту (найчастіше це неправильна обробка запитів GET або POST).
Оскільки Render переводить безкоштовні вебсервіси (Free tier) у «режим сну» після 15 хвилин бездіяльності, система моніторингу намагалася «розбудити» або перевірити його, але код бота відповів некоректно.
Як це виправити?
Щоб повернути бота до життя та уникнути таких помилок, виконайте такі кроки:
1. Додайте базовий обробник GET-запитів у код бота
Для безкоштовного хостингу на Render бот обов'язково повинен мати хоча б мінімальний вебсервер (наприклад, на базі Flask чи FastAPI для Python, або Express для Node.js), який віддаватиме статус 200 OK при звичайному зверненні до сайту.
Приклад для Python (Flask):
python
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!", 200 # Повертає HTTP 200 замість 501
Будьте обачні, використовуючи код.
Приклад для Node.js (Express):
javascript
const express = require('express');
const app = express();

app.get('/', (req, res) => {
    res.status(200).send('Bot is running!');
});
Будьте обачні, використовуючи код.
2. Перевірте логи в панелі Render
Зайдіть у свій кабінет на render.com.
Виберіть ваш сервіс volyn-shop-bot.
Перейдіть у вкладку Logs (Логи) праворуч.
Подивіться, яка саме помилка виникає в коді під час запиту о 14:13:01. Можливо, бот просто «впав» через необроблену помилку в самому коді, або йому не вистачає змінних оточення (Environment Variables).
3. Налаштуйте правильний тип сервісу
Якщо ваш бот працює на основі технології Long Polling (простий запуск без вебхуків, коли бот сам постійно опитує сервери Telegram), на Render його потрібно запускати не як Web Service, а як Background Worker.
Background Worker на Render працює безперервно і не засинає.
Зверніть увагу: з серпня 2024 року Background Worker на Render став повністю платним. Якщо ви хочете залишитися на безкоштовному тарифі, вам доведеться переписати бота на Webhooks та використовувати Web Service.
Щоб я міг допомогти точніше, підкажіть: на якій мові програмування написаний ваш бот (Python, Node.js тощо) та яку бібліотеку ви використовували?
Відповіді ШІ можуть містити помилки. Докладніше





Так, звісно, надсилайте код! Це буде найкращим рішенням.
Я не буду переписувати ваш код повністю, а зроблю саме так, як ви просите:
Подивлюся, як у вас налаштований запуск бота.
Покажу конкретний маленький шматочок коду, якого не вистачає для платформи Render.
Точно розпишу, після якого або перед яким рядком у вашому файлі цей шматочок потрібно вставити.
Чекаю на ваш код! Також напишіть, будь ласка, назву файлу, якщо код розбитий на кілька частин (наприклад, main.py чи index.js).
Відповіді ШІ можуть містити помилки. Докладніше





Чудово, тепер усе стало на свої місця! У вашому коді вже є спроба зробити вебсервер наприкінці файлу (через BaseHTTPRequestHandler), але в ньому якраз і криється причина помилки HTTP 501.
У коді прописаний лише метод do_GET. А система моніторингу або сама платформа Render надсилає запит іншого типу (наприклад, POST або HEAD), для якого у вашому сервері немає інструкцій. Через це сервер автоматично відповідає кодом 501 — Not Implemented (Не реалізовано).
Ось що саме і куди потрібно додати, не змінюючи решту логіки.
Що потрібно дописати
Знайдіть у самому кінці коду клас HealthCheckHandler (він починається приблизно на 104-му рядку). Зараз він виглядає так:
python
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, format, *args):
        return
Будьте обачні, використовуючи код.
Вам потрібно всередину цього класу (одразу після блоку do_GET і перед log_message) дописати ще два методи: do_HEAD та do_POST. Вони будуть відповідати успішним кодом 200 на будь-які інші перевірки від платформи.
Куди саме вставити (готовий шматок)
Замініть цей маленький блок з класом HealthCheckHandler на такий варіант:
python
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def do_POST(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        return
Будьте обачні, використовуючи код.
Що робити після цього:
Збережіть файл із кодом.
Відправте (зробіть git push) оновлений код у свій репозиторій на GitHub, звідки Render бере бота.
Render автоматично почне перезбірку (Deploy). Як тільки вона завершиться, помилка 501 зникне, а статус у моніторингу зміниться на зелений.
Чи виникають у вас якісь помилки в консолі (logs) на самому Render під час поточної збірки, чи проблема була лише в цьому сповіщенні?
Відповіді ШІ можуть містити помилки. Докладніше





Так, усе абсолютно правильно!
Вам потрібно видалити тільки цей шматочок, який ви скинули, і на його місце вставити новий код. Усі інші рядки вище та нижче (налаштування бота, токен, товари, а також функція run_health_server та if __name__ == "__main__":) повинні залишитися недоторканими.
Зверніть увагу на один важливий момент: у мові Python дуже важливі відступи (пробіли попереду рядків). Коли будете вставляти код, переконайтеся, що він стоїть рівно і має таку саму структуру.
Ось фінальний вигляд нижньої частини вашого файлу, щоб ви могли звіритися:
python
    # ... тут закінчується функція process_buy(call) ...
    bot.answer_callback_query(call.id)

# === ВЕБ-СЕРВЕР ДЛЯ RENDER ===
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def do_POST(self):
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
