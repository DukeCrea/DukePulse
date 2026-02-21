"""
💓 DukePulse — Analytics Bot
============================
Bot de Telegram que monitorea y analiza el rendimiento de tus redes sociales.
Optimizado para deployar en Railway.

Flujo:
  N8N (PostFlow AI) → Webhook Duke Pulse → Tracking de posts → Reportes
"""

import os
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
from aiohttp import web

load_dotenv()

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "duke-secret-key-2024")

# Para Railway: el puerto viene de la env var PORT
PORT = int(os.getenv("PORT", "8080"))

# Hostname público de Railway (se configura en Railway dashboard)
RAILWAY_DOMAIN = os.getenv("RAILWAY_DOMAIN", "localhost")

TZ_PANAMA = ZoneInfo("America/Panama")

# Data persistence
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "authorized_users.json"
POSTS_DB = DATA_DIR / "tracked_posts.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# AUTORIZACIÓN
# ═══════════════════════════════════════════════════════════════

def load_authorized_users() -> set:
    """Carga usuarios autorizados desde JSON."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return {ADMIN_USER_ID} if ADMIN_USER_ID else set()

def save_authorized_users(users: set):
    """Guarda usuarios autorizados a JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f, indent=2)

authorized_users = load_authorized_users()

def is_authorized(user_id: int) -> bool:
    """Verifica si un usuario está autorizado."""
    return user_id in authorized_users


# ═══════════════════════════════════════════════════════════════
# TRACKING DE POSTS
# ═══════════════════════════════════════════════════════════════

