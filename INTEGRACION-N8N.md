# 🔗 Guía de Integración: PostFlow AI ↔️ DukePulse via N8N

## 📋 Resumen

Esta guía te muestra cómo conectar **PostFlow AI** (bot publicador) con **DukePulse** (bot analista) usando **N8N** como orquestador.

---

## 🏗️ Arquitectura

```
┌─────────────────────┐
│   PostFlow AI       │
│   (Publisher Bot)   │
└──────────┬──────────┘
           │
           │ 1. Publica post en IG/FB
           │
           ▼
┌─────────────────────┐
│   Webhook Interno   │ (dentro de PostFlow)
│   trigger_n8n()     │
└──────────┬──────────┘
           │
           │ 2. HTTP POST
           │
           ▼
┌─────────────────────┐
│       N8N           │
│   (Orchestrator)    │
└──────────┬──────────┘
           │
           │ 3. Formatea datos
           │
           ▼
┌─────────────────────┐
│   DukePulse         │
│   (Analytics Bot)   │
│   /webhook          │
└──────────┬──────────┘
           │
           │ 4. Empieza tracking
           │
           ▼
┌─────────────────────┐
│   Meta Graph API    │
│   (IG + FB)         │
└─────────────────────┘
```

---

## 📝 Paso 1: Modificar PostFlow AI

### 1.1 Agregar función de notificación N8N

Edita `bot.py` de PostFlow AI y agrega esta función después de la sección de HTTP Client:

```python
# ─── N8N Integration ──────────────────────────────────────────
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/postflow-published")

async def notify_n8n(post_data: dict):
    """Notifica a N8N cuando se publica un post."""
    try:
        client = await get_http()
        resp = await client.post(
            N8N_WEBHOOK_URL,
            json=post_data,
            timeout=5
        )
        if resp.status_code == 200:
            logger.info(f"✅ N8N notificado: {post_data.get('post_id')}")
        else:
            logger.warning(f"⚠️ N8N respondió {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Error notificando N8N: {e}")
```

### 1.2 Llamar la función después de publicar

Busca la función donde se publica en Instagram/Facebook (probablemente en `Pub.post_instagram()` o similar) y agrega:

```python
# Después de publicar exitosamente
if post_id:  # Si la publicación fue exitosa
    await notify_n8n({
        "post_id": post_id,
        "platform": "instagram",  # o "facebook"
        "published_at": datetime.now(TZ_PANAMA).isoformat(),
        "copy": copy_text,
        "media_url": cloudinary_url,
        "metadata": {
            "marca": car.get("marca"),
            "modelo": car.get("modelo"),
            "año": car.get("año"),
            "precio": car.get("precio")
        }
    })
```

### 1.3 Agregar variable de entorno

En el `.env` de PostFlow:

```bash
N8N_WEBHOOK_URL=http://tu-n8n-url:5678/webhook/postflow-published
```

---

## 🔧 Paso 2: Configurar N8N

### 2.1 Instalar N8N (si no lo tienes)

**Opción A: Docker (recomendado)**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Opción B: npm**
```bash
npm install n8n -g
n8n start
```

Abre: http://localhost:5678

### 2.2 Crear el Workflow

1. **Login a N8N** → http://localhost:5678
2. **+ (New Workflow)**
3. **Importar el template:**
   - Click en "..." (menú)
   - "Import from File"
   - Selecciona `n8n-workflow-template.json`

O créalo manualmente:

#### Node 1: Webhook (Trigger)
- **Type:** Webhook
- **HTTP Method:** POST
- **Path:** `postflow-published`
- **Response Mode:** On Received

#### Node 2: Function (Transform)
```javascript
const postData = items[0].json;

return [{
  json: {
    secret: "duke-secret-key-2024",
    event: "post_published",
    data: {
      post_id: postData.post_id,
      platform: postData.platform,
      published_at: postData.published_at,
      copy: postData.copy,
      media_url: postData.media_url,
      metadata: postData.metadata || {}
    }
  }
}];
```

#### Node 3: HTTP Request
- **Method:** POST
- **URL:** `http://dukepulse-url:8080/webhook`
- **Body:** JSON
- **JSON:** `{{ $json }}`

### 2.3 Activar Workflow

- Click en el toggle "Active" (arriba derecha)
- Copia la URL del webhook (aparece en el node Webhook)

---

## 🤖 Paso 3: Desplegar DukePulse

### 3.1 Crear bot en Telegram

```
/newbot
Name: DukePulse
Username: dukepulse_bot
```

Guarda el token.

### 3.2 Configurar .env

```bash
cd dukepulse
cp .env.example .env
nano .env
```

Completa:
```bash
TELEGRAM_TOKEN=tu_token_dukepulse
ADMIN_USER_ID=tu_user_id
WEBHOOK_SECRET=duke-secret-key-2024
WEBHOOK_PORT=8080

# Mismo que PostFlow
FACEBOOK_PAGE_TOKEN=...
INSTAGRAM_ACCOUNT_ID=...
ANTHROPIC_API_KEY=...
```

### 3.3 Ejecutar localmente (testing)

