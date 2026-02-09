import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)

# simpan mode user
user_mode = {}

SYSTEM_PROMPT = (
    "Kamu adalah bot curhat berbahasa Indonesia yang terasa seperti manusia, "
    "santai, tidak baku, tidak menggurui, dan tidak terdengar seperti AI, "
    "balasan HARUS satu kalimat panjang yang mengalir alami, "
    "jika user hanya curhat cukup tanggapi perasaannya, "
    "jika user minta solusi beri saran realistis dan kalem tanpa klise."
)

def butuh_solusi(text: str) -> bool:
    kata = ["gimana", "harus", "ngapain", "cara", "solusi", "ngelakuin"]
    return any(k in text.lower() for k in kata)

def panggil_gemini(prompt: str) -> str:
    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    res = requests.post(
        f"{GEMINI_URL}?key={GEMINI_API_KEY}",
        json=payload,
        timeout=30
    )

    data = res.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🤍 Perhatian", callback_data="perhatian"),
            InlineKeyboardButton("🧊 Dingin tapi peduli", callback_data="dingin")
        ],
        [
            InlineKeyboardButton("🧠 Reflektif", callback_data="reflektif"),
            InlineKeyboardButton("⚖️ Bebas", callback_data="bebas")
        ]
    ]

    await update.message.reply_text(
        "Gue di sini buat dengerin, pilih dulu cara gue nemenin lo.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# set mode
async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_mode[query.from_user.id] = query.data

    pesan = {
        "perhatian": "Oke, gue bakal jawab lebih hangat.",
        "dingin": "Sip, gue bakal jujur tanpa basa-basi.",
        "reflektif": "Oke, gue bakal ngajak lo mikir pelan.",
        "bebas": "Siap, gue jawab senatural mungkin."
    }

    await query.edit_message_text(pesan.get(query.data, "Siap."))

# chat utama
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    text = update.message.text

    mode = user_mode.get(uid)
    if not mode:
        await update.message.reply_text("Klik /start dulu ya.")
        return

    gaya = {
        "perhatian": "Gunakan nada sangat hangat dan empatik.",
        "dingin": "Gunakan nada tenang, dingin tapi peduli.",
        "reflektif": "Gunakan nada reflektif dengan pertanyaan halus.",
        "bebas": "Gunakan gaya ngobrol alami seperti teman."
    }

    status = "User minta solusi." if butuh_solusi(text) else "User hanya curhat."

    prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"{gaya[mode]}\n"
        f"{status}\n"
        f"Curhatan user: {text}"
    )

    try:
        reply = panggil_gemini(prompt)
        await update.message.reply_text(reply.strip())
    except Exception:
        await update.message.reply_text(
            "Gue lagi ke-distract sebentar, coba kirim ulang ya."
        )

# run bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(set_mode))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()
