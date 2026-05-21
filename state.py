"""
Global State for Vestre Viken Demo.
Inneholder minne-basert "database" for hele appen med en stor, kompleks ansattliste.
"""

from datetime import datetime, timedelta
import random

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

def analyze_candidates_for_shift(sick_name, shift_type):
    """
    Kjernen i demoen: Agenten simulerer en dyp analyse av 30+ ansatte.
    Returnerer en prioritert kø av kandidater.
    """
    total = len(state["turnus"]["rows"])
    db = state["turnus"]["rows"]
    
    analysis = []
    analysis.append(f"🔍 Starter analyse av {total} ansatte for akutt '{shift_type}'-dekning...")
    
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
