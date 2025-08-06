import telebot
import time
import datetime
from telebot import types
import MetaTrader5 as mt5

# ================= CONFIG =====================
BOT_TOKEN = '7721803001:AAFNnxixf7y-hnto6COrqwWn9b72Ov7p1hc'
SUPER_ADMIN_ID = 7015203619
ADMINS = [7015203619, 7805523169, 1599494951]

MT5_LOGIN = 400452722
MT5_PASSWORD = '200054828aA*'
MT5_SERVER = 'XMGlobal-MT5 15'

CARDS = {
    "MasterCard": "5217395903176537",
    "Uzcard": "5614683510367204",
    "Humo": "9860350118562171",
    "Name": "Bekhruzbek Z."
}

SUBSCRIPTIONS = {
    "trial": {"price": 30, "duration": 30},
    "1month": {"price": 50, "duration": 30},
    "5months": {"price": 100, "duration": 150},
    "12months": {"price": 200, "duration": 365},
    "lifetime": {"price": 1000, "duration": 9999}
}

users = {}
blocked_users = set()

bot = telebot.TeleBot(BOT_TOKEN)

# ================ MT5 Connection ===============
def connect_mt5():
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print("MT5ga ulanishda xatolik:", mt5.last_error())
        return False
    print("MT5ga muvaffaqiyatli ulandi.")
    return True

# ================ Obuna Tekshirish =============
def check_subscription(user_id):
    user = users.get(user_id)
    if not user or user_id in blocked_users:
        return False
    expire = user.get("expires")
    if expire and expire > time.time():
        return True
    return False

# ================ Start Komandasi ==============
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    if user_id not in users:
        now = time.time()
        trial_days = SUBSCRIPTIONS["trial"]["duration"] * 86400
        users[user_id] = {"expires": now + trial_days, "subscription": "trial"}
        bot.reply_to(message, "👋 Xush kelibsiz! Sizga 1 oylik BEPUL sinov muddati taqdim etildi.")
    else:
        bot.reply_to(message, "👋 Xush kelibsiz qaytadan!")

# ================ Obuna Holati ================
@bot.message_handler(commands=['subscription'])
def handle_subscription(message):
    user_id = message.from_user.id
    if check_subscription(user_id):
        sub = users[user_id]['subscription']
        remaining = int((users[user_id]['expires'] - time.time()) / 86400)
        bot.reply_to(message, f"✅ Obunangiz: {sub}\n⏳ Tugashiga: {remaining} kun")
    else:
        bot.reply_to(message, "❌ Obunangiz tugagan. Yangilash uchun /buy ni bosing.")

# ================ Obuna Sotib Olish ===========
@bot.message_handler(commands=['buy'])
def handle_buy(message):
    markup = types.InlineKeyboardMarkup()
    for key, val in SUBSCRIPTIONS.items():
        if key == 'trial': continue
        btn = types.InlineKeyboardButton(f"{key} - ${val['price']}", callback_data=f"buy_{key}")
        markup.add(btn)
    bot.send_message(message.chat.id, "💳 Qaysi obunani tanlaysiz?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_payment_option(call):
    sub_type = call.data.split("_")[1]
    amount = SUBSCRIPTIONS[sub_type]['price']
    pay_text = f"💰 To'lov summasi: ${amount}\n\nTo'lov kartalari:\n"
    for k, v in CARDS.items():
        pay_text += f"{k}: {v}\n"
    pay_text += "\n📤 To'lovni tasdiqlash uchun to'lov screenshotini yuboring."
    users[call.from_user.id]['pending'] = sub_type
    bot.send_message(call.from_user.id, pay_text)

# =============== Screenshot Qabul =============
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    if user_id not in users or 'pending' not in users[user_id]:
        bot.reply_to(message, "📸 Sizda tasdiqlanadigan obuna mavjud emas.")
        return
    for admin in ADMINS:
        bot.forward_message(admin, message.chat.id, message.message_id)
        bot.send_message(admin, f"✅ Yangi to'lov tasdig'i\nUser: {user_id}\nObuna: {users[user_id]['pending']}")
    bot.reply_to(message, "⏳ To'lov tasdiqlash uchun yuborildi. 24 soat ichida tasdiqlanadi.")

# ============== Admin Tasdig'i ================
@bot.message_handler(commands=['approve'])
def approve_user(message):
    if message.from_user.id not in ADMINS:
        return
    try:
        args = message.text.split()
        user_id = int(args[1])
        sub_type = users[user_id]['pending']
        duration = SUBSCRIPTIONS[sub_type]['duration'] * 86400
        users[user_id]['expires'] = time.time() + duration
        users[user_id]['subscription'] = sub_type
        users[user_id].pop('pending', None)
        bot.send_message(user_id, f"🎉 To'lov tasdiqlandi! Obuna: {sub_type}")
        bot.reply_to(message, "✅ Foydalanuvchi tasdiqlandi.")
    except:
        bot.reply_to(message, "❌ Format: /approve user_id")

# =============== Statistika ===================
@bot.message_handler(commands=['stats'])
def handle_stats(message):
    if message.from_user.id != SUPER_ADMIN_ID:
        return
    total = len(users)
    active = sum(1 for u in users.values() if u['expires'] > time.time())
    pending = sum(1 for u in users.values() if 'pending' in u)
    bot.reply_to(message, f"👥 Foydalanuvchilar: {total}\n✅ Faollar: {active}\n⏳ Kutilayotgan to'lovlar: {pending}")

# ================ Polling =====================
def main():
    connect_mt5()
    bot.polling(non_stop=True)

if __name__ == '__main__':
    main()
