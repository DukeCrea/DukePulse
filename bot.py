"""
💓 DukePulse — Analytics Bot
============================
Bot de Telegram que monitorea y analiza el rendimiento de tus redes sociales.
Se integra con PostFlow AI vía N8N para tracking automático de publicaciones.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
from aiohttp import web

try:
    import analytics
except ImportError:
    analytics = None

load_dotenv()

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "duke-secret-key-2024")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

TZ_PANAMA = ZoneInfo("America/Panama")
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

USERS_FILE = DATA_DIR / "authorized_users.json"
POSTS_DB = DATA_DIR / "tracked_posts.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_authorized_users() -> set:
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return {ADMIN_USER_ID}

def save_authorized_users(users: set):
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f, indent=2)

authorized_users = load_authorized_users()

def is_authorized(user_id: int) -> bool:
    return user_id in authorized_users


def load_tracked_posts() -> dict:
    if POSTS_DB.exists():
        try:
            with open(POSTS_DB, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_tracked_posts(posts: dict):
    with open(POSTS_DB, 'w') as f:
        json.dump(posts, f, indent=2, ensure_ascii=False)

tracked_posts = load_tracked_posts()


async def add_tracked_post(post_data: dict):
    post_id = post_data.get("post_id")
    if not post_id:
        logger.error("Post sin ID")
        return
    
    tracked_posts[post_id] = {
        **post_data,
        "tracked_since": datetime.now(TZ_PANAMA).isoformat(),
        "snapshots": []
    }
    save_tracked_posts(tracked_posts)
    logger.info(f"✅ Post {post_id} agregado")


async def cmd_start(update: Update, context):
    uid = update.effective_user.id
    if not is_authorized(uid):
        await update.message.reply_text(
            f"⛔ No autorizado. Tu ID: `{uid}`",
            parse_mode="Markdown"
        )
        return
    
    keyboard = [
        [InlineKeyboardB"""
💓 DukePulse — Analytics Bot
============================
Bot de Telegram que monitorea y analiza el rendimiento de tus redes sociales.
Se integra con PostFlow AI vía N8N para tracking automático de publicaciones.

