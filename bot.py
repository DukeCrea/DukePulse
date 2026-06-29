"""
💓 DukePulse — Analytics Bot (sin webhook)
"""
import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from dotenv import load_dotenv

try:
    import analytics
except ImportError:
    analytics = None

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
TZ_PANAMA = ZoneInfo("America/Panama")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def cmd_start(update, context):
    await update.message.reply_text(
        f"💓 DukePulse\n\nHora: {datetime.now(TZ_PANAMA).strftime('%H:%M')}\n\nComandos:\n/reporte\n/estado"
    )

async def cmd_reporte(update, context):
    await update.message.reply_text("📊 Generando reporte...")
    try:
        if analytics:
            report = await analytics.get_full_report(10)
            await update.message.reply_text(report, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Analytics no disponible")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_estado(update, context):
    fb = "✅" if os.getenv("FACEBOOK_PAGE_TOKEN") else "❌"
    ig = "✅" if os.getenv("INSTAGRAM_ACCOUNT_ID") else "❌"
    ai = "✅" if os.getenv("ANTHROPIC_API_KEY") else "❌"
    await update.message.reply_text(f"⚙️ Estado\n\n🤖 Bot: ✅\n📘 FB: {fb}\n📸 IG: {ig}\n🧠 AI: {ai}")

def main():
    print("\n" + "="*50)
    print("💓 DukePulse Analytics Bot")
    print("="*50)
    print(f"Admin: {ADMIN_USER_ID}")
    print("="*50 + "\n")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("estado", cmd_estado))
    
    print("🚀 Bot iniciado. Presiona Ctrl+C para detener.\n")
    app.run_polling()

if __name__ == "__main__":
    main()
