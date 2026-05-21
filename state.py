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
    """Lager en stor fiktiv database med ansatte, stillingsprosent og restriksjoner."""
    
    # De 3 publikummerne (Sjefene som skal få vakten til slutt)
    # Rangert etter optimalitet: Mette (80%) > Anton (75%) > Wes (60%)
    audience = [
        {"name": "Mette Prada Hansen", "role": "Intensivsykepleier", "contract": 80, "status": "AVAILABLE", "shifts": ["FRI", "DAG 08-20", "FRI", "FRI", "KVELD 14-22"]},
        {"name": "Dr. Anton Graff", "role": "Intensivsykepleier", "contract": 75, "status": "AVAILABLE", "shifts": ["FRI", "KVELD 14-22", "FRI", "DAG 08-20", "NATT 20-08"]},
        {"name": "Wes Side Story", "role": "Intensivsykepleier", "contract": 60, "status": "AVAILABLE", "shifts": ["FRI", "DAG 08-20", "FRI", "NATT 20-08", "FRI"]},
    ]
    
    # Den som blir syk
    sick_person = [
        {"name": "Nils Dagenderpå", "role": "Intensivsykepleier", "contract": 100, "status": "OK", "shifts": ["DAG 08-20", "NATT 20-08", "FRI", "DAG 08-20", "DAG 08-20"]}
    ]
    
    # Fyll på med masse fiktive folk som Agenten må filtrere UT
    fillers_names = [
        "Kari Vaktmester", "Ole Tidsklemme", "Lise Trøtt", "Bernt Overtid", "Siri Småbarnsmor", 
        "Jonas Helse", "Nina Turnus", "Per Kaffe", "Trude Nattevakt", "Simen Stress",
        "Anne Vikar", "Petter Gips", "Mari Sprøyte", "Geir Skalpell", "Kine Plaster",
        "Jan EKG", "Turid Puls", "Magnus Blod", "Silje Sår", "Bjarne Pille",
        "Hanne Seng", "Rune Rullestol", "Vilde Krykke", "Knut Kateter", "Gro Bandasje"
    ]
    
    fillers = []
    for name in fillers_names:
        # Lag ulike grunner til at de ikke kan ta vakten i dag
        reasons = [
            ("Overstiger 100% (Arbeidsmiljøloven)", 100, "OK", ["DAG 08-20", "DAG 08-20", "DAG 08-20", "DAG 08-20", "DAG 08-20"]),
            ("Brudd på 11-timers hviletid", 80, "OK", ["NATT 20-08", "FRI", "DAG 08-20", "FRI", "DAG 08-20"]),
            ("I foreldrepermisjon", 100, "PERMISJON", ["PERMISJON", "PERMISJON", "PERMISJON", "PERMISJON", "PERMISJON"]),
            ("Ferieavvikling", 100, "FERIE", ["FERIE", "FERIE", "FERIE", "FERIE", "FERIE"]),
            ("Feil kompetanse (Hjelpepleier)", 80, "OK", ["FRI", "FRI", "DAG 08-20", "DAG 08-20", "DAG 08-20"]),
            ("Egenmelding Sykt Barn", 80, "SYKT BARN", ["SYKT BARN", "SYKT BARN", "DAG 08-20", "FRI", "FRI"]),
            ("Har allerede vakt i dag", 80, "OK", ["KVELD 14-22", "FRI", "FRI", "DAG 08-20", "DAG 08-20"])
        ]
        
        reason, contract, status, shifts = random.choice(reasons)
        role = "Hjelpepleier" if "kompetanse" in reason else "Sykepleier"
        
        fillers.append({
            "name": name,
            "role": role,
            "contract": contract,
            "status": status,
            "shifts": shifts,
            "exclusion_reason": reason
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
        "candidate_timeout": 12        # Sekunder å vente på hver kandidat
    },
    
    "colleagues": set(),

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


def analyze_candidates_for_shift(sick_name, shift_type, use_deepseek=False, api_key=None):
    """
    Kjernen i demoen: Agenten analyserer ansatte.
    Hvis use_deepseek=True og api_key, bruker ekte DeepSeek AI.
    Ellers: simulert analyse.
    """
    total = len(state["turnus"]["rows"])
    db = state["turnus"]["rows"]
    
    # PRØV DEEPSEEK FØRST HVIS AKTIVERT
    if use_deepseek and api_key:
        try:
            analysis, candidate_names = analyze_with_deepseek(sick_name, shift_type, db, api_key)
            
            # Hvis DeepSeek returnerte kandidater, bruk dem
            if candidate_names:
                state["shift_request"]["candidate_queue"] = candidate_names
                state["shift_request"]["current_candidate_index"] = 0
                state["shift_request"]["candidate_start_time"] = datetime.now().timestamp()
                
                analysis.append("")
                analysis.append(f"� Ringer Kandidat 1: {candidate_names[0]}...")
                return analysis
            # Hvis tom liste, fall gjennom til simulert
        except Exception as e:
            # Fortsett til simulert
            pass
    
    # SIMULERT AI (fallback eller standard)
    analysis = []
    analysis.append(f"⚡ SIMULERT AI: Starter analyse av {total} ansatte for akutt '{shift_type}'-dekning...")
    
    # 1. Fjern de med feil kompetanse
    wrong_comp = [p for p in db if p.get("role") == "Hjelpepleier"]
    analysis.append(f"❌ Utelukket {len(wrong_comp)} ansatte: Feil kompetanse (krever Intensivsykepleier).")
    
    # 2. Fjern de på ferie/permisjon
    leave = [p for p in db if p.get("status") in ["FERIE", "PERMISJON", "SYKT BARN"]]
    analysis.append(f"❌ Utelukket {len(leave)} ansatte: Lovfestet fravær (Ferie/Permisjon/Sykt barn).")
    
    # 3. Arbeidsmiljøloven (100% stilling eller hviletid)
    aml = [p for p in db if p.get("exclusion_reason", "").startswith("Overstiger") or p.get("exclusion_reason", "").startswith("Brudd")]
    analysis.append(f"❌ Utelukket {len(aml)} ansatte: AML-brudd (11-timers hvile / 100% overtid).")
    
    # 4. Jobber allerede
    working = [p for p in db if p.get("exclusion_reason", "").startswith("Har allerede")]
    analysis.append(f"❌ Utelukket {len(working)} ansatte: Tildelt annen vakt (kollisjon).")
    
    # 5. Prioriter kandidatene (høyest stillingsprosent først)
    candidates = [p for p in db if p.get("status") == "AVAILABLE" and p.get("role") == "Intensivsykepleier"]
    candidates.sort(key=lambda x: x["contract"], reverse=True)
    
    candidate_names = [c["name"] for c in candidates]
    analysis.append(f"✅ FANT {len(candidates)} KVALIFISERTE KANDIDATER.")
    analysis.append(f"📊 Prioritering (høyest stillingsprosent først):")
    for i, c in enumerate(candidates):
        analysis.append(f"   {i+1}. {c['name']} ({c['contract']}% stilling)")
    
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
        new_row = {"name": vikar_name, "role": "Intensivsykepleier", "shifts": ["FRI", "FRI", "FRI", "FRI", "FRI"]}
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
