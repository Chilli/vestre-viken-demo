"""
Global State for Vestre Viken Demo.
Inneholder minne-basert "database" for hele appen (i stedet for Excel).
"""

from datetime import datetime, timedelta

def get_dates_for_week():
    """Hjelpefunksjon for å finne datoer for gjeldende uke (mandag-fredag)"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    dates = []
    for i in range(5):
        dates.append((monday + timedelta(days=i)).strftime("%d.%m.%Y"))
    return dates

def get_initial_turnus():
    """Lager en standard turnusplan i minnet."""
    return [
        {"name": "Nils Dagenderpå", "shifts": ["DAG 08-20", "NATT 20-08", "FRI", "DAG 08-20", "DAG 08-20"]},
        {"name": "Mette Prada Hansen", "shifts": ["KVELD 14-22", "FRI", "DAG 08-20", "FRI", "KVELD 14-22"]},
        {"name": "Wes Side Story", "shifts": ["NATT 20-08", "DAG 08-20", "FRI", "NATT 20-08", "FRI"]},
        {"name": "Dr. Anton Graff", "shifts": ["FRI", "KVELD 14-22", "KVELD 14-22", "FRI", "NATT 20-08"]},
        {"name": "Kari Vaktmester", "shifts": ["DAG 08-20", "DAG 08-20", "NATT 20-08", "FRI", "FRI"]},
        {"name": "Ole Tidsklemme", "shifts": ["FRI", "FRI", "DAG 08-20", "DAG 08-20", "KVELD 14-22"]},
        {"name": "Lise Trøtt", "shifts": ["NATT 20-08", "NATT 20-08", "FRI", "KVELD 14-22", "FRI"]}
    ]

# Globale state-variabler
state = {
    # Active shift request (når alarmen går)
    "shift_request": {
        "active": False,
        "sick_name": None,
        "shift_type": None,
        "winner_name": None,
        "timestamp": None
    },
    
    # Registered colleagues (publikum som har registrert seg via mobilen)
    "colleagues": set(),

    # Selve turnusplanen
    "turnus": {
        "dates": get_dates_for_week(),
        "rows": get_initial_turnus()
    }
}

def mark_sick(name):
    """Markerer noen som syk i minnet på dagens dag."""
    day_idx = datetime.now().weekday()
    if day_idx > 4: day_idx = 0  # Helg -> Mandag
    
    for row in state["turnus"]["rows"]:
        if row["name"] == name:
            orig = row["shifts"][day_idx]
            row["shifts"][day_idx] = f"❌ SYK ({orig})"
            break

def mark_replacement(sick_name, vikar_name):
    """Setter inn en vikar for den syke."""
    day_idx = datetime.now().weekday()
    if day_idx > 4: day_idx = 0
    
    # Finn og oppdater vikarens rad
    for row in state["turnus"]["rows"]:
        if row["name"].lower() == vikar_name.lower() or (row["name"] == "Mette Prada Hansen" and "mette" in vikar_name.lower()):
            row["shifts"][day_idx] = f"✅ VIKAR for {sick_name}"
            # Standardiser navn hvis det ikke matchet 100%
            if row["name"] != vikar_name and any(p in row["name"].lower() for p in vikar_name.lower().split()):
               return row["name"]
            break
            
    # Hvis personen ikke fantes fra før i tabellen, legger vi dem til
    if not any(r["name"] == vikar_name for r in state["turnus"]["rows"]):
        new_row = {"name": vikar_name, "shifts": ["FRI", "FRI", "FRI", "FRI", "FRI"]}
        new_row["shifts"][day_idx] = f"✅ VIKAR for {sick_name}"
        state["turnus"]["rows"].insert(1, new_row)
        
    return vikar_name

def reset_turnus():
    """Tilbakestiller turnusplanen."""
    state["turnus"]["rows"] = get_initial_turnus()
