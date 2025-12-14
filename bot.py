import telegram
from telegram.ext import ApplicationBuilder
from telegram import KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, filters
from telegram.ext import CallbackQueryHandler
from telegram.ext import ConversationHandler
import logging
import json
import os
import datetime
import time
import tempfile
import shutil
import pandas as pd
import io
import re
import random
import asyncio

# ----------------- ✅ توابع سازگاری برای اسکیپ کردن کاراکترها -----------------

def escape_html(text):
    """کاراکترهای خاص را برای استفاده در حالت parse_mode="HTML" اسکیپ می‌کند."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text

def escape_markdown(text):
    """کاراکترهای خاص را برای استفاده در حالت parse_mode="Markdown" اسکیپ می‌کند."""
    if text is None:
        return ""
    text = str(text)
    chars_to_escape = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

    escaped_text = ""
    for char in text:
        if char in chars_to_escape:
            escaped_text += '\\' + char
        else:
            escaped_text += char
    return escaped_text

# -----------------------------------------------------------------------------


# --- تنظیمات اولیه ---
TOKEN_FILE = "token.txt"
TOKEN = None

if os.path.exists(TOKEN_FILE):
    try:
        with open(TOKEN_FILE, "r") as f:
            TOKEN = f.read().strip()
    except Exception as e:
        logging.error(f"Failed to read token file: {e}")

if not TOKEN:
    # ⚠️ حتماً توکن ربات خود را در فایل token.txt قرار دهید یا آن را اینجا مستقیم تعریف کنید
    raise ValueError(f"Bot token not found. Please ensure your token is set in '{TOKEN_FILE}' file.")


ADMIN_HANDLES = [
    "YOUR_HANDLE", # 👈 این را با یوزرنیم خود جایگزین کنید
    "amirhoseyn_karim",
    "mahdi1386212"
    "MrMohamad_taha"
]
SUPPORT_ID = 8425368868 # 👈 آیدی عددی پشتیبانی
ADMIN_ID = 8425368868 # 👈 آیدی عددی ادمین اصلی
ORDER_CHANNEL = "@stars12222" # 👈 کانال ثبت سفارشات

# --- ثابت‌ها برای UX (استیکرها) ---
STICKER_WELCOME = "CAACAgIAAxkBAAITxmVm043_1gABd9g0t0xYk2o_l3I35AACEwADOzJ5S-zW9Vf-9gABMwQ"
STICKER_SUCCESS = "CAACAgIAAxkBAAIT2mXW_f0Y1c0dD7M1gR1jYx9Y77-2AAI7AgACLw_QSr-qM90Y1X0zBA"


# --- ثابت‌ها برای فروشگاه پیشرفته ---
INPUT_TYPE_STARLINK_POST = "STARLINK_POST"
INPUT_TYPE_GIFT_ACCOUNT_ID = "GIFT_ACCOUNT_ID"
INPUT_TYPE_BANK_CARD = "BANK_CARD"
INPUT_TYPE_GIFT_CHANNEL_ID = "GIFT_CHANNEL_ID"
INPUT_TYPE_NONE = "NONE"

STORE_INPUT_TYPES = {
    INPUT_TYPE_STARLINK_POST: {"text": "لینک پست استارلینک", "regex": r"^https?:\/\/(t\.me|telegram\.me)\/.+\/\d+$"},
    # ✅ FIX: رگولار اکسپرشن فقط باید 16 رقم را چک کند، تمیزکاری ورودی قبل از آن انجام می‌شود.
    INPUT_TYPE_BANK_CARD: {"text": "شماره کارت بانکی (۱۶ رقمی)", "regex": r"^\d{16}$"},
    INPUT_TYPE_GIFT_ACCOUNT_ID: {"text": "آیدی عددی اکانت", "regex": r"^\d{6,15}$"},
    INPUT_TYPE_GIFT_CHANNEL_ID: {"text": "آیدی کانال (با @)", "regex": r"^@[a-zA-Z0-9_]{5,32}$"},
    INPUT_TYPE_NONE: {"text": "هیچکدام (ورودی نمی‌خواهد)", "regex": None}
}


NAVIGATION_BUTTONS = [
    "🔙 برگشت به ربات", "🆔 تنظیم کانال", "⚙️ زیرمجموعه گیری", "🏆 برترین اعضا",
    "📈 آمار ربات", "📨 ارسال پیام", "📊 گزارش اکسل کاربران", "📸 تنظیم بنر",
    "📝 تنظیم متن زیرمجموعه", "✍️ تنظیم متن خوش آمدگویی", "پنل مدیریت",
    "⚙️ تنظیم سیستم زیرمجموعه گیری", "💎 تنظیم امتیاز کاربر", "🎁 مدیریت محصولات",
    "➕ افزودن محصول جدید", "❌ حذف محصول", "تغییر امتیاز برای هر عضو جدید",
    "تغییر امتیاز مورد نیاز برای ۱ استارز"
]
ADMIN_PANEL_BUTTONS = [
    "🆔 تنظیم کانال", "⚙️ زیرمجموعه گیری", "🏆 برترین اعضا", "📈 آمار ربات",
    "📨 ارسال پیام", "📊 گزارش اکسل کاربران", "📸 تنظیم بنر",
    "📝 تنظیم متن زیرمجموعه", "✍️ تنظیم متن خوش آمدگویی",
    "⚙️ تنظیم سیستم زیرمجموعه گیری", "💎 تنظیم امتیاز کاربر",
    "🎁 مدیریت محصولات"
]


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

DATA_FILE = "bot_data.json"
ADMIN_CONFIG_FILE = "admin_config.json"

# وضعیت های مکالمات (ConversationHandler)
SUPPORT_MESSAGE, BROADCAST_MESSAGE_RECEIVE = range(2) # ✅ FIX: Rename BROADCAST_STATE
CHANNEL_ACTION_SELECT, CHANNEL_ADD_INPUT, CHANNEL_DELETE_SELECT, CHANNEL_SET_TARGET = range(2, 6)
SET_BANNER_STATE, SET_REFERRAL_TEXT_STATE, SET_WELCOME_TEXT_STATE = range(6, 9)
REFERRAL_SYSTEM_MENU, SET_POINTS_PER_JOIN, SET_POINTS_PER_STAR = range(9, 12)
SET_POINTS_STATE = 12
PRODUCT_MENU, PRODUCT_ADD_NAME, PRODUCT_ADD_COST, PRODUCT_ADD_INPUT_TYPE, PRODUCT_DELETE_SELECT_FINAL = range(13, 18)
ORDER_INPUT = 18
BROADCAST_CONFIRM_STATE = 100 # ✅ FIX: New state for confirmation

# --- متغیرهای بازی گروهی ---
group_games = {}
GAME_DURATION_SECONDS = 30


# --- توابع مدیریت داده‌ها ---

def load_data():
    user_points, user_join_dates, user_last_active, support_message_last_time = {}, {}, {}, {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return user_points, user_join_dates, user_last_active, support_message_last_time
            try:
                data = json.loads(content)
                user_points = {k: v for k, v in data.get("user_points", {}).items() if k.isdigit()}
                user_join_dates = data.get("user_join_dates", {})
                user_last_active = data.get("user_last_active", {})
                support_message_last_time = data.get("support_message_last_time", {})
            except Exception as e:
                logging.error(f"Failed to load data file: {e}")
    return user_points, user_join_dates, user_last_active, support_message_last_time

def save_data():
    """ذخیره امن داده‌های کاربر در فایل."""
    try:
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8') as tf:
            json.dump({
                "user_points": user_points,
                "user_join_dates": user_join_dates,
                "user_last_active": user_last_active,
                "support_message_last_time": support_message_last_time,
            }, tf, ensure_ascii=False, indent=2)
            tempname = tf.name
        shutil.move(tempname, DATA_FILE)
    except Exception as e:
        # اگر خطا به دلیل دسترسی فایل بود، باید مجوزهای فایل/پوشه را چک کنید
        logging.warning(f"Failed to save data file: {e}")

# بارگذاری داده‌ها
user_points, user_join_dates, user_last_active, support_message_last_time = load_data()

def load_admin_config():
    """بارگذاری تنظیمات ادمین و اعمال اصلاحات ساختاری (Migration) برای کانال‌ها."""
    if os.path.exists(ADMIN_CONFIG_FILE):
        with open(ADMIN_CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                admin_config = json.load(f)
            except Exception:
                admin_config = {}
    else:
        admin_config = {}

    # تنظیمات پیش‌فرض
    if "texts" not in admin_config:
        admin_config["texts"] = {"welcome": "سلام! به ربات استارز خوش آمدید. 🎉"}

    if "referral_message" not in admin_config.get("texts", {}):
        admin_config["texts"]["referral_message"] = ("ربات رسمی استارز رایگان ساخته شد😍❤️\n\nهدیه بگیر، ستاره جمع کن، سود کن!")

    if "banner" not in admin_config:
        admin_config["banner"] = "telegram-stars.jpg"

    # --- FIX: اطمینان از ساختار دیکشنری برای کانال‌ها ---
    channels_list = admin_config.get("channels", [])
    new_channels = []

    for item in channels_list:
        if isinstance(item, dict) and "username" in item:
            new_channels.append({
                "username": item.get("username", "-"),
                "url": item.get("url", "-"),
                "is_active": item.get("is_active", item.get("username") != "-"),
                "target_count": item.get("target_count", 0),
                "current_joins": item.get("current_joins", 0)
            })
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            username, url = item[0], item[1]
            new_channels.append({
                "username": username,
                "url": url,
                "is_active": username != "-",
                "target_count": 0,
                "current_joins": 0
            })

    # پر کردن اسلات‌های خالی تا ۱۰ اسلات
    while len(new_channels) < 10:
        new_channels.append({
            "username": "-", "url": "-", "is_active": False, "target_count": 0, "current_joins": 0
        })

    admin_config["channels"] = new_channels
    # ----------------- پایان FIX -----------------


    if "products" not in admin_config:
        admin_config["products"] = []

    # Migration for old products to include input_type
    for product in admin_config["products"]:
        if "input_type" not in product:
            product['input_type'] = INPUT_TYPE_NONE


    if "referral_system" not in admin_config:
        admin_config["referral_system"] = {
            "points_per_join": 1,
            "points_per_star": 2
        }

    return admin_config

def save_admin_config():
    """ذخیره تنظیمات ادمین در فایل."""
    try:
        with open(ADMIN_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(admin_config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save admin config: {e}")

admin_config = load_admin_config()
save_admin_config() # اطمینان از ذخیره شدن ساختار جدید

def is_admin(user):
    """بررسی ادمین بودن کاربر بر اساس یوزرنیم."""
    if user.username:
        return user.username.lower() in [h.lower() for h in ADMIN_HANDLES]
    return False

def get_referral_points_per_join():
    """دریافت امتیاز هر جوین جدید."""
    return admin_config.get("referral_system", {}).get("points_per_join", 1)

def get_star_cost_points():
    """دریافت هزینه ۱ استارز به امتیاز."""
    return admin_config.get("referral_system", {}).get("points_per_star", 2)

async def update_user_activity(user_id):
    """بروزرسانی آخرین فعالیت کاربر."""
    now = datetime.datetime.now().strftime("%Y-%m-%d")
    user_id_str = str(user_id)
    if user_id_str not in user_join_dates:
        user_join_dates[user_id_str] = now
    user_last_active[user_id_str] = now
    save_data()

# --- توابع ناوبری کمکی ---

async def back_to_main_menu(update, context):
    """تابع برگرداندن کاربر به منوی اصلی. (اصلاح شده برای پایداری دکمه برگشت)"""
    user = update.effective_user

    keyboard = [
        [KeyboardButton("فروشگاه🛍️"), KeyboardButton("حساب کاربری👤")],
        [KeyboardButton("لینک زیرمجموعه گیری👥"), KeyboardButton("پشتیبانی📞")]
    ]
    if is_admin(user):
        keyboard.append([KeyboardButton("پنل مدیریت")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text_raw = admin_config.get("texts", {}).get("welcome", "👋 به ربات استارز خوش آمدید.")
    welcome_text = escape_html(welcome_text_raw)

    chat_id = user.id

    try:
        # ارسال استیکر فقط در صورت جدید بودن چت
        if not update.callback_query and update.message and update.message.text not in NAVIGATION_BUTTONS:
            await context.bot.send_sticker(chat_id=chat_id, sticker=STICKER_WELCOME)
    except Exception:
        logging.warning("Failed to send welcome sticker.")

    try:
        # ✅ FIX: هنگام برگشت از دکمه شیشه‌ای (callback_query)، همیشه پیام جدید ارسال کن تا باگ ویرایش پیام عکس حل شود.
        if update.callback_query:
            await context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        elif update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Failed to send welcome message in back_to_main_menu: {e}")

    return ConversationHandler.END

async def back_to_admin_menu(update, context):
    """تابع برگرداندن کاربر به پنل مدیریت."""
    # این تابع توسط admin_fallback_handler فراخوانی می‌شود
    if update.callback_query:
        update.message = update.callback_query.message
    return await admin_panel_button(update, context)

async def admin_fallback_handler(update, context):
    """بازگشت به منوی ادمین در صورت کلیک روی دکمه 'پنل مدیریت' در حین مکالمه."""
    return await back_to_admin_menu(update, context)

async def admin_fallback_handler_callback(update, context):
    """هندلر برای دکمه‌های شیشه‌ای برگشت به منوی ادمین در حین مکالمه."""
    query = update.callback_query
    await query.answer("بازگشت به پنل مدیریت...")
    # تنظیم update برای استفاده در back_to_admin_menu
    update.message = query.message
    update.callback_query = query
    return await back_to_admin_menu(update, context)

# -----------------------------------------------------------------------------
# --- توابع جوین اجباری (Jouin Ejbari) ---

async def check_membership(bot, user_id):
    """
    چک می‌کند که آیا کاربر در تمامی کانال‌های اجباری عضو است یا خیر.
    (ربات باید ادمین کانال باشد)
    """
    channels_config = admin_config.get("channels", [])
    required_channels = [
        (c['username'], c['url'])
        for c in channels_config
        if c['username'] != "-" and c.get('is_active', False)
    ]

    not_joined_channels = []

    for username, url in required_channels:
        try:
            chat_member = await bot.get_chat_member(username, user_id)
            status = chat_member.status
            if status not in ['member', 'creator', 'administrator', 'restricted']:
                not_joined_channels.append((username, url))
        except telegram.error.BadRequest as e:
            if "User not found" in str(e):
                 not_joined_channels.append((username, url))
            elif "Chat not found" in str(e) or "bot is not a member" in str(e):
                 logging.error(f"Bot is not a member of required channel {username} or channel not found. Check bot admin status in channel.")
                 not_joined_channels.append((username, url))
            else:
                 not_joined_channels.append((username, url))
        except Exception:
            not_joined_channels.append((username, url))

    return not_joined_channels

# 🛑 FIX: اعمال اصلاحیه اصلی برای رفع خطای Button_url_invalid
async def join_guard(handler_func, update, context):
    """گارد محافظ برای چک کردن جوین اجباری قبل از اجرای هر عملیات اصلی."""
    user = update.effective_user
    user_id = user.id

    not_joined = await check_membership(context.bot, user_id)

    if not not_joined:
        return await handler_func(update, context)
    else:
        inline_keyboard = []
        for username, url in not_joined:
            # ✅ FIX: برای رفع خطای Button_url_invalid، همیشه از لینک استاندارد t.me
            # بر اساس یوزرنیم کانال استفاده می‌کنیم، حتی اگر URL سفارشی در تنظیمات وجود داشته باشد.
            final_url = f"https://t.me/{username.lstrip('@')}"

            inline_keyboard.append([InlineKeyboardButton(f"✅ عضویت در {username}", url=final_url)])

        inline_keyboard.append([InlineKeyboardButton("تایید عضویت و ورود", callback_data="check_join_re_check")])
        reply_markup = InlineKeyboardMarkup(inline_keyboard)

        msg = ("⚠️ <b>برای استفاده از ربات، لطفاً در کانال‌های زیر عضو شوید:</b>\n"
               "بعد از عضویت، روی دکمه 'تایید عضویت و ورود' کلیک کنید.")

        try:
            if update.callback_query:
                await update.callback_query.answer()
                await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="HTML")
            elif update.message:
                await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            # Fallback: send a new message if edit fails (e.g., trying to edit a non-text message)
            await context.bot.send_message(chat_id=user_id, text=msg, reply_markup=reply_markup, parse_mode="HTML")

        return None

async def handle_join_re_check(update, context):
    """هندلر برای چک کردن مجدد عضویت پس از کلیک کاربر."""
    query = update.callback_query
    await query.answer("در حال بررسی مجدد عضویت...")

    return await join_guard(check_and_award_referral, update, context)

async def check_and_award_referral(update, context):
    """اهدای امتیاز زیرمجموعه‌گیری معلق و ادامه به منوی اصلی."""
    user = update.effective_user
    user_id = user.id
    user_id_str = str(user.id)

    referrer_id = context.user_data.pop('pending_referrer_id', None)

    # 1. Award Referral Points
    if referrer_id:
        reward = get_referral_points_per_join()

        user_points[referrer_id] = user_points.get(referrer_id, 0) + reward
        save_data() # ذخیره داده پس از اعطای امتیاز

        try:
            await context.bot.send_message(
                chat_id=int(referrer_id),
                text=(
                    f"یک نفر با لینک اختصاصی شما وارد ربات شد و در کانال‌های اجباری عضو شد! 🎉\n"
                    f"امتیاز دریافتی: {reward}"
                )
            )
        except Exception as e:
            logging.warning(f"Could not notify referrer {referrer_id}: {e}")

    # 2. Smart Mandatory Join Count and Removal
    channels_config = admin_config.get("channels", [])
    config_changed = False

    for c in channels_config:
        if c.get('is_active', False) and c.get('target_count', 0) > 0:
            # Check if this user is a new join
            if user_id_str not in user_join_dates: # فقط برای کاربرانی که تازه ثبت نام کرده‌اند
                 c['current_joins'] += 1
                 config_changed = True

            if c['current_joins'] >= c['target_count']:
                c['is_active'] = False
                config_changed = True

                try:
                    admin_msg = (
                        f"🎉 <b>جوین اجباری کانال خودکار برداشته شد!</b> 🎉\n"
                        f"کانال: <b>{escape_html(c['username'])}</b>\n"
                        f"هدف <b>{c['target_count']}</b> نفر محقق شد."
                    )
                    await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="HTML")
                except Exception:
                    pass

    if config_changed:
        save_admin_config()

    try:
         await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ عضویت شما در کانال‌ها تایید شد. می‌توانید از ربات استفاده کنید."
            )
        )
    except Exception:
        pass

    return await start_continue(update, context)


# --- تابع نمایش منوی اصلی ---
async def start_continue(update, context):
    """نمایش منوی اصلی ربات و بستن ConversationHandler."""
    user = update.effective_user

    keyboard = [
        [KeyboardButton("فروشگاه🛍️"), KeyboardButton("حساب کاربری👤")],
        [KeyboardButton("لینک زیرمجموعه گیری👥"), KeyboardButton("پشتیبانی📞")]
    ]
    if is_admin(user):
        keyboard.append([KeyboardButton("پنل مدیریت")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_text_raw = admin_config.get("texts", {}).get("welcome", "👋 به ربات استارز خوش آمدید.")
    welcome_text = escape_html(welcome_text_raw)

    chat_id = user.id

    try:
        # ✅ FIX: هنگام برگشت از دکمه شیشه‌ای (callback_query)، همیشه پیام جدید ارسال کن تا باگ ویرایش پیام عکس حل شود.
        if update.callback_query:
            await context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup, parse_mode="HTML")
        elif update.message:
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

    except Exception as e:
        logging.error(f"Failed to send welcome message in start_continue: {e}")

    return ConversationHandler.END

# --- Command Handlers ---

async def start(update, context):
    """نقطه شروع ربات: بررسی رفرال، ثبت کاربر و گارد جوین اجباری."""
    user = update.effective_user
    user_id = user.id
    user_id_str = str(user.id)

    is_new_user = user_id_str not in user_points

    # 1. User Initialization and Referrer Storage
    if is_new_user:
        user_points[user_id_str] = 0

        if context.args:
            referrer_id = context.args[0]
            if user_id_str != referrer_id and referrer_id.isdigit():
                context.user_data['pending_referrer_id'] = referrer_id
                logging.info(f"User {user_id} started with pending referrer {referrer_id}")

    # 2. ثبت تاریخ عضویت و فعالیت
    await update_user_activity(user_id)

    # 3. بررسی عضویت اجباری
    return await join_guard(check_and_award_referral, update, context)

# --- Guaded Handlers (برای محافظت از دکمه‌های اصلی) ---

async def safe_user_profile(update, context):
    return await join_guard(user_profile, update, context)

async def safe_referral_link(update, context):
    return await join_guard(referral_link, update, context)

async def safe_support_menu(update, context):
    return await join_guard(start_support_message, update, context)

async def safe_admin_panel_button(update, context):
    return await join_guard(admin_panel_button, update, context)

async def safe_store_menu(update, context):
    return await join_guard(store_menu, update, context)


# --- Core Logic Handlers (User) ---

async def user_profile(update, context):
    """نمایش پروفایل کاربر."""
    await update_user_activity(update.effective_user.id)
    user = update.effective_user

    name = escape_html(user.full_name or "-")
    user_id = user.id
    username = f"@{user.username}" if user.username else "-"
    points = user_points.get(str(user_id), 0)

    join_date = escape_html(user_join_dates.get(str(user_id), "-"))
    last_active = escape_html(user_last_active.get(str(user_id), "-"))

    msg = (
        "👤 <b>اطلاعات حساب کاربری</b>⚡️\n\n"
        f"☆ نام: {name} 💎\n"
        f"☆ ایدی عددی: <code>{user_id}</code> 🧸\n"
        f"☆ یوزرنیم: {username} 🔗\n"
        f"☆ امتیاز: <b>{points}</b> 🎊\n"
        f"☆ تاریخ عضویت: {join_date}\n"
        f"☆ آخرین فعالیت: {last_active}"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def referral_link(update, context):
    """نمایش لینک زیرمجموعه‌گیری و بنر."""
    await update_user_activity(update.effective_user.id)
    user_id = update.effective_user.id
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start={user_id}"

    points_per_join = get_referral_points_per_join()
    points_per_star = get_star_cost_points()

    # FIX: Ensure calculation handles division by zero safely
    required_joins = points_per_star / points_per_join if points_per_join > 0 else 0
    required_joins_display = str(required_joins)

    raw_base_msg = admin_config.get("texts", {}).get("referral_message",
        "ربات رسمی استارز رایگان ساخته شد! هدیه بگیر، ستاره جمع کن، سود کن!")

    base_msg = escape_markdown(raw_base_msg)

    dynamic_part = (
        f"\n\nبا دعوت هر عضو جدید **{points_per_join}** امتیاز می‌گیرید.\n"
        f"برای دریافت ۱ استارز، به **{points_per_star}** امتیاز نیاز دارید.\n"
        f"**نتیجه:** برای دریافت ۱ استارز، نیاز به دعوت **{required_joins_display}** نفر دارید. ✨\n\n"
        f"لینک اختصاصی شما برای دعوت دوستان:\n`{link}`"
    )

    msg = base_msg + dynamic_part

    banner_path = admin_config.get("banner", "telegram-stars.jpg")
    try:
        with open(banner_path, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=msg, parse_mode="Markdown")
    except FileNotFoundError:
        await update.message.reply_text(msg, parse_mode="Markdown")

# --- توابع مدیریت فروشگاه ---

def get_all_store_items(points_per_star):
    """ترکیب محصول برداشت استارز با محصولات تعریف شده."""
    products = admin_config.get("products", [])
    star_withdraw_item = {
        "name": "برداشت ۱ استارز ⭐",
        "cost": points_per_star,
        "is_star_withdraw": True,
        "input_type": INPUT_TYPE_STARLINK_POST
    }
    for p in products:
        if "input_type" not in p:
            p['input_type'] = INPUT_TYPE_NONE

    return [star_withdraw_item] + products

async def display_product(update, context, index, is_new_message=False):
    """نمایش جزئیات یک محصول با دکمه‌های ناوبری."""
    user = update.effective_user
    user_id = user.id
    user_points_current = user_points.get(str(user_id), 0)
    points_per_star = get_star_cost_points()
    all_items = get_all_store_items(points_per_star)
    total_items = len(all_items)

    if not all_items:
        msg = "⚠️ هیچ محصولی در فروشگاه تعریف نشده است."
        if update.callback_query:
             await update.callback_query.message.edit_text(msg, parse_mode="HTML")
        else:
             await update.message.reply_text(msg, parse_mode="HTML")
        return

    index = index % total_items

    current_item = all_items[index]
    cost = current_item['cost']
    product_name = escape_html(current_item['name'])
    is_affordable = user_points_current >= cost
    action_text = "✨ برداشت استارز" if current_item.get('is_star_withdraw') else "🛒 خرید محصول"

    input_type = current_item.get('input_type', INPUT_TYPE_NONE)
    required_input_text = STORE_INPUT_TYPES.get(input_type, {}).get('text', 'بدون نیاز به ورودی')

    context.user_data['current_store_index'] = index

    msg = (
        f"<b>🛍️ فروشگاه استارز - آیتم {index+1} از {total_items}</b>\n\n"
        f"<b>⭐️ امتیاز شما:</b> <b>{user_points_current}</b>\n"
        "--- <b>جزئیات آیتم</b> ---\n"
        f"<b>💎 آیتم:</b> <b>{product_name}</b>\n"
        f"<b>💰 هزینه:</b> <b>{cost}</b> امتیاز\n"
        f"<b>🔥 نوع عملیات:</b> {action_text}\n"
        f"<b>🔗 ورودی مورد نیاز:</b> <i>{required_input_text}</i>\n"
        "--------------------"
    )

    if is_affordable:
        buy_button_text = f"✅ اقدام به {action_text.split()[1]}"
        buy_callback_data = f"handle_purchase:{index}"
    else:
        required_more = cost - user_points_current
        buy_button_text = f"❌ امتیاز کافی نیست (نیاز به {required_more} امتیاز دیگر)"
        buy_callback_data = "no_action"

    main_button_row = [InlineKeyboardButton(buy_button_text, callback_data=buy_callback_data)]

    prev_index = (index - 1 + total_items) % total_items
    next_index = (index + 1) % total_items

    prev_label = f"❮❮ قبلی ({prev_index+1}/{total_items})"
    next_label = f"بعدی ({next_index+1}/{total_items}) ❯❯"

    nav_row = [
        InlineKeyboardButton(prev_label, callback_data=f"nav_product:{prev_index}"),
        InlineKeyboardButton(next_label, callback_data=f"nav_product:{next_index}")
    ]

    back_row = [InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data="back_to_main_menu")]

    inline_keyboard = [main_button_row, nav_row, back_row]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    # تعیین منبع پیام (برای reply_photo یا edit_caption/text)
    message_source = update.callback_query.message if update.callback_query else update.message

    if update.callback_query and not is_new_message:
        try:
            # سعی در ویرایش پیام قبلی
            if message_source.photo:
                 await update.callback_query.message.edit_caption(caption=msg, reply_markup=reply_markup, parse_mode="HTML")
            else:
                 await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="HTML")
            return
        except Exception as e:
            # اگر ویرایش موفقیت‌آمیز نبود (مثلاً خطای Message is not modified)، فقط Logging
            logging.debug(f"Error editing message in display_product: {e}")
            pass


    # ارسال پیام جدید (فالو بک اصلی یا اولین ورود)
    banner_path = admin_config.get("banner", "telegram-stars.jpg")
    try:
        with open(banner_path, 'rb') as photo:
            await message_source.reply_photo(
                photo=photo,
                caption=msg,
                reply_markup=reply_markup,
                parse_mode="HTML"
            )
    except Exception:
        # اگر عکس پیدا نشد یا ارسال عکس موفق نبود
        await message_source.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")


async def store_menu(update, context):
    """نقطه ورود اولیه به منوی فروشگاه."""
    await update_user_activity(update.effective_user.id)
    current_index = context.user_data.get('current_store_index', 0)
    await display_product(update, context, current_index, is_new_message=True)

async def handle_product_navigation(update, context):
    """هندلر دکمه‌های قبلی/بعدی."""
    query = update.callback_query
    await query.answer()

    try:
        new_index = int(query.data.split(":")[1])
        await display_product(update, context, new_index)
    except Exception:
        await query.message.reply_text("❌ خطایی در ناوبری رخ داد.")

async def back_to_main_menu_callback(update, context):
    """هندلر بازگشت از دکمه شیشه‌ای (فروشگاه) به منوی اصلی."""
    query = update.callback_query
    await query.answer("در حال بازگشت به منوی اصلی...")

    # تنظیم update برای استفاده در back_to_main_menu (مهم برای FIX دکمه برگشت)
    update.message = query.message
    update.callback_query = query

    return await back_to_main_menu(update, context)

async def handle_purchase_callback(update, context):
    """هندلر نهایی کردن خرید محصول یا ورود به مکالمه برداشت استارز."""
    user = update.effective_user
    await update_user_activity(user.id)
    query = update.callback_query

    if query.data == "no_action":
        await query.answer("❌ امتیاز شما برای این آیتم کافی نیست.")
        return ConversationHandler.END

    await query.answer("در حال پردازش...")

    user_id = user.id
    user_id_str = str(user.id)

    points_per_star = get_star_cost_points()
    all_items = get_all_store_items(points_per_star)

    try:
        idx = int(query.data.split(":")[1])
        item = all_items[idx]
        cost = item['cost']
        product_name = escape_html(item['name'])
        is_star_withdraw = item.get('is_star_withdraw', False)
        required_input_type = item.get('input_type', INPUT_TYPE_NONE)
    except (IndexError, ValueError, KeyError):
        await query.message.reply_text("❌ آیتم نامعتبر یا خطای سیستمی رخ داده است.")
        return ConversationHandler.END

    user_points_current = user_points.get(user_id_str, 0)

    if user_points_current < cost:
        await query.message.reply_text("❌ امتیاز شما برای خرید/برداشت این آیتم کافی نیست.")
        return ConversationHandler.END

    if required_input_type != INPUT_TYPE_NONE or is_star_withdraw:
        # ذخیره اطلاعات سفارش برای مرحله بعد
        context.user_data['order_data'] = {
            'product_name': product_name,
            'cost': cost,
            'input_type': required_input_type,
            'product_index': idx,
        }

        input_text = STORE_INPUT_TYPES.get(required_input_type, {}).get('text', 'ورودی مورد نیاز')

        msg = (
            f"✅ **آماده برای تکمیل سفارش:** <b>{product_name}</b>\n\n"
            f"لطفاً <b>{input_text}</b> مورد نیاز را برای ثبت سفارش ارسال کنید.\n"
            "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید."
        )
        await query.message.reply_text(msg, parse_mode="HTML")
        return ORDER_INPUT

    else:
        # محصول بدون نیاز به ورودی (خرید فوری)
        user_points[user_id_str] -= cost
        save_data()

        # ثبت سفارش در کانال ادمین
        order_msg = (
            "⭐ <b>سفارش جدید (خرید فوری)</b>\n\n"
            f"👤 کاربر: <a href='tg://user?id={user_id}'>{escape_html(user.full_name)}</a> (<code>{user_id}</code>)\n"
            f"🎁 محصول: <b>{product_name}</b>\n"
            f"💰 هزینه: <b>{cost}</b> امتیاز\n"
            f"🔗 ورودی: <i>نیاز ندارد</i>\n"
            f"⏳ زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
             await context.bot.send_message(chat_id=ORDER_CHANNEL, text=order_msg, parse_mode="HTML")
        except Exception:
             logging.error(f"Failed to send order to {ORDER_CHANNEL}")

        try:
            await context.bot.send_sticker(chat_id=user_id, sticker=STICKER_SUCCESS)
        except Exception:
            logging.warning("Failed to send success sticker. Check STICKER_SUCCESS ID.")

        await query.message.reply_text(
            f"✅ خرید محصول <b>{product_name}</b> با موفقیت انجام شد. <b>{cost}</b> امتیاز از شما کسر گردید. ✅\n"
            f"امتیاز باقی مانده شما: <b>{user_points[user_id_str]}</b>",
            parse_mode="HTML"
        )
        # بازگشت به نمایش محصول
        await display_product(update, context, idx, is_new_message=False)
        return ConversationHandler.END

async def receive_order_input(update, context):
    """✅ FIX: دریافت ورودی نهایی کاربر، تمیز کردن شماره کارت و ثبت سفارش."""
    user = update.effective_user
    input_raw = update.message.text.strip()
    user_id_str = str(user.id)
    order_data = context.user_data.pop('order_data', None)

    if not order_data:
        await update.message.reply_text("❌ خطایی در فرآیند ثبت سفارش رخ داد. لطفا مجدداً از منوی فروشگاه اقدام کنید.")
        return ConversationHandler.END

    cost = order_data['cost']
    product_name = order_data['product_name']
    input_type = order_data['input_type']
    product_index = order_data['product_index']

    # ✅ FIX: هندل کردن ناوبری با دکمه‌ها در حین مکالمه
    if input_raw in NAVIGATION_BUTTONS:
        context.user_data['order_data'] = order_data # برگرداندن داده برای جلوگیری از خطا
        return await back_to_main_menu(update, context)


    # 1. Cleaning Input (Crucial for Bank Card)
    input_value_cleaned = input_raw
    if input_type == INPUT_TYPE_BANK_CARD:
         # حذف تمام فواصل و خط تیره برای اعتبارسنجی
         input_value_cleaned = re.sub(r'[\s\-]+', '', input_raw)

    input_value = input_value_cleaned # استفاده از مقدار تمیز شده برای اعتبارسنجی و ذخیره‌سازی

    # 2. Validation
    validation_regex = STORE_INPUT_TYPES.get(input_type, {}).get('regex')
    input_text = STORE_INPUT_TYPES.get(input_type, {}).get('text', 'ورودی مورد نیاز')

    if validation_regex:
        # اعتبارسنجی روی مقدار تمیز شده انجام می‌شود
        if not re.match(validation_regex, input_value):
            error_msg = f"❌ **{input_text}** ارسالی شما معتبر نیست. لطفا ورودی را با فرمت صحیح ارسال کنید."
            if input_type == INPUT_TYPE_STARLINK_POST:
                error_msg += "\n\n**فرمت صحیح لینک پست تلگرام:** لینک باید شبیه `https://t.me/ChannelUsername/123` یا `https://telegram.me/ChannelUsername/123` باشد."
            elif input_type == INPUT_TYPE_BANK_CARD:
                error_msg += "\n\n**فرمت صحیح شماره کارت:** ۱۶ رقم (می‌تواند با فاصله یا خط تیره ارسال شود)."

            await update.message.reply_text(error_msg, parse_mode="Markdown")
            # برگرداندن داده سفارش برای تلاش مجدد
            context.user_data['order_data'] = order_data
            return ORDER_INPUT

    # 3. Point Deduction
    user_points_current = user_points.get(user_id_str, 0)
    if user_points_current < cost:
        await update.message.reply_text("❌ امتیاز شما برای خرید/برداشت این آیتم کافی نیست.")
        return ConversationHandler.END

    user_points[user_id_str] -= cost
    save_data()

    # 4. Order Channel Notification

    # ساخت لینک مستقیم اگر ورودی URL باشد
    if input_type == INPUT_TYPE_STARLINK_POST:
         input_link = f"<a href='{input_value}'>لینک پست</a>"
    else:
         input_link = escape_html(input_value)

    order_msg = (
        "⭐ <b>سفارش جدید (با ورودی)</b>\n\n"
        f"👤 کاربر: <a href='tg://user?id={user.id}'>{escape_html(user.full_name)}</a> (<code>{user.id}</code>)\n"
        f"🎁 محصول: <b>{product_name}</b>\n"
        f"💰 هزینه: <b>{cost}</b> امتیاز\n"
        f"🔗 {input_text}: {input_link}\n"
        f"⏳ زمان: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
         await context.bot.send_message(chat_id=ORDER_CHANNEL, text=order_msg, parse_mode="HTML")
    except Exception:
         logging.error(f"Failed to send order to {ORDER_CHANNEL}")

    # 5. User Notification
    try:
        await context.bot.send_sticker(chat_id=user.id, sticker=STICKER_SUCCESS)
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ سفارش شما برای <b>{product_name}</b> با موفقیت ثبت شد و <b>{cost}</b> امتیاز از شما کسر گردید. ✅\n"
        f"ورودی شما ({input_text}): <code>{escape_html(input_value)}</code>\n"
        "درخواست شما به زودی توسط مدیر بررسی و انجام می‌شود.",
        parse_mode="HTML"
    )

    # بازگشت به منوی فروشگاه
    # چون این هندلر با MessageHandler فعال شده، باید update.message را استفاده کنیم
    await display_product(update, context, product_index, is_new_message=False)
    return ConversationHandler.END


# --- Admin Panel Handlers (Utility) ---

async def admin_panel_button(update, context):
    """نمایش منوی پنل مدیریت."""
    user = update.effective_user
    if not is_admin(user):
        await update.message.reply_text("❌ دسترسی مدیریتی ندارید.")
        return ConversationHandler.END

    keyboard = []
    for i in range(0, len(ADMIN_PANEL_BUTTONS), 2):
        row = [KeyboardButton(ADMIN_PANEL_BUTTONS[i])]
        if i + 1 < len(ADMIN_PANEL_BUTTONS):
            row.append(KeyboardButton(ADMIN_PANEL_BUTTONS[i + 1]))
        keyboard.append(row)
    keyboard.append([KeyboardButton("🔙 برگشت به ربات")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("به پنل مدیریت خوش آمدید، مدیر عزیز. عملیات مورد نظر خود را انتخاب کنید:", reply_markup=reply_markup)
    return ConversationHandler.END

# 🛑 FIX: تابع جدید برای ساخت گزارش اکسل
async def export_users_to_excel(update, context):
    """ساخت فایل اکسل از اطلاعات کاربران و ارسال آن به ادمین."""
    if not is_admin(update.effective_user):
        return

    await update.message.reply_text("⏳ در حال جمع‌آوری داده‌ها و ساخت فایل اکسل...")

    data = []
    # Combine data from different sources
    for user_id_str, points in user_points.items():
        # Try to get user info (optional, but nice to have username/name)
        username = "-"
        full_name = "-"
        try:
            # از get_chat برای گرفتن اطلاعات کاربر استفاده می‌شود
            chat_info = await context.bot.get_chat(int(user_id_str))
            username = f"@{chat_info.username}" if chat_info.username else "-"
            # FIX: Get full name safely
            full_name = chat_info.full_name or chat_info.first_name or "-"
        except Exception:
            # کاربر ممکن است حریم خصوصی داشته باشد یا ربات را بلاک کرده باشد
            pass

        data.append({
            "آیدی عددی": user_id_str,
            "نام کامل": full_name,
            "یوزرنیم": username,
            "امتیاز": points,
            "تاریخ عضویت": user_join_dates.get(user_id_str, "-"),
            "آخرین فعالیت": user_last_active.get(user_id_str, "-"),
        })

    if not data:
        await update.message.reply_text("⚠️ هیچ کاربری در سیستم ثبت نشده است.")
        return

    df = pd.DataFrame(data)

    # استفاده از io.BytesIO برای ساخت فایل اکسل در حافظه
    excel_file = io.BytesIO()
    # نوشتن به اکسل با استفاده از موتور openpyxl
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='User_Data', index=False, encoding='utf-8')
    except Exception as e:
        logging.error(f"Error writing Excel file: {e}")
        await update.message.reply_text("❌ خطایی در ساخت فایل اکسل رخ داد.")
        return

    excel_file.seek(0)

    # ارسال فایل
    filename = f"User_Report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    try:
        await update.message.reply_document(
            document=excel_file,
            filename=filename,
            caption="✅ گزارش کامل کاربران ربات به صورت فایل اکسل."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ خطایی در ارسال فایل اکسل رخ داد: {e}", parse_mode="HTML")


async def bot_stats(update, context):
    """نمایش آمار کلی ربات."""
    if not is_admin(update.effective_user):
        return

    total_users = len(user_points)
    # محاسبه مجموع امتیازات
    total_points = sum(user_points.values())

    # محاسبه کاربران فعال (در ۷ روز اخیر)
    now = datetime.datetime.now()
    active_users_7_days = 0
    seven_days_ago = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")

    for last_active_str in user_last_active.values():
        if last_active_str >= seven_days_ago:
            active_users_7_days += 1

    # ساخت پیام آمار
    msg = (
        "📈 <b>آمار کلی ربات</b>\n\n"
        f"👤 تعداد کل کاربران: <b>{total_users}</b>\n"
        f"💎 مجموع کل امتیازات: <b>{total_points}</b>\n"
        f"🌟 کاربران فعال در ۷ روز اخیر: <b>{active_users_7_days}</b>"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def top_members(update, context):
    """نمایش ۱۰ کاربر برتر بر اساس امتیاز."""
    if not is_admin(update.effective_user):
        return

    # تبدیل دیکشنری به لیست و مرتب‌سازی بر اساس امتیاز
    sorted_users = sorted(user_points.items(), key=lambda item: item[1], reverse=True)
    top_10 = sorted_users[:10]

    msg = "🏆 <b>۱۰ کاربر برتر ربات (بر اساس امتیاز)</b>\n\n"

    for rank, (user_id_str, points) in enumerate(top_10):
        try:
            # تلاش برای گرفتن نام کاربر
            user = await context.bot.get_chat(int(user_id_str))
            user_link = f"<a href='tg://user?id={user_id_str}'>{escape_html(user.full_name)}</a>"
        except Exception:
            user_link = f"<code>{user_id_str}</code>"

        msg += f"{rank+1}. {user_link}: <b>{points}</b> امتیاز\n"

    if not top_10:
        msg = "⚠️ هیچ کاربری برای نمایش وجود ندارد."

    await update.message.reply_text(msg, parse_mode="HTML")


async def start_set_points(update, context):
    """شروع فرآیند تنظیم امتیاز کاربر."""
    if not is_admin(update.effective_user):
        return
    await update.message.reply_text("💎 **لطفا آیدی عددی کاربر و میزان امتیاز جدید را با فاصله ارسال کنید.**\n\nمثال: `123456789 100`", parse_mode="Markdown")
    return SET_POINTS_STATE

async def receive_set_points(update, context):
    """دریافت و تنظیم امتیاز کاربر."""
    if not is_admin(update.effective_user):
        return
    try:
        parts = update.message.text.strip().split()
        if len(parts) != 2:
            raise ValueError

        user_id = parts[0]
        new_points = int(parts[1])

        if not user_id.isdigit():
            raise ValueError("User ID must be numeric.")
        if new_points < 0:
            raise ValueError("Points must be non-negative.")

        # ✅ FIX: امتیاز بلافاصله در حافظه تغییر و ذخیره می‌شود
        user_points[user_id] = new_points
        save_data()

        # Try to notify user
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"🎁 امتیاز شما توسط مدیر به <b>{new_points}</b> تغییر یافت.",
                parse_mode="HTML"
            )
        except Exception:
            pass

        await update.message.reply_text(f"✅ امتیاز کاربر <code>{user_id}</code> با موفقیت به <b>{new_points}</b> تغییر یافت.", parse_mode="HTML")

    except ValueError:
        await update.message.reply_text("❌ فرمت ورودی نامعتبر. لطفا آیدی عددی کاربر و میزان امتیاز را به‌صورت صحیح و بدون متن اضافی ارسال کنید. (مثلا: 123456789 100).", parse_mode="Markdown")
        return SET_POINTS_STATE

    return ConversationHandler.END


# --- Admin Panel Handlers (Broadcast/ارسال پیام) --- 🛑 FIX: توابع جدید برای رفع مشکل ارسال پیام همگانی

async def start_broadcast(update, context):
    """شروع فرآیند ارسال پیام همگانی."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 **لطفاً پیام (متن، عکس، فوروارد، استیکر و...) را که می‌خواهید برای همه کاربران ارسال شود، بفرستید.**\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="Markdown"
    )
    return BROADCAST_MESSAGE_RECEIVE


async def broadcast_message_receive(update, context):
    """دریافت پیام برای ارسال همگانی و درخواست تایید."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    # ✅ Safety check for navigation buttons
    if update.message.text:
        all_reply_buttons = NAVIGATION_BUTTONS + [
            "فروشگاه🛍️", "حساب کاربری👤", "لینک زیرمجموعه گیری👥", "پشتیبانی📞", "پنل مدیریت"
        ]

        # اگر پیام دریافتی، یکی از دکمه‌های منو بود، یعنی کاربر قصد ناوبری داشته و نه ارسال پیام
        if update.message.text in all_reply_buttons:
             await update.message.reply_text("⚠️ دکمه‌ای که فشار دادید به عنوان پیام همگانی تشخیص داده شد. عملیات لغو شد.", parse_mode="Markdown")
             return await back_to_admin_menu(update, context)

    # Store message info
    context.user_data['broadcast_message_info'] = {
        'chat_id': update.effective_chat.id,
        'message_id': update.message.message_id
    }

    # Confirmation message and buttons
    msg = "⚠️ **تایید ارسال پیام همگانی** ⚠️\n\nآیا مطمئن هستید که می‌خواهید این پیام را برای **همه کاربران** ارسال کنید؟"

    inline_keyboard = [
        [InlineKeyboardButton("✅ ارسال پیام به همه", callback_data="broadcast_confirm_send")],
        [InlineKeyboardButton("❌ لغو ارسال و بازگشت", callback_data="broadcast_confirm_cancel")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    # Use reply_to_message_id to clearly show WHICH message is about to be broadcast
    await update.message.reply_text(
        msg,
        reply_markup=reply_markup,
        parse_mode="Markdown",
        reply_to_message_id=update.message.message_id # Link to the message
    )

    return BROADCAST_CONFIRM_STATE


async def confirm_broadcast_callback(update, context):
    """هندلر نهایی برای ارسال یا لغو پیام همگانی."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    broadcast_info = context.user_data.pop('broadcast_message_info', None)

    if query.data == "broadcast_confirm_cancel":
        await query.message.edit_text("❌ ارسال پیام همگانی لغو شد.")
        return await admin_fallback_handler_callback(update, context)

    # --- Actual Broadcast Logic ---
    if not broadcast_info:
        await query.message.edit_text("❌ خطای سیستمی: اطلاعات پیام برای ارسال پیدا نشد.")
        return await admin_fallback_handler_callback(update, context)

    await query.message.edit_text("⏳ پیام در حال ارسال به کاربران است...")

    user_ids = list(user_points.keys())
    success_count = 0
    failed_count = 0

    bot_me = await context.bot.get_me()
    bot_username = bot_me.username

    # ساخت دکمه برگشت به ربات (Inline) برای پیام همگانی
    back_to_bot_button = InlineKeyboardButton(
        text="🔙 برگشت به ربات", url=f"https://t.me/{bot_username}"
    )

    final_reply_markup = InlineKeyboardMarkup([[back_to_bot_button]]) # فقط دکمه برگشت به ربات


    # 2. Broadcast loop
    for user_id_str in user_ids:
        try:
            user_id = int(user_id_str)

            # استفاده از copy_message برای ارسال هر نوع محتوا
            await context.bot.copy_message(
                chat_id=user_id,
                from_chat_id=broadcast_info['chat_id'],
                message_id=broadcast_info['message_id'],
                reply_markup=final_reply_markup
            )
            success_count += 1
            await asyncio.sleep(0.05) # تأخیر کوچک برای جلوگیری از محدودیت‌های تلگرام

        # 🛑 FIX: Changed from telegram.error.Unauthorized to telegram.error.Forbidden
        # This fixes the AttributeError and correctly handles blocked users.
        except telegram.error.Forbidden:
            logging.info(f"User {user_id_str} blocked the bot (Forbidden error). Skipping.")
            failed_count += 1
        except Exception as e:
            logging.error(f"Failed to send broadcast to {user_id_str}: {e}")
            failed_count += 1

    # 3. Final Report
    report_msg = (
        f"✅ ارسال پیام همگانی با موفقیت به پایان رسید.\n\n"
        f"تعداد کل کاربران: {len(user_ids)}\n"
        f"ارسال موفق: {success_count}\n"
        f"ارسال ناموفق (بلاکی/خطا): {failed_count}"
    )
    await query.message.edit_text(report_msg, parse_mode="HTML")

    return ConversationHandler.END


