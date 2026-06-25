# Undercurrent — Guía de despliegue (GitHub + Render)

Esto te deja la web viva en internet, con su propia URL, corriendo 24/7 sin que
tu computadora esté prendida.

---

## Paso 1 — Subir el código a GitHub

1. Ve a [github.com/new](https://github.com/new) y crea un repo nuevo.
   - Nombre: `undercurrent` (o el que quieras)
   - Déjalo **Public** o **Private**, cualquiera funciona con Render gratis.
   - NO marques "Add a README" (ya tienes uno).

2. En tu computadora, abre una terminal dentro de esta carpeta (`undercurrent-app`)
   y corre:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/undercurrent.git
   git push -u origin main
   ```
   (Cambia `TU-USUARIO` por tu usuario real de GitHub — la URL exacta te la
   da GitHub en la página del repo recién creado, botón "Code".)

---

## Paso 2 — Crear cuenta en Render

1. Ve a [render.com](https://render.com) → "Get Started" → conecta con tu
   cuenta de GitHub (es lo más rápido, un solo clic).

---

## Paso 3 — Crear la base de datos (Postgres)

1. En el dashboard de Render: **New +** → **PostgreSQL**.
2. Nombre: `undercurrent-db`. Plan: **Free**.
3. Click **Create Database**.
4. Espera ~1 minuto a que esté lista. Luego copia el valor de **"Internal
   Database URL"** (lo vas a necesitar en el paso 5) — no hace falta pegarlo
   en ningún lado todavía, solo tenlo a la mano.

---

## Paso 4 — Crear el servicio web

1. En el dashboard: **New +** → **Web Service**.
2. Conecta el repo `undercurrent` que subiste en el paso 1.
3. Configuración:
   - **Name:** `undercurrent` (esto define parte de tu URL final)
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Plan:** Free

---

## Paso 5 — Variables de entorno

Antes de darle "Create", bájale a la sección **Environment Variables** y
agrega:

| Key | Value |
|---|---|
| `ANTHROPIC_API_KEY` | tu API key de [console.anthropic.com](https://console.anthropic.com) |
| `DATABASE_URL` | el "Internal Database URL" que copiaste en el paso 3 |

Click **Create Web Service**. Render va a instalar todo y desplegar
automáticamente — toma 2-3 minutos la primera vez.

---

## Paso 6 — Verificar que funciona

Cuando termine el deploy, Render te da una URL como:
`https://undercurrent.onrender.com`

- Visita esa URL → deberías ver el sitio público (vacío al inicio, normal).
- Visita `https://undercurrent.onrender.com/admin` → panel de aprobación
  (también vacío al inicio).

---

## Paso 7 — Cargar tus primeros eventos

Render no te deja correr comandos sueltos fácilmente desde la web gratis, así
que por ahora la forma más simple es correr el scraper **desde tu compu**,
apuntando a la base de datos de Render:

1. En tu terminal local, dentro de la carpeta del proyecto:
   ```bash
   export DATABASE_URL="el-Internal-Database-URL-de-Render"
   export ANTHROPIC_API_KEY="tu-key"
   python scraper.py
   python ai_review.py
   ```
   Nota: para correr esto desde tu compu (no desde Render) vas a necesitar el
   **"External Database URL"** de Render, no el "Internal" — ambos están en
   la página de tu base de datos en Render, justo debajo uno del otro.

2. Recarga `/admin` en tu navegador → deberías ver los eventos esperando
   aprobación.

---

## Cosas pendientes antes de que esto sea "negocio real"

- [ ] **Proteger `/admin` con contraseña** — ahora mismo cualquiera con la URL
  puede aprobar o rechazar eventos. Es lo primero que deberíamos arreglar
  juntos antes de compartir la URL públicamente.
- [ ] Conectar el formulario de suscripción a un servicio real de email
  (Beehiiv, Mailchimp) — ahora solo guarda el email en la base de datos, no
  envía nada.
- [ ] Stripe para cobrar el tier de $5/mes.
- [ ] Conectar una fuente real de eventos (Resident Advisor vía Apify, con
  su API key) en vez de los datos de ejemplo en `scraper.py`.
- [ ] Programar `scraper.py` + `ai_review.py` para correr solos cada día
  (Render tiene "Cron Jobs" en planes pagos; en el plan free tocaría correrlo
  manual desde tu compu por ahora).

## Costo real de mantener esto vivo

- Render Free: $0/mes, pero el sitio "duerme" tras 15 min sin tráfico y tarda
  unos segundos en despertar cuando alguien entra. Para validar la idea está
  perfecto.
- Cuando quieras que esté siempre despierto + cron jobs automáticos: el plan
  pago de Render arranca en ~$7-25/mes dependiendo de lo que actives.
- La API de Claude se cobra por uso (centavos por evento procesado) —
  revisa precios en [anthropic.com/pricing](https://www.anthropic.com/pricing).
