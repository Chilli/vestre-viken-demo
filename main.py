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

from state import state, mark_sick, mark_replacement, reset_turnus, generate_reasoning_report, load_state, save_state
from web_dashboard import render_live_dashboard

app = Flask(__name__)
PORT = int(os.environ.get("PORT", 5000))

# Last inn tidligere state hvis den finnes
load_state()

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
        "winner_name": state["shift_request"]["winner_name"],
        "candidate_queue": state["shift_request"].get("candidate_queue", []),
        "escalation_triggered": state["shift_request"].get("escalation_triggered", False),
        "agency_worker": state["shift_request"].get("agency_worker", None)
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
    <!-- Ingen auto-refresh - manuell oppdatering med F5 -->
    <style>
        body { font-family: -apple-system, sans-serif; background: #f5f7fa; padding: 20px; text-align: center; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
        button { background: #d32f2f; color: white; border: none; padding: 15px 30px; font-size: 18px; border-radius: 8px; cursor: pointer; width: 100%; font-weight: bold;}
        button:hover { background: #b71c1c; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .reset { background: #757575; margin-top: 20px;}
        .reset:hover { background: #616161; }
        .ai-config { background: #e3f2fd; border: 1px solid #2196f3; padding: 15px; border-radius: 8px; margin: 20px 0; text-align: left; }
        .ai-config h4 { margin-top: 0; color: #1565c0; }
        .ai-status { font-size: 12px; padding: 5px 10px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
        .ai-live { background: #4caf50; color: white; }
        .ai-sim { background: #ff9800; color: white; }
        input[type="password"], input[type="text"] { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        .analysis { background: #1e1e1e; color: #00ff00; font-family: monospace; padding: 15px; border-radius: 8px; text-align: left; font-size: 14px; margin-top: 20px; line-height: 1.5; }
        .btn-ai { background: #2196f3; margin-top: 10px; }
        .btn-ai:hover { background: #1976d2; }
        small { color: #666; }
    </style>
</head>
<body>
    <div class="card">
        <h2>🛠️ Kontrollpanel</h2>
        <p>Tilkoblede sykepleiere: <b>{{ count }}</b></p>
        <p style="color: #666; font-size: 12px;">Totalt i fiktiv database: {{ total_db }} ansatte</p>
        
        <!-- AI Configuration Panel -->
        <div class="ai-config">
            <h4>🤖 AI Agent Konfigurasjon</h4>
            {% if ai_mode == 'live' %}
                <span class="ai-status ai-live">✅ LIVE - DeepSeek AI Aktiv</span>
                <p style="font-size: 12px; color: #666; margin-top: 5px;">API-nøkkel lagret kun i minnet (ikke persistert)</p>
            {% else %}
                <span class="ai-status ai-sim">⚡ SIMULERT AI</span>
            {% endif %}
            
            <form action="/admin/configure-ai" method="POST">
                <input type="password" name="api_key" placeholder="DeepSeek API-nøkkel (skjult)" {% if ai_mode == 'live' %}value="********" disabled{% endif %}>
                <small>Limes inn ved demo-start. Lagres kun i RAM.</small>
                <button type="submit" class="btn-ai" {% if ai_mode == 'live' %}disabled{% endif %}>Aktiver DeepSeek AI</button>
            </form>
            
            {% if ai_mode == 'live' %}
            <form action="/admin/disable-ai" method="POST" style="margin-top: 10px;">
                <button type="submit" style="background: #757575; font-size: 14px; padding: 10px;">Bruk Simulert AI i stedet</button>
            </form>
            {% endif %}
        </div>
        
        <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
        
        <form action="/admin/trigger" method="POST">
            <label for="sick_person" style="display: block; margin-bottom: 10px; font-weight: bold;">Velg person som melder seg syk:</label>
            <select name="sick_person" id="sick_person" style="width: 100%; padding: 10px; margin-bottom: 15px; border-radius: 4px; border: 1px solid #ccc; font-size: 16px;">
                {% for person in turnus_rows %}
                <option value="{{ person.name }}" {% if person.today_shift %}data-shift="{{ person.today_shift }}"{% endif %}>
                    {{ person.name }} {% if person.today_shift %}(Dagens vakt: {{ person.today_shift }}){% endif %}
                </option>
                {% endfor %}
            </select>
            <small style="display: block; margin-bottom: 15px; color: #666;">
                AI vil analysere turnusen og finne erstatter uavhengig av hvem som blir syk
            </small>
            <button type="submit" {% if ai_mode == 'live' %}style="background: #4caf50;"{% endif %}>🚨 MELD VALGT PERSON SYK</button>
        </form>
        
        {% if analysis %}
        <div class="analysis">
            {% for line in analysis %}
                <div>> {{ line }}</div>
            {% endfor %}
        </div>
        {% if shift_resolved %}
        <a href="/admin/report" target="_blank" style="display: block; background: #4caf50; color: white; text-decoration: none; padding: 15px; border-radius: 8px; margin-top: 15px; font-weight: bold;">📄 Last ned AI Tenkerapport (HTML/PDF)</a>
        {% else %}
        <div style="display: block; background: #ff9800; color: white; padding: 15px; border-radius: 8px; margin-top: 15px; font-weight: bold;">
            ⏳ Venter på at vakten blir tildelt...<br>
            <small style="font-weight: normal;">Rapporten blir tilgjengelig når:</small><br>
            <small style="font-weight: normal;">• En deltaker aksepterer, ELLER</small><br>
            <small style="font-weight: normal;">• Bemanningsbyrå kontaktes, ELLER</small><br>
            <small style="font-weight: normal;">• Alle kandidater svarer</small>
        </div>
        {% endif %}
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
    from datetime import datetime
    
    # Sjekk om vakten er ferdig løst
    shift_resolved = (
        state["shift_request"].get("winner_name") is not None or
        state["shift_request"].get("escalation_triggered") or
        state["shift_request"].get("active") is False and state["shift_request"].get("candidate_queue") == []
    )
    
    # Bygg turnus data med dagens vakt for hver person
    day_idx = datetime.now().weekday()
    if day_idx > 4:
        day_idx = 0
    
    turnus_rows = []
    for person in state["turnus"]["rows"]:
        shifts = person.get("shifts", [])
        today_shift = shifts[day_idx] if len(shifts) > day_idx else "Ukjent"
        turnus_rows.append({
            "name": person["name"],
            "today_shift": today_shift
        })
    
    return render_template_string(
        ADMIN_HTML,
        count=len(state["colleagues"]),
        total_db=len(state["turnus"]["rows"]),
        analysis=state["shift_request"].get("agent_analysis"),
        ai_mode=state.get("ai_mode", "simulated"),
        shift_resolved=shift_resolved,
        turnus_rows=turnus_rows
    )

@app.route('/admin/trigger', methods=['POST'])
def admin_trigger():
    """Utløser sykdomsalarmen!"""
    try:
        from datetime import datetime
        
        # Les valgt person fra form
        sick_name = request.form.get('sick_person', 'Nils Dagenderpå')
        
        # Finn dagens vakt for valgt person
        day_idx = datetime.now().weekday()
        if day_idx > 4:
            day_idx = 0
        
        today_shift = "DAG 08-20"  # default
        for person in state["turnus"]["rows"]:
            if person["name"] == sick_name:
                shifts = person.get("shifts", [])
                if len(shifts) > day_idx:
                    today_shift = shifts[day_idx]
                    # Hvis personen har LEDIG eller sykemelding, bruk default
                    if "LEDIG" in today_shift or "SYK" in today_shift or "FERIE" in today_shift:
                        today_shift = "DAG 08-20"
                break
        
        state["shift_request"]["active"] = True
        state["shift_request"]["sick_name"] = sick_name
        state["shift_request"]["shift_type"] = today_shift
        state["shift_request"]["winner_name"] = None

        # Sjekk om DeepSeek er aktivert
        use_deepseek = state.get("ai_mode") == "live"
        api_key = state.get("deepseek_api_key") if use_deepseek else None

        # Kjør smart matching (Agenten tenker) - med eller uten DeepSeek
        analysis_log = analyze_candidates_for_shift(
            sick_name,
            today_shift,
            use_deepseek=use_deepseek,
            api_key=api_key
        )
        state["shift_request"]["agent_analysis"] = analysis_log

        # Oppdater minne-databasen
        mark_sick(sick_name)

        return redirect(url_for('admin_panel'))
    except Exception as e:
        import traceback
        error_msg = f"ERROR: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return f"<h1>Server Error</h1><pre>{error_msg}</pre>", 500

@app.route('/admin/reset', methods=['POST'])
def admin_reset():
    """Nullstiller systemet."""
    state["shift_request"]["active"] = False
    state["shift_request"]["sick_name"] = None
    state["shift_request"]["winner_name"] = None
    state["colleagues"] = set()
    # VI BEHOLDER ai_mode og api_key VED RESET (kun minne)
    reset_turnus()
    return redirect(url_for('admin_panel'))

@app.route('/admin/configure-ai', methods=['POST'])
def admin_configure_ai():
    """Lagrer API-nøkkel i minnet (aldri på disk/Git)."""
    api_key = request.form.get('api_key', '').strip()
    if api_key:
        state["deepseek_api_key"] = api_key
        state["ai_mode"] = "live"
        print("\n🔐 DeepSeek AI aktivert (API-nøkkel lagret i minnet)")
        print("⚠️  Nøkkelen forsvinner ved server restart\n")
    return redirect(url_for('admin_panel'))

@app.route('/admin/disable-ai', methods=['POST'])
def admin_disable_ai():
    """Bytter tilbake til simulert AI."""
    state["ai_mode"] = "simulated"
    state.pop("deepseek_api_key", None)  # Fjern fra minnet
    print("\n⚡ Byttet til Simulert AI")
    print("🗑️  API-nøkkel fjernet fra minnet\n")
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
        
        input, select { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; box-sizing: border-box;}
        button { background: #1F4E79; color: white; border: none; padding: 15px; font-size: 16px; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;}
        button.secondary { background: #757575; margin-top: 10px; font-size: 14px;}
        
        .alert-card { background: #ffebee; border: 2px solid #f44336; display: none;}
        .btn-accept { background: #4CAF50; font-size: 20px; padding: 20px; margin-top: 15px; animation: pulse 1.5s infinite;}
        .btn-accept:active { background: #388E3C; transform: scale(0.98); }
        
        .success-card { background: #e8f5e9; border: 2px solid #4CAF50; display: none;}
        .missed-card { background: #eeeeee; border: 2px solid #9e9e9e; display: none;}
        .excluded-card { background: #ffebee; border: 2px solid #f44336; display: none;}
        .excluded-card h2 { color: #d32f2f; margin-top: 0; }
        .excluded-reason { background: white; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: left; font-size: 14px;}
        
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(76, 175, 80, 0); }
            100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
        }
        
        .spinner { margin-top: 20px; font-size: 14px; color: #666; }
        .form-group { text-align: left; margin-bottom: 15px; }
        .form-group label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; font-size: 14px;}
        .hint { font-size: 13px; color: #666; margin-top: -10px; margin-bottom: 15px; text-align: left;}
        .warning { background: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; margin: 10px 0; text-align: left; font-size: 13px; color: #e65100;}
    </style>
</head>
<body>
    <div class="header">🏥 VESTRE VIKEN HF</div>
    
    <!-- REGISTRATION SCREEN -->
    <div class="card" id="register-screen">
        <h3>🎭 Din Profil</h3>
        <p style="color: #666; font-size: 14px;">Velg dine egne variabler for denne demoen!</p>
        
        <div class="form-group">
            <label for="reg-name">Navn</label>
            <input type="text" id="reg-name" placeholder="Ditt navn">
        </div>
        
        <div class="form-group">
            <label for="reg-role">Kompetanse / Fagautorisasjon</label>
            <select id="reg-role">
                <option value="Intensivsykepleier">Intensivsykepleier ✅ (Godkjent)</option>
                <option value="Sykepleier">Sykepleier ⚠️ (Må godkjennes)</option>
                <option value="Vernepleier">Vernepleier ❌ (Feil spesialisering)</option>
                <option value="Helsefagarbeider">Helsefagarbeider ❌ (Mangler autorisasjon)</option>
            </select>
        </div>

        <div class="form-group">
            <label for="reg-status">Din status i dag</label>
            <select id="reg-status">
                <option value="AVAILABLE" selected>🟢 Tilgjengelig</option>
                <option value="FERIE">🏖️ På ferie</option>
                <option value="PERMISJON">👶 I permisjon</option>
                <option value="SYKT BARN">🤒 Sykt barn</option>
                <option value="SYK">🤕 Syk selv</option>
            </select>
        </div>

        <div class="form-group">
            <label for="reg-last-shift">Når var din siste vakt?</label>
            <select id="reg-last-shift">
                <option value="long_ago" selected>For 2 dager siden ✅ (Nok hvile)</option>
                <option value="yesterday">I går kl 14-22 ⚠️ (9 timer siden)</option>
                <option value="recent">I natt kl 20-08 ❌ (Kun 6 timer siden)</option>
            </select>
        </div>

        <div class="form-group">
            <label for="reg-sickleave">Sykemeldingshistorikk</label>
            <select id="reg-sickleave">
                <option value="none" selected>Ingen sykemelding siste 2 år ✅</option>
                <option value="over6m">Sykemeldt >6 måneder siden ✅</option>
                <option value="under6m">Sykemeldt siste 6 måneder ❌ (AML-brudd)</option>
            </select>
        </div>

        <div class="form-group">
            <label for="reg-has-shift">Har du allerede vakt i dag?</label>
            <select id="reg-has-shift">
                <option value="no" selected>Nei, jeg er ledig</option>
                <option value="yes">Ja, jeg jobber allerede ❌</option>
            </select>
        </div>
        
        <div class="warning">
            💡 <strong>Tips:</strong> Hvis alle velger ugunstige variabler, vil AI-en ringe bemanningsbyrå!
        </div>
        
        <button onclick="registerWithProfile()">Registrer i systemet</button>
    </div>

    <!-- IDLE SCREEN -->
    <div class="card" id="idle-screen" style="display: none;">
        <h3 id="welcome-text">Velkommen</h3>
        <div id="profile-summary" style="background: #f5f7fa; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: left; font-size: 14px;"></div>
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
    
    <!-- EXCLUDED SCREEN -->
    <div class="card excluded-card" id="excluded-screen" style="display: none;">
        <h2>❌ DU BLE UTELUKKET</h2>
        <p>AI-agenten har analysert profilen din.</p>
        <div class="excluded-reason" id="exclusion-reason">
            <strong>Årsak:</strong> <span id="exclusion-text"></span>
        </div>
        <p style="font-size: 13px; color: #666;">Du kan ikke ta denne vakten basert på valgte variabler.</p>
    </div>

    <!-- MISSED SCREEN -->
    <div class="card missed-card" id="missed-screen">
        <h2 style="color: #616161; margin-top:0;">ℹ️ VAKT DEKKET</h2>
        <p>Vakten ble tildelt <b><span id="winner-name-display"></span></b>.</p>
        <p>Takk for at du responderte raskt.</p>
    </div>

    <script>
        let myName = "";
        let myProfile = null;
        let amIExcluded = false;

        function registerWithProfile() {
            let name = document.getElementById("reg-name").value.trim();
            if(name === "") return alert("Vennligst skriv inn navnet ditt.");

            myName = name;
            myProfile = {
                name: name,
                role: document.getElementById("reg-role").value,
                status: document.getElementById("reg-status").value,
                last_shift: document.getElementById("reg-last-shift").value,
                sickleave: document.getElementById("reg-sickleave").value,
                has_shift: document.getElementById("reg-has-shift").value === "yes"
            };

            // Registrer med profil hos serveren
            fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: myName, profile: myProfile})
            });

            document.getElementById("register-screen").style.display = "none";
            document.getElementById("idle-screen").style.display = "block";
            document.getElementById("welcome-text").innerText = "Velkommen, " + myName;

            // Vis profil-oppsummering
            let statusEmoji = {"AVAILABLE": "🟢", "FERIE": "🏖️", "PERMISJON": "👶", "SYKT BARN": "🤒", "SYK": "🤕"}[myProfile.status] || "⚪";
            let roleIcon = myProfile.role === "Intensivsykepleier" ? "✅" : (myProfile.role === "Sykepleier" ? "⚠️" : "❌");
            let restOK = myProfile.last_shift === "long_ago" && myProfile.sickleave !== "under6m";
            document.getElementById("profile-summary").innerHTML = `
                <strong>Din profil:</strong><br>
                ${roleIcon} ${myProfile.role}<br>
                ${statusEmoji} ${myProfile.status}<br>
                ${restOK ? "✅" : "⚠️"} Hvile/sykemelding OK${myProfile.has_shift ? '<br>❌ Har allerede vakt' : ''}
            `;

            // Start polling for status
            startPolling();
        }

        function acceptShift() {
            fetch('/api/accept', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name: myName, profile: myProfile})
            }).then(res => res.json()).then(data => {
                if (data.success === false) {
                    amIExcluded = true;
                    document.getElementById("exclusion-text").innerText = data.error;
                    showScreen('excluded-screen');
                } else if (data.winner) {
                    document.getElementById("alert-screen").style.display = "none";
                } else {
                    // Noen andre var raskere
                    document.getElementById("alert-screen").style.display = "none";
                }
            });
        }

        function showScreen(screenId) {
            ['register-screen', 'idle-screen', 'alert-screen', 'success-screen', 'missed-screen', 'excluded-screen'].forEach(id => {
                document.getElementById(id).style.display = (id === screenId) ? 'block' : 'none';
            });
        }

        function startPolling() {
            setInterval(() => {
                if (amIExcluded) return; // Ikke bytt skjerm hvis utelukket

                fetch('/api/status')
                .then(res => res.json())
                .then(data => {
                    if (amIExcluded) return;

                    if (data.active && !data.winner_name) {
                        // ALARM! Sjekk om brukeren er i candidate_queue
                        let inQueue = data.candidate_queue && data.candidate_queue.some(n =>
                            n.toLowerCase().includes(myName.toLowerCase()) ||
                            myName.toLowerCase().includes(n.toLowerCase().split(' ')[0])
                        );

                        if (inQueue) {
                            showScreen('alert-screen');
                            document.getElementById("sick-name").innerText = data.sick_name;
                            document.getElementById("shift-type").innerText = data.shift_type;
                            if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
                        }
                        // Hvis ikke i kø, fortsett å vise idle

                    } else if (data.winner_name) {
                        // NOEN VANT!
                        let iWon = data.winner_name.toLowerCase().includes(myName.toLowerCase()) ||
                                   myName.toLowerCase().includes(data.winner_name.toLowerCase().split(' ')[0]);

                        if (iWon) {
                            showScreen('success-screen');
                            document.getElementById("win-name").innerText = myName;
                        } else {
                            showScreen('missed-screen');
                            document.getElementById("winner-name-display").innerText = data.winner_name;
                        }
                    } else {
                        // IDLE
                        showScreen('idle-screen');
                    }
                });
            }, 1000);
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
    """Registrerer en ny mobilbruker med profil."""
    data = request.json
    name = data.get("name", "")
    profile = data.get("profile", {})

    if name:
        state["colleagues"].add(name)
        # Lagre profilen
        if "profiles" not in state:
            state["profiles"] = {}
        state["profiles"][name] = profile
        print(f"📱 Ny tilkobling: {name} ({profile.get('role', 'ukjent')}, {profile.get('contract', '?')}%)")
    return jsonify({"status": "ok"})

@app.route('/api/accept', methods=['POST'])
def api_accept():
    """Håndterer når en sykepleier trykker 'BEKREFT TILGJENGELIGHET'."""
    data = request.json
    name = data.get("name", "")
    profile = data.get("profile", {})

    # DYNAMISK VALIDERING basert på profilen deltakeren valgte
    errors = []

    # 1. Sjekk kompetanse (kun Intensivsykepleier får automatisk vakt)
    role = profile.get("role")
    if role == "Intensivsykepleier":
        pass  # OK
    elif role == "Sykepleier":
        errors.append("Sykepleier må godkjennes av vakthavende - ikke autorisert for intensiv")
    elif role == "Vernepleier":
        errors.append("Vernepleier har feil spesialisering (krever intensivkompetanse)")
    else:
        errors.append("Mangler fagautorisasjon for intensivavdeling")

    # 2. Sjekk status (ferie, permisjon, syk)
    if profile.get("status") in ["FERIE", "PERMISJON", "SYKT BARN", "SYK"]:
        status_names = {"FERIE": "på ferie", "PERMISJON": "i permisjon", "SYKT BARN": "hjemme med sykt barn", "SYK": "syk"}
        errors.append(f"Du er {status_names.get(profile.get('status'), 'utilgjengelig')}")

    # 3. Sjekk hviletid (11-timers regelen)
    last_shift = profile.get("last_shift")
    if last_shift == "recent":
        errors.append("Kun 6 timer siden forrige vakt (brudd på 11-timers hvileregel)")
    elif last_shift == "yesterday":
        errors.append("9 timer siden forrige vakt (brudd på 11-timers hvileregel)")

    # 4. Sjekk sykemeldingshistorikk (AML: ikke overtid etter nylig sykemelding)
    if profile.get("sickleave") == "under6m":
        errors.append("Sykemeldt siste 6 måneder (kan ikke ta overtid etter AML)")

    # 5. Sjekk om har vakt allerede
    if profile.get("has_shift", False):
        errors.append("Har allerede vakt i dag (kollisjon)")

    # Hvis noen feil, returner utelukkelse
    if errors:
        return jsonify({"success": False, "error": "; ".join(errors)})

    # Sjekk om denne personen er i candidate_queue
    candidate_queue = state["shift_request"].get("candidate_queue", [])
    is_in_queue = any(name.lower() in cq.lower() or cq.lower() in name.lower() for cq in candidate_queue)

    if not is_in_queue and not state["shift_request"].get("escalation_triggered"):
        # Ikke i køen - ble filtrert ut av AI
        return jsonify({"success": False, "error": "Du ble utelukket av AI-agenten under analysefasen"})

    # Førstemann til mølla sjekk
    if state["shift_request"]["active"] and state["shift_request"]["winner_name"] is None:
        # VI HAR EN VINNER!
        state["shift_request"]["active"] = False
        sick_name = state["shift_request"]["sick_name"]

        print(f"\n🎉 VAKT DEKKET: {name} var raskest!")

        # Oppdater minne-databasen
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

@app.route('/admin/report')
def admin_report():
    """Genererer og viser rapport over AI-tenkingen."""
    if not state["shift_request"].get("agent_analysis"):
        return "<h2>Ingen analyse tilgjengelig ennå</h2><p>Trigger en sykdomsmelding først.</p><a href='/admin'>Tilbake til admin</a>", 400
    
    # Sjekk om vakten er ferdig løst (vinner funnet eller eskalert)
    shift_resolved = (
        state["shift_request"].get("winner_name") is not None or
        state["shift_request"].get("escalation_triggered") or
        state["shift_request"].get("active") is False and state["shift_request"].get("candidate_queue") == []
    )
    
    if not shift_resolved:
        return """<h2>⏳ Venter på at vakten blir tildelt...</h2>
        <p>Rapporten vil være tilgjengelig når:</p>
        <ul>
            <li>✅ En deltaker har akseptert vakten, ELLER</li>
            <li>📞 Bemanningsbyrå har blitt kontaktet, ELLER</li>
            <li>⏰ Alle kandidater har svart (timeout)</li>
        </ul>
        <p><a href='/admin'>Tilbake til admin</a></p>""", 202

    html_report = generate_reasoning_report()

    # Returner som HTML med download-forslag
    from flask import Response
    return Response(
        html_report,
        mimetype='text/html',
        headers={
            'Content-Disposition': f'inline; filename=vestre-viken-ai-rapport-{datetime.now().strftime("%Y%m%d")}.html'
        }
    )

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
