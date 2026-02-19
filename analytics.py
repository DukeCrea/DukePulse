"""
📊 Analytics Module — PostFlow AI
==================================
Obtiene métricas de publicaciones de Instagram y Facebook vía Graph API,
y genera reportes con análisis y recomendaciones usando IA.
"""

import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

logger = logging.getLogger(__name__)

# Config from environment
FACEBOOK_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AI_PROVIDER = "claude" if ANTHROPIC_API_KEY else ("openai" if OPENAI_API_KEY else None)

GRAPH_API_VERSION = "v22.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
TZ_PANAMA = ZoneInfo("America/Panama")


# ─── HTTP Client ──────────────────────────────────────────────
_http_client = None

async def _get_http():
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0))
    return _http_client


# ═══════════════════════════════════════════════════════════════
#  INSTAGRAM METRICS
# ═══════════════════════════════════════════════════════════════

async def get_ig_recent_media(limit: int = 10) -> list:
    """Obtiene las últimas publicaciones de Instagram con métricas básicas."""
    client = await _get_http()
    try:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{INSTAGRAM_ACCOUNT_ID}/media",
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count,permalink",
                "limit": limit,
                "access_token": FACEBOOK_PAGE_TOKEN,
            }
        )
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo media IG: {e}")
        return []


async def get_ig_media_insights(media_id: str, media_type: str = "IMAGE") -> dict:
    """Obtiene insights detallados de un post de Instagram."""
    client = await _get_http()

    # Métricas dependen del tipo de contenido
    if media_type in ("VIDEO", "REELS"):
        metrics = "reach,plays,likes,comments,shares,saved,total_interactions"
    elif media_type == "CAROUSEL_ALBUM":
        metrics = "reach,impressions,likes,comments,shares,saved,total_interactions"
    else:  # IMAGE
        metrics = "reach,impressions,likes,comments,shares,saved,total_interactions"

    try:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{media_id}/insights",
            params={
                "metric": metrics,
                "access_token": FACEBOOK_PAGE_TOKEN,
            }
        )
        data = resp.json()
        insights = {}
        for item in data.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            insights[name] = values[0].get("value", 0) if values else 0
        return insights
    except Exception as e:
        logger.error(f"Error insights IG {media_id}: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
#  FACEBOOK METRICS
# ═══════════════════════════════════════════════════════════════

async def get_fb_recent_posts(limit: int = 10) -> list:
    """Obtiene los últimos posts de Facebook con métricas."""
    client = await _get_http()
    try:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{FACEBOOK_PAGE_ID}/posts",
            params={
                "fields": "id,message,created_time,full_picture,permalink_url,"
                          "shares,reactions.summary(true),comments.summary(true)",
                "limit": limit,
                "access_token": FACEBOOK_PAGE_TOKEN,
            }
        )
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo posts FB: {e}")
        return []


