"""
Global State for Vestre Viken Demo.
Inneholder minne-basert "database" for hele appen med en stor, kompleks ansattliste.
"""

from datetime import datetime, timedelta
import random
import requests
import json

def get_dates_for_week():
    """Hjelpefunksjon for å finne datoer for gjeldende uke (mandag-fredag)"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    dates = []
    for i in range(5):
        dates.append((monday + timedelta(days=i)).strftime("%d.%m.%Y"))
    return dates

def generate_complex_database():
    """Lager realistiske turnuser for sykepleiere med dag/kveld/natt-vakter."""

    # Realistiske turnusmønstre (mandag-fredag)
    # DAG 07:00-15:30 / KVELD 14:30-23:00 / NATT 23:00-07:30 / 12T DAG 07:00-19:00 / 12T NATT 19:00-07:00

    # De 3 publikummerne - ulike turnusmønstre
    audience = [
        # Mette: 3-skift klassisk turnus
        {"name": "Mette Prada Hansen", "role": "Intensivsykepleier", "status": "AVAILABLE",
         "shifts": ["NATT 23-07", "LEDIG", "DAG 07-15", "KVELD 14-23", "LEDIG"],
         "turnus_type": "3-skift"},
        # Anton: 12-timers turnus (dager)
        {"name": "Dr. Anton Graff", "role": "Intensivsykepleier", "status": "AVAILABLE",
         "shifts": ["12T DAG 07-19", "LEDIG", "12T NATT 19-07", "LEDIG", "12T DAG 07-19"],
         "turnus_type": "12-timers"},
        # Wes: Kun dagvakter (eldre/senior)
        {"name": "Wes Side Story", "role": "Intensivsykepleier", "status": "AVAILABLE",
         "shifts": ["DAG 07-15", "DAG 07-15", "LEDIG", "DAG 07-15", "DAG 07-15"],
         "turnus_type": "dag-kun"},
    ]

    # Den som blir syk - 3-skift turnus
    sick_person = [
        {"name": "Nils Dagenderpå", "role": "Intensivsykepleier", "status": "OK",
         "shifts": ["DAG 07-15", "KVELD 14-23", "LEDIG", "NATT 23-07", "DAG 07-15"],
         "turnus_type": "3-skift"}
    ]

    # Fyll på med realistiske turnuser
    fillers_data = [
        # Intensivsykepleiere med ulike turnuser
        ("Kari Vaktmester", "3-skift", ["DAG 07-15", "KVELD 14-23", "NATT 23-07", "LEDIG", "DAG 07-15"]),
        ("Ole Tidsklemme", "3-skift", ["LEDIG", "DAG 07-15", "KVELD 14-23", "LEDIG", "NATT 23-07"]),
        ("Lise Trøtt", "3-skift", ["NATT 23-07", "LEDIG", "DAG 07-15", "KVELD 14-23", "LEDIG"]),
        ("Bernt Overtid", "12-timers", ["12T DAG 07-19", "LEDIG", "12T DAG 07-19", "12T NATT 19-07", "LEDIG"]),
        ("Siri Småbarnsmor", "dag-kun", ["DAG 07-15", "DAG 07-15", "LEDIG", "DAG 07-15", "LEDIG"]),
        ("Jonas Helse", "3-skift", ["KVELD 14-23", "NATT 23-07", "LEDIG", "DAG 07-15", "KVELD 14-23"]),
        ("Nina Turnus", "12-timers", ["LEDIG", "12T NATT 19-07", "12T DAG 07-19", "LEDIG", "12T DAG 07-19"]),
        ("Per Kaffe", "3-skift", ["DAG 07-15", "LEDIG", "NATT 23-07", "LEDIG", "DAG 07-15"]),
        ("Trude Nattevakt", "natt-preferanse", ["NATT 23-07", "NATT 23-07", "LEDIG", "NATT 23-07", "LEDIG"]),
        ("Simen Stress", "3-skift", ["KVELD 14-23", "DAG 07-15", "LEDIG", "KVELD 14-23", "NATT 23-07"]),
        # Andre roller (ikke intensiv)
        ("Anne Vikar", "Vernepleier", "3-skift", ["DAG 07-15", "KVELD 14-23", "LEDIG", "DAG 07-15", "KVELD 14-23"]),
        ("Petter Gips", "Helsefagarbeider", "dag-kun", ["DAG 07-15", "DAG 07-15", "DAG 07-15", "LEDIG", "DAG 07-15"]),
        ("Mari Sprøyte", "Sykepleier", "3-skift", ["LEDIG", "NATT 23-07", "DAG 07-15", "KVELD 14-23", "LEDIG"]),
        ("Geir Skalpell", "Vernepleier", "12-timers", ["12T DAG 07-19", "LEDIG", "LEDIG", "12T DAG 07-19", "12T NATT 19-07"]),
        # Permisjon/ferie
        ("Kine Plaster", "Intensivsykepleier", "PERMISJON", ["FORELDREPERM", "FORELDREPERM", "FORELDREPERM", "FORELDREPERM", "FORELDREPERM"]),
        ("Jan EKG", "Intensivsykepleier", "FERIE", ["FERIE", "FERIE", "FERIE", "FERIE", "FERIE"]),
        # AML-brudd (for kort hviletid)
        ("Turid Puls", "Intensivsykepleier", "3-skift-kort-hvile", ["NATT 23-07", "LEDIG", "DAG 07-15", "KVELD 14-23", "DAG 07-15"]),
        ("Magnus Blod", "Intensivsykepleier", "12-timers-tett", ["12T NATT 19-07", "12T DAG 07-19", "LEDIG", "12T NATT 19-07", "LEDIG"]),
        # Sykemeldt/sykt barn
        ("Silje Sår", "Intensivsykepleier", "SYK", ["SYKEMELDT", "SYKEMELDT", "LEDIG", "SYKEMELDT", "SYKEMELDT"]),
        ("Bjarne Pille", "Intensivsykepleier", "SYKT BARN", ["HJEMME SYKT BARN", "HJEMME SYKT BARN", "LEDIG", "HJEMME SYKT BARN", "HJEMME SYKT BARN"]),
    ]

    fillers = []
    for data in fillers_data:
        if len(data) == 4:
            name, role, turnus_type, shifts = data
        else:
            name, turnus_type, shifts = data
            role = "Intensivsykepleier" if turnus_type not in ["Vernepleier", "Helsefagarbeider", "Sykepleier"] else turnus_type
            turnus_type = "standard" if turnus_type in ["Vernepleier", "Helsefagarbeider", "Sykepleier"] else turnus_type

        # Bestem status og exclusion_reason basert på turnus_type
        status = "AVAILABLE"
        exclusion_reason = None

        if turnus_type == "PERMISJON" or "FORELDREPERM" in shifts[0]:
            status = "PERMISJON"
        elif turnus_type == "FERIE" or "FERIE" in shifts[0]:
            status = "FERIE"
        elif turnus_type == "SYK" or "SYKEMELDT" in shifts[0]:
            status = "SYK"
        elif turnus_type == "SYKT BARN" or "HJEMME SYKT BARN" in shifts[0]:
            status = "SYKT BARN"
        # Sjekk for AML-brudd (tette vakter)
        elif turnus_type == "3-skift-kort-hvile":
            # Natt til dag uten nok hvile = AML brudd
            exclusion_reason = "Brudd på 11-timers hviletid (natt til dag)"
        elif turnus_type == "12-timers-tett":
            # Natt til 12t dag = for tett
            exclusion_reason = "Brudd på 11-timers hviletid (12t natt til 12t dag)"
        # Sjekk for feil kompetanse
        elif role in ["Vernepleier", "Helsefagarbeider"]:
            exclusion_reason = f"{role} - feil spesialisering for intensiv"

        fillers.append({
            "name": name,
            "role": role,
            "status": status,
            "shifts": shifts,
            "turnus_type": turnus_type,
            "exclusion_reason": exclusion_reason
        })

    return sick_person + audience + fillers


# Globale state-variabler
state = {
    "shift_request": {
        "active": False,
        "sick_name": None,
        "shift_type": None,
        "winner_name": None,
        "timestamp": None,
        "agent_analysis": None,
        "current_candidate_index": 0,  # Hvilken kandidat vi ringer nå (0, 1, 2)
        "candidate_queue": [],         # Den prioriterte rekkefølgen
        "candidate_start_time": None,  # Når vi begynte å vente på nåværende kandidat
        "candidate_timeout": 12,       # Sekunder å vente på hver kandidat
        "escalation_triggered": False, # Om bemanningsbyrå ble kontaktet
        "agency_worker": None          # Navn på vikar fra byrå
    },
    
    "colleagues": set(),
    "profiles": {},  # Deltaker-profiler (navn -> {rolle, %, status, ...})

    "turnus": {
        "dates": get_dates_for_week(),
        "rows": generate_complex_database()
    }
}

def analyze_with_deepseek(sick_name, shift_type, db, api_key):
    """
    Kaller ekte DeepSeek AI for å analysere kandidater.
    Returnerer (analysis_log, candidate_names).
    """
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    # Forbered ansattdata for AI
    employees_json = json.dumps([{
        "id": i,
        "name": p["name"],
        "role": p["role"],
        "contract_percentage": p["contract"],
        "status": p.get("status", "OK"),
        "shifts": p["shifts"],
        "exclusion_reason": p.get("exclusion_reason", "")
    } for i, p in enumerate(db)], ensure_ascii=False, indent=2)
    
    system_prompt = """Du er en AI Vaktplanlegger for Vestre Viken Sykehus.
