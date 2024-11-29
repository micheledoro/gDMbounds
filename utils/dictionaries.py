# ~/disctionaries.py

# Dictionary for instrument classes
instrument_classes = {
    "iact": {"description": "Imaging Atmospheric Cherenkov Telescopes",},
    "sfd": {"description": "Shower Front Detectors",},
    "sat": {"description": "Satellite-Borne Pair Production",},
    # Add more instrument classes here
}

target_class = {
    "dsph": {"description":"Dwarf Spheroidal Galaxies",},
    "dirr": {"description":"Dwarf Irregular Galaxies",},
    "gacluster": {"description":"Galaxy Cluster",},
    "glcluster": {"description":"Globular Cluster",},
# Add more instrument classes here
}

# Dizionario per strumenti
instruments = {
    "hess": {
        "name": "H.E.S.S.",
        "description": "High Energy Stereoscopic System",
        "class": instrument_classes["iact"], 
    },
    # Aggiungi altri strumenti qui
}

# Dizionario per canali di annichilazione
annihilation_channels = {
    "KK": {
        "description": "Kaluza-Klein",
    },
    # Aggiungi altri canali qui
}

# Dizionario per canali di annichilazione
dm_reaction_modes = {
    "annihilation": {
        "description": "Annihilating DM",
        "shortname": "ann",
    },
    "decay": {
        "description": "Decay DM",
        "shortname": "dec",
    },
    # Aggiungi altri canali qui
}

# Dizionario per target
targets = {
    "sagittarius": {
        "description": "Sagittarius Dwarf Galaxy",
        "class": target_class["dsph"],
        "shortname": "Sgr"
    },
    # Aggiungi altri target qui
}