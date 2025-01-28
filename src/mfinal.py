import os
import logging
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
from dotenv import load_dotenv
import time

# بارگذاری متغیرهای محیطی از فایل .env
load_dotenv()

# تنظیمات لاگ‌گیری
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),  # ذخیره لاگ در فایل
        logging.StreamHandler(),  # نمایش لاگ در کنسول
    ],
)
logger = logging.getLogger(__name__)

# خواندن اطلاعات از محیط‌های متغیر
TOKEN = os.getenv("TOKEN")  # توکن بات
CHANNEL_ID = os.getenv("CHANNEL_ID")  # آیدی کانال
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # آیدی ادمین برای پشتیبانی

# بررسی وجود توکن و آیدی کانال
if not TOKEN or not CHANNEL_ID or not ADMIN_CHAT_ID:
    logger.error("❌ توکن، آیدی کانال یا آیدی ادمین در فایل .env تنظیم نشده است.")
    exit(1)

# ایجاد نمونه از بات
bot = telebot.TeleBot(TOKEN)

# ذخیره اطلاعات کاربران
user_data = {}


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

        # جدا کردن اسامی اساتید با خط جدید
        professors_list = professor.replace("،", "\n").replace("/", "\n").replace(",", "\n")

        # ساخت متن نهایی با فرمت مورد نظر
        final_message = (
            f"درس: #{course.replace(' ', '_')}\n\n"
            f"🚬استاد: {professors_list}\n\n"
            f"❔سوال: {question}\n\n"
            f"⚡️ به ما بپیوندید ↙️\n\n"
            f"@dars_ba_ki_br_darm"
        )

        # ذخیره پیام نهایی برای تأیید
        user_data[message.chat.id]['final_message'] = final_message

        # ارسال پیام برای تأیید (بدون استفاده از Markdown)
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("✅ تایید", callback_data="confirm"),
            InlineKeyboardButton("❌ لغو", callback_data="cancel")
        )
        bot.send_message(message.chat.id, "پیام شما به این شکل خواهد بود:\n\n" + final_message,
                         reply_markup=markup, parse_mode=None)  # parse_mode=None
    except Exception as e:
        handle_error(e, message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == "confirm":
            # بررسی وجود اطلاعات کاربر
            if call.message.chat.id not in user_data or 'final_message' not in user_data[call.message.chat.id]:
                bot.send_message(call.message.chat.id, "⛔ مشکلی در پردازش پیام شما پیش آمد. لطفاً دوباره تلاش کنید.")
                return

            # ارسال پیام به کانال (بدون استفاده از Markdown)
            final_message = user_data[call.message.chat.id]['final_message']
            bot.send_message(CHANNEL_ID, final_message, parse_mode=None)  # parse_mode=None
            bot.send_message(call.message.chat.id, "✅ پیام شما با موفقیت به کانال ارسال شد!")
            main_menu(call.message.chat.id)

        elif call.data == "cancel":
            bot.send_message(call.message.chat.id, "❌ ارسال پیام لغو شد.")
            main_menu(call.message.chat.id)

        # پاک کردن اطلاعات کاربر
        if call.message.chat.id in user_data:
            user_data.pop(call.message.chat.id)

    except apihelper.ApiTelegramException as e:
        logger.error(f"❌ Telegram API Error: {e}")
        bot.send_message(call.message.chat.id, "⛔ مشکلی در ارتباط با Telegram API پیش آمد.")
    except Exception as e:
        handle_error(e, call.message)

# تابع عمومی مدیریت خطا
def handle_error(exception, message=None):
    logger.error(f"⚠️ خطا رخ داد: {exception}")
    if message:
        try:
            bot.send_message(message.chat.id, "⛔ مشکلی پیش آمده است. لطفاً دوباره تلاش کنید.")
        except Exception as e:
            logger.error(f"❌ خطای اضافی در ارسال پیام خطا: {e}")

# ساخت منوی اصلی
def main_menu(chat_id):
    try:
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("📚 کتاب"),
            KeyboardButton("👨‍🏫 اساتید"),
            KeyboardButton("❓ سوالات متداول"),
            KeyboardButton("🎮 بازی"),
            KeyboardButton("📞 پشتیبانی")
        )
        bot.send_message(chat_id, "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=markup)
    except Exception as e:
        handle_error(e)

# مدیریت گزینه‌های منوی اصلی
@bot.message_handler(commands=['start', 'help'])
def start(message):
    try:
        if message.text == '/start':
            main_menu(message.chat.id)
        elif message.text == '/help':
            help_text = """
            🤖 راهنمای بات:
            /start - شروع کار با بات
            /help - نمایش راهنما
            /courses - کتاب
            /professors - لیست اساتید
            /game - شروع یک بازی ساده
            /support - ارتباط با پشتیبانی
            """
            bot.send_message(message.chat.id, help_text)
    except Exception as e:
        handle_error(e, message)

# مدیریت پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    try:
        if message.text == "📚 کتاب":
            bot.send_message(message.chat.id, "شما گزینه 'کتاب' را انتخاب کردید.")
        elif message.text == "👨‍🏫 اساتید":
            bot.send_message(message.chat.id, "شما گزینه 'اساتید' را انتخاب کردید.")
            start_ask_about_professors(message)
        elif message.text == "❓ سوالات متداول":
            bot.send_message(message.chat.id, "شما گزینه 'سوالات متداول' را انتخاب کردید.")
        elif message.text == "🎮 بازی":
            start_game(message)
        elif message.text == "📞 پشتیبانی":
            start_support(message)
    except Exception as e:
        handle_error(e, message)

# شروع بازی
def start_game(message):
    try:
        bot.send_message(message.chat.id, "به بازی خوش آمدید! عددی بین 1 تا 10 حدس بزنید.")
        bot.register_next_step_handler(message, guess_number)
    except Exception as e:
        handle_error(e, message)

def guess_number(message):
    try:
        if message.text == "5":
            bot.send_message(message.chat.id, "آفرین! درست حدس زدید.")
        else:
            bot.send_message(message.chat.id, "متاسفانه اشتباه حدس زدید. دوباره تلاش کنید.")
    except Exception as e:
        handle_error(e, message)

# شروع پشتیبانی
def start_support(message):
    try:
        bot.send_message(message.chat.id, "برای ارتباط با پشتیبانی، پیام خود را ارسال کنید.")
        bot.register_next_step_handler(message, forward_to_support)
    except Exception as e:
        handle_error(e, message)

def forward_to_support(message):
    try:
        bot.send_message(ADMIN_CHAT_ID, f"پیام از کاربر {message.chat.id}:\n{message.text}")
        bot.send_message(message.chat.id, "پیام شما به پشتیبانی ارسال شد.")
    except Exception as e:
        handle_error(e, message)

# مدیریت دکمه‌های اینلاین
@bot.callback_query_handler(func=lambda call: True)
def handle_callback_query(call):
    try:
        if call.data == "confirm":
            bot.send_message(call.message.chat.id, "شما گزینه 'تایید' را انتخاب کردید.")
        elif call.data == "cancel":
            bot.send_message(call.message.chat.id, "شما گزینه 'لغو' را انتخاب کردید.")
    except Exception as e:
        handle_error(e, call.message)

# اجرای بات
def run_bot():
    logger.info("🤖 Bot is running...")
    while True:  # حلقه برای اجرای مجدد بات در صورت خطا
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as e:
            logger.error(f"❌ Bot stopped due to an error: {e}")
            time.sleep(5)  # منتظر بمانید و دوباره تلاش کنید

if __name__ == "__main__":
    run_bot()