import telebot
from telebot import types
import sqlite3
import pay
from datetime import datetime
import time
import threading
from threading import Timer
user_last_gift_message = {}

user_cooldown = {}
FLOOD_TIME = 3

now = datetime.now().strftime("%d.%m.%Y %H:%M")

bot = '8579111497:AAHvOKSOpcs6IxxcooQN1gGE9EseQ1kbh20'

cb_global = {}

def global_cb_limit(user_id, delay=2):
    now = time.time()
    if now - cb_global.get(user_id, 0) < delay:
        return True
    cb_global[user_id] = now
    return False

def antiflood(user_id, key, delay=3):
    now = time.time()
    if user_id not in user_cooldown:
        user_cooldown[user_id] = {}

    if key in user_cooldown[user_id]:
        if now - user_cooldown[user_id][key] < delay:
            return True

    user_cooldown[user_id][key] = now
    return False

cb_cooldown = {}

def antiflood_cb(user_id, key, delay=5):
    now = time.time()
    if user_id not in cb_cooldown:
        cb_cooldown[user_id] = {}

    if key in cb_cooldown[user_id]:
        if now - cb_cooldown[user_id][key] < delay:
            return True

    cb_cooldown[user_id][key] = now
    return False

CHANNEL_ID = -1003555382095
CHANNEL_LINK = "https://t.me/woldevs"

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def ask_to_join(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔔Obuna bo'lish", url=CHANNEL_LINK),
        types.InlineKeyboardButton("✅Obuna bo'ldim", callback_data="check_join")
    )

    bot.send_message(
        chat_id,
        "⚠️Botdan to'liq foydalanish uchun kanalga obuna bo'ling!",
        reply_markup=markup

    )
ADMIN_ID = 6067312074

conn = sqlite3.connect('users.db', check_same_thread=False)
cur = conn.cursor()

cur.execute("""
            CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,phone TEXT,balance INTEGER DEFAULT 0)
            """)
conn.commit()

def add_user(user_id, username=None, first_name=None, phone=None, referred_by=None):
    cur.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, first_name, phone, balance, referred_by, ref_bonus_given, used_promos)
        VALUES (?, ?, ?, ?, 0, ?, 0, '')
    """, (user_id, username, first_name, phone, referred_by))
    conn.commit()

def get_balance(user_id):
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    return result[0] if result else 0

def add_balance(user_id, amount):
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def subtract_balance(user_id, amount_tiyin):
    cur.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()

    if result and result[0] >= amount_tiyin:
        cur.execute(
            "UPDATE users SET balance = balance - ? WHERE user_id = ?",
            (amount_tiyin, user_id)
        )
        conn.commit()
        return True
    return False

def update_username(user_id, username=None, first_name=None):
    cur.execute(
        "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
        (username, first_name, user_id)
    )
    conn.commit()

def reset_balance(user_id):
    cur.execute("UPDATE users SET balance = balance - balance WHERE user_id = ?", (user_id,))
    conn.commit()

def ban_user(user_id):
    cur.execute(
        "UPDATE users SET is_banned = 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()

def unban_user(user_id):
    cur.execute(
        "UPDATE users SET is_banned = 0 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()

def is_banned(user_id):
    cur.execute(
        "SELECT is_banned FROM users WHERE user_id = ?",
        (user_id,)
    )
    r = cur.fetchone()
    return r and r[0] == 1

def reset_weekly_refs():
    cur.execute("""
        UPDATE users SET ref_time = NULL
    """)
    conn.commit()

def weekly_reset_scheduler():
    while True:
        now = datetime.now()
        if now.weekday() == 0 and now.hour == 0:
            reset_weekly_refs()
            time.sleep(60)
        time.sleep(30)

threading.Thread(target=weekly_reset_scheduler, daemon=True).start()

def has_used_promo(user_id, promo_code):
    cur.execute("SELECT * FROM used_promos WHERE user_id=? AND promo_code=?",
                (user_id, promo_code))
    return cur.fetchone() is not None

def add_used_promo(user_id, promo_code):
    cur.execute(
        "INSERT OR IGNORE INTO used_promos (user_id, promo_code) VALUES (?, ?)",
        (user_id, promo_code)
    )
    conn.commit()

def sum_to_tiyin(summa):
    return summa * 100

def tiyin_to_sum(tiyin):
    return tiyin // 100

# VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS,
# VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS,
# VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS, VERIFICATION STARTS,

@bot.callback_query_handler(func=lambda c: c.data == "check_join")
def check_join(c):
    bot.answer_callback_query(c.id)

    if is_member(c.from_user.id):
        bot.answer_callback_query(
            c.id,
            "✅ Muvaffaqiyatli!",
            show_alert=True
        )
        try:
            bot.delete_message(c.message_id, c.message.id)
        except:
            pass
        start_msg(c.message)
    else:
        bot.answer_callback_query(
            c.id,
            "❌ Avval kanalga obuna bo‘ling",
            show_alert=True
        )

@bot.message_handler(commands=['start'])
def start_msg(message):
    if antiflood(message.from_user.id, "start"):
        return

    if not is_member(message.from_user.id):
        ask_to_join(message.chat.id)
        return

    name = message.from_user.first_name
    user_id = message.from_user.id
    tg_username = message.from_user.username
    username = f"@{tg_username}" if tg_username else "No username"

    ref_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            ref_id = int(args[1])
            if ref_id == user_id:
                ref_id = None
        except:
            ref_id = None

    add_user(user_id, username, name, referred_by=ref_id)

    cur.execute("SELECT phone FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()

    if result and result[0]:
        show_main_menu(message)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Raqamni yuborish", request_contact=True))

    bot.send_message(
        message.chat.id,
        f"""⚠️ <b>Ro‘yxatdan o‘tish uchun telefon raqamingizni kiriting!</b>
❗️Bu sizning balansingiz xavfsizligi uchun
📞 Pastdagi tugmani bosing.""",
        reply_markup=markup,
        parse_mode="HTML"
    )

# VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS,
# VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS,
# VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS, VERIFICATION ENDS,

# ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS,
# ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS,
# ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS,
# ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS,
# ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS, ADMIN PANEL STARTS,

@bot.message_handler(commands=['ad'])
def admin(message):
    if message.from_user.id != ADMIN_ID:
        return
    bot.send_message(
        message.chat.id,
        f"""admin commands:
/add_bilol - adds defined amount of money
/subtract - subtracts defined amount of money
/reset - resets balance
/getusersinfo - all information about users
/ban user_id - ban defined user 
/unban user_id - unban defined user 
"""
    )

@bot.message_handler(commands=['getusersinfo'])
def show_users_button(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            text="👥 Show Users",
            callback_data="show_users"
        )
    )
    bot.send_message(
        message.chat.id,
        "Click the button below 👇",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "show_users")
def callback_handler(call):
    bot.answer_callback_query(call.id)

    if global_cb_limit(call.from_user.id):
        return

    if call.from_user.id != ADMIN_ID:
        bot.send_message(call.message.chat.id, "⛔ Access denied")
        return

    cur.execute("""
                SELECT user_id, username, first_name, phone, balance
                FROM users
                """)
    users = cur.fetchall()

    if not users:
        bot.send_message(call.message.chat.id, "❌ No users found")
        return

    text = "👥 <b>Registered Users:</b>\n\n"

    for idx, (user_id, username, first_name, phone, balance) in enumerate(users, start=1):
        phone_text = phone if phone else "Not shared"
        username_text = username if username else "NoUsername"

        cur.execute(
            "SELECT promo_code FROM used_promos WHERE user_id = ?",
            (user_id,)
        )
        promo_rows = cur.fetchall()

        used_promos_text = ", ".join(p[0] for p in promo_rows) if promo_rows else "—"

        cur.execute("""
            SELECT COUNT(*) 
            FROM users 
            WHERE referred_by = ?
              AND phone IS NOT NULL
        """, (user_id,))
        ref_count = cur.fetchone()[0]

        text += (
            f"{idx}. 👤 <b>Name:</b> {first_name}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🔗 <b>Username:</b> @{username_text}\n"
            f"📞 <b>Phone:</b> {phone_text}\n"
            f"💳 <b>Balance:</b> {tiyin_to_sum(balance)} so'm\n"
            f"🎟 <b>Promocode:</b> {used_promos_text}\n"
            f"🗣 <b>Referrals:</b> {ref_count} ta\n\n"
        )

    text += f"📊 <b>Total users:</b> {len(users)}"

    bot.send_message(call.message.chat.id, text[:4000], parse_mode="HTML")

@bot.message_handler(commands=['add_bilol'])
def add_points(message):
    if message.from_user.id != ADMIN_ID:
        return
    add_balance(message.from_user.id, sum_to_tiyin(100000))
    new_balance = get_balance(message.from_user.id)
    new_tiyin = tiyin_to_sum(new_balance)
    bot.reply_to(message, f"❗️hisobingizga 100.000 uzs qo'shildi!\n 💳Yangi hisob: {new_tiyin} so'm")

@bot.message_handler(commands=['reset'])
def reset(message):
    if message.from_user.id != ADMIN_ID:
        return
    reset_balance(message.from_user.id)
    bot.reply_to(message, f'❗️hisobingiz 0 ga tushirildi!\n 💳Yangi hisob: {tiyin_to_sum(get_balance(message.from_user.id))}')

@bot.message_handler(commands=['subtract'])
def subtract_points(message):
    if message.from_user.id != ADMIN_ID:
        return
    subtract_balance(message.from_user.id, sum_to_tiyin(100000))
    new_balance = get_balance(message.from_user.id)
    new_tiyin = tiyin_to_sum(new_balance)
    bot.reply_to(message, f"❗️hisobingizdan 100.000 so'm ayirildi!\n 💳Yangi hisob: {new_tiyin} so'm")

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❗ Foydalanish: /ban USER_ID")
        return

    user_id = int(parts[1])
    ban_user(user_id)

    bot.reply_to(message, f"🚫 User {user_id} ban qilindi")

@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "❗ Foydalanish: /unban USER_ID")
        return

    user_id = int(parts[1])
    unban_user(user_id)

    bot.reply_to(message, f"✅ User {user_id} unban qilindi")

# ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS,
# ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS,
# ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS,
# ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS,
# ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS, ADMIN PANEL ENDS,

def give_referral_bonus(user_id):
    cur.execute("""
        SELECT referred_by, ref_bonus_given FROM users WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()

    if not row:
        return

    referred_by, bonus_given = row

    if referred_by and bonus_given == 0:
        # refererga +200 so'm
        add_balance(referred_by, sum_to_tiyin(200))

        # belgilab qo'yamiz (yana bermaslik uchun)
        cur.execute("""
            UPDATE users SET ref_bonus_given = 1 WHERE user_id = ?
        """, (user_id,))
        conn.commit()

        try:
            bot.send_message(
                referred_by,
                "🎉 Referalingiz ro‘yxatdan o‘tdi!\n💸 Sizga +200 so‘m berildi."
            )
        except:
            pass


@bot.message_handler(content_types=['contact'])
def save_contact(message):
    if antiflood(message.from_user.id, "contact"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    if message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "❌ O'zingizning raqamingizni yuboring")
        return

    phone = message.contact.phone_number
    user_id = message.from_user.id

    cur.execute("""UPDATE users SET phone = ? WHERE user_id = ?""", (phone, user_id))
    conn.commit()

    give_referral_bonus(user_id)

    bot.send_message(
        message.chat.id,
        "✅ <b>Ro‘yxatdan o‘tish yakunlandi!</b>",
        parse_mode="HTML"
    )
    show_main_menu(message)

# MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS,
# MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS,
# MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS, MAIN MENU STARTS,