Funcionalidades:
- Reportes automáticos (diario/semanal/mensual)
- Monitoreo en tiempo real de posts
- Alertas de bajo rendimiento
- Predicciones con IA
- Webhook para N8N
"""

import os
import json
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
from aiohttp import web

# Importar módulo de analytics (lo crearemos después)
try:
    import analytics
except ImportError:
    analytics = None

load_dotenv()

# ─── Config ───────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Token del bot DukePulse
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "duke-secret-key-2024")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

# Zona horaria Panamá
TZ_PANAMA = ZoneInfo("America/Panama")

# Directorio para datos
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
#  AUTORIZACIÓN
# ═══════════════════════════════════════════════════════════════

def load_authorized_users() -> set:
    """Carga usuarios autorizados desde JSON."""
    if USERS_FILE.exists():
        try:
            with open(USERS_FILE, 'r') as f:
                return set(json.load(f))
        except:
            pass
    return {ADMIN_USER_ID}

def save_authorized_users(users: set):
    """Guarda usuarios autorizados a JSON."""
    with open(USERS_FILE, 'w') as f:
        json.dump(list(users), f, indent=2)

authorized_users = load_authorized_users()


def is_authorized(user_id: int) -> bool:
    """Verifica si un usuario está autorizado."""
    return user_id in authorized_users


# ═══════════════════════════════════════════════════════════════
#  TRACKING DE POSTS
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
    """Agrega un nuevo post para tracking.
    
    Args:
        post_data: {
            "post_id": "ig_post_123",
            "platform": "instagram",
            "published_at": "2024-02-19T10:00:00",
            "copy": "texto del post...",
            "media_url": "https://...",
        }
    """
    post_id = post_data.get("post_id")
    if not post_id:
        logger.error("Post sin ID, no se puede trackear")
        return
    
    tracked_posts[post_id] = {
        **post_data,
        "tracked_since": datetime.now(TZ_PANAMA).isoformat(),
        "snapshots": []  # Métricas cada 2 horas
    }
    save_tracked_posts(tracked_posts)
    logger.info(f"✅ Post {post_id} agregado al tracking")


# ═══════════════════════════════════════════════════════════════
#  COMANDOS DEL BOT
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
    
    user_name = update.effective_user.first_name
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
    
    await update.message.reply_text("📊 Generando reporte... (esto toma ~10s)")
    
    try:
        if analytics:
            report = await analytics.get_full_report(num_posts=10)
            await update.message.reply_text(report, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "⚠️ Módulo de analytics no disponible.\n"
                "Asegúrate de tener `analytics.py` configurado."
            )
    except Exception as e:
        logger.error(f"Error generando reporte: {e}")
        await update.message.reply_text(f"❌ Error generando reporte: {e}")


async def cmd_estado(update: Update, context):
    """Comando /estado - Estado del sistema."""
    uid = update.effective_user.id
    if not is_authorized(uid):
        return
    
    # Verificar conexiones
    fb_ok = "✅" if os.getenv("FACEBOOK_PAGE_TOKEN") else "❌"
    ig_ok = "✅" if os.getenv("INSTAGRAM_ACCOUNT_ID") else "❌"
    ai_ok = "✅" if os.getenv("ANTHROPIC_API_KEY") else "❌"
    n8n_ok = "✅" if WEBHOOK_SECRET else "❌"
    
    txt = (
        f"⚙️ *Estado del Sistema — DukePulse*\n\n"
        f"🤖 Bot: ✅ Activo\n"
        f"📘 Facebook: {fb_ok}\n"
        f"📸 Instagram: {ig_ok}\n"
        f"🧠 Claude AI: {ai_ok}\n"
        f"🔗 N8N Webhook: {n8n_ok}\n"
        f"📊 Posts trackeados: {len(tracked_posts)}\n"
        f"👥 Usuarios autorizados: {len(authorized_users)}\n\n"
        f"🕐 {datetime.now(TZ_PANAMA).strftime('%d/%m/%Y %H:%M')} (Panamá)"
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
        copy_preview = data.get("copy", "")[:50] + "..."
        
        txt += f"{i}. {platform.upper()}\n"
        txt += f"   📅 {published}\n"
        txt += f"   📝 {copy_preview}\n\n"
    
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
            "Uso: `/autorizar USER_ID`\n\n"
            "El usuario debe enviar un mensaje a @userinfobot para obtener su ID.",
            parse_mode="Markdown"
        )
        return
    
    try:
        new_uid = int(context.args[0])
        authorized_users.add(new_uid)
        save_authorized_users(authorized_users)
        await update.message.reply_text(f"✅ Usuario {new_uid} autorizado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido. Debe ser un número.")


async def cmd_desautorizar(update: Update, context):
    """Comando /desautorizar [user_id] - Remover usuario (solo admin)."""
    uid = update.effective_user.id
    if uid != ADMIN_USER_ID:
        await update.message.reply_text("⛔ Solo el administrador puede desautorizar usuarios.")
        return
    
    if not context.args:
        await update.message.reply_text("Uso: `/desautorizar USER_ID`", parse_mode="Markdown")
        return
    
    try:
        rem_uid = int(context.args[0])
        if rem_uid == ADMIN_USER_ID:
            await update.message.reply_text("❌ No puedes desautorizar al administrador.")
            return
        
        if rem_uid in authorized_users:
            authorized_users.remove(rem_uid)
            save_authorized_users(authorized_users)
            await update.message.reply_text(f"✅ Usuario {rem_uid} desautorizado.")
        else:
            await update.message.reply_text(f"❌ Usuario {rem_uid} no estaba autorizado.")
    except ValueError:
        await update.message.reply_text("❌ ID inválido.")


# ═══════════════════════════════════════════════════════════════
#  CALLBACKS (botones inline)
# ═══════════════════════════════════════════════════════════════

async def button_callback(update: Update, context):
    """Handler para botones inline."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "report_now":
        await query.message.reply_text("📊 Generando reporte... (esto toma ~10s)")
        try:
            if analytics:
                report = await analytics.get_full_report(num_posts=10)
                await query.message.reply_text(report, parse_mode="Markdown")
            else:
                await query.message.reply_text("⚠️ Módulo de analytics no disponible.")
        except Exception as e:
            await query.message.reply_text(f"❌ Error: {e}")
    
    elif data == "tracked_list":
        await cmd_tracked(update, context)
    
    elif data == "system_status":
        await cmd_estado(update, context)
    
    elif data == "top_posts":
        await query.message.reply_text(
            "📈 *Top Posts*\n\n"
            "Esta funcionalidad se implementará en la siguiente fase.\n"
            "Por ahora, usa `/reporte` para ver el análisis completo.",
            parse_mode="Markdown"
        )
    
    elif data == "low_posts":
        await query.message.reply_text(
            "📉 *Posts con Bajo Rendimiento*\n\n"
            "Esta funcionalidad se implementará en la siguiente fase.",
            parse_mode="Markdown"
        )
    
    elif data == "prediction":
        await query.message.reply_text(
            "🔮 *Predicción Semanal*\n\n"
            "Esta funcionalidad usará IA para predecir los mejores días/horarios.\n"
            "Se implementará en la siguiente fase.",
            parse_mode="Markdown"
        )


# ═══════════════════════════════════════════════════════════════
#  N8N WEBHOOK SERVER
# ═══════════════════════════════════════════════════════════════