async def get_fb_post_insights(post_id: str) -> dict:
    """Obtiene insights de un post de Facebook."""
    client = await _get_http()
    try:
        resp = await client.get(
            f"{GRAPH_BASE_URL}/{post_id}/insights",
            params={
                "metric": "post_impressions,post_impressions_unique,"
                          "post_engaged_users,post_clicks",
                "access_token": FACEBOOK_PAGE_TOKEN,
            }
        )
        data = resp.json()
        insights = {}
        for item in data.get("data", []):
            name = item.get("name", "")
            values = item.get("values", [{}])
            insights[name] = values[0].get("value", 0) if values else 0
        return insights
    except Exception as e:
        logger.error(f"Error insights FB {post_id}: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
#  COMPILE REPORT DATA
# ═══════════════════════════════════════════════════════════════

async def compile_metrics(num_posts: int = 10) -> dict:
    """Recopila métricas de IG y FB en un solo diccionario."""
    report = {"instagram": [], "facebook": [], "timestamp": datetime.now(TZ_PANAMA).isoformat()}

    # Instagram
    ig_posts = await get_ig_recent_media(num_posts)
    for post in ig_posts:
        media_id = post.get("id", "")
        media_type = post.get("media_type", "IMAGE")
        insights = await get_ig_media_insights(media_id, media_type)

        caption = post.get("caption", "")
        if len(caption) > 100:
            caption = caption[:100] + "..."

        report["instagram"].append({
            "id": media_id,
            "caption": caption,
            "type": media_type,
            "timestamp": post.get("timestamp", ""),
            "likes": post.get("like_count", 0),
            "comments": post.get("comments_count", 0),
            "reach": insights.get("reach", 0),
            "impressions": insights.get("impressions", 0),
            "saves": insights.get("saved", 0),
            "shares": insights.get("shares", 0),
            "plays": insights.get("plays", 0),
            "total_interactions": insights.get("total_interactions", 0),
            "permalink": post.get("permalink", ""),
        })

    # Facebook
    fb_posts = await get_fb_recent_posts(num_posts)
    for post in fb_posts:
        post_id = post.get("id", "")
        insights = await get_fb_post_insights(post_id)

        message = post.get("message", "")
        if len(message) > 100:
            message = message[:100] + "..."

        reactions = post.get("reactions", {}).get("summary", {}).get("total_count", 0)
        comments = post.get("comments", {}).get("summary", {}).get("total_count", 0)
        shares = post.get("shares", {}).get("count", 0)

        report["facebook"].append({
            "id": post_id,
            "message": message,
            "timestamp": post.get("created_time", ""),
            "reactions": reactions,
            "comments": comments,
            "shares": shares,
            "impressions": insights.get("post_impressions", 0),
            "reach": insights.get("post_impressions_unique", 0),
            "engaged_users": insights.get("post_engaged_users", 0),
            "clicks": insights.get("post_clicks", 0),
            "permalink": post.get("permalink_url", ""),
        })

    return report


# ═══════════════════════════════════════════════════════════════
#  AI ANALYSIS
# ═══════════════════════════════════════════════════════════════

async def _ai_analyze(metrics_json: str) -> str:
    """Usa IA para analizar métricas y dar recomendaciones."""
    prompt = f"""Eres un experto en marketing digital y analítica de redes sociales.
Analiza estas métricas de publicaciones recientes en Instagram y Facebook y genera un reporte
actionable en español. Usa emojis para hacer el reporte visual y fácil de leer.

DATOS DE MÉTRICAS:
{metrics_json}

GENERA UN REPORTE CON ESTA ESTRUCTURA:

📊 *RESUMEN GENERAL*
- Rendimiento general (bueno/regular/bajo)
- Totales: alcance, interacciones, engagement rate promedio

📸 *TOP 3 PUBLICACIONES* (las de mejor rendimiento)
- Por qué funcionaron bien

⚠️ *PUBLICACIONES CON BAJO RENDIMIENTO*
- Qué se puede mejorar

💡 *RECOMENDACIONES*
1. Copy: ¿Qué tipo de textos generan más engagement?
2. Horarios: ¿Los horarios actuales son efectivos?
3. Contenido: ¿Qué tipo de contenido funciona mejor?
4. Hashtags: ¿Sugerencias de mejora?
5. Frecuencia: ¿Se publica mucho o poco?

📈 *PLAN DE ACCIÓN* (3 acciones concretas para la próxima semana)

Sé conciso pero específico. Basa tus recomendaciones en los datos reales.
Responde SOLO con el reporte, sin explicaciones adicionales."""

    client = await _get_http()

    try:
        if AI_PROVIDER == "claude":
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60
            )
            return resp.json()["content"][0]["text"].strip()

        elif AI_PROVIDER == "openai":
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60
            )
            return resp.json()["choices"][0]["message"]["content"].strip()

        else:
            return _generate_basic_report_text(json.loads(metrics_json))

    except Exception as e:
        logger.error(f"Error análisis IA: {e}")
        return _generate_basic_report_text(json.loads(metrics_json))


