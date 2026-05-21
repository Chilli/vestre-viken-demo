# Deploy til Render.com

## Steg 1: Push til GitHub
✅ Allerede gjort! Repository: `Chilli/vestre-viken-demo`

## Steg 2: Opprett ny Web Service på Render

1. Gå til https://dashboard.render.com
2. Klikk **"New +"** → **"Web Service"**
3. Koble til GitHub-repo: `Chilli/vestre-viken-demo`
4. Fyll inn:
   - **Name:** `vestre-viken-demo`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app --bind 0.0.0.0:$PORT`
   - **Plan:** Free

5. Klikk **"Create Web Service"**

## Steg 3: Vent på deploy
- Render bygger automatisk fra `main` branch
- Første deploy tar ~2-3 minutter
- URL blir: `https://vestre-viken-demo.onrender.com`

## Steg 4: Test!
- **Admin:** `https://vestre-viken-demo.onrender.com/admin`
- **Mobil-app:** `https://vestre-viken-demo.onrender.com/app`
- **Live:** `https://vestre-viken-demo.onrender.com/live`
- **QR:** `https://vestre-viken-demo.onrender.com/qr`

## Viktig for Flask på Render
- `render.yaml` er allerede laget
- `PORT` leser fra miljøvariabel
- `gunicorn` er i requirements.txt

## Troubleshooting

**Hvis appen ikke starter:**
Sjekk logs i Render dashboard

**Hvis QR-kode ikke funker:**
Sjekk at URL i `main.py` linje 648 er oppdatert med din faktiske URL

**Hvis deltakere ikke ser oppdateringer:**
Dette er normalt på Free tier (SSE/WebSocket begrensninger). Refresh siden manuelt.
