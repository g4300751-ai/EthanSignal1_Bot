"""
All-in-One Converter & Utility Bot
No AI API used anywhere — pure logic + free, keyless APIs only.
Run locally with a .env file, or deploy to Railway using the Procfile.
"""
import logging
import os
from io import BytesIO

import cv2
import numpy as np
import qrcode
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import utils
from pdf_tools import merge_pdfs, split_pdf

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

HELP_TEXT = (
    "Here's everything I can do:\n\n"
    "/currency <amount> <from> <to> — e.g. /currency 100 USD EUR\n"
    "/unit <value> <from> <to> — e.g. /unit 10 km mi\n"
    "/time <HH:MM> <from_tz> <to_tz> — e.g. /time 14:30 Asia/Manila America/New_York\n"
    "/b64encode <text>\n"
    "/b64decode <text>\n"
    "/qr <text> — generates a QR code image\n"
    "Send me a photo containing a QR code and I'll read it for you\n"
    "/case <upper|lower|title|snake> <text>\n"
    "/count <text> — word and character count\n"
    "/password <length> — generates a strong password\n"
    "/shorten <url>\n"
    "/json <text> — formats and validates JSON\n"
    "/hash <text> — MD5, SHA1, SHA256\n"
    "/hex2rgb <hex> — e.g. /hex2rgb #1E90FF\n"
    "/rgb2hex <r> <g> <b> — e.g. /rgb2hex 30 144 255\n"
    "/age <YYYY-MM-DD>\n\n"
    "PDF tools:\n"
    "Send two or more PDF files, then type /mergepdf\n"
    "Send one PDF, then type /splitpdf <start> <end>\n"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome! I'm a free all-in-one utility bot — no sign-up needed.\n\n"
        "Type /help to see everything I can do."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /currency <amount> <from> <to>")
        return
    try:
        amount = float(args[0])
    except ValueError:
        await update.message.reply_text("Amount must be a number.")
        return
    result = utils.convert_currency(amount, args[1], args[2])
    await update.message.reply_text(result)


async def unit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /unit <value> <from_unit> <to_unit>")
        return
    try:
        value = float(args[0])
    except ValueError:
        await update.message.reply_text("Value must be a number.")
        return
    result = utils.convert_unit(value, args[1], args[2])
    await update.message.reply_text(result)


async def time_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "Usage: /time <HH:MM> <from_timezone> <to_timezone>\n"
            "Example: /time 14:30 Asia/Manila America/New_York"
        )
        return
    result = utils.convert_timezone(args[0], args[1], args[2])
    await update.message.reply_text(result)


async def b64encode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /b64encode <text>")
        return
    await update.message.reply_text(utils.b64_encode(text))


async def b64decode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /b64decode <text>")
        return
    await update.message.reply_text(utils.b64_decode(text))


async def qr_generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /qr <text or link>")
        return
    img = qrcode.make(text)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    await update.message.reply_photo(photo=buffer)


async def qr_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()
    np_arr = np.frombuffer(bytes(file_bytes), np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    detector = cv2.QRCodeDetector()
    data, points, _ = detector.detectAndDecode(img)

    if data:
        await update.message.reply_text(f"QR code content:\n{data}")
    else:
        await update.message.reply_text("No QR code found in that image.")


async def case_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: /case <upper|lower|title|snake> <text>"
        )
        return
    mode = args[0]
    text = " ".join(args[1:])
    await update.message.reply_text(utils.convert_case(text, mode))


async def count_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /count <text>")
        return
    await update.message.reply_text(utils.count_text(text))


async def password_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    length = 12
    if context.args:
        try:
            length = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Usage: /password <length>")
            return
    pwd = utils.generate_password(length)
    await update.message.reply_text(f"`{pwd}`", parse_mode=ParseMode.MARKDOWN)


async def shorten_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = " ".join(context.args)
    if not url:
        await update.message.reply_text("Usage: /shorten <url>")
        return
    await update.message.reply_text(utils.shorten_url(url))


async def json_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.partition(" ")[2]
    if not text:
        await update.message.reply_text("Usage: /json <json_text>")
        return
    result = utils.format_json(text)
    await update.message.reply_text(f"```\n{result}\n```", parse_mode=ParseMode.MARKDOWN)


async def hash_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: /hash <text>")
        return
    await update.message.reply_text(utils.hash_text(text))


async def hex2rgb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /hex2rgb <hex_code>")
        return
    await update.message.reply_text(utils.hex_to_rgb(context.args[0]))


async def rgb2hex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /rgb2hex <r> <g> <b>")
        return
    try:
        r, g, b = int(args[0]), int(args[1]), int(args[2])
    except ValueError:
        await update.message.reply_text("RGB values must be whole numbers.")
        return
    await update.message.reply_text(utils.rgb_to_hex(r, g, b))


async def age_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /age <YYYY-MM-DD>")
        return
    await update.message.reply_text(utils.calculate_age(context.args[0]))


# ---------- PDF handling ----------

async def receive_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    file = await document.get_file()
    file_bytes = await file.download_as_bytearray()

    pdf_list = context.user_data.setdefault("pdfs", [])
    pdf_list.append(bytes(file_bytes))

    await update.message.reply_text(
        f"PDF received ({len(pdf_list)} total). "
        "Send more, or type /mergepdf to combine them, "
        "or /splitpdf <start> <end> to split the most recent one."
    )


async def mergepdf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_list = context.user_data.get("pdfs", [])
    if len(pdf_list) < 2:
        await update.message.reply_text(
            "Send at least two PDF files first, then type /mergepdf."
        )
        return
    streams = [BytesIO(data) for data in pdf_list]
    try:
        merged = merge_pdfs(streams)
    except Exception as e:
        await update.message.reply_text(f"Could not merge PDFs: {e}")
        return
    await update.message.reply_document(document=merged, filename="merged.pdf")
    context.user_data["pdfs"] = []


async def splitpdf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdf_list = context.user_data.get("pdfs", [])
    if not pdf_list:
        await update.message.reply_text("Send a PDF file first, then use /splitpdf <start> <end>.")
        return
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /splitpdf <start_page> <end_page>")
        return
    try:
        start_page, end_page = int(args[0]), int(args[1])
    except ValueError:
        await update.message.reply_text("Page numbers must be whole numbers.")
        return

    stream = BytesIO(pdf_list[-1])
    try:
        result = split_pdf(stream, start_page, end_page)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return
    except Exception as e:
        await update.message.reply_text(f"Could not split PDF: {e}")
        return

    await update.message.reply_document(document=result, filename="split.pdf")


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("currency", currency))
    app.add_handler(CommandHandler("unit", unit))
    app.add_handler(CommandHandler("time", time_convert))
    app.add_handler(CommandHandler("b64encode", b64encode_cmd))
    app.add_handler(CommandHandler("b64decode", b64decode_cmd))
    app.add_handler(CommandHandler("qr", qr_generate))
    app.add_handler(CommandHandler("case", case_convert))
    app.add_handler(CommandHandler("count", count_cmd))
    app.add_handler(CommandHandler("password", password_cmd))
    app.add_handler(CommandHandler("shorten", shorten_cmd))
    app.add_handler(CommandHandler("json", json_cmd))
    app.add_handler(CommandHandler("hash", hash_cmd))
    app.add_handler(CommandHandler("hex2rgb", hex2rgb_cmd))
    app.add_handler(CommandHandler("rgb2hex", rgb2hex_cmd))
    app.add_handler(CommandHandler("age", age_cmd))
    app.add_handler(CommandHandler("mergepdf", mergepdf_cmd))
    app.add_handler(CommandHandler("splitpdf", splitpdf_cmd))

    app.add_handler(MessageHandler(filters.PHOTO, qr_scan))
    app.add_handler(MessageHandler(filters.Document.PDF, receive_pdf))

    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
