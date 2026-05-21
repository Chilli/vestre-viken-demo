"""
Global State for Vestre Viken Demo.
Håndterer hvem som har koblet seg til, og status på aktive vaktforespørsler.
"""

state = {
    # Active shift request
    "shift_request": {
        "active": False,
        "sick_name": None,
        "shift_type": None,  # F.eks "DAG 08-20"
        "winner_name": None,
        "timestamp": None
    },
    
    # Registered colleagues (publikum som har registrert seg via mobilen)
    "colleagues": set()
}