def show_main_menu(call):
    user_id = call.from_user.id
    username = call.from_user.username or "Nousername"

    cur.execute("SELECT first_name FROM users WHERE user_id = ?", (user_id,))
    result = cur.fetchone()
    name = result[0] if result else call.from_user.first_name

    add_user(user_id, username, name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛍Xizmatlar")
    btn2 = types.KeyboardButton("💳Hisobim")
    btn3 = types.KeyboardButton("💰Pul ishlash")
    btn4 = types.KeyboardButton("❓Qo'llab-Quvvatlash")
    btn5 = types.KeyboardButton("💸Hisob to'ldirish")
    btn6 = types.KeyboardButton("🔒[TEZ KUNDA]NFT")

    markup.row(btn6, btn1)
    markup.row(btn5, btn2)
    markup.row(btn3, btn4)

    chat_id = call.message.chat.id if hasattr(call, "message") else call.chat.id

    bot.send_message(
        chat_id,
        f"""Salom {name} !

✅ Bu botda siz ishonchli, arzon va tez
🎁 Telegram Gift va NFT larni sotib olishingiz mumkin!

<b>❗️BOT BETA VERSIYADA! Agarda botda biror nosozlik sezsangiz adminga murojat qiling!, 
albatta buning uchun taqdirlanasiz, Raxmat!. </b>

☎️ Qo'shimcha:
💎 Asosiy Kanal: https://t.me/woldevs
💎 Isbot Kanal: https://t.me/isbotlarnftvasovga

👇Marhamat botimizdan foydalanishingiz mumkin.
""",
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "💰Pul ishlash")
def earn(message):
    if antiflood(message.from_user.id, "nft"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton('👥Referral'))
    markup.add(types.KeyboardButton('🎟Promocode'))
    markup.add(types.KeyboardButton('↩️Orqaga'))

    bot.send_message(
        message.chat.id,
        '👇Pul ishlash turini tanlang',
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "💎NFT")
def services(message):
    if antiflood(message.from_user.id, "nft"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    bot.send_message(
        message.chat.id,
        'Tez kunda'
    )

@bot.message_handler(func=lambda m: m.text == "🛍Xizmatlar")
def services(message):
    if antiflood(message.from_user.id, "services"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn1 = types.KeyboardButton('🎁Giftlar')
    btn2 = types.KeyboardButton('✅Telegram premium')
    btn3 = types.KeyboardButton('🔒[TEZ KUNDA]Stars sotib olish')
    btn4 = types.KeyboardButton('↩️Orqaga')

    markup.row(btn1, btn2)
    markup.row(btn3, btn4)

    bot.send_message(
        message.chat.id,
        "👇 O'zingizga kerakli xizmatni tanlang.",
        reply_markup=markup,
    )


def balance_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💳hisob to'ldirish", callback_data='hisobtoldirish'))
    return markup


def open_balance_inline(bot_message, user_message):
    add_user(user_message.from_user.id, user_message.from_user.username)

    username = user_message.from_user.username or "NoUsername"
    user_id = user_message.from_user.id
    bal = get_balance(user_id)
    bal_sum = tiyin_to_sum(bal)

    bot.edit_message_text(
        f"👤Foydalanuvchi: @{username}\n"
        f"🆔ID raqam: <code>{user_id}</code>\n\n"
        f"💰Hisobingiz: {bal_sum} so'm.",
        chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        reply_markup=balance_markup(),
        parse_mode="HTML"
    )


@bot.message_handler(func=lambda m: m.text == "💳Hisobim")
def balance_button(message):
    if antiflood(message.from_user.id, "balance"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
        message.chat.id,
        "⏳ Yuklanmoqda...",
    )
    open_balance_inline(bot_msg, message)


def hisobtoldirish_markup():
    markup = types.InlineKeyboardMarkup()
    # btn1 = types.InlineKeyboardButton("🟡Payme(Avto)", callback_data="payme")
    # btn2 = types.InlineKeyboardButton("🔵Click(Avto)", callback_data="click")
    # btn3 = types.InlineKeyboardButton("🟣Hazna(Avto)", callback_data="hazna")
    # btn4 = types.InlineKeyboardButton("🟢Paynet(Avto)", callback_data="paynet")
    btn5 = types.InlineKeyboardButton("☎️Admin orqali", url="https://t.me/wolframxm")
    btn6 = types.InlineKeyboardButton("↩️Orqaga", callback_data="back")

    # markup.row(btn1, btn2)
    # markup.row(btn3, btn4)
    markup.row(btn5)
    markup.row(btn6)

    return markup


def get_hisob_text(bot_message, user_id):
    balance = get_balance(user_id)
    tiyin = tiyin_to_sum(balance)

    bot.edit_message_text(
        f"👇Quyidagilardan birini tanlang\n\n"

        "<b>❗️ HOZIRCHA AVTO TO'LOVLAR ISHLAMAYPTI</b> (22.12.2025)\n\n"

        # "<b>❗️Bizda payme,click,hazna,paynet ilovalari bilan rasmiy shartnomamiz bor."
        # "❗️Kartangiz botga ulanmaydi va belgilaganingizdan 1 so'm ham ortiq yechilmaydi</b>"

        f"🆔ID raqam: <code>{user_id}</code>\n"
        f"💳Hisobingiz: {tiyin} so'm",
        chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        reply_markup=hisobtoldirish_markup(),
        parse_mode="HTML"
    )


@bot.callback_query_handler(func=lambda call: call.data == "hisobtoldirish")
def hisobtoldirish_callback(call):
    bot.answer_callback_query(call.id)
    get_hisob_text(call.message, call.from_user.id)


@bot.message_handler(func=lambda m: m.text == "💸Hisob to'ldirish")
def hisob_button(m):
    if global_cb_limit(m.from_user.id): return
    if antiflood_cb(m.from_user.id, "hisobtoldirish2"): return
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
        m.chat.id,
        "⏳ Yuklanmoqda...",
    )
    get_hisob_text(bot_msg, m.from_user.id)

# REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START,
# REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START,
# REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START, REFERRAL SYSTEM START,

@bot.message_handler(func=lambda m: m.text == "👥Referral")
def my_ref(message):
    if global_cb_limit(message.from_user.id): return
    if antiflood_cb(message.from_user.id, "hisobtoldirish2"): return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    user_id = message.from_user.id

    cur.execute("SELECT COUNT(*) FROM users WHERE referred_by = ?", (user_id,))
    refs = cur.fetchone()[0]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('🏆Top takliflar', callback_data="top"))
    markup.add(types.InlineKeyboardButton('🏆Top haftalik takliflar', callback_data="top_week"))
    markup.add(types.InlineKeyboardButton("📊 Mening o‘rnim", callback_data="my_rank"))

    bot.send_message(
        message.chat.id,
        f"""🔗 <b>Sizning referal havolangiz:</b>

https://t.me/starsvanft3bot?start={user_id}

💸 Har bir taklifingiz uchun: <b>200 so‘m</b> beriladi.

🗣 Referallaringiz soni: <b>{refs} ta</b>
""",
        parse_mode="HTML",
        reply_markup=markup,
    )

# MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS,
# MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS,
# MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS, MAIN MENU ENDS,

@bot.callback_query_handler(func=lambda m: m.data == "top")
def referral_leaderboard(m):
    cur.execute("""
        SELECT u.user_id, u.first_name, COUNT(r.user_id) as ref_count
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL
        GROUP BY u.user_id
        ORDER BY ref_count DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    if not rows:
        bot.send_message(m.message.chat.id, "📭 Hozircha leaderboard bo‘sh")
        return

    text = "🏆 <b>TOP-10 eng ko'p odam taklif qilganlar</b>\n\n"

    medals = ["🥇", "🥈", "🥉"]

    for i, (user_id, name, count) in enumerate(rows, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        earned = count * 200
        text += f"{medal} {name} — {count} ta | 💸 {earned} so‘m\n"

    bot.send_message(m.message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['top_admin'])
def leaderboard_admin(message):
    if message.from_user.id != ADMIN_ID:
        return

    cur.execute("""
        SELECT u.user_id, u.first_name, COUNT(r.user_id) as ref_count
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL
        GROUP BY u.user_id
        ORDER BY ref_count DESC
        LIMIT 10
    """)

    rows = cur.fetchall()

    text = "👮 <b>TOP-10 Referral (ADMIN)</b>\n\n"

    for i, (uid, name, count) in enumerate(rows, 1):
        text += f"{i}. {name} | ID: {uid} | {count} ta\n"

    bot.send_message(message.chat.id, text, parse_mode="HTML")

def give_referral_bonus(user_id):
    cur.execute("""
        SELECT referred_by, ref_bonus_given FROM users WHERE user_id = ?
    """, (user_id,))
    row = cur.fetchone()

    if not row:
        return

    referred_by, bonus_given = row

    if referred_by and bonus_given == 0:
        add_balance(referred_by, sum_to_tiyin(200))

        cur.execute("""
            UPDATE users 
            SET ref_bonus_given = 1,
                ref_time = ?
            WHERE user_id = ?
        """, (int(time.time()), user_id))

        conn.commit()

        try:
            bot.send_message(
                referred_by,
                "🎉 Referalingiz ro‘yxatdan o‘tdi!\n💸 Sizga +200 so‘m berildi."
            )
        except:
            pass

@bot.callback_query_handler(func=lambda c: c.data == "top_week")
def weekly_leaderboard(c):
    if antiflood_cb(c.from_user.id, "top_week"):
        return

    bot.answer_callback_query(c.id)

    week_ago = int(time.time()) - 7 * 24 * 60 * 60

    cur.execute("""
        SELECT u.user_id, u.first_name, COUNT(r.user_id) as ref_count
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL
          AND r.ref_time >= ?
        GROUP BY u.user_id
        ORDER BY ref_count DESC
        LIMIT 10
    """, (week_ago,))

    rows = cur.fetchall()

    if not rows:
        bot.send_message(c.message.chat.id, "📭 Bu hafta hali referallar yo‘q")
        return

    text = "📅 <b>HAFTALIK TOP-10 takliflar</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (uid, name, count) in enumerate(rows, 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        text += f"{medal} {name} — {count} ta\n"

    bot.send_message(c.message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['myrank'])
def my_rank(message):
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return
    user_id = message.from_user.id
    week_ago = int(time.time()) - 7 * 24 * 60 * 60

    # ===== HAFTALIK RANK =====
    cur.execute("""
        SELECT u.user_id, COUNT(r.user_id) as cnt
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL
          AND r.ref_time >= ?
        GROUP BY u.user_id
        ORDER BY cnt DESC
    """, (week_ago,))
    weekly = cur.fetchall()

    weekly_rank = "—"
    for i, (uid, _) in enumerate(weekly, 1):
        if uid == user_id:
            weekly_rank = i
            break

    # ===== ALL-TIME RANK =====
    cur.execute("""
        SELECT u.user_id, COUNT(r.user_id) as cnt
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL
        GROUP BY u.user_id
        ORDER BY cnt DESC
    """)
    alltime = cur.fetchall()

    all_rank = "—"
    for i, (uid, _) in enumerate(alltime, 1):
        if uid == user_id:
            all_rank = i
            break

    bot.send_message(
        message.chat.id,
        f"""📊 <b>Sizning rankingiz</b>

📅 Haftalik: <b>{weekly_rank}</b>
🏆 All-time: <b>{all_rank}</b>
""",
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda c: c.data == "my_rank")
def my_rank_cb(c):
    bot.answer_callback_query(c.id)
    fake_msg = c.message
    my_rank(fake_msg)

def weekly_top3_bonus():
    week_ago = int(time.time()) - 7 * 24 * 60 * 60

    cur.execute("""
        SELECT u.user_id, u.first_name, COUNT(r.user_id) as cnt
        FROM users u
        JOIN users r ON r.referred_by = u.user_id
        WHERE r.phone IS NOT NULL AND r.ref_time >= ?
        GROUP BY u.user_id
        HAVING COUNT(r.user_id) >= 3
        ORDER BY cnt DESC
        LIMIT 3
    """, (week_ago,))

    winners = cur.fetchall()
    if not winners:
        # bonus bermaslik
        return

    rewards = [5000, 3000, 1000]
    text = "📅 <b>Haftalik TOP-3 g‘oliblar</b>\n\n"

    for i, (uid, name, count) in enumerate(winners):
        # bonus berish
        add_balance(uid, sum_to_tiyin(rewards[i]))
        text += f"{i+1}. {name} — {count} ta referral | 💸 +{rewards[i]} so‘m\n"

        # userga dm berish
        try:
            bot.send_message(uid, f"🏆 Siz haftalik TOP-{i+1} bo‘ldingiz!\n💸 +{rewards[i]} so‘m sizning hisobingizga qo‘shildi!")
        except:
            pass

    # Kanalga elon
    try:
        bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    except:
        pass


# REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END,
# REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END,
# REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END, REFERRAL SYSTEM END,

# 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS,
# 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS,
# 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS, 2ND MENU STARTS,

@bot.message_handler(func=lambda m: m.text == "↩️Orqaga")
def orqaga(call):
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "back_button"): return
    if is_banned(call.from_user.id):
        bot.reply_to(call.message.chat.id, "🚫 Siz ban qilingansiz")
        return

    show_main_menu(call)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def show_main_menu_callback(call):
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "back"): return

    bot.answer_callback_query(call.id)

    try:
        bot.delete_message(call.message_id, call.message.id)
    except:
        pass

    show_main_menu(call)

def stars_markup(bot_message):
    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton("100🌟(30 399,00 UZS)", callback_data="open2:q")
    btn2 = types.InlineKeyboardButton("150🌟(41 999,00 UZS)", callback_data="open2:w")
    btn3 = types.InlineKeyboardButton("250🌟(64 999,00 UZS)", callback_data="open2:e")
    btn4 = types.InlineKeyboardButton("350🌟(88 999,00 UZS)", callback_data="open2:r")
    btn5 = types.InlineKeyboardButton("500🌟(127 999,00 UZS)", callback_data="open2:t")
    btn6 = types.InlineKeyboardButton("750🌟(185 999,00 UZS)", callback_data="open2:y")
    btn7 = types.InlineKeyboardButton("1000🌟(243 999,00 UZS)", callback_data="open2:u")
    btn8 = types.InlineKeyboardButton("1500🌟(359 999,00 UZS)", callback_data="open2:i")
    btn9 = types.InlineKeyboardButton("2500🌟(599 999,00 UZS)", callback_data="open2:o")
    btn10 = types.InlineKeyboardButton("5000🌟(1 199 999,00 UZS)", callback_data="open2:p")
    btn11 = types.InlineKeyboardButton("10000🌟(2 499 999,00 UZS)", callback_data="open2:a")
    btn12 = types.InlineKeyboardButton("25000🌟(5 999 999,00 UZS)", callback_data="open2:s")
    btn13 = types.InlineKeyboardButton("50000🌟(12 599 999,00 UZS)", callback_data="open2:d")
    btn14 = types.InlineKeyboardButton("100000🌟(23 999 999,00 UZS)", callback_data="open2:f")
    btn15 = types.InlineKeyboardButton("150000🌟(36 999 999,00 UZS)", callback_data="open2:g")
    btn16 = types.InlineKeyboardButton("↩️ Orqaga", callback_data="back")

    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5, btn6)
    markup.row(btn7, btn8)
    markup.row(btn9, btn10)
    markup.row(btn11, btn12)
    markup.row(btn13, btn14)
    markup.row(btn15, btn16)

    bot.edit_message_text(
        "🌟 Iltimos o'zingizga kerakli bo'lgan stars miqdorini belgilang",
        bot_message.chat.id,
        bot_message.message_id,
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "🌟Stars sotib olish")
def open_stars(m):
    if antiflood(m.from_user.id, "stars"):
        return
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
        m.chat.id,
        "⏳ Yuklanmoqda...",
    )
    stars_markup(bot_msg)

def gifts_markup():
    markup = types.InlineKeyboardMarkup()

    markup.row(
    types.InlineKeyboardButton("❤️ Yurakcha (15⭐) - 5.000 so'm", callback_data="open:heart"),
    types.InlineKeyboardButton("🧸 Ayiqcha (15⭐) - 5.000 so'm", callback_data="open:toy")
    )
    markup.row(
    types.InlineKeyboardButton("🎁 Sovg'a (25⭐) - 8.000 so'm", callback_data="open:gift"),
    types.InlineKeyboardButton("🌹 Atirgul (25⭐) - 8.000 so'm", callback_data="open:rose")
    )
    markup.row(
    types.InlineKeyboardButton("🍰 To'rt (50⭐) - 14.000 so'm", callback_data="open:cake"),
    types.InlineKeyboardButton("💐 Buket Gul (50⭐) - 14.000 so'm", callback_data="open:flowers")
    )
    markup.row(
    types.InlineKeyboardButton("🚀 Raketa (50⭐) - 14.000 so'm", callback_data="open:rocket"),
    types.InlineKeyboardButton("🍾 Vino (50⭐) - 14.000 so'm", callback_data="open:bottle")
    )
    markup.row(
    types.InlineKeyboardButton("🏆 Kubok (100⭐) - 29.000 so'm", callback_data="open:trophy"),
    types.InlineKeyboardButton("💍 Uzuk (100⭐) - 29.000 so'm", callback_data="open:ring")
    )
    markup.row(
    types.InlineKeyboardButton("💎 Olmos (100⭐) - 29.000 so'm", callback_data="open:diamond"),
    types.InlineKeyboardButton("↩️ Orqaga", callback_data="back")
    )
    return markup

def open_gift_inline(bot_message):
    bot.edit_message_text(
        '👇 Quyidagi giftlardan birini tanlang',
        chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        reply_markup=gifts_markup(),
    )

@bot.message_handler(func=lambda m: m.text == "🎁Giftlar")
def open_gifts(m):
    if antiflood(m.from_user.id, "gift"):
        return
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
        m.chat.id,
        "⏳ Yuklanmoqda...",
    )
    open_gift_inline(bot_msg)

@bot.callback_query_handler(func=lambda c: c.data == "back2")
def back_gifts(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="👇 Quyidagi giftlardan birini tanlang",
        reply_markup=gifts_markup()
    )
#NFT
# def send_nft_inline(message):
#     markup = types.InlineKeyboardMarkup()
#
#     # btn1 = types.InlineKeyboardButton("Snoop Dogg (420+⭐) - 120.000 so'm", callback_data="snoopdogg")
#     # btn2 = types.InlineKeyboardButton("Swag Bag (420+⭐) - 120.000 so'm", callback_data="swagbag")
#     # btn3 = types.InlineKeyboardButton("Ice Cream (260+⭐) - 80.000 so'm", callback_data="icecream")
#     # btn4 = types.InlineKeyboardButton("Faith Amulet (390+⭐) - 90.000 so'm", callback_data="amulet")
#     # btn5 = types.InlineKeyboardButton("Moon Pendant (420+⭐) - 120.000 so'm", callback_data="moon")
#     # btn6 = types.InlineKeyboardButton("Clover Pin (370+⭐) - 100.000 so'm", callback_data="clover")
#     # btn7 = types.InlineKeyboardButton("Money Pot (350+⭐) - 100.000 so'm", callback_data="moneypot")
#     # btn8 = types.InlineKeyboardButton("🍾 Vino (50⭐) - 14.000 so'm", callback_data="bottle")
#     # btn9 = types.InlineKeyboardButton("🏆 Kubok (100⭐) - 29.000 so'm", callback_data="trophy")
#     # btn10 = types.InlineKeyboardButton("💍 Uzuk (100⭐) - 29.000 so'm", callback_data="ring")
#     # btn11 = types.InlineKeyboardButton("💎 Olmos (100⭐) - 29.000 so'm", callback_data="diamond")
#     # btn12 = types.InlineKeyboardButton("↩️ Orqaga", callback_data="back3")
#
#     # markup.add(btn12)
#     # markup.row(btn1, btn2)
#     # markup.row(btn3, btn4)
#     # markup.row(btn5, btn6)
#     # markup.row(btn7, btn12)
#
#     bot.send_message(
#         message.chat.id,
#         "❗️Tez Kunda",
#         reply_markup=markup,
#     )

def prem_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        '✅1 Oylik premium (akkauntga kirib) - 41.000 so\'m',
        callback_data='open3:premium_one'
    ))
    markup.add(types.InlineKeyboardButton(
        '✅3 Oylik premium (akkauntga kirmasdan) - 165.000 so\'m',
        callback_data='open3:premium_three'
    ))
    markup.add(types.InlineKeyboardButton(
        '✅6 Oylik premium (akkauntga kirmasdan) - 219.000 so\'m',
        callback_data='open3:premium_six'
    ))
    markup.add(types.InlineKeyboardButton(
        '✅12 Oylik premium (akkauntga kirmasdan) - 389.000 so\'m',
        callback_data='open3:premium_dozen'
    ))
    markup.add(types.InlineKeyboardButton(
        '↩️ Orqaga',
        callback_data='back'
    ))
    return markup

def open_prem_inline(bot_message):
    bot.edit_message_text(
        "👇 Quyidagi xizmatlardan birini tanlang.",
        chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        reply_markup=prem_markup()
    )

@bot.message_handler(func=lambda m: m.text == "✅Telegram premium")
def open_prem(m):
    if antiflood(m.from_user.id, "premium"):
        return
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
        m.chat.id,
        "⏳ Yuklanmoqda...",
    )
    open_prem_inline(bot_msg)

@bot.callback_query_handler(func=lambda c: c.data == "back1")
def back_prem(call):
    bot.answer_callback_query(call.id)

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="👇 Quyidagi giftlardan birini tanlang",
        reply_markup=prem_markup()
    )

@bot.callback_query_handler(func=lambda call: call.data in button_actions_gift)
def handle_gifts(call):
    bot.answer_callback_query(call.id)
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "action"): return

    button_actions_gift[call.data](call.message)

@bot.message_handler(func=lambda message: message.text == "🎟Promocode")
def promocode_start(message):
    if antiflood(message.from_user.id, "promocode"):
        return
    if is_banned(message.from_user.id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    bot.send_message(
        message.chat.id,
        f"🫴Marhamat <code>PROMOCODE</code> ni kiriting.\n\n"
        f"👇siz promocode larni ushbu kanaldan olishingiz mumkin.\n"
        f"https://t.me/woldevs",
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    bot.register_next_step_handler(message, promocode_apply)

PROMO_CODE = "woldev"
PROMO_REWARD = 200  # so'm
PROMO_EXPIRE = datetime(2026, 1, 7)

used_promos = {}


def promocode_apply(message):
    user_id = message.from_user.id
    promo = message.text.strip()

    if antiflood(user_id, "promocode"):
        return
    if is_banned(user_id):
        bot.reply_to(message, "🚫 Siz ban qilingansiz")
        return

    if datetime.now() > PROMO_EXPIRE:
        bot.send_message(message.chat.id, "❌ Promo code muddati tugagan.")
        return

    if promo != PROMO_CODE:
        bot.send_message(message.chat.id, "❌ Noto'g'ri promo code.")
        return

    if has_used_promo(user_id, PROMO_CODE):
        bot.send_message(message.chat.id, "❌ Siz allaqachon bu promo code ni ishlatdingiz.")
        return

    price_tiyin = sum_to_tiyin(PROMO_REWARD)
    add_balance(user_id, price_tiyin)
    add_used_promo(user_id, PROMO_CODE)

    bot.send_message(
        message.chat.id,
        f"✅ Siz promo code ishlatdingiz.\n💸 Hisobingizga +{PROMO_REWARD} so'm qo'shildi",
    )

# 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS,
# 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS,
# 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS, 2ND MENU ENDS,


# WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW
# WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW

PREM = {
    'premium_one':{
        'name': '✅1 Oylik premium',
        'price': 41000,
        'status': 'Akkauntga kirib olinadi',
        'time': 1,
    },
    'premium_three':{
        'name': '✅3 Oylik premium',
        'price': 165000,
        'status': 'Akkauntga kirmasdan olinadi',
        'time': 3
    },
    'premium_six':{
        'name': '✅6 Oylik premium',
        'price': 219000,
        'status': 'Akkauntga kirmasdan olinadi',
        'time': 6
    },
    'premium_dozen':{
        'name': '✅12 Oylik premium',
        'price': 389000,
        'status': 'Akkauntga kirmasdan olinadi',
        'time': 12
    }
}

@bot.callback_query_handler(func=lambda call: call.data.startswith("open3:"))
def open_premium_handler(call):
    bot.answer_callback_query(call.id)

    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "open3"): return

    item_key = call.data.split(":")[1]
    show_prem_page(call.message, item_key, call.from_user.id)

def show_prem_page(message, item_key, user_id):
    if item_key not in PREM:
        bot.edit_message_text("❌ Noma'lum mahsulot", message.chat.id,
            message.message_id)
        return

    balance = get_balance(user_id)
    tiyin = tiyin_to_sum(balance)
    item = PREM[item_key]
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data=f"buy3:{item_key}"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "↩️ Orqaga",
            callback_data="back1"
        )
    )
    bot.edit_message_text(
        f"""{item['name']}
<b>🏷 Modeli: yo'q</b>
<b>✅ olinish usuli:</b> {item['status']}
<b>⏳ Muddati:</b> {item['time']}
<b>💰 Narxi:</b> {item['price']} so'm

<b>💳 Sizning hisobingiz: {tiyin} so'm</b>

<b>👆Quyidagilar bilan tanishib chiqib 'tasdiqlash' tugmasini bosing</b>
""",
        message.chat.id,
        message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy3:"))
def universal_buy_handler3(call):
    bot.answer_callback_query(call.id)
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "buy3"): return

    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    update_username(user_id, username)

    item_key = call.data.split(":")[1]
    if item_key not in PREM:
        bot.send_message(call.message.chat.id, "❌ Noma'lum mahsulot")
        return

    item = PREM[item_key]
    price_som = item["price"]
    price_tiyin = sum_to_tiyin(price_som)

    if subtract_balance(user_id, price_tiyin):
        new_balance = get_balance(user_id)
        balance_display = tiyin_to_sum(new_balance)
        balance_display = f"{balance_display:,}".replace(",", ".")

        bot.edit_message_text(
            f"""🎉 <b>Xarid tasdiqlandi!</b>
⏳ Bajarilish vaqti: 10-240 daqiqa
💳 Qolgan balans: <b>{balance_display} so'm</b>
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        Timer(
            2.0,
            bot.send_message,
            args=(
                6067312074,
                f"""🎉 <b>Xarid tasdiqlandi!</b>
{item['name']}
💰 Narxi: {price_som} so'm
👤Buyurtma egasi: @{username}
🆔ID: <code>{user_id}</code>
📅Buyurtma sanasi: {now}
💳 Qolgan balans: <b>{balance_display} so'm</b>
"""
            ),
            kwargs={"parse_mode": "HTML"}
        ).start()

    else:
        bot.send_message(call.message.chat.id, "❌ Hisobingizda yetarli mablag' mavjud emas!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    show_main_menu(call)


GIFTS = {
    "heart":{
        "name": "❤️Telegram yurakcha gift",
        "price": 5000,
        "stars": 15,
        "convert": 13
    },
    "toy":{
        "name": "🧸Telegram ayiqcha gift",
        "price": 5000,
        "stars": 15,
        "convert": 13
    },
    "gift":{
        "name": "🎁Telegram sovg'a gift",
        "price": 8000,
        "stars": 25,
        "convert": 21
    },
    "rose":{
        "name": "🌹Telegram atirgul gift",
        "price": 8000,
        "stars": 25,
        "convert": 21
    },
    "cake":{
        "name": "🍰Telegram to'rt gift",
        "price": 14000,
        "stars": 50,
        "convert": 42
    },
    "flowers": {
        "name":" 💐Telegram buket gul gift",
        "price": 14000,
        "stars": 50,
        "convert": 42
    },
    "rocket":{
        "name": "🚀Telegram raketa gift",
        "price": 14000,
        "stars": 50,
        "convert": 42
    },
    "bottle": {
        "name": "🍾Telegram vino gift",
        "price": 14000,
        "stars": 50,
        "convert": 42
    },
    "trophy": {
        "name": "🏆Telegram kubok gift",
        "price": 29000,
        "stars": 100,
        "convert": 85
    },
    "ring": {
        "name": "💍Telegram uzuk gift",
        "price": 29000,
        "stars": 100,
        "convert": 85
    },
    "diamond": {
        "name": "💎Telegram olmos gift",
        "price": 29000,
        "stars": 100,
        "convert": 85
    },


}

@bot.callback_query_handler(func=lambda call: call.data.startswith("open:"))
def open_gift_handler(call):
    bot.answer_callback_query(call.id)

    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "open"): return

    item_key = call.data.split(":")[1]

    show_gift_page(call.message, item_key, call.from_user.id)

def show_gift_page(message, item_key, user_id):
    if item_key not in GIFTS:
        bot.edit_message_text("❌ Noma'lum mahsulot", message.chat.id,
            message.message_id)
        return

    balance = get_balance(user_id)
    tiyin = tiyin_to_sum(balance)
    item = GIFTS[item_key]

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "✅ Tasdiqlash",
            callback_data=f"buy:{item_key}"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "↩️ Orqaga",
            callback_data="back2"
        )
    )

    bot.edit_message_text(
        f"""{item['name']}
<b>🏷 Modeli: yo'q</b>
<b>🌟 Yulduzdagi narxi:</b> {item['stars']}
<b>🌟 Yulduzga aylantirish:</b> {item['convert']}
<b>⏳ Bajarilish vaqti:</b> 30–240 daqiqa(0.5-4 soat)
<b>💰 Narxi:</b> {item['price']} so'm

<b>💳 Sizning hisobingiz: {tiyin} so'm</b>

<b>👆Quyidagilar bilan tanishib chiqib 'tasdiqlash' tugmasini bosing</b>
""",
        message.chat.id,
        message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy:"))
def universal_buy_handler(call):
    bot.answer_callback_query(call.id)
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "buy"): return

    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    update_username(user_id, username)

    item_key = call.data.split(":")[1]
    if item_key not in GIFTS:
        bot.send_message(call.message.chat.id, "❌ Noma'lum mahsulot")
        return

    item = GIFTS[item_key]
    price_som = item["price"]
    price_tiyin = sum_to_tiyin(price_som)

    if subtract_balance(user_id, price_tiyin):
        new_balance = get_balance(user_id)
        balance_display = tiyin_to_sum(new_balance)
        balance_display = f"{balance_display:,}".replace(",", ".")

        bot.edit_message_text(
            f"""🎉 <b>Xarid tasdiqlandi!</b>
⏳ Bajarilish vaqti: 10-240 daqiqa
💳 Qolgan balans: <b>{balance_display} so'm</b>
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        Timer(
            2.0,
            bot.send_message,
            args=(
                6067312074,
                f"""🎉 <b>Xarid tasdiqlandi!</b>
{item['name']}
💰 Narxi: {price_som} so'm
👤Buyurtma egasi: @{username}
🆔ID: <code>{user_id}</code>
📅Buyurtma sanasi: {now}
💳 Qolgan balans: <b>{balance_display} so'm</b>
"""
            ),
            kwargs={"parse_mode": "HTML"}
        ).start()
    else:
        bot.send_message(call.message.chat.id, "❌ Hisobingizda yetarli mablag' mavjud emas!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    show_main_menu(call)

STARS = {
    "q":{
        "name": "🌟Telegram 100 star",
        "price": 30399,
        "stars": 100,
    },
    "w":{
        "name": "🌟Telegram 150 star",
        "price": 41999,
        "stars": 150,
    },
    "e":{
        "name": "🌟Telegram 250 star",
        "price": 64999,
        "stars": 250,
    },
    "r":{
        "name": "🌟Telegram 350 star",
        "price": 88999,
        "stars": 350,
    },
    "t":{
        "name": "🌟Telegram 500 star",
        "price": 127999,
        "stars": 500,
    },
    "y":{
        "name": "🌟Telegram 750 star",
        "price": 185999,
        "stars": 750,
    },
    "u":{
        "name": "🌟Telegram 1.000 star",
        "price": 243999,
        "stars": 1000,
    },
    "i":{
        "name": "🌟Telegram 1.500 star",
        "price": 359999,
        "stars": 1500,
    },
    "o":{
        "name": "🌟Telegram 2.500 star",
        "price": 599999,
        "stars": 2500,
    },
    "p":{
        "name": "🌟Telegram 5.000 star",
        "price": 1199999,
        "stars": 5000,
    },
    "a":{
        "name": "🌟Telegram 10.000 star",
        "price": 2499999,
        "stars": 10000,
    },
    "s":{
        "name": "🌟Telegram 25.000 star",
        "price": 5999999,
        "stars": 25000,
    },
    "d":{
        "name": "🌟Telegram 50.000 star",
        "price": 12599999,
        "stars": 50000,
    },
    "f":{
        "name": "🌟Telegram 100.000 star",
        "price": 23999999,
        "stars": 100000,
    },
    "g":{
        "name": "🌟Telegram 150.000 star",
        "price": 36999999,
        "stars": 150000,
    }

}

@bot.callback_query_handler(func=lambda call: call.data.startswith("open2:"))
def open_stars_handler(call):
    bot.answer_callback_query(call.id)
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "open2"): return

    item_key = call.data.split(":")[1]

    show_stars_page(call.message, item_key, call.from_user.id)

def show_stars_page(message, item_key, user_id):
    if item_key not in STARS:
        bot.send_message(message.chat.id, "❌ Noma'lum mahsulot")
        return

    balance = get_balance(user_id)
    item = STARS[item_key]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash",callback_data=f"buy2:{item_key}"))
    markup.add(types.InlineKeyboardButton("↩️ Orqaga",callback_data="back3"))

    bot.edit_message_text(
        f"""<b>{item['name']}</b>
<b>🏷Modeli:</b> yo'q
<b>⏳Bajarilish vaqti:</b> 30-240 daqiqa
<b>💰Narxi:</b> {item['price']}
<b>💳Sizning hisobingiz:</b> {balance}

<b>👆Shu ma'lumotlar bilan tanishib chiqib 'tasdiqlash' tugmasini bosing</b>
""",
        message.chat.id,
        message.message_id,
        parse_mode="HTML",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy2:"))
def universal_buy_handler2(call):
    bot.answer_callback_query(call.id)
    if global_cb_limit(call.from_user.id): return
    if antiflood_cb(call.from_user.id, "buy"): return

    user_id = call.from_user.id
    username = call.from_user.username or "NoUsername"
    update_username(user_id, username)

    item_key = call.data.split(":")[1]
    if item_key not in STARS:
        bot.send_message(call.message.chat.id, "❌ Noma'lum mahsulot")
        return

    item = STARS[item_key]
    price_som = item["price"]
    price_tiyin = sum_to_tiyin(price_som)
    id = call.from_user.id

    if subtract_balance(user_id, price_tiyin):
        new_balance = get_balance(user_id)
        balance_display = tiyin_to_sum(new_balance)
        balance_display = f"{balance_display:,}".replace(",", ".")
        bot.edit_message_text(
            f"""🎉 <b>Xarid tasdiqlandi!</b>
⏳ Bajarilish vaqti: 10-240 daqiqa
💳 Qolgan balans: <b>{balance_display} so'm</b>
""",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML"
        )

        Timer(
            2.0,
            bot.send_message,
            args=(
                6067312074,
                f"""🎉 <b>Xarid tasdiqlandi!</b>

{item['name']}
💰 Narxi: {price_som} so'm
⏳ Bajarilish vaqti: 30-240 daqiqa
👤Buyurtma egasi: @{username}
🆔ID: <code>{id}</code>
📅Buyurtma sanasi: {now}

💳 Qolgan balans: <b>{balance_display} so'm</b>
"""
            ),
            kwargs={
                "parse_mode": "HTML"
            }
        ).start()

    else:
        bot.send_message(call.message.chat.id, "❌ Hisobingizda yetarli mablag' mavjud emas!")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
    show_main_menu(call)

# WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW WW
def faq(bot_message):
    markup = types.InlineKeyboardMarkup()
    # markup.add(types.InlineKeyboardButton("✅ BOT", url="https://t.me/yordamchifaqbot"))
    markup.add(types.InlineKeyboardButton("☎️ Admin", url="https://t.me/wolframxm"))
    markup.add(types.InlineKeyboardButton("↩️ Orqaga", callback_data="back"))

    bot.edit_message_text(
        # "✅ BOT tugmasini bosib qo‘llab-quvvatlovchi botga o‘tishingiz mumkin.\n\n"
        "☎️ Admin tugmasini bosib adminga murojaat qilishingiz mumkin.",
        chat_id=bot_message.chat.id,
        message_id=bot_message.message_id,
        reply_markup=markup
    )

button_actions_gift = {
    "back2": gifts_markup,
    "back3": stars_markup,
    'back1': open_prem
}

@bot.message_handler(func=lambda m: m.text == "❓Qo'llab-Quvvatlash")
def handle_text_buttons(m):
    if antiflood(m.from_user.id, "faq"):
        return
    if is_banned(m.from_user.id):
        bot.reply_to(m, "🚫 Siz ban qilingansiz")
        return

    bot_msg = bot.send_message(
    m.chat.id,
    "⏳ Yuklanmoqda...",
    )
    faq(bot_msg)

bot.polling(none_stop=True)

