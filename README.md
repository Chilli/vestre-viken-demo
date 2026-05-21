# 🏥 Vestre Viken Vaktassistent - Web/QR Demo

En moderne, sanntidsbasert demo for Vestre Viken som viser hvordan en intelligent vaktassistent orkestrerer fraværshåndtering umiddelbart via web-teknologi.

1. 🤒 Fravær registreres i systemet.
2. 📊 Turnusplan (Excel og storskjerm) oppdateres til "Syk" i sanntid.
3. 🤖 Systemet sender ut umiddelbar vaktforespørsel til alle tilkoblede kollegaer.
4. 🏃 Håndterer "Førstemann til mølla"-logikk for tildeling av vakt.
5. 📱 Dele ut vakten, oppdatere Excel, og varsle alle om utfallet i sanntid.

Denne løsningen krever **ingen** tredjeparts SMS/Tale-leverandører og kjører 100% via web!

## 🛠️ Forutsetninger

- Python 3.8+
- [ngrok](https://ngrok.com) installert (`brew install ngrok`)

## ⚙️ Oppsett

### 1. Installer avhengigheter

```bash
cd vestre-viken-demo
pip install -r requirements.txt
```

### 2. Start serveren

**Terminal 1 - Flask:**
```bash
python main.py
```

**Terminal 2 - ngrok (Valgfritt, men nødvendig for at publikum skal nå appen via 4G):**
```bash
ngrok http 5000
```
Kopier ngrok-URLen (f.eks. `https://abc123.ngrok.io`).

## 🎬 Demo-flyt (Slik gjennomfører du presentasjonen)

### 1. Forberedelser før publikum kommer
* Åpne **Storskjermen** (Koble PC-en til projektor) og gå til: `http://localhost:5000/live`
* Åpne **Admin-panelet** (Skjult på din egen PC-skjerm): `http://localhost:5000/admin`
* Lag en QR-kode (bruk f.eks qr-code-generator.com) som peker til: `https://[din-ngrok-url]/app`
* Legg denne QR-koden i en PowerPoint-slide.

### 2. Selve presentasjonen
1. **Onboarding:** Be sjefene scanne QR-koden med mobilen sin. 
   - De skriver inn navnet sitt (f.eks "Mette Prada Hansen"). 
   - De ser en skjerm som sier at systemet "lytter". Du kan se i Admin-panelet at antall tilkoblede sykepleiere øker!
2. **Utløs Krisen:** Trykk på den røde knappen i Admin-panelet: **"MELD NILS DAGENDERPÅ SYK"**.
3. **Magien:** 
   - På storskjermen begynner Nils sin rad å blinke RØDT.
   - På sjefenes mobiler popper det opp en rød alarm: *"Varsel om fravær. Ledig dagvakt."*
4. **Kappløpet:** Sjefene trykker på **"BEKREFT TILGJENGELIGHET"**.
5. **Utfallet:**
   - Den som trykket først får grønn "VAKT BEKREFTET"-skjerm.
   - De andre får grå "VAKT DEKKET"-skjerm.
   - Storskjermen oppdateres live med vinnerens navn!

## 🏗️ Prosjektstruktur

```
vestre-viken-demo/
├── README.md              # Denne filen
├── PITCH_ARGUMENTER.md    # Hjelpedokument for presentasjonen din
├── requirements.txt       # Python-avhengigheter
├── turnus.xlsx            # 📊 Excel-turnusplan (genereres auto)
├── main.py                # 🚀 Flask-server, Web-App og Admin
├── turnus_manager.py      # 📊 Leser/Skriver til Excel
├── web_dashboard.py       # 📺 Storskjerm-visningen (Auto-refresh)
└── state.py               # 🗃️ Holder styr på hvem som vinner kappløpet
```