def _generate_basic_report_text(metrics: dict) -> str:
    """Genera un reporte básico sin IA cuando no hay API key disponible."""
    txt = "📊 *REPORTE DE PUBLICACIONES*\n\n"

    # Instagram
    ig = metrics.get("instagram", [])
    if ig:
        total_reach = sum(p.get("reach", 0) for p in ig)
        total_likes = sum(p.get("likes", 0) for p in ig)
        total_comments = sum(p.get("comments", 0) for p in ig)
        total_saves = sum(p.get("saves", 0) for p in ig)

        txt += f"📸 *Instagram* ({len(ig)} publicaciones)\n"
        txt += f"  👁 Alcance total: {total_reach:,}\n"
        txt += f"  ❤️ Likes: {total_likes:,}\n"
        txt += f"  💬 Comentarios: {total_comments:,}\n"
        txt += f"  🔖 Guardados: {total_saves:,}\n"
        if total_reach > 0:
            eng_rate = ((total_likes + total_comments + total_saves) / total_reach) * 100
            txt += f"  📈 Engagement: {eng_rate:.1f}%\n"
        txt += "\n"

        # Top post
        best = max(ig, key=lambda p: p.get("likes", 0) + p.get("comments", 0))
        txt += f"  ⭐ *Mejor post:* {best.get('likes', 0)} ❤️ + {best.get('comments', 0)} 💬\n"
        txt += f"     _{best.get('caption', 'Sin caption')}_\n\n"

    # Facebook
    fb = metrics.get("facebook", [])
    if fb:
        total_reach_fb = sum(p.get("reach", 0) for p in fb)
        total_reactions = sum(p.get("reactions", 0) for p in fb)
        total_comments_fb = sum(p.get("comments", 0) for p in fb)
        total_shares = sum(p.get("shares", 0) for p in fb)

        txt += f"📘 *Facebook* ({len(fb)} publicaciones)\n"
        txt += f"  👁 Alcance total: {total_reach_fb:,}\n"
        txt += f"  👍 Reacciones: {total_reactions:,}\n"
        txt += f"  💬 Comentarios: {total_comments_fb:,}\n"
        txt += f"  🔄 Compartidos: {total_shares:,}\n"
        if total_reach_fb > 0:
            eng_rate_fb = ((total_reactions + total_comments_fb + total_shares) / total_reach_fb) * 100
            txt += f"  📈 Engagement: {eng_rate_fb:.1f}%\n"
        txt += "\n"

        best_fb = max(fb, key=lambda p: p.get("reactions", 0) + p.get("comments", 0))
        txt += f"  ⭐ *Mejor post:* {best_fb.get('reactions', 0)} 👍 + {best_fb.get('comments', 0)} 💬\n"
        txt += f"     _{best_fb.get('message', 'Sin mensaje')}_\n\n"

    if not ig and not fb:
        txt += "❌ No se pudieron obtener métricas. Verifica los tokens de acceso.\n"

    txt += f"\n🕐 Reporte generado: {datetime.now(TZ_PANAMA).strftime('%d/%m/%Y %H:%M')} (hora Panamá)"
    return txt


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API — called from bot.py
# ═══════════════════════════════════════════════════════════════

async def get_full_report(num_posts: int = 10) -> str:
    """Genera el reporte completo: obtiene métricas + análisis IA."""
    metrics = await compile_metrics(num_posts)

    # Si hay datos, usar IA para análisis
    ig_count = len(metrics.get("instagram", []))
    fb_count = len(metrics.get("facebook", []))

    if ig_count == 0 and fb_count == 0:
        return (
            "📊 *Reporte de analítica*\n\n"
            "❌ No se encontraron publicaciones recientes.\n\n"
            "Esto puede deberse a:\n"
            "• No hay publicaciones aún\n"
            "• El token de acceso expiró\n"
            "• Las credenciales son incorrectas\n\n"
            "Usa /estado para verificar las conexiones."
        )

    metrics_json = json.dumps(metrics, ensure_ascii=False, indent=2)
    report = await _ai_analyze(metrics_json)

    header = (
        f"📊 *Reporte de Analítica — PostFlow AI*\n"
        f"🇵🇦 {datetime.now(TZ_PANAMA).strftime('%d/%m/%Y %H:%M')} (Panamá)\n"
        f"📸 IG: {ig_count} posts | 📘 FB: {fb_count} posts\n"
        f"{'─' * 30}\n\n"
    )

    return header + report