Din oppgave er å analysere ansattlisten og finne de beste kandidatene for å dekke et akutt vaktskifte.

REGLER (i prioritert rekkefølge):
1. KOMPETANSE: Kun "Intensivsykepleier" kan ta vakten. Hjelpepleiere utelukkes.
2. LOVFESTET FRAVÆR: De med status FERIE, PERMISJON, eller SYKT BARN kan ikke jobbe.
3. ARBEIDSMILJØLOVEN: 
   - Ingen over 100% stilling (overtid)
   - 11-timers hviletid mellom vakter (sjekk forrige/neste dag)
4. VAKT-KOLLISJON: De som allerede jobber samme dag utelukkes.
5. PRIORITERING: Blant gyldige kandidater, velg høyest stillingsprosent først.

VIKTIG: Returner KUN et JSON-objekt med denne strukturen:
{
  "analysis": ["linje 1", "linje 2", ...],
  "candidates": ["Navn1", "Navn2", "Navn3"]
}
"""
    
    user_prompt = f"""AKUTT VAKTBEHOV:
- Sykepleier: {sick_name}
- Vakt-type: {shift_type}

ANSATTE I DATABASE:
{employees_json}

Analyser listen og returner JSON med:
1. Analyse-logg ( forklar hvem du utelukker og hvorfor )
2. Prioritert liste med kandidat-navn (kun Intensivsykepleiere som kan jobbe)"""

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000
            },
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        ai_content = result["choices"][0]["message"]["content"]
        
        # Parse JSON fra AI-respons
        # AI kan returnere med markdown ```json ... ``` så vi må rydde
        clean_content = ai_content.strip()
        if clean_content.startswith("```json"):
            clean_content = clean_content[7:]
        if clean_content.startswith("```"):
            clean_content = clean_content[3:]
        if clean_content.endswith("```"):
            clean_content = clean_content[:-3]
        clean_content = clean_content.strip()
        
        ai_result = json.loads(clean_content)
        
        analysis = ["🤖 DEEPSEEK AI ANALYSE"] + ai_result.get("analysis", [])
        candidates = ai_result.get("candidates", [])
        
        # Hvis AI returnerte tom liste, fallback til simulert
        if not candidates:
            raise ValueError("AI returnerte ingen kandidater")
            
        return analysis, candidates
        
    except Exception as e:
        # Fallback: marker som AI-feil og returner tomme lister
        analysis = [
            "⚠️ DeepSeek AI feilet (fallback til simulert)",
            f"Feil: {str(e)[:50]}...",
            ""
        ]
        return analysis, []


def generate_realistic_shifts_for_participant(participant_name, profile):
    """Genererer realistisk turnus for en deltaker basert på dagens dag."""
    import random

    # Få dagens indeks (0=mandag, 4=fredag)
    today_idx = datetime.now().weekday()
    if today_idx > 4:
        today_idx = 0  # Weekend -> mandag

    # Ulike turnusmønstre
    turnus_templates = [
        # 3-skift klassisk
        ["DAG 07-15", "KVELD 14-23", "NATT 23-07", "LEDIG", "DAG 07-15"],
        ["NATT 23-07", "LEDIG", "DAG 07-15", "KVELD 14-23", "LEDIG"],
        ["LEDIG", "DAG 07-15", "KVELD 14-23", "LEDIG", "NATT 23-07"],
        # 12-timers
        ["12T DAG 07-19", "LEDIG", "12T NATT 19-07", "LEDIG", "12T DAG 07-19"],
        ["LEDIG", "12T NATT 19-07", "12T DAG 07-19", "LEDIG", "12T DAG 07-19"],
        # Kun dag
        ["DAG 07-15", "DAG 07-15", "LEDIG", "DAG 07-15", "DAG 07-15"],
        ["DAG 07-15", "LEDIG", "DAG 07-15", "DAG 07-15", "LEDIG"],
        # Natt-preferanse
        ["NATT 23-07", "NATT 23-07", "LEDIG", "NATT 23-07", "LEDIG"],
    ]

    # Velg tilfeldig turnus basert på navn (konsistent)
    random.seed(participant_name)
    shifts = random.choice(turnus_templates)
    random.seed()  # Reset

    return shifts


def build_database_from_profiles():
    """Bygger dynamisk database fra deltaker-profiler + fyller på med fiktive folk."""
    profiles = state.get("profiles", {})

    # Start med den syke personen - realistisk 3-skift turnus
    db = [
        {"name": "Nils Dagenderpå", "role": "Intensivsykepleier", "status": "OK",
         "shifts": ["DAG 07-15", "KVELD 14-23", "LEDIG", "NATT 23-07", "DAG 07-15"],
         "turnus_type": "3-skift"}
    ]

    # Legg til deltakere som har registrert seg
    for name, profile in profiles.items():
        # Bygg exclusion_reason basert på profilen
        exclusion_reason = None
        priority_note = None

        # Sjekk kompetanse
        role = profile.get("role")
        if role == "Intensivsykepleier":
            priority_note = "Godkjent kompetanse"
        elif role == "Sykepleier":
            exclusion_reason = "Sykepleier må godkjennes - ikke autorisert for intensiv"
        elif role == "Vernepleier":
            exclusion_reason = "Vernepleier har feil spesialisering"
        else:
            exclusion_reason = "Mangler fagautorisasjon"

        # Sjekk status
        status = profile.get("status")
        if status == "FERIE":
            exclusion_reason = "Ferieavvikling"
        elif status == "PERMISJON":
            exclusion_reason = "I foreldrepermisjon"
        elif status in ["SYKT BARN", "SYK"]:
            exclusion_reason = "Egenmelding/Sykt barn"

        # Sjekk hviletid (11-timers regel)
        last_shift = profile.get("last_shift")
        if last_shift == "recent":
            exclusion_reason = "Kun 6 timer siden forrige vakt (brudd på 11-timers hvileregel)"
        elif last_shift == "yesterday":
            exclusion_reason = "9 timer siden forrige vakt (brudd på 11-timers hvileregel)"

        # Sjekk sykemeldingshistorikk
        if profile.get("sickleave") == "under6m":
            exclusion_reason = "Sykemeldt siste 6 måneder (kan ikke ta overtid etter AML)"

        # Sjekk om har vakt allerede
        if profile.get("has_shift", False):
            exclusion_reason = "Har allerede vakt i dag (kollisjon)"

        # Generer realistisk turnus for deltakeren
        shifts = generate_realistic_shifts_for_participant(name, profile)

        person = {
            "name": name,
            "role": role,
            "status": status,
            "shifts": shifts,
            "exclusion_reason": exclusion_reason,
            "priority_note": priority_note,
            "from_participant": True
        }
        db.append(person)

    # Fyll på med fiktive folk hvis få deltakere
    existing_names = {p["name"] for p in db}
    filler_names = [
        "Kari Vaktmester", "Ole Tidsklemme", "Lise Trøtt", "Bernt Overtid",
        "Siri Småbarnsmor", "Jonas Helse", "Nina Turnus", "Per Kaffe"
    ]

    reasons_pool = [
        "Brudd på 11-timers hviletid (vakt i natt 20-08)",
        "Sykemeldt siste 6 måneder (kan ikke ta overtid)",
        "I foreldrepermisjon",
        "Ferieavvikling",
        "Vernepleier - feil spesialisering",
        "Helsefagarbeider - mangler autorisasjon",
        "Egenmelding/Sykt barn",
        "Har allerede vakt i dag (DAG 08-20)"
    ]

    for name in filler_names:
        if name not in existing_names:
            reason = random.choice(reasons_pool)
            # Bestem rolle basert på årsak
            if "Vernepleier" in reason:
                role = "Vernepleier"
                status = "AVAILABLE"
            elif "Helsefagarbeider" in reason:
                role = "Helsefagarbeider"
                status = "AVAILABLE"
            elif "foreldrepermisjon" in reason:
                role = "Intensivsykepleier"
                status = "PERMISJON"
            elif "Ferie" in reason:
                role = "Intensivsykepleier"
                status = "FERIE"
            elif "Sykt barn" in reason or "Egenmelding" in reason:
                role = "Intensivsykepleier"
                status = "SYKT BARN"
            else:
                role = "Intensivsykepleier"
                status = "OK"

            db.append({
                "name": name,
                "role": role,
                "status": status,
                "shifts": ["FRI", "FRI", "FRI", "FRI", "FRI"],
                "exclusion_reason": reason if status == "OK" else None
            })

    return db


def analyze_candidates_for_shift(sick_name, shift_type, use_deepseek=False, api_key=None):
    """
    Kjernen i demoen: Agenten analyserer ansatte.
    Bygger dynamisk database fra deltaker-profiler.
    Hvis ingen kandidater -> escalation til bemanningsbyrå.
    """
    # BYGG DYNAMISK DATABASE fra deltaker-profiler
    db = build_database_from_profiles()
    total = len(db)

    # Oppdater state med ny database
    state["turnus"]["rows"] = db

    # Reset escalation-state
    state["shift_request"]["escalation_triggered"] = False
    state["shift_request"]["agency_worker"] = None

    # PRØV DEEPSEEK HVIS AKTIVERT
    if use_deepseek and api_key:
        try:
            analysis, candidate_names = analyze_with_deepseek(sick_name, shift_type, db, api_key)

            if candidate_names:
                state["shift_request"]["candidate_queue"] = candidate_names
                state["shift_request"]["current_candidate_index"] = 0
                state["shift_request"]["candidate_start_time"] = datetime.now().timestamp()

                analysis.append("")
                analysis.append(f"📱 Ringer Kandidat 1: {candidate_names[0]}...")
                return analysis
        except Exception as e:
            pass  # Fall gjennom til simulert

    # SIMULERT AI ANALYSE
    analysis = []
    analysis.append(f"⚡ SIMULERT AI: Starter analyse av {total} ansatte for akutt '{shift_type}'-dekning...")
    analysis.append(f"   (Inkluderer {len(state.get('profiles', {}))} deltakere med egne variabler)")

    # 1. Filtreringsregler - telling
    wrong_comp = [p for p in db if p.get("role") != "Intensivsykepleier"]
    analysis.append(f"❌ Utelukket {len(wrong_comp)} ansatte: Feil kompetanse/mangler autorisasjon.")

    leave = [p for p in db if p.get("status") in ["FERIE", "PERMISJON", "SYKT BARN", "SYK"]]
    analysis.append(f"❌ Utelukket {len(leave)} ansatte: Lovfestet fravær (Ferie/Permisjon/Sykdom).")

    # 11-timers hvileregel (brudd)
    rest_violation = [p for p in db if "11-timers" in (p.get("exclusion_reason") or "")]
    analysis.append(f"❌ Utelukket {len(rest_violation)} ansatte: Brudd på 11-timers hvileregel.")

    # Sykemelding siste 6m
    sickleave_violation = [p for p in db if "Sykemeldt siste 6 måneder" in (p.get("exclusion_reason") or "")]
    analysis.append(f"❌ Utelukket {len(sickleave_violation)} ansatte: Sykemeldt siste 6m (AML).")

    working = [p for p in db if (p.get("exclusion_reason") or "").startswith("Har allerede")]
    analysis.append(f"❌ Utelukket {len(working)} ansatte: Har allerede vakt (kollisjon).")

    # 2. Finn kvalifiserte kandidater
    candidates = [p for p in db if p.get("status") == "AVAILABLE"
                  and p.get("role") == "Intensivsykepleier"
                  and not p.get("exclusion_reason")]
    # Ingen prioritet basert på stillingsprosent - førstemann til mølla
    candidate_names = [c["name"] for c in candidates]

    # 3. ESKALERING: Hvis ingen kandidater, kontakt bemanningsbyrå
    if not candidates:
        analysis.append(f"")
        analysis.append(f"⚠️  INGEN KVALIFISERTE KANDIDATER FUNNET I LOKAL DATABASE!")
        analysis.append(f"📞 ESKALERER: Ringer bemanningsbyrå...")

        # Generer en vikar fra byrå
        agency_name = f"Vikar fra Byrå ({datetime.now().strftime('%H:%M')})"
        agency_worker = {
            "name": agency_name,
            "role": "Intensivsykepleier",
            "status": "AVAILABLE",
            "shifts": ["FRI", "FRI", "FRI", "FRI", "FRI"],
            "exclusion_reason": None,
            "from_agency": True
        }

        # Legg til i database
        state["turnus"]["rows"].append(agency_worker)
        candidate_names = [agency_name]

        analysis.append(f"✅ Bemanningsbyrå sendte vikar: {agency_name}")
        analysis.append(f"   Kompetanse: Intensivsykepleier (verifisert)")
        analysis.append(f"   Tilgjengelighet: Umiddelbar")

        # Marker at eskalering skjedde
        state["shift_request"]["escalation_triggered"] = True
        state["shift_request"]["agency_worker"] = agency_name

        analysis.append(f"")
        analysis.append(f"📱 Ringer vikar fra bemanningsbyrå...")
    else:
        analysis.append(f"")
        analysis.append(f"✅ FANT {len(candidates)} KVALIFISERTE KANDIDATER.")
        analysis.append(f"📊 Kandidater (førstemann til mølla):")
        for i, c in enumerate(candidates):
            analysis.append(f"   {i+1}. {c['name']}")

        analysis.append(f"")
        analysis.append(f"📱 Ringer Kandidat 1: {candidates[0]['name']}...")

    # Lagre køen i state
    state["shift_request"]["candidate_queue"] = candidate_names
    state["shift_request"]["current_candidate_index"] = 0
    state["shift_request"]["candidate_start_time"] = datetime.now().timestamp()

    return analysis


def mark_sick(name):
    """Markerer noen som syk i minnet på dagens dag."""
    day_idx = datetime.now().weekday()
    if day_idx > 4: day_idx = 0
    
    for row in state["turnus"]["rows"]:
        if row["name"] == name:
            orig = row["shifts"][day_idx]
            row["shifts"][day_idx] = f"❌ SYK ({orig})"
            break

def mark_replacement(sick_name, vikar_name):
    """Setter inn en vikar for den syke."""
    day_idx = datetime.now().weekday()
    if day_idx > 4: day_idx = 0
    
    for row in state["turnus"]["rows"]:
        if row["name"].lower() == vikar_name.lower() or (row["name"] == "Mette Prada Hansen" and "mette" in vikar_name.lower()):
            row["shifts"][day_idx] = f"✅ VIKAR for {sick_name}"
            if row["name"] != vikar_name and any(p in row["name"].lower() for p in vikar_name.lower().split()):
               return row["name"]
            break
            
    if not any(r["name"] == vikar_name for r in state["turnus"]["rows"]):
        new_row = {"name": vikar_name, "role": "Intensivsykepleier", "shifts": ["LEDIG", "LEDIG", "LEDIG", "LEDIG", "LEDIG"]}
        new_row["shifts"][day_idx] = f"✅ VIKAR for {sick_name}"
        state["turnus"]["rows"].insert(1, new_row)
        
    return vikar_name

def reset_turnus():
    """Tilbakestiller turnusplanen og all state."""
    state["turnus"]["rows"] = generate_complex_database()
    state["shift_request"]["agent_analysis"] = None
    state["shift_request"]["candidate_queue"] = []
    state["shift_request"]["current_candidate_index"] = 0
    state["shift_request"]["candidate_start_time"] = None
    state["shift_request"]["escalation_triggered"] = False
    state["shift_request"]["agency_worker"] = None
    state["profiles"] = {}  # Fjern deltaker-profiler
    state["colleagues"] = set()


def generate_reasoning_report():
    """Genererer et detaljert sammendrag av AI-tenkingen for nedlasting."""
    from datetime import datetime

    shift_req = state["shift_request"]
    turnus = state["turnus"]
    profiles = state.get("profiles", {})

    sick_name = shift_req.get("sick_name", "Ukjent")
    shift_type = shift_req.get("shift_type", "Ukjent")
    winner = shift_req.get("winner_name", "Ikke tildelt")
    analysis = shift_req.get("agent_analysis", [])
    candidates = shift_req.get("candidate_queue", [])
    ai_mode = state.get("ai_mode", "simulated")
    escalation = shift_req.get("escalation_triggered", False)
    agency_worker = shift_req.get("agency_worker", None)

    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    date_str = datetime.now().strftime("%d.%m.%Y")

    # Bygg HTML-rapport
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>AI Vaktplanlegging - Rapport {date_str}</title>
    <style>
        @media print {{
            body {{ font-size: 12pt; }}
            .no-print {{ display: none; }}
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{ color: #1F4E79; border-bottom: 3px solid #1F4E79; padding-bottom: 10px; }}
        h2 {{ color: #1565c0; margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        .header {{
            background: linear-gradient(135deg, #1F4E79 0%, #1565c0 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{ margin: 0; border: none; color: white; }}
        .meta {{ color: rgba(255,255,255,0.8); font-size: 14px; margin-top: 10px; }}
        .info-box {{
            background: #f5f7fa;
            border-left: 4px solid #1F4E79;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 0 8px 8px 0;
        }}
        .info-box h3 {{ margin-top: 0; color: #1F4E79; }}
        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .status-live {{ background: #4caf50; color: white; }}
        .status-sim {{ background: #ff9800; color: white; }}
        .analysis-log {{
            background: #1e1e1e;
            color: #00ff00;
            font-family: 'Consolas', 'Monaco', monospace;
            padding: 20px;
            border-radius: 8px;
            font-size: 14px;
            line-height: 1.8;
            overflow-x: auto;
        }}
        .analysis-log .timestamp {{ color: #888; }}
        .winner-box {{
            background: linear-gradient(135deg, #4caf50 0%, #388e3c 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            margin: 30px 0;
        }}
        .winner-box h2 {{ color: white; border: none; margin: 0; }}
        .winner-name {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
        .candidate-list {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
        }}
        .candidate {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .candidate:last-child {{ border-bottom: none; }}
        .candidate.selected {{
            background: #e8f5e9;
            border-left: 4px solid #4caf50;
            margin: 0 -15px;
            padding-left: 11px;
        }}
        .rank {{
            background: #1F4E79;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }}
        .print-btn {{
            background: #1F4E79;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            position: fixed;
            bottom: 30px;
            right: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .print-btn:hover {{ background: #1565c0; }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #eee;
            text-align: center;
            color: #666;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <button class="print-btn no-print" onclick="window.print()">🖨️ Skriv ut / Lagre som PDF</button>

    <div class="header">
        <h1>🏥 VESTRE VIKEN HF</h1>
        <div class="meta">AI Vaktplanlegging - Automatisk Generert Rapport</div>
        <div class="meta">Generert: {timestamp}</div>
    </div>

    <div class="info-box">
        <h3>📋 Saksinformasjon</h3>
        <p><strong>Fraværsmelding:</strong> {sick_name}</p>
        <p><strong>Vakt som må dekkes:</strong> {shift_type}</p>
        <p><strong>Dato:</strong> {date_str}</p>
        <p><strong>AI-modus:</strong>
            <span class="status-badge {'status-live' if ai_mode == 'live' else 'status-sim'}">
                {'🤖 DeepSeek AI' if ai_mode == 'live' else '⚡ Simulert AI'}
            </span>
        </p>
    </div>

    <h2>🧠 AI Analyse & Tenkeprosess</h2>
    <div class="analysis-log">
"""

    # Legg til analyseloggen
    for line in analysis:
        html += f"        <div>{line}</div>\n"

    html += f"""    </div>

    <h2>📊 Prioritert Kandidatliste</h2>
    <div class="candidate-list">
"""

    # Legg til kandidater
    for i, name in enumerate(candidates[:5], 1):  # Vis topp 5
        is_winner = name == winner
        selected_class = "selected" if is_winner else ""
        check = "✅ " if is_winner else ""
        html += f"""        <div class="candidate {selected_class}">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div class="rank">{i}</div>
                <div><strong>{check}{name}</strong></div>
            </div>
            {'<span style="color: #4caf50; font-weight: bold;">TILDELT VAKT</span>' if is_winner else ''}
        </div>
"""

    if winner and winner != "Ikke tildelt":
        html += f"""    </div>

    <div class="winner-box">
        <h2>✅ VAKT TILDELT</h2>
        <div class="winner-name">{winner}</div>
        <p>Vakten ble automatisk tildelt basert på AI-analyse</p>
    </div>
"""
    else:
        html += f"""    </div>

    <div class="info-box" style="border-left-color: #ff9800;">
        <h3>⏳ Status: Venter på respons</h3>
        <p>Vakten er ennå ikke tildelt. Kandidater kontaktes i prioritert rekkefølge.</p>
    </div>
"""

    html += f"""
    <h2>� Deltaker-profiler (Egne Variabler)</h2>
    <div class="candidate-list">
        {f'<p style="color: #666; font-size: 14px; text-align: center;">Ingen deltakere registrerte seg</p>' if not profiles else ''}
"""

    # Vis deltaker-profiler
    for name, profile in profiles.items():
        role_icon = "✅" if profile.get("role") == "Intensivsykepleier" else "❌"
        status_colors = {"AVAILABLE": "#4caf50", "FERIE": "#ff9800", "PERMISJON": "#9c27b0", "SYKT BARN": "#f44336", "SYK": "#f44336"}
        status_color = status_colors.get(profile.get("status"), "#666")
        status_text = profile.get("status", "Ukjent")

        # Sjekk ekstra felt
        rest_status = "✅ Hvile OK" if profile.get('last_shift') == 'long_ago' else ("⚠️ 9t siden" if profile.get('last_shift') == 'yesterday' else "❌ Kun 6t")
        sick_status = "✅ Sykemelding OK" if profile.get('sickleave') != 'under6m' else "❌ Sykemeldt <6m"

        html += f"""        <div class="candidate" style="border-left: 4px solid {status_color}; margin: 0 -20px; padding-left: 16px;">
            <div>
                <strong>{name}</strong><br>
                <small>{role_icon} {profile.get('role', '?')} | <span style="color: {status_color}">●</span> {status_text}</small><br>
                <small>{rest_status} | {sick_status}</small>
                {f'<br><small style="color: #f44336;">❌ Har allerede vakt</small>' if profile.get('has_shift') else ''}
            </div>
        </div>
"""

    html += """    </div>

    <h2>�� Statistikk</h2>
    <div class="info-box">
        <p><strong>Totalt antall ansatte analysert:</strong> {len(turnus['rows'])}</p>
        <p><strong>Kvalifiserte kandidater funnet:</strong> {len(candidates)}</p>
        <p><strong>Deltakere med egne variabler:</strong> {len(profiles)}</p>
        <p><strong>Filtreringskriterier brukt:</strong> 5 (Kompetanse/Autorisasjon, Lovfestet fravær, 11-timers hvileregel, Sykemelding <6m, Vakt-kollisjon)</p>
        {f'<p style="color: #ff9800; margin-top: 10px;"><strong>⚠️ Eskalering:</strong> Bemanningsbyrå ble kontaktet</p>' if escalation else ''}
        {f'<p style="color: #4caf50; margin-top: 5px;"><strong>✅ Vikar fra byrå:</strong> {agency_worker}</p>' if agency_worker else ''}
    </div>

    <div class="footer">
        <p>🏥 Vestre Viken HF - Vaktplanleggingssystem</p>
        <p>Denne rapporten er automatisk generert av AI-agenten</p>
        <p>Rapport ID: VV-{datetime.now().strftime('%Y%m%d-%H%M%S')}</p>
    </div>

</body>
</html>"""

    return html
