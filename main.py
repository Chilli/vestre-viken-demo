"""
🏥 Vestre Viken - Hovedapplikasjon (Web App Mode)
"""

import os
import sys
import io
import base64
import qrcode
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import state, mark_sick, mark_replacement, reset_turnus
from web_dashboard import render_live_dashboard

app = Flask(__name__)
PORT = 5000

# ============================================================
# EVENT STREAM (SSE) FOR SANNTIDSOPPDATERINGER PÅ MOBIL
# ============================================================
# Dette gjør at publikums telefoner reagerer *umiddelbart* når noen meldes syk.

@app.route('/api/status')
def api_status():
    """Returnerer gjeldende status for mobil-klientene."""
    return jsonify({
        "active": state["shift_request"]["active"],
        "sick_name": state["shift_request"]["sick_name"],
        "shift_type": state["shift_request"]["shift_type"],
        "winner_name": state["shift_request"]["winner_name"]
    })

# ============================================================
# ADMIN PANEL (For presentatøren)
# ============================================================

from state import analyze_candidates_for_shift

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Admin - Vestre Viken</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="3">
    <style>
        body { font-family: -apple-system, sans-serif; background: #f5f7fa; padding: 20px; text-align: center; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
        button { background: #d32f2f; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold;}
        button:hover { background: #b71c1c; }
        .reset { background: #757575; margin-top: 20px;}
        .reset:hover { background: #616161; }
        .analysis { background: #1e1e1e; color: #00ff00; font-family: monospace; padding: 15px; border-radius: 8px; text-align: left; font-size: 14px; margin-top: 20px; line-height: 1.5; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛠️ Kontrollpanel</h2>
        <p>Tilkoblede sykepleiere: <b>{{ count }}</b></p>
        <p style="color: #666; font-size: 12px;">Totalt i fiktiv database: {{ total_db }} ansatte</p>
        <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
        <form action="/admin/trigger" method="POST">
            <button type="submit">🚨 MELD NILS DAGENDERPÅ SYK</button>
        </form>
        
        {% if analysis %}
        <div class="analysis">
            {% for line in analysis %}
                <div>> {{ line }}</div>
            {% endfor %}
        </div>
        {% endif %}
        
        <form action="/admin/reset" method="POST">
            <button type="submit" class="reset">🔄 Nullstill System</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/admin')
def admin_panel():
    """Admin panelet Jarl bruker for å trigge krisen."""
    return render_template_string(
        ADMIN_HTML, 
        count=len(state["colleagues"]),
        total_db=len(state["turnus"]["rows"]),
        analysis=state["shift_request"].get("agent_analysis")
    )

@app.route('/admin/trigger', methods=['POST'])
def admin_trigger():
    """Utløser sykdomsalarmen!"""
    state["shift_request"]["active"] = True
    state["shift_request"]["sick_name"] = "Nils Dagenderpå"
    state["shift_request"]["shift_type"] = "DAG 08-20"
    state["shift_request"]["winner_name"] = None
    
    # Kjør smart matching (Agenten tenker)
    analysis_log = analyze_candidates_for_shift("Nils Dagenderpå", "DAG 08-20")
    state["shift_request"]["agent_analysis"] = analysis_log
    
    # Oppdater minne-databasen
    mark_sick("Nils Dagenderpå")
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    """Nullstiller systemet."""
    state["shift_request"]["active"] = False
    state["shift_request"]["sick_name"] = None
    state["shift_request"]["winner_name"] = None
    state["colleagues"] = set()
    reset_turnus()
    return redirect(url_for('admin_panel'))


# ============================================================
# MOBIL APP (For publikum)
# ============================================================

MOBILE_APP_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ansattportal - Vestre Viken</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        body { font-family: -apple-system, sans-serif; background: #f5f7fa; padding: 20px; text-align: center; margin: 0;}
        .header { background: #1F4E79; color: white; padding: 15px; margin: -20px -20px 20px -20px; font-weight: bold;}
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; transition: all 0.3s;}
        
        input { width: 90%; padding: 12px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px;}
        button { background: #1F4E79; color: white; border: none; padding: 15px; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;}
        
        .alert-card { background: #ffebee; border: 2px solid #f44336; display: none;}
        .btn-accept { background: #4CAF50; font-size: 20px; padding: 20px; margin-top: 15px; animation: pulse 1.5s infinite;}
        .btn-accept:active { background: #388E3C; transform: scale(0.98); }
        
        .success-card { background: #e8f5e9; border: 2px solid #4CAF50; display: none;}
        .missed-card { background: #eeeeee; border: 2px solid #9e9e9e; display: none;}
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
            100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
        
        .spinner { margin-top: 20px; font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="header">🏥 VESTRE VIKEN HF</div>
    
    <!-- LOGIN SCREEN -->
    <div class="card" id="login-screen">
        <h3>Registrer deg for vakt</h3>
        <p style="color: #666; font-size: 14px;">Skriv inn ditt fornavn for å koble deg til vakt-systemet.</p>
        <input type="text" id="name-input" placeholder="Ditt navn (f.eks Mette)">
        <button onclick="register()">Koble til systemet</button>
    </div>

    <!-- IDLE SCREEN -->
    <div class="card" id="idle-screen" style="display: none;">
        <h3 id="welcome-text">Velkommen</h3>
        <div class="spinner">
            📡 Lytter etter fraværsmeldinger...<br><br>
            <small>Systemet er tilkoblet. Du kan slappe av.</small>
        </div>
    </div>

    <!-- ALARM SCREEN -->
    <div class="card alert-card" id="alert-screen">
        <h2 style="color: #d32f2f; margin-top:0;">🚨 VARSEL OM FRAVÆR</h2>
        <p><b><span id="sick-name"></span></b> har meldt fravær.</p>
        <p style="background: white; padding: 10px; border-radius: 4px; border: 1px solid #f44336;">Behov for dekning:<br><b><span id="shift-type"></span></b></p>
        <p style="font-size: 13px; color: #666;">Første som bekrefter tildeles vakten.</p>
        <button class="btn-accept" onclick="acceptShift()">BEKREFT TILGJENGELIGHET</button>
    </div>
    
    <!-- SUCCESS SCREEN -->
    <div class="card success-card" id="success-screen">
        <h2 style="color: #2E7D32; margin-top:0;">✅ VAKT BEKREFTET</h2>
        <p>Turnusplanen er oppdatert.</p>
        <p>Takk for at du stiller opp, <b id="win-name"></b>!</p>
    </div>
    
    <!-- MISSED SCREEN -->
    <div class="card missed-card" id="missed-screen">
        <h2 style="color: #616161; margin-top:0;">ℹ️ VAKT DEKKET</h2>
        <p>Vakten ble tildelt <b><span id="winner-name-display"></span></b>.</p>
        <p>Takk for at du responderte raskt.</p>
    </div>

    <script>
        let myName = "";
        
        function register() {
            let input = document.getElementById("name-input").value.trim();
            if(input === "") return alert("Vennligst skriv inn navnet ditt.");
            
            myName = input;
            
            // Registrer hos serveren
            fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: myName})
            });
            
            document.getElementById("login-screen").style.display = "none";
            document.getElementById("idle-screen").style.display = "block";
            document.getElementById("welcome-text").innerText = "Velkommen, " + myName;
            
            // Start polling for status
            startPolling();
        }
        
        function acceptShift() {
            fetch('/api/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: myName})
            }).then(res => res.json()).then(data => {
                if (data.success === false) {
                    alert(data.error);
                } else {
                    document.getElementById("alert-screen").style.display = "none";
                }
            });
        }
        
        function startPolling() {
            setInterval(() => {
                fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    // Skjul alle skjermer først
                    document.getElementById("idle-screen").style.display = "none";
                    document.getElementById("alert-screen").style.display = "none";
                    document.getElementById("success-screen").style.display = "none";
                    document.getElementById("missed-screen").style.display = "none";
                    
                    if (data.active && !data.winner_name) {
                        // ALARM!
                        document.getElementById("alert-screen").style.display = "block";
                        document.getElementById("sick-name").innerText = data.sick_name;
                        document.getElementById("shift-type").innerText = data.shift_type;
                        
                        // Vibrate if mobile
                        if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                        
                    } else if (data.winner_name) {
                        // NOEN VANT!
                        if (data.winner_name === myName) {
                            document.getElementById("success-screen").style.display = "block";
                            document.getElementById("win-name").innerText = myName;
                        } else {
                            document.getElementById("missed-screen").style.display = "block";
                            document.getElementById("winner-name-display").innerText = data.winner_name;
                        }
                    } else {
                        // IDLE
                        document.getElementById("idle-screen").style.display = "block";
                    }
                });
            }, 1000); // Sjekker hvert sekund
        }
    </script>
</body>
</html>
"""

@app.route('/app')
def mobile_app():
    """Mobil-appen for sykepleierne/publikum."""
    return render_template_string(MOBILE_APP_HTML)

@app.route('/api/register', methods=['POST'])
def api_register():
    """Registrerer en ny mobilbruker."""
    data = request.json
    if "name" in data:
        state["colleagues"].add(data["name"])
        print(f"📱 Ny tilkobling: {data['name']}")
    return jsonify({"status": "ok"})

@app.route('/api/accept', methods=['POST'])
def api_accept():
    """Håndterer når en sykepleier trykker 'BEKREFT TILGJENGELIGHET'."""
    data = request.json
    name = data.get("name", "")
    
    # Valider mot "Smart Matching" logikken: Må være en av de lovlige publikummerne
    valid_names = ["Mette Prada Hansen", "Wes Side Story", "Dr. Anton Graff"]
    is_valid = any(p.lower() in name.lower() for p in ["mette", "wes", "anton"])
    
    if not is_valid:
        return jsonify({"success": False, "error": "Du ble utelukket av Agenten pga Arbeidsmiljøloven eller feil kompetanse!"})
    
    # Førstemann til mølla sjekk
    if state["shift_request"]["active"] and state["shift_request"]["winner_name"] is None:
        # VI HAR EN VINNER!
        state["shift_request"]["active"] = False
        sick_name = state["shift_request"]["sick_name"]
        
        print(f"\n🎉 VAKT DEKKET: {name} var raskest!")
        
        # Oppdater minne-databasen (den returnerer det normaliserte navnet)
        actual_name = mark_replacement(sick_name, name)
        state["shift_request"]["winner_name"] = actual_name
        
        return jsonify({"success": True, "winner": True})
        
    # Noen andre var raskere
    return jsonify({"success": True, "winner": False})


# ============================================================
# LIVE STORSKJERM
# ============================================================

@app.route('/qr')
def show_qr():
    """Genererer og viser en QR-kode som peker til appen på mobil."""
    # Finn URL-en til serveren (f.eks https://vestre-viken.onrender.com)
    host_url = request.host_url.rstrip('/')
    app_url = f"{host_url}/app"
    
    # Generer QR koden
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(app_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Konverter bildet til base64 for å vise i HTML
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Koble til Vestre Viken Demo</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f5f7fa; text-align: center; padding-top: 50px; color: #1F4E79; }}
            h1 {{ font-size: 40px; margin-bottom: 10px; }}
            p {{ font-size: 24px; color: #666; margin-bottom: 40px; }}
            .qr-container {{ background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); display: inline-block; }}
            img {{ width: 400px; height: 400px; }}
            .url-text {{ margin-top: 20px; font-size: 20px; font-weight: bold; background: #eee; padding: 10px; border-radius: 8px; display: inline-block;}}
        </style>
    </head>
    <body>
        <h1>📲 Bli med som Sykepleier</h1>
        <p>Scan QR-koden med mobilkameraet ditt for å koble deg til systemet.</p>
        <div class="qr-container">
            <img src="data:image/png;base64,{img_str}" alt="QR Code">
            <br>
            <div class="url-text">{app_url}</div>
        </div>
        <p style="margin-top: 40px;"><a href="/live" style="color: #1F4E79; text-decoration: none; font-size: 18px; font-weight: bold;">➡️ Gå til Live Turnusplan (Storskjerm)</a></p>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/live')
def live_dashboard():
    """Live HTML-visning av turnusen (Auto-refresh)"""
    return render_live_dashboard()

@app.route('/')
def index():
    return redirect(url_for('live_dashboard'))

# ============================================================
# OPPSTART
# ============================================================

def print_startup_info():
    print(f"""
{'='*60}
  🏥 VESTRE VIKEN VAKTASSISTENT - WEB DEMO
{'='*60}

  Slik kjører du presentasjonen:

  1. STORSKJERM (Projektor):
     Åpne: https://vestre-viken-demo.onrender.com/live

  2. PUBLIKUM (Mobiler):
     La publikum scanne en QR-kode (eller gå til) denne URLen:
     👉 https://vestre-viken-demo.onrender.com/app

  3. DU (Skjult på din PC):
     Åpne Admin-panelet for å utløse krisen:
     👉 https://vestre-viken-demo.onrender.com/admin

{'='*60}
""")

if __name__ == '__main__':
    print_startup_info()
    reset_turnus()
    app.run(host='0.0.0.0', port=PORT, debug=False)