# --- Channel Management Handlers ---

async def admin_channel_settings(update, context):
    """نمایش تنظیمات کانال و دکمه‌های شیشه‌ای."""
    if not is_admin(update.effective_user):
        return

    msg = "🆔 <b>تنظیمات کانال‌های اجباری</b>\n\n"
    channels = admin_config.get("channels", [])
    inline_keyboard = []

    for i, c in enumerate(channels):
        status = "✅ فعال" if c.get('is_active', False) else "❌ غیرفعال"
        username_display = escape_html(c['username'])
        target_display = f" (هدف: {c['current_joins']}/{c['target_count']})" if c.get('target_count', 0) > 0 else ""

        button_text = f"اسلات {i+1}: {username_display} {status}{target_display}"

        # دکمه اصلی: ویرایش/تنظیم
        edit_button = InlineKeyboardButton(button_text, callback_data=f"select_slot:{i}")

        # دکمه تنظیم هدف
        target_button = InlineKeyboardButton("⚙️ هدف", callback_data=f"set_target_slot:{i}")

        inline_keyboard.append([edit_button, target_button])

    # دکمه‌های مدیریتی پایین
    inline_keyboard.append([InlineKeyboardButton("🔙 برگشت به پنل مدیریت", callback_data="back_to_admin_menu_callback")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")


async def select_channel_slot(update, context):
    """شروع ویرایش/افزودن کانال در اسلات مشخص."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    try:
        slot_index = int(query.data.split(":")[1])
        context.user_data['channel_slot_index'] = slot_index
    except (IndexError, ValueError):
        await query.message.reply_text("❌ خطای اسلات نامعتبر.")
        return ConversationHandler.END

    current_channel = admin_config["channels"][slot_index]

    if current_channel['username'] == '-':
        msg = f"➕ **شروع افزودن کانال در اسلات {slot_index+1}.**\n\n"
        msg += "لطفا یوزرنیم کانال (با @) و لینک عضویت (مثلا `https://t.me/yourchannel`) را با فاصله ارسال کنید.\n"
        msg += "مثال: `@MyChannel https://t.me/MyChannel`"
    else:
        username = escape_markdown(current_channel['username'])
        url = escape_markdown(current_channel['url'])
        status = "فعال" if current_channel['is_active'] else "غیرفعال"

        msg = f"⚙️ **ویرایش کانال اسلات {slot_index+1}:**\n"
        msg += f"یوزرنیم فعلی: `{username}`\n"
        msg += f"لینک فعلی: `{url}`\n"
        msg += f"وضعیت: **{status}**\n\n"
        msg += "لطفا یوزرنیم کانال (با @) و لینک عضویت (مثلا `https://t.me/yourchannel`) را با فاصله ارسال کنید تا تغییر یابد."
        msg += "\n\nیا می‌توانید `حذف` را ارسال کنید یا `فعال/غیرفعال` را برای تغییر وضعیت ارسال کنید."

    await query.message.reply_text(msg, parse_mode="Markdown")
    return CHANNEL_ADD_INPUT

async def receive_channel_input(update, context):
    """دریافت ورودی کاربر برای افزودن/ویرایش کانال."""
    if not is_admin(update.effective_user):
        return

    text = update.message.text.strip()
    slot_index = context.user_data.get('channel_slot_index')

    if slot_index is None:
        await update.message.reply_text("❌ خطای اسلات نامعتبر، لطفا دوباره اقدام کنید.")
        return ConversationHandler.END

    if text in ["حذف", "فعال", "غیرفعال"]:
        current_channel = admin_config["channels"][slot_index]
        if text == "حذف":
            # ریست کردن اسلات
            admin_config["channels"][slot_index] = {
                "username": "-", "url": "-", "is_active": False, "target_count": 0, "current_joins": 0
            }
            msg = f"✅ کانال اسلات **{slot_index+1}** با موفقیت حذف شد."
        elif text == "فعال":
            if current_channel['username'] == '-':
                msg = "❌ برای فعال‌سازی، ابتدا باید کانال را تعریف کنید."
                await update.message.reply_text(msg, parse_mode="Markdown")
                return CHANNEL_ADD_INPUT # ماندن در همین حالت
            current_channel["is_active"] = True
            msg = f"✅ کانال اسلات **{slot_index+1}** فعال شد."
        elif text == "غیرفعال":
            current_channel["is_active"] = False
            msg = f"✅ کانال اسلات **{slot_index+1}** غیرفعال شد."

        save_admin_config()
        await update.message.reply_text(msg, parse_mode="Markdown")
        # بازگشت به منوی کانال
        return await admin_fallback_handler(update, context)

    try:
        parts = text.split()
        if len(parts) < 2:
            raise ValueError("ورودی نامعتبر: باید شامل یوزرنیم و لینک دعوت باشد.")

        username = parts[0]
        url = parts[1]

        if not username.startswith('@') or not url.startswith('http'):
            raise ValueError("یوزرنیم باید با @ شروع شود و لینک باید یک URL معتبر باشد.")

        admin_config["channels"][slot_index].update({
            "username": username,
            "url": url,
            "is_active": True, # به صورت پیش فرض فعال می‌شود
            # Target and current joins remain intact or reset if user removed it before
            "target_count": admin_config["channels"][slot_index].get("target_count", 0),
            "current_joins": admin_config["channels"][slot_index].get("current_joins", 0),
        })
        save_admin_config()

        await update.message.reply_text(f"✅ کانال اسلات **{slot_index+1}** با موفقیت تنظیم شد و فعال گردید.\nیوزرنیم: **{escape_markdown(username)}**", parse_mode="Markdown")

    except ValueError as e:
        await update.message.reply_text(f"❌ خطای ورودی: {e}\nلطفا ورودی را مطابق با الگو ارسال کنید.", parse_mode="Markdown")
        return CHANNEL_ADD_INPUT # ماندن در همین حالت

    return await admin_fallback_handler(update, context)


async def start_set_target_slot(update, context):
    """شروع تنظیم هدف جوین برای کانال."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    try:
        slot_index = int(query.data.split(":")[1])
        context.user_data['channel_slot_index'] = slot_index
    except (IndexError, ValueError):
        await query.message.reply_text("❌ خطای اسلات نامعتبر.")
        return ConversationHandler.END

    current_channel = admin_config["channels"][slot_index]

    if current_channel['username'] == '-':
        await query.message.reply_text("❌ این اسلات کانالی تعریف نشده است. ابتدا کانال را تنظیم کنید.", parse_mode="Markdown")
        return await admin_fallback_handler_callback(update, context)

    username = escape_markdown(current_channel['username'])
    target = current_channel['target_count']
    current = current_channel['current_joins']

    msg = (f"🎯 **تنظیم هدف جوین برای کانال {username} (اسلات {slot_index+1})**\n\n"
           f"هدف فعلی: **{target}** نفر\n"
           f"تعداد جوین‌های ثبت شده: **{current}** نفر\n\n"
           "لطفا تعداد هدف جدید را ارسال کنید (عدد).\n"
           "برای غیرفعال کردن هدف، عدد **0** را ارسال کنید.")

    await query.message.reply_text(msg, parse_mode="Markdown")
    return CHANNEL_SET_TARGET


async def receive_target_count(update, context):
    """دریافت عدد هدف جوین."""
    if not is_admin(update.effective_user):
        return

    text = update.message.text.strip()
    slot_index = context.user_data.get('channel_slot_index')

    if slot_index is None:
        await update.message.reply_text("❌ خطای اسلات نامعتبر، لطفا دوباره اقدام کنید.")
        return ConversationHandler.END

    try:
        new_target = int(text)
        if new_target < 0:
            raise ValueError

        current_channel = admin_config["channels"][slot_index]
        current_channel['target_count'] = new_target

        # اگر هدف 0 شد، current_joins را هم 0 می‌کنیم و کانال را غیرفعال می‌کنیم
        if new_target == 0:
            current_channel['current_joins'] = 0
            current_channel['is_active'] = False
            msg = f"✅ هدف‌گذاری برای کانال **{escape_markdown(current_channel['username'])}** برداشته شد و کانال **غیرفعال** شد."
        else:
            msg = f"✅ هدف‌گذاری برای کانال **{escape_markdown(current_channel['username'])}** با موفقیت به **{new_target}** نفر تنظیم شد."
            # اگر کانال غیرفعال است، آن را فعال می‌کنیم
            if not current_channel['is_active']:
                 current_channel['is_active'] = True
                 msg += "\n⚠️ **کانال مجدداً فعال گردید.**"

        save_admin_config()
        await update.message.reply_text(msg, parse_mode="Markdown")

    except ValueError:
        await update.message.reply_text("❌ لطفا فقط یک **عدد صحیح مثبت** برای هدف ارسال کنید (یا 0 برای غیرفعال‌سازی).", parse_mode="Markdown")
        return CHANNEL_SET_TARGET # ماندن در همین حالت

    return await admin_fallback_handler(update, context)


# --- Admin Panel Handlers (Referral Texts/Settings) ---

async def start_set_banner(update, context):
    """شروع فرآیند تنظیم بنر."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END
    await update.message.reply_text(
        "📸 **لطفاً یک عکس جدید برای بنر زیرمجموعه‌گیری ارسال کنید.**\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="Markdown"
    )
    return SET_BANNER_STATE

async def receive_banner(update, context):
    """دریافت و ذخیره عکس بنر جدید."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    if update.message.photo:
        file_id = update.message.photo[-1].file_id

        # ذخیره فایل در سیستم فایل
        new_banner_name = "new_telegram-stars.jpg"
        new_banner_path = os.path.join(os.getcwd(), new_banner_name)

        # دانلود فایل (برای استفاده مجدد در ربات)
        new_file = await context.bot.get_file(file_id)
        await new_file.download_to_drive(custom_path=new_banner_path)

        # حذف بنر قبلی (اگر وجود داشته باشد)
        old_banner_path = admin_config.get("banner")
        if old_banner_path and os.path.exists(old_banner_path):
             os.remove(old_banner_path)

        admin_config["banner"] = new_banner_name
        save_admin_config()

        await update.message.reply_text("✅ بنر زیرمجموعه‌گیری با موفقیت تنظیم شد.", parse_mode="Markdown")

    else:
        # اگر ورودی متن بود (مثلا دکمه ناوبری)
        if update.message.text in NAVIGATION_BUTTONS:
             return await admin_fallback_handler(update, context)

        await update.message.reply_text("❌ لطفا یک **عکس معتبر** برای بنر ارسال کنید. پیام شما عکس نبود.", parse_mode="Markdown")
        return SET_BANNER_STATE # ماندن در همین حالت

    return await admin_fallback_handler(update, context)


async def start_set_referral_text(update, context):
    """شروع فرآیند تنظیم متن زیرمجموعه‌گیری."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    current_text = admin_config.get("texts", {}).get("referral_message", "تعریف نشده")

    await update.message.reply_text(
        f"📝 **لطفاً متن جدید زیرمجموعه‌گیری را ارسال کنید.**\n\n"
        f"**متن فعلی:**\n{escape_markdown(current_text)}\n\n"
        "⚠️ از کاراکترهای Markdown برای زیبایی متن می‌توانید استفاده کنید. (مانند `**Bold**`)\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="Markdown"
    )
    return SET_REFERRAL_TEXT_STATE

async def receive_referral_text(update, context):
    """دریافت و ذخیره متن زیرمجموعه‌گیری جدید."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    new_text = update.message.text.strip()

    # FIX: If the message is a navigation button, it shouldn't be saved as referral text.
    if new_text in NAVIGATION_BUTTONS:
        return await admin_fallback_handler(update, context)

    admin_config["texts"]["referral_message"] = new_text
    save_admin_config()

    await update.message.reply_text(
        f"✅ متن زیرمجموعه‌گیری با موفقیت تنظیم شد.\n\n**متن ذخیره شده (نمونه):**\n{escape_markdown(new_text)}",
        parse_mode="Markdown"
    )

    return await admin_fallback_handler(update, context)


async def start_set_welcome_text(update, context):
    """شروع فرآیند تنظیم متن خوش آمدگویی."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    current_text = admin_config.get("texts", {}).get("welcome", "تعریف نشده")

    await update.message.reply_text(
        f"✍️ **لطفاً متن جدید خوش آمدگویی را ارسال کنید.**\n\n"
        f"**متن فعلی:**\n{escape_html(current_text)}\n\n"
        "⚠️ از تگ‌های HTML برای زیبایی متن می‌توانید استفاده کنید. (مانند `<b>Bold</b>`)\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="HTML"
    )
    return SET_WELCOME_TEXT_STATE

async def receive_welcome_text(update, context):
    """دریافت و ذخیره متن خوش آمدگویی جدید."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    new_text = update.message.text.strip()

    # ✅ FIX: اگر پیام یک دکمه ناوبری بود، نباید به عنوان متن خوش‌آمدگویی ذخیره شود.
    if new_text in NAVIGATION_BUTTONS:
        return await admin_fallback_handler(update, context)

    admin_config["texts"]["welcome"] = new_text
    save_admin_config()

    # متن خوش‌آمدگویی با parse_mode="HTML" استفاده می‌شود.
    await update.message.reply_text(
        f"✅ متن خوش آمدگویی با موفقیت تنظیم شد.\n\n<b>متن ذخیره شده (نمونه):</b>\n{escape_html(new_text)}",
        parse_mode="HTML"
    )

    return await admin_fallback_handler(update, context)


# --- Admin Panel Handlers (Referral System) ---

async def referral_system_settings(update, context):
    """نمایش تنظیمات سیستم زیرمجموعه گیری."""
    if not is_admin(update.effective_user):
        return

    points_per_join = get_referral_points_per_join()
    points_per_star = get_star_cost_points()

    msg = (
        "⚙️ <b>تنظیمات سیستم زیرمجموعه گیری</b>\n\n"
        f"<b>امتیاز برای هر جوین جدید:</b> <b>{points_per_join}</b>\n"
        f"<b>امتیاز مورد نیاز برای ۱ استارز:</b> <b>{points_per_star}</b>\n\n"
        "لطفاً آیتم مورد نظر برای تغییر را انتخاب کنید:"
    )

    inline_keyboard = [
        [InlineKeyboardButton(f"تغییر امتیاز برای هر عضو جدید (فعلی: {points_per_join})", callback_data="change_points_per_join")],
        [InlineKeyboardButton(f"تغییر امتیاز مورد نیاز برای ۱ استارز (فعلی: {points_per_star})", callback_data="change_points_per_star")],
        [InlineKeyboardButton("🔙 برگشت به پنل مدیریت", callback_data="back_to_admin_menu_callback")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")


async def start_set_points_per_join(update, context):
    """شروع مکالمه تنظیم امتیاز هر جوین."""
    query = update.callback_query
    await query.answer()

    points_per_join = get_referral_points_per_join()

    await query.message.reply_text(
        f"🔢 **لطفاً عدد صحیح جدید امتیاز برای هر عضو جدید را ارسال کنید.**\n"
        f"امتیاز فعلی: **{points_per_join}**\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="Markdown"
    )
    return SET_POINTS_PER_JOIN

async def receive_points_per_join(update, context):
    """دریافت و ذخیره امتیاز هر جوین."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    try:
        new_value = int(update.message.text.strip())
        if new_value < 0:
            raise ValueError

        admin_config["referral_system"]["points_per_join"] = new_value
        save_admin_config()

        await update.message.reply_text(f"✅ امتیاز برای هر جوین جدید با موفقیت به <b>{new_value}</b> تغییر یافت.", parse_mode="HTML")

    except ValueError:
        await update.message.reply_text("❌ لطفا فقط یک **عدد صحیح مثبت** ارسال کنید.", parse_mode="Markdown")
        return SET_POINTS_PER_JOIN

    # ✅ FIX: بازگشت به منوی ادمین
    return await admin_fallback_handler(update, context)


async def start_set_points_per_star(update, context):
    """شروع مکالمه تنظیم امتیاز مورد نیاز برای ۱ استارز."""
    query = update.callback_query
    await query.answer()

    points_per_star = get_star_cost_points()

    await query.message.reply_text(
        f"🔢 **لطفاً عدد صحیح جدید امتیاز مورد نیاز برای ۱ استارز را ارسال کنید.**\n"
        f"امتیاز فعلی: **{points_per_star}**\n"
        "برای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.",
        parse_mode="Markdown"
    )
    return SET_POINTS_PER_STAR

async def receive_points_per_star(update, context):
    """دریافت و ذخیره امتیاز مورد نیاز برای ۱ استارز."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    try:
        new_value = int(update.message.text.strip())
        if new_value < 1:
            raise ValueError("Value must be greater than 0")

        admin_config["referral_system"]["points_per_star"] = new_value
        save_admin_config()

        await update.message.reply_text(f"✅ امتیاز مورد نیاز برای ۱ استارز با موفقیت به <b>{new_value}</b> تغییر یافت.", parse_mode="HTML")

    except ValueError:
        await update.message.reply_text("❌ لطفا فقط یک **عدد صحیح بزرگتر از صفر** ارسال کنید.", parse_mode="Markdown")
        return SET_POINTS_PER_STAR

    # ✅ FIX: بازگشت به منوی ادمین
    return await admin_fallback_handler(update, context)


# --- Admin Panel Handlers (Product Management) ---

async def product_management_menu(update, context):
    """نمایش منوی مدیریت محصولات."""
    if not is_admin(update.effective_user):
        return

    products = admin_config.get("products", [])
    msg = "🎁 <b>مدیریت محصولات فروشگاه</b>\n\n"

    if not products:
        msg += "⚠️ هیچ محصولی به جز برداشت استارز تعریف نشده است."
    else:
        msg += "لیست محصولات:\n"
        for i, p in enumerate(products):
            input_text = STORE_INPUT_TYPES.get(p.get('input_type', INPUT_TYPE_NONE), {}).get('text', 'بدون ورودی')
            msg += f"  - **{i+1}.** {escape_html(p['name'])} ({p['cost']} امتیاز | ورودی: {input_text})\n"

    inline_keyboard = [
        [InlineKeyboardButton("➕ افزودن محصول جدید", callback_data="add_product_start")],
        [InlineKeyboardButton("❌ حذف محصول", callback_data="delete_product_start")],
        [InlineKeyboardButton("🔙 برگشت به پنل مدیریت", callback_data="back_to_admin_menu_callback")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="HTML")
    return PRODUCT_MENU

async def start_add_product_name(update, context):
    """شروع فرآیند افزودن محصول: دریافت نام."""
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("➕ **لطفاً نام محصول جدید را ارسال کنید.**\nبرای لغو، دکمه '🔙 برگشت به ربات' را فشار دهید.", parse_mode="Markdown")
    return PRODUCT_ADD_NAME

async def receive_product_name(update, context):
    """دریافت نام محصول و رفتن به مرحله بعد."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    new_product_name = update.message.text.strip()

    # FIX: If the message is a navigation button, it shouldn't be processed as product name.
    if new_product_name in NAVIGATION_BUTTONS:
        return await admin_fallback_handler(update, context)

    context.user_data['new_product'] = {'name': new_product_name}

    await update.message.reply_text(
        f"💰 **نام محصول '{escape_markdown(new_product_name)}' ثبت شد.**\n"
        "**لطفاً هزینه (امتیاز) محصول را ارسال کنید (فقط عدد صحیح مثبت).**",
        parse_mode="Markdown"
    )
    return PRODUCT_ADD_COST

async def receive_product_cost(update, context):
    """دریافت هزینه محصول و رفتن به مرحله بعد."""
    if not is_admin(update.effective_user):
        return ConversationHandler.END

    try:
        cost = int(update.message.text.strip())
        if cost <= 0:
            raise ValueError

        context.user_data['new_product']['cost'] = cost

        # نمایش دکمه‌های نوع ورودی
        msg = (
            f"🔗 **هزینه {cost} امتیاز ثبت شد.**\n"
            "**لطفاً نوع ورودی مورد نیاز برای تکمیل این سفارش را انتخاب کنید:**"
        )

        input_type_buttons = []
        for input_type, data in STORE_INPUT_TYPES.items():
            input_type_buttons.append(
                [InlineKeyboardButton(data['text'], callback_data=f"set_input_type:{input_type}")]
            )

        input_type_buttons.append([InlineKeyboardButton("🔙 برگشت به پنل مدیریت", callback_data="back_to_admin_menu_callback")])

        reply_markup = InlineKeyboardMarkup(input_type_buttons)

        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

        # در این مرحله ConversationHandler باید منتظر CallbackQuery باشد
        return PRODUCT_ADD_INPUT_TYPE

    except ValueError:
        await update.message.reply_text("❌ لطفا فقط یک **عدد صحیح مثبت** برای هزینه ارسال کنید.", parse_mode="Markdown")
        return PRODUCT_ADD_COST


async def receive_product_input_type(update, context):
    """دریافت نوع ورودی و ذخیره نهایی محصول."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    input_type = query.data.split(":")[1]
    new_product = context.user_data.pop('new_product', None)

    if not new_product:
        await query.message.reply_text("❌ خطای داده محصول، لطفا مجدداً شروع کنید.", parse_mode="Markdown")
        return await admin_fallback_handler_callback(update, context)

    new_product['input_type'] = input_type

    # ذخیره نهایی محصول
    admin_config["products"].append(new_product)
    save_admin_config()

    input_text = STORE_INPUT_TYPES.get(input_type, {}).get('text', 'بدون ورودی')

    msg = (
        f"✅ محصول **{escape_html(new_product['name'])}** با موفقیت اضافه شد.\n"
        f"هزینه: **{new_product['cost']}** امتیاز\n"
        f"نوع ورودی: **{input_text}**"
    )

    await query.message.edit_text(msg, parse_mode="HTML")

    # بازگشت به منوی مدیریت محصولات
    return await admin_fallback_handler_callback(update, context)


async def start_delete_product(update, context):
    """شروع فرآیند حذف محصول: نمایش لیست محصولات."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    products = admin_config.get("products", [])
    if not products:
        await query.message.reply_text("⚠️ هیچ محصولی برای حذف وجود ندارد.", parse_mode="Markdown")
        return await admin_fallback_handler_callback(update, context)

    msg = "❌ **لطفاً محصولی را که می‌خواهید حذف کنید، انتخاب کنید:**"

    delete_buttons = []
    for i, p in enumerate(products):
        delete_buttons.append(
            [InlineKeyboardButton(f"❌ حذف: {escape_html(p['name'])}", callback_data=f"delete_product_confirm:{i}")]
        )

    delete_buttons.append([InlineKeyboardButton("🔙 برگشت به پنل مدیریت", callback_data="back_to_admin_menu_callback")])
    reply_markup = InlineKeyboardMarkup(delete_buttons)

    await query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="HTML")
    return PRODUCT_DELETE_SELECT_FINAL


async def delete_product_final(update, context):
    """حذف نهایی محصول."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user):
        return ConversationHandler.END

    try:
        index_to_delete = int(query.data.split(":")[1])

        products = admin_config.get("products", [])
        if index_to_delete < 0 or index_to_delete >= len(products):
             raise IndexError

        deleted_product = products.pop(index_to_delete)
        save_admin_config()

        msg = f"✅ محصول **{escape_html(deleted_product['name'])}** با موفقیت حذف شد."

        await query.message.edit_text(msg, parse_mode="HTML")

    except (IndexError, ValueError):
        await query.message.edit_text("❌ خطای حذف: محصول نامعتبر یا حذف شده بود.", parse_mode="Markdown")

    # بازگشت به منوی مدیریت محصولات
    return await admin_fallback_handler_callback(update, context)

# --- Support Handlers ---

async def start_support_message(update, context):
    """شروع مکالمه برای ارسال پیام به پشتیبانی."""
    await update_user_activity(update.effective_user.id)

    keyboard = [[KeyboardButton("🔙 برگشت به ربات")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "📞 **لطفاً پیام خود را برای پشتیبانی ارسال کنید.**\n"
        "لطفاً صبور باشید، پیام شما به مدیران ارسال می‌شود.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SUPPORT_MESSAGE

async def receive_support_message(update, context):
    """دریافت پیام پشتیبانی و ارسال آن به ادمین."""
    user = update.effective_user
    user_id = user.id

    # محدودیت ارسال پیام (مثلاً هر 30 ثانیه یکبار)
    last_time = support_message_last_time.get(str(user_id), 0)
    now = time.time()
    if now - last_time < 30 and user_id != ADMIN_ID: # ادمین همیشه می‌تواند بفرستد
        await update.message.reply_text(
            "⏳ **لطفاً کمی صبر کنید!**\nشما می‌توانید هر ۳۰ ثانیه یک پیام برای پشتیبانی ارسال کنید.",
            parse_mode="Markdown"
        )
        return SUPPORT_MESSAGE

    support_message_last_time[str(user_id)] = now
    save_data()

    # ساخت دکمه‌های اینلاین برای پاسخ مدیر
    inline_keyboard = [[
        InlineKeyboardButton("✅ پاسخ دادن به کاربر", url=f"tg://user?id={user_id}")
    ]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)

    header_text = (
        f"📩 **پیام جدید پشتیبانی از کاربر:**\n"
        f"👤 کاربر: <a href='tg://user?id={user_id}'>{escape_html(user.full_name)}</a>\n"
        f"🆔 آیدی عددی: <code>{user_id}</code>\n"
        f"🔗 یوزرنیم: @{user.username or 'ندارد'}\n"
        "--- **متن پیام** ---"
    )

    try:
        # ارسال هدر و سپس کپی کردن پیام کاربر
        await context.bot.send_message(
            chat_id=SUPPORT_ID,
            text=header_text,
            parse_mode="HTML"
        )
        await context.bot.copy_message(
            chat_id=SUPPORT_ID,
            from_chat_id=user_id,
            message_id=update.message.message_id,
            reply_markup=reply_markup # اضافه کردن دکمه پاسخ
        )

        await update.message.reply_text(
            "✅ پیام شما با موفقیت برای پشتیبانی ارسال شد. متشکریم.",
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Failed to send support message to admin: {e}")
        await update.message.reply_text("❌ متاسفانه، خطایی در ارسال پیام به پشتیبانی رخ داد.", parse_mode="Markdown")

    return ConversationHandler.END

# --- Fallback/Unknown Message Handlers ---

async def unknown_message_private(update, context):
    """هندلر برای پیام‌های متنی در چت خصوصی که توسط هیچ هندلر دیگری پوشش داده نشده."""
    # اگر کاربر در حال مکالمه نباشد، این پیام دریافت می‌شود.
    if update.message and update.message.text:
        # اگر متنی باشد که ربات نفهمد
        if update.message.text not in NAVIGATION_BUTTONS:
             await update.message.reply_text(
                 "🧐 متوجه نشدم. لطفاً از دکمه‌های زیر برای تعامل با ربات استفاده کنید."
             )
    # اگر پیام غیرمتنی باشد (عکس، استیکر و...) و در مکالمه نباشد، نادیده گرفته می‌شود.
    # این هندلر فقط برای filters.TEXT تعریف شده است.

async def unknown_message_group(update, context):
    """هندلر برای نادیده گرفتن پیام‌های گروهی که کامند نیستند."""
    # هیچ کاری انجام نمی‌دهد. (برای جلوگیری از اسپم در گروه‌ها)
    pass


# --- Main Application Setup ---

def main():
    """شروع کار ربات و تعریف هندلرها."""
    global user_points, user_join_dates, user_last_active, support_message_last_time, admin_config

    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation Handlers

    # 1. Support Conversation
    support_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^پشتیبانی📞$"), start_support_message)],
        states={
            SUPPORT_MESSAGE: [MessageHandler(filters.ALL & filters.ChatType.PRIVATE & ~filters.COMMAND, receive_support_message)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), back_to_main_menu)],
        allow_reentry=True
    )

    # 2. Broadcast Conversation 🛑 FIX: Implementation for confirmation state
    broadcast_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📨 ارسال پیام$"), start_broadcast)],
        states={
            # State 1: Receive the message (Text/Photo/etc.)
            BROADCAST_MESSAGE_RECEIVE: [MessageHandler(filters.ALL & filters.ChatType.PRIVATE & ~filters.COMMAND, broadcast_message_receive)],
            # State 2: Wait for confirmation (Inline Callback)
            BROADCAST_CONFIRM_STATE: [CallbackQueryHandler(confirm_broadcast_callback, pattern="^broadcast_confirm_")],
        },
        # ✅ FIX: برگشت به منوی ادمین
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler),
                   MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^پنل مدیریت$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 3. Admin: Set Points Conversation
    set_points_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^💎 تنظیم امتیاز کاربر$"), start_set_points)],
        states={
            SET_POINTS_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_set_points)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 4. Product Management Conversation
    product_management_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_add_product_name, pattern="^add_product_start$"),
            CallbackQueryHandler(start_delete_product, pattern="^delete_product_start$"),
            CallbackQueryHandler(delete_product_final, pattern="^delete_product_confirm:")
        ],
        states={
            PRODUCT_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_name)],
            PRODUCT_ADD_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_product_cost)],
            PRODUCT_ADD_INPUT_TYPE: [CallbackQueryHandler(receive_product_input_type, pattern="^set_input_type:")],
            PRODUCT_DELETE_SELECT_FINAL: [CallbackQueryHandler(delete_product_final, pattern="^delete_product_confirm:")]
        },
        fallbacks=[CallbackQueryHandler(admin_fallback_handler_callback, pattern="^back_to_admin_menu_callback$"),
                   MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 5. Channel Management Conversation
    channel_management_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(select_channel_slot, pattern="^select_slot:"),
            CallbackQueryHandler(start_set_target_slot, pattern="^set_target_slot:")
        ],
        states={
            CHANNEL_ADD_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_input)],
            CHANNEL_SET_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_target_count)],
        },
        fallbacks=[CallbackQueryHandler(admin_fallback_handler_callback, pattern="^back_to_admin_menu_callback$"),
                   MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 6. Set Banner Conversation
    set_banner_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📸 تنظیم بنر$"), start_set_banner)],
        states={
            # filters.ALL is necessary to catch text (for nav buttons) and photos
            SET_BANNER_STATE: [MessageHandler(filters.ALL & filters.ChatType.PRIVATE & ~filters.COMMAND, receive_banner)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 7. Set Referral Text Conversation
    referral_text_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📝 تنظیم متن زیرمجموعه$"), start_set_referral_text)],
        states={
            SET_REFERRAL_TEXT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_referral_text)],
        },
        # ✅ FIX: برگشت به منوی ادمین
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 8. Set Welcome Text Conversation
    welcome_text_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^✍️ تنظیم متن خوش آمدگویی$"), start_set_welcome_text)],
        states={
            SET_WELCOME_TEXT_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_welcome_text)],
        },
        # ✅ FIX: برگشت به منوی ادمین
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 9. Referral System Settings Conversation
    referral_system_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_set_points_per_join, pattern="^change_points_per_join$"),
            CallbackQueryHandler(start_set_points_per_star, pattern="^change_points_per_star$")
        ],
        states={
            SET_POINTS_PER_JOIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_points_per_join)],
            SET_POINTS_PER_STAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_points_per_star)],
        },
        # ✅ FIX: برگشت به منوی ادمین
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), admin_fallback_handler)],
        allow_reentry=True
    )

    # 10. Store Purchase Conversation
    purchase_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_purchase_callback, pattern="^handle_purchase:")],
        states={
            # filters.TEXT is enough here as we expect text input (link, ID, etc.)
            ORDER_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_order_input)],
        },
        fallbacks=[MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex("^🔙 برگشت به ربات$"), back_to_main_menu)],
        allow_reentry=True
    )

    # Core Handlers (Must be before general MessageHandlers)
    app.add_handler(CommandHandler("start", start))

    # Main Menu Button Handlers
    app.add_handler(MessageHandler(filters.Regex("^فروشگاه🛍️$"), safe_store_menu))
    app.add_handler(MessageHandler(filters.Regex("^حساب کاربری👤$"), safe_user_profile))
    app.add_handler(MessageHandler(filters.Regex("^لینک زیرمجموعه گیری👥$"), safe_referral_link))
    app.add_handler(MessageHandler(filters.Regex("^پشتیبانی📞$"), safe_support_menu))
    app.add_handler(MessageHandler(filters.Regex("^🔙 برگشت به ربات$"), back_to_main_menu))

    # Admin Panel Handlers
    app.add_handler(MessageHandler(filters.Regex("^پنل مدیریت$"), safe_admin_panel_button))
    app.add_handler(MessageHandler(filters.Regex("^🆔 تنظیم کانال$"), admin_channel_settings))
    app.add_handler(MessageHandler(filters.Regex("^🏆 برترین اعضا$"), top_members))
    app.add_handler(MessageHandler(filters.Regex("^📈 آمار ربات$"), bot_stats))
    app.add_handler(MessageHandler(filters.Regex("^📊 گزارش اکسل کاربران$"), export_users_to_excel))
    app.add_handler(MessageHandler(filters.Regex("^⚙️ تنظیم سیستم زیرمجموعه گیری$"), referral_system_settings))
    app.add_handler(MessageHandler(filters.Regex("^🎁 مدیریت محصولات$"), product_management_menu))
    # Note: Handlers for 📸 تنظیم بنر, 📝 تنظیم متن زیرمجموعه, ✍️ تنظیم متن خوش آمدگویی, 📨 ارسال پیام, 💎 تنظیم امتیاز کاربر
    # are handled as entry points to ConversationHandlers below.

    # Add Conversation Handlers
    app.add_handler(support_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(set_points_conv)
    app.add_handler(purchase_conv)
    app.add_handler(channel_management_conv)
    app.add_handler(product_management_conv)
    app.add_handler(set_banner_conv)
    app.add_handler(referral_text_conv)
    app.add_handler(welcome_text_conv)
    app.add_handler(referral_system_conv) # Add the fixed referral system conv

    # Handlers for callback queries (store navigation & admin navigation)
    app.add_handler(CallbackQueryHandler(handle_product_navigation, pattern="^nav_product:"))
    app.add_handler(CallbackQueryHandler(back_to_main_menu_callback, pattern="^back_to_main_menu$"))
    app.add_handler(CallbackQueryHandler(admin_fallback_handler_callback, pattern="^back_to_admin_menu_callback$")) # ✅ Added callback for back to admin menu
    app.add_handler(CallbackQueryHandler(handle_join_re_check, pattern="^check_join_re_check$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer("❌ امتیاز کافی نیست!"), pattern="^no_action$"))


    # ⚠️ مهم: این هندلرها باید در انتها باشند. (برای جلوگیری از تداخل با دکمه‌ها)

    # 1. Private Chat: Reply only to text messages not covered by commands/buttons
    # This captures text messages not handled by the main buttons or conversation handlers.
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, unknown_message_private))

    # 2. Group Chat: Ignore all messages that are not commands or callbacks (to prevent "command not found" spam)
    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, unknown_message_group))


    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    # اطمینان از وجود فایل‌های کانفیگ
    load_admin_config()
    load_data()
    main()