async def webhook_handler(request):
    """Recibe webhooks de N8N cuando PostFlow AI publica un post.
    
    Expected payload:
    {
        "secret": "duke-secret-key-2024",
        "event": "post_published",
        "data": {
            "post_id": "ig_123456",
            "platform": "instagram",
            "published_at": "2024-02-19T10:00:00",
            "copy": "Texto del post...",
            "media_url": "https://..."
        }
    }
    """
    try:
        payload = await request.json()
        
        # Verificar secret
        if payload.get("secret") != WEBHOOK_SECRET:
            logger.warning("⚠️ Webhook con secret inválido")
            return web.Response(status=401, text="Unauthorized")
        
        event = payload.get("event")
        data = payload.get("data", {})
        
        if event == "post_published":
            await add_tracked_post(data)
            logger.info(f"✅ Post {data.get('post_id')} recibido vía webhook")
            
            # Opcional: Notificar al admin
            if ADMIN_USER_ID:
                app = request.app['telegram_app']
                await app.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=f"🔔 *Nuevo post en tracking*\n\n"
                         f"📱 {data.get('platform', 'N/A').upper()}\n"
                         f"🕐 {data.get('published_at', 'N/A')}\n"
                         f"📝 {data.get('copy', '')[:100]}...",
                    parse_mode="Markdown"
                )
            
            return web.Response(status=200, text="OK")
        
        else:
            logger.warning(f"⚠️ Evento desconocido: {event}")
            return web.Response(status=400, text="Unknown event")
    
    except Exception as e:
        logger.error(f"❌ Error en webhook: {e}")
        return web.Response(status=500, text=str(e))


async def start_webhook_server(app):
    """Inicia servidor HTTP para webhooks de N8N."""
    logger.info(f"🔗 Webhook server iniciado en puerto {WEBHOOK_PORT}")
    logger.info(f"📥 Endpoint: http://localhost:{WEBHOOK_PORT}/webhook")


# ═══════════════════════════════════════════════════════════════
#  REPORTES AUTOMÁTICOS (APScheduler)
# ═══════════════════════════════════════════════════════════════

async def daily_report_job():
    """Job que se ejecuta diariamente a las 8:00 AM (Panamá)."""
    logger.info("📊 Ejecutando reporte diario...")
    
    try:
        if not analytics or not ADMIN_USER_ID:
            logger.warning("⚠️ Analytics o Admin ID no configurados")
            return
        
        report = await analytics.get_full_report(num_posts=10)
        
        # Enviar a admin
        app = Application.builder().token(TELEGRAM_TOKEN).build()
        await app.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=f"☀️ *Reporte Diario Automático*\n\n{report}",
            parse_mode="Markdown"
        )
        
        logger.info("✅ Reporte diario enviado")
    
    except Exception as e:
        logger.error(f"❌ Error en reporte diario: {e}")


def setup_scheduler(app):
    """Configura el scheduler de reportes automáticos."""
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///data/jobs.db')
    }
    
    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        timezone=TZ_PANAMA
    )
    
    # Reporte diario a las 8:00 AM
    scheduler.add_job(
        daily_report_job,
        'cron',
        hour=8,
        minute=0,
        id='daily_report',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("⏰ Scheduler iniciado — Reporte diario a las 8:00 AM")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    """Inicia el bot + webhook server."""
    
    # Banner
    print("\n" + "="*50)
    print("💓 DukePulse — Analytics Bot")
    print("="*50)
    print(f"🤖 Admin ID: {ADMIN_USER_ID}")
    print(f"📊 Posts trackeados: {len(tracked_posts)}")
    print(f"👥 Usuarios autorizados: {len(authorized_users)}")
    print(f"🔗 Webhook puerto: {WEBHOOK_PORT}")
    print(f"🕐 Zona horaria: {TZ_PANAMA}")
    print("="*50 + "\n")
    
    # Telegram Bot
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reporte", cmd_reporte))
    app.add_handler(CommandHandler("estado", cmd_estado))
    app.add_handler(CommandHandler("tracked", cmd_tracked))
    app.add_handler(CommandHandler("autorizar", cmd_autorizar))
    app.add_handler(CommandHandler("desautorizar", cmd_desautorizar))
    
    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Scheduler
    setup_scheduler(app)
    
    # Webhook Server (aiohttp)
    web_app = web.Application()
    web_app['telegram_app'] = app
    web_app.router.add_post('/webhook', webhook_handler)
    web_app.on_startup.append(start_webhook_server)
    
    runner = web.Runner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEBHOOK_PORT)
    await site.start()
    
    # Iniciar bot
    logger.info("🚀 DukePulse iniciado correctamente")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    
    # Mantener corriendo
    import asyncio
    await asyncio.Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
