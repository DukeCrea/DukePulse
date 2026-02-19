# 💓 DukePulse — Analytics Bot

Bot de Telegram que monitorea y analiza el rendimiento de tus publicaciones en Instagram y Facebook. Se integra con **PostFlow AI** vía **N8N** para tracking automático.

---

## 🚀 Características

### ✅ Funcionalidades actuales (Fase 1):

- 📊 **Reportes on-demand** - Comando `/reporte` para análisis instantáneo
- ⏰ **Reportes automáticos** - Diarios a las 8:00 AM (Panamá)
- 📋 **Tracking de posts** - Monitorea publicaciones de PostFlow AI
- 🔗 **Webhook N8N** - Recibe notificaciones cuando PostFlow publica
- 👥 **Multi-usuario** - Sistema de autorización admin/usuarios
- ⚙️ **Sistema de estado** - Verifica conexiones con APIs

### 🔜 Próximamente (Fase 2):

- 📈 Top 10 mejores posts
- 📉 Alertas de bajo rendimiento
- 🔮 Predicciones con IA
- 📊 Métricas en tiempo real cada 2 horas
- 📅 Reportes semanales/mensuales personalizables

---

## 📦 Instalación

### 1. Crear bot en Telegram

Ve a [@BotFather](https://t.me/BotFather) y crea un nuevo bot:
```
/newbot
Nombre: DukePulse
Username: dukepulse_bot (o el que quieras)
```

Guarda el token que te da.

### 2. Configurar variables de entorno

Copia `.env.example` a `.env` y completa:

```bash
cp .env.example .env
nano .env
```

**Variables requeridas:**
- `TELEGRAM_TOKEN` - Token del bot DukePulse
- `ADMIN_USER_ID` - Tu ID de Telegram
- `WEBHOOK_SECRET` - Clave secreta para N8N
- `FACEBOOK_PAGE_TOKEN` - Token de tu página (mismo que PostFlow)
- `INSTAGRAM_ACCOUNT_ID` - ID de cuenta IG (mismo que PostFlow)
- `ANTHROPIC_API_KEY` - API key de Claude

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar localmente

```bash
python bot.py
```

Verás:
```
==================================================
💓 DukePulse — Analytics Bot
==================================================
🤖 Admin ID: 123456789
📊 Posts trackeados: 0
👥 Usuarios autorizados: 1
🔗 Webhook puerto: 8080
🕐 Zona horaria: America/Panama
==================================================

🔗 Webhook server iniciado en puerto 8080
📥 Endpoint: http://localhost:8080/webhook
⏰ Scheduler iniciado — Reporte diario a las 8:00 AM
🚀 DukePulse iniciado correctamente
```

---

## 🔗 Integración con N8N

### Workflow recomendado:

```
PostFlow AI publica post
    ↓
Trigger en PostFlow (webhook)
    ↓
N8N recibe datos
    ↓
N8N procesa y formatea
    ↓
POST a DukePulse webhook
    ↓
DukePulse empieza tracking
```

### Configurar N8N:

1. **Crear workflow nuevo** en N8N

2. **Node 1: Webhook Trigger**
   - Method: POST
   - Path: `/postflow-published`

3. **Node 2: Function**
   ```javascript
   return [{
     json: {
       secret: "duke-secret-key-2024",
       event: "post_published",
       data: {
         post_id: items[0].json.post_id,
         platform: items[0].json.platform,
         published_at: items[0].json.published_at,
         copy: items[0].json.copy,
         media_url: items[0].json.media_url
       }
     }
   }];
   ```

4. **Node 3: HTTP Request**
   - Method: POST
   - URL: `http://tu-dukepulse-url:8080/webhook`
   - Body: JSON (from previous node)

5. **Activar workflow**

---

## 🎮 Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Menú principal con botones |
| `/reporte` | Genera reporte instantáneo de últimos 10 posts |
| `/estado` | Verifica conexiones con APIs |
| `/tracked` | Lista posts siendo monitoreados |
| `/autorizar ID` | Agregar usuario (solo admin) |
| `/desautorizar ID` | Remover usuario (solo admin) |

---

## 🚂 Deploy en Railway

### Opción A: Desde GitHub

1. Sube este código a un repo de GitHub
2. En Railway: **New Project** → **Deploy from GitHub**
3. Selecciona el repo
4. Agrega variables de entorno en **Variables**
5. Deploy automático

### Opción B: Desde Railway CLI

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Crear proyecto
railway init

# Deploy
railway up

# Agregar variables
railway variables set TELEGRAM_TOKEN=...
railway variables set ADMIN_USER_ID=...
# ... etc
```

**⚠️ Importante:** En Railway, obtén la URL pública de tu servicio y úsala en N8N:
```
https://tu-proyecto.railway.app/webhook
```

---

## 📊 Reportes Automáticos

DukePulse genera reportes automáticos usando **APScheduler**:

| Frecuencia | Hora (Panamá) | Contenido |
|------------|---------------|-----------|
| **Diario** | 8:00 AM | Resumen últimas 24 horas |

**Próximamente:**
- Semanal (Lunes 9:00 AM)
- Mensual (día 1, 10:00 AM)

---

## 🔒 Seguridad

- ✅ Sistema de autorización por User ID
- ✅ Webhook protegido con secret key
- ✅ Solo admin puede autorizar usuarios
- ✅ Tokens en variables de entorno (nunca en código)

---

## 🐛 Troubleshooting

### Bot no responde

```bash
# Verifica que el token sea correcto
echo $TELEGRAM_TOKEN

# Verifica que el bot esté corriendo
ps aux | grep bot.py
```

### Webhook no recibe datos

```bash
# Verifica que el puerto esté abierto
curl http://localhost:8080/webhook

# Verifica logs
tail -f logs.log
```

### Reportes no se generan

```bash
# Verifica que analytics.py esté presente
ls -la analytics.py

# Verifica que las API keys estén configuradas
echo $ANTHROPIC_API_KEY
```

---

## 📁 Estructura del Proyecto

```
dukepulse/
├── bot.py                 # Bot principal + webhook server
├── analytics.py           # Módulo de métricas (de PostFlow)
├── requirements.txt       # Dependencias Python
├── Dockerfile             # Para Railway/Docker
├── railway.toml           # Config Railway
├── .env.example           # Template de variables
├── README.md              # Esta documentación
└── data/                  # Datos persistentes (auto-creado)
    ├── authorized_users.json
    ├── tracked_posts.json
    └── jobs.db
```

---

## 🔄 Roadmap

### Fase 1 (✅ Completada)
- [x] Bot básico con comandos
- [x] Integración N8N webhook
- [x] Reportes on-demand
- [x] Reportes automáticos diarios
- [x] Sistema de autorización

### Fase 2 (🔜 Próxima)
- [ ] Top/worst posts
- [ ] Alertas en tiempo real
- [ ] Predicciones con IA
- [ ] Métricas cada 2 horas
- [ ] Dashboard web (opcional)

### Fase 3 (💡 Futuro)
- [ ] Integración con Google Analytics
- [ ] Exportar reportes a PDF
- [ ] Comparación con competencia
- [ ] Sugerencias automáticas de mejora

---

## 🤝 Ecosistema DukeCrea

DukePulse es parte del ecosistema de automatización:

- **PostFlow AI** - Publicación automática IG/FB
- **DukePulse** - Analytics y monitoreo
- **N8N** - Orquestación de workflows

Próximamente:
- **DukeCurator** - Curación automática de contenido
- **DukeResponder** - Respuestas automáticas a comentarios

---

## 📄 Licencia

Software propietario. Todos los derechos reservados © 2024 DukeCrea
