import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper

def read_config():
    config = {}
    with open("config.txt", "r") as file:
        for line in file:
            # تقسیم خط‌ها بر اساس '='
            key, value = line.strip().split("=")
            config[key] = value
    return config

# خواندن اطلاعات از فایل
config = read_config()
TOKEN = config.get("TOKEN")  # توکن بات
CHANNEL_ID = config.get("CHANNEL_ID")  # آیدی کانال

# ایجاد نمونه از بات
bot = telebot.TeleBot(TOKEN)

# ذخیره اطلاعات کاربران
user_data = {}

# تابع عمومی مدیریت خطا
def handle_error(exception, message):
    print(f"⚠️ خطا رخ داد: {exception}")
    try:
        bot.send_message(message.chat.id, "⛔ مشکلی پیش آمده است. لطفاً دوباره تلاش کنید.")
    except Exception as e:
        print(f"❌ خطای اضافی در ارسال پیام خطا: {e}")

# ساخت منوی اصلی
def main_menu(chat_id):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("  1️⃣ اجرای مجدد بات  "),
        KeyboardButton("  2️⃣ سوال درباره اساتید   "),
        KeyboardButton("  3️⃣ خروج   ")
    )
    bot.send_message(chat_id, "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=markup)

# مدیریت گزینه‌های منوی اصلی
@bot.message_handler(commands=['start'])
def start(message):
    try:
        main_menu(message.chat.id)
    except Exception as e:
        handle_error(e, message)

@bot.message_handler(func=lambda message: message.text in ["1️⃣ اجرای مجدد بات", "2️⃣ سوال درباره اساتید", "3️⃣ خروج"])
def menu_selection(message):
    try:
        if message.text == "1️⃣ اجرای مجدد بات":
            bot.send_message(message.chat.id, "✅ بات دوباره راه‌اندازی شد!")
            main_menu(message.chat.id)
        elif message.text == "2️⃣ سوال درباره اساتید":
            start_ask_about_professors(message)
        elif message.text == "3️⃣ خروج":
            bot.send_message(message.chat.id, "👋 خداحافظ! اگر نیاز داشتید، دوباره /start را ارسال کنید.")
            bot.clear_step_handler(message)  # پایان فرآیند
    except Exception as e:
        handle_error(e, message)

# مسیر سوال درباره اساتید
def start_ask_about_professors(message):
    try:
        user_data[message.chat.id] = {}
        bot.send_message(message.chat.id, "لطفاً نام درس را وارد کنید:")
        bot.register_next_step_handler(message, get_course)
    except Exception as e:
        handle_error(e, message)

def get_course(message):
    try:
        user_data[message.chat.id]['course'] = message.text
        bot.send_message(message.chat.id, "اسم استاد را وارد کنید:")
        bot.register_next_step_handler(message, get_professor)
    except Exception as e:
        handle_error(e, message)

def get_professor(message):
    try:
        user_data[message.chat.id]['professor'] = message.text
        bot.send_message(message.chat.id, "سوال خود را بنویسید:")
        bot.register_next_step_handler(message, get_question)
    except Exception as e:
        handle_error(e, message)

def get_question(message):
    try:
        user_data[message.chat.id]['question'] = message.text
        course = user_data[message.chat.id]['course']
        professor = user_data[message.chat.id]['professor']
        question = user_data[message.chat.id]['question']

        # ساخت متن نهایی
        final_message = (
            f"📚 **درس**: {course}\n"
            f"👨‍🏫 **استاد**: {professor}\n"
            f"❓ **سوال**: {question}\n\n"
             f"⚡️ **به ما بپیوندید:** \n\n @dars_ba_ki_br_darm")

        # ذخیره پیام نهایی برای تأیید
        user_data[message.chat.id]['final_message'] = final_message

        # ارسال پیام برای تأیید
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ تایید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        )
        bot.send_message(message.chat.id, "پیام شما به این شکل خواهد بود:\n\n" + final_message,
                         reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        handle_error(e, message)

# مدیریت تأیید یا لغو
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == "confirm":
            # ارسال پیام به کانال
            final_message = user_data[call.message.chat.id]['final_message']
            bot.send_message(CHANNEL_ID, final_message, parse_mode="Markdown")
            bot.send_message(call.message.chat.id, "✅ پیام شما با موفقیت به کانال ارسال شد!")
            main_menu(call.message.chat.id)
        elif call.data == "cancel":
            bot.send_message(call.message.chat.id, "❌ ارسال پیام لغو شد.")
            main_menu(call.message.chat.id)

        # پاک کردن اطلاعات کاربر
        user_data.pop(call.message.chat.id, None)
    except apihelper.ApiTelegramException as e:
        print(f"❌ Telegram API Error: {e}")
        bot.send_message(call.message.chat.id, "⛔ مشکلی در ارتباط با Telegram API پیش آمد.")
    except Exception as e:
        handle_error(e, call.message)

# اجرای بات
def run_bot():
    while True:  # حلقه برای اجرای مجدد بات در صورت خطا
        try:
            print("🤖 Bot is running...")
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            print(f"❌ Bot stopped due to an error: {e}")
            continue  # اجرای مجدد بات

run_bot()