def load_tracked_posts() -> dict:
    """Carga posts trackeados desde JSON."""
    if POSTS_DB.exists():
        try:
            with open(POSTS_DB, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_tracked_posts(posts: dict):
    """Guarda posts trackeados a JSON."""
    with open(POSTS_DB, 'w') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

tracked_posts = load_tracked_posts()


async def add_tracked_post(post_data: dict):
    """Agrega un nuevo post para tracking desde N8N.
    
    Args:
        post_data: {
            "post_id": "ig_post_123",
            "platform": "instagram",
            "published_at": "2024-02-19T10:00:00",
            "copy": "texto del post...",
            "media_url": "https://...",
            "content_type": "carousel|image|video|reel"
        }
    """
    post_id = post_data.get("post_id")
    if not post_id:
        logger.error("Post sin ID, no se puede trackear")
        return
    
    tracked_posts[post_id] = {
        **post_data,
        "tracked_since": datetime.now(TZ_PANAMA).isoformat(),
        "snapshots": []
    }
    save_tracked_posts(tracked_posts)
    logger.info(f"✅ Post {post_id} agregado al tracking")


# ═══════════════════════════════════════════════════════════════
# COMANDOS DEL BOT
# ═══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, context):
    """Comando /start - Menú principal."""
    uid = update.effective_user.id
    if not is_authorized(uid):
        await update.message.reply_text(
            "⛔ No estás autorizado para usar este bot.\n"
            f"Tu ID: `{uid}`\n\n"
            "Contacta al administrador para acceso.",
            parse_mode="Markdown"
        )
        return
    
    user_name = update.effective_user.first_name or "Usuario"
    keyboard = [
        [InlineKeyboardButton("📊 Reporte Instantáneo", callback_data="report_now")],
        [InlineKeyboardButton("📈 Top Posts", callback_data="top_posts"),
         InlineKeyboardButton("📉 Bajo Rendimiento", callback_data="low_posts")],
        [InlineKeyboardButton("🔮 Predicción Semanal", callback_data="prediction")],
        [InlineKeyboardButton("📋 Posts Trackeados", callback_data="tracked_list")],
        [InlineKeyboardButton("⚙️ Estado del Sistema", callback_data="system_status")],
    ]
    
    await update.message.reply_text(
        f"💓 *DukePulse — El pulso de tus redes*\n\n"
        f"¡Hola {user_name}! Estoy monitoreando tus redes sociales 24/7.\n\n"
        f"📊 Posts trackeados: {len(tracked_posts)}\n"
        f"🕐 Hora Panamá: {datetime.now(TZ_PANAMA).strftime('%H:%M')}\n\n"
        f"Selecciona una opción:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def cmd_reporte(update: Update, context):
    """Comando /reporte - Genera reporte instantáneo."""
    uid = update.effective_user.id
    if not is_authorized(uid):
        return
    
    if not tracked_posts:
        await update.message.reply_text(
            "📊 No hay posts en tracking aún.\n"
            "Los posts se agregarán cuando PostFlow AI publique vía N8N."
        )
        return
    
    txt = f"📊 *Reporte de Posts Trackeados*\n\n"
    txt += f"Total: {len(tracked_posts)}\n"
    txt += f"🕐 Generado: {datetime.now(TZ_PANAMA).strftime('%d/%m/%Y %H:%M')}\n\n"
    
    txt += "📋 *Últimos 5 posts:*\n\n"
    
    for i, (post_id, data) in enumerate(list(tracked_posts.items())[-5:], 1):
        platform = data.get("platform", "N/A").upper()
        published = data.get("published_at", "N/A")
        copy_preview = data.get("copy", "")[:50]
        
        txt += f"{i}. *{platform}*\n"
        txt += f"   📅 {published}\n"
        txt += f"   📝 {copy_preview}...\n"
        txt += f"   🔗 ID: `{post_id}`\n\n"
    
    await update.message.reply_text(txt, parse_mode="Markdown")


async def cmd_estado(update: Update, context):
    """Comando /estado - Estado del sistema."""
    uid = update.effective_user.id
    if not is_authorized(uid):
        return
    
    fb_ok = "✅" if os.getenv("FACEBOOK_PAGE_TOKEN") else "❌"
    ig_ok = "✅" if os.getenv("INSTAGRAM_ACCOUNT_ID") else "❌"
    ai_ok = "✅" if os.getenv("ANTHROPIC_API_KEY") else "❌"
    
    txt = (
        f"⚙️ *Estado del Sistema — DukePulse*\n\n"
        f"🤖 Bot: ✅ Activo\n"
        f"📘 Facebook: {fb_ok}\n"
        f"📸 Instagram: {ig_ok}\n"
        f"🧠 Claude AI: {ai_ok}\n"
        f"📊 Posts trackeados: {len(tracked_posts)}\n"
        f"👥 Usuarios autorizados: {len(authorized_users)}\n\n"
        f"🕐 {datetime.now(TZ_PANAMA).strftime('%d/%m/%Y %H:%M')} (Panamá)\n"
        f"🌐 Endpoint público: `{RAILWAY_DOMAIN}/webhook`"
    )
    
    await update.message.reply_text(txt, parse_mode="Markdown")


async def cmd_tracked(update: Update, context):
    """Comando /tracked - Lista posts siendo monitoreados."""
    uid = update.effective_user.id
    if not is_authorized(uid):
        return
    
    if not tracked_posts:
        await update.message.reply_text(
            "📋 No hay posts en tracking.\n\n"
            "Los posts se agregan automáticamente cuando PostFlow AI publica."
        )
        return
    
    txt = f"📋 *Posts en Tracking ({len(tracked_posts)})*\n\n"
    
    for i, (post_id, data) in enumerate(list(tracked_posts.items())[-10:], 1):
        platform = data.get("platform", "N/A")
        published = data.get("published_at", "")
        copy_preview = data.get("copy", "")[:40]
        
        txt += f"{i}. {platform.upper()}\n"
        txt += f"   📅 {published}\n"
        txt += f"   📝 {copy_preview}...\n\n"
    
    if len(tracked_posts) > 10:
        txt += f"_Mostrando últimos 10 de {len(tracked_posts)} totales_"
    
    await update.message.reply_text(txt, parse_mode="Markdown")


async def cmd_autorizar(update: Update, context):
    """Comando /autorizar [user_id] - Agregar usuario (solo admin)."""
    uid = update.effective_user.id
    if uid != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Solo el administrador puede autorizar usuarios.")
        return
    
    if not context.args:
        await update.message.reply_text(
            "Uso: `/autorizar USER_ID`",
            parse_mode="Markdown"
        )
        return
    
    try:
        new_uid = int(context.args[0])
        authorized_users.add(new_uid)
        save_authorized_users(authorized_users)
        await update.message.reply_text(f"✅ Usuario {new_uid} autorizado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")


# ═══════════════════════════════════════════════════════════════
# CALLBACKS (botones inline)
# ═══════════════════════════════════════════════════════════════

async def button_callback(update: Update, context):
    """Handler para botones inline."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "report_now":
        await query.message.reply_text("📊 Generando reporte...")
        await cmd_reporte(update, context)
    
    elif data == "tracked_list":
        await cmd_tracked(update, context)
    
    elif data == "system_status":
        await cmd_estado(update, context)
    
    elif data == "top_posts":
        await query.message.reply_text(
            "📈 *Top Posts*\n\n"
            "Mostrará los posts con mejor rendimiento.\n"
            "(Fase 2 — Coming soon)",
            parse_mode="Markdown"
        )
    
    elif data == "low_posts":
        await query.message.reply_text(
            "📉 *Posts con Bajo Rendimiento*\n\n"
            "Alertas automáticas cuando algo no funciona.\n"
            "(Fase 2 — Coming soon)",
            parse_mode="Markdown"
        )
    
    elif data == "prediction":
        await query.message.reply_text(
            "🔮 *Predicción Semanal*\n\n"
            "IA te dirá cuándo publicar.\n"
            "(Fase 2 — Coming soon)",
            parse_mode="Markdown"
        )


# ═══════════════════════════════════════════════════════════════
# N8N WEBHOOK SERVER
# ═══════════════════════════════════════════════════════════════

async def webhook_handler(request):
    """Recibe webhooks de N8N cuando PostFlow AI publica un post.
    
    Expected payload from N8N:
    {
        "secret": "duke-secret-key-2024",
        "event": "post_published",
        "data": {
            "post_id": "ig_123456",
            "platform": "instagram",
            "published_at": "2024-02-19T10:00:00",
            "copy": "Texto del post...",
            "media_url": "https://...",
            "content_type": "image|carousel|video|reel"
        }
    }
    """
    try:
        payload = await request.json()
        
        if payload.get("secret") != WEBHOOK_SECRET:
            logger.warning("⚠️ Webhook con secret inválido")
            return web.Response(status=401, text="Unauthorized")
        
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "post_published":
            await add_tracked_post(data)
            logger.info(f"✅ Post {data.get('post_id')} recibido vía webhook N8N")
            
            if ADMIN_USER_ID:
                try:
                    app = request.app['telegram_app']
                    await app.bot.send_message(
                        chat_id=ADMIN_USER_ID,
                        text=f"🔔 *Nuevo post en tracking*\n\n"
                             f"📱 {data.get('platform', 'N/A').upper()}\n"
                             f"🕐 {data.get('published_at', 'N/A')}\n"
                             f"📝 {data.get('copy', '')[:80]}...",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Error notificando admin: {e}")
            
            return web.Response(status=200, text=json.dumps({"ok": True}))
        
        else:
            logger.warning(f"⚠️ Evento desconocido: {event}")
            return web.Response(status=400, text="Unknown event")
    
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return web.Response(status=500, text=str(e))


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECK (para Railway)
# ═══════════════════════════════════════════════════════════════

async def health_check(request):
    """Endpoint para Health Check de Railway."""
    return web.Response(
        status=200,
        text=json.dumps({
            "status": "ok",
            "tracked_posts": len(tracked_posts),
            "timestamp": datetime.now(TZ_PANAMA).isoformat()
        }),
        content_type='application/json'
    )


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    """Inicia el bot + webhook server."""
    
    print("\n" + "="*60)
    print("💓 DukePulse — Analytics Bot")
    print("="*60)
    print(f"🤖 Admin ID: {ADMIN_USER_ID}")
    print(f"📊 Posts trackeados: {len(tracked_posts)}")
    print(f"👥 Usuarios autorizados: {len(authorized_users)}")
    print(f"🌐 Endpoint público: {RAILWAY_DOMAIN}/webhook")
    print(f"🔗 Puerto: {PORT}")
    print(f"🕐 Zona horaria: {TZ_PANAMA}")
    print("="*60 + "\n")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("tracked", cmd_tracked))
    app.add_handler(CommandHandler("autorizar", cmd_autorizar))
    
    app.add_handler(CallbackQueryHandler(button_callback))
    
    await app.initialize()
    await app.start()
    
    web_app = web.Application()
    web_app['telegram_app'] = app
    web_app.router.add_post('/webhook', webhook_handler)
    web_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    logger.info(f"🚀 DukePulse iniciado en puerto {PORT}")
    logger.info(f"📥 Webhook disponible en: {RAILWAY_DOMAIN}/webhook")
    logger.info(f"❤️ Health check en: {RAILWAY_DOMAIN}/health")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("🛑 Deteniendo DukePulse...")
        await app.stop()
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