```bash
pip install -r requirements.txt
python bot.py
```

### 3.4 Deploy en Railway (producción)

```bash
# Subir a GitHub
git init
git add .
git commit -m "Initial DukePulse"
git remote add origin https://github.com/tu-usuario/dukepulse.git
git push -u origin main

# En Railway
1. New Project
2. Deploy from GitHub
3. Seleccionar repo dukepulse
4. Add variables (todas las del .env)
5. Deploy
```

Obtén la URL pública (ej: `https://dukepulse-production.up.railway.app`)

---

## 🔗 Paso 4: Conectar todo

### 4.1 URLs finales

Anota las URLs de cada servicio:

```
PostFlow AI:     https://postflow.railway.app
N8N:             https://n8n.tu-dominio.com (o localhost:5678 si es local)
DukePulse:       https://dukepulse.railway.app
```

### 4.2 Actualizar variables

**En PostFlow `.env`:**
```bash
N8N_WEBHOOK_URL=https://n8n.tu-dominio.com/webhook/postflow-published
```

**En N8N workflow (Node HTTP Request):**
```
URL: https://dukepulse.railway.app/webhook
```

### 4.3 Verificar secret

Asegúrate que `WEBHOOK_SECRET` sea el MISMO en:
- DukePulse `.env`
- N8N Function node

---

## ✅ Paso 5: Probar la integración

### 5.1 Test end-to-end

1. **Publica un post desde PostFlow:**
   ```
   /publicar
   [envía foto]
   [genera copy]
   [publica]
   ```

2. **Verifica N8N:**
   - Ve a N8N → Executions
   - Deberías ver una ejecución nueva
   - Status: Success ✅

3. **Verifica DukePulse:**
   - Abre DukePulse en Telegram
   - `/tracked`
   - Deberías ver el nuevo post

4. **Verifica notificación:**
   - DukePulse te envía mensaje automático:
   ```
   🔔 Nuevo post en tracking
   📱 INSTAGRAM
   🕐 2024-02-19T10:00:00
   📝 [preview del copy]
   ```

### 5.2 Test del reporte

```
/reporte
```

Deberías recibir análisis de últimos 10 posts.

---

## 🐛 Troubleshooting

### PostFlow no notifica N8N

**Problema:** N8N no recibe webhooks.

**Solución:**
```bash
# Verifica que N8N esté corriendo
curl http://localhost:5678

# Verifica la URL en PostFlow
echo $N8N_WEBHOOK_URL

# Revisa logs de PostFlow
tail -f logs.log | grep "N8N"
```

### N8N no conecta con DukePulse

**Problema:** HTTP Request falla en N8N.

**Solución:**
```bash
# Verifica que DukePulse esté corriendo
curl http://dukepulse-url:8080/webhook

# Verifica que el secret sea correcto
# En N8N Function node debe ser: "duke-secret-key-2024"
# En DukePulse .env debe ser: WEBHOOK_SECRET=duke-secret-key-2024
```

### DukePulse rechaza webhook

**Problema:** 401 Unauthorized en logs de N8N.

**Solución:**
- Verifica que el `secret` en el payload sea correcto
- Debe coincidir con `WEBHOOK_SECRET` en DukePulse

---

## 📊 Flujo completo de datos

```json
// 1. PostFlow publica y envía a N8N
{
  "post_id": "ig_18105762367823",
  "platform": "instagram",
  "published_at": "2024-02-19T10:30:00-05:00",
  "copy": "🚗 Toyota Corolla 2022...",
  "media_url": "https://res.cloudinary.com/...",
  "metadata": {
    "marca": "Toyota",
    "modelo": "Corolla",
    "año": "2022",
    "precio": "18500"
  }
}

// 2. N8N formatea y envía a DukePulse
{
  "secret": "duke-secret-key-2024",
  "event": "post_published",
  "data": {
    "post_id": "ig_18105762367823",
    "platform": "instagram",
    "published_at": "2024-02-19T10:30:00-05:00",
    "copy": "🚗 Toyota Corolla 2022...",
    "media_url": "https://res.cloudinary.com/...",
    "metadata": { ... }
  }
}

// 3. DukePulse confirma recepción
HTTP 200 OK
```

---

## 🎯 Próximos pasos

Una vez funcionando la integración básica:

1. **Fase 2 de DukePulse:**
   - Tracking cada 2 horas
   - Alertas de bajo rendimiento
   - Predicciones con IA

2. **Webhooks adicionales:**
   - PostFlow → DukePulse: `post_scheduled`
   - PostFlow → DukePulse: `post_failed`
   - DukePulse → PostFlow: `low_performance_alert`

3. **Dashboard web:**
   - Streamlit o Gradio
   - Visualización de métricas
   - Acceso desde navegador

---

## 📞 Soporte

Si algo no funciona:

1. Revisa los logs de cada servicio
2. Verifica que todas las URLs estén correctas
3. Confirma que los secrets coincidan
4. Prueba cada componente individualmente

---

**¡Listo! Ahora tienes PostFlow AI y DukePulse trabajando juntos. 🚀**
