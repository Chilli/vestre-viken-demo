# 🚀 Guide: Legg prosjektet ut på Internett (Render.com)

Å kjøre demoen fra internett betyr at du slipper å ha terminalvinduer og `ngrok` åpen på PC-en din under presentasjonen. Koden din vil kjøre døgnet rundt i skyen (gratis).

Følg disse stegene for å få Vestre Viken-demoen din live:

## Steg 1: Legg koden din på GitHub

1. Gå til [GitHub.com](https://github.com) og logg inn (eller opprett en gratis konto).
2. Trykk på **+** øverst i høyre hjørne og velg **New repository**.
3. Gi den navnet `vestre-viken-demo`, velg **Private** (eller Public hvis du vil), og trykk **Create repository**.
4. Åpne terminalen (Terminal-appen på Mac) og skriv inn disse tre linjene (husk å bytt ut `DITT_BRUKERNAVN` med ditt faktiske GitHub-brukernavn):

```bash
cd ~/Desktop/vestre-viken-demo
git branch -M main
git remote add origin https://github.com/DITT_BRUKERNAVN/vestre-viken-demo.git
git push -u origin main
```
Nå ligger all koden din trygt på GitHub!

## Steg 2: Deploy på Render (Gratis skytjeneste)

Nå skal vi fortelle en server-leverandør at de skal kjøre koden din.

1. Gå til [Render.com](https://render.com) og registrer deg med GitHub-kontoen din.
2. Klikk på knappen **New +** og velg **Web Service**.
3. Under "Connect a repository", finn `vestre-viken-demo` fra GitHub og klikk **Connect**.
4. Fyll inn skjemaet slik:
   - **Name:** `vestre-viken-demo` (eller hva du vil)
   - **Region:** Frankfurt (eller den som er nærmest)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn main:app` (Dette henter den fra `Procfile` uansett)
   - **Instance Type:** `Free`
5. Trykk på **Create Web Service** helt nederst.

## Steg 3: Ferdig! 🎉

Nå vil du se en terminalskjerm på Render som bygger prosjektet ditt. Det tar ca 2-3 minutter.

Når det står "Live", får du utdelt en fast, profesjonell nettadresse oppe i venstre hjørne. Den vil se omtrent slik ut:
👉 `https://vestre-viken-demo-1234.onrender.com`

**Bruk denne under presentasjonen:**
* **Storskjerm:** `https://vestre-viken-demo-1234.onrender.com/live`
* **Sjefenes mobiler (QR-koden):** `https://vestre-viken-demo-1234.onrender.com/app`
* **Ditt skjulte admin-panel:** `https://vestre-viken-demo-1234.onrender.com/admin`

*(PS: Render sin Free-tier "sover" hvis den ikke har blitt brukt på 15 minutter, og det tar 30 sekunder å våkne. Bare husk å åpne /live linken 5 minutter før presentasjonen din starter slik at maskinen er våken).*
