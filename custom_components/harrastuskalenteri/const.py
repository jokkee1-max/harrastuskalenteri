DOMAIN = "harrastuskalenteri"
PLATFORMS = ["sensor", "switch"]

CHILDREN = {
    "elias": "Elias",
    "amanda": "Amanda",
    "lydia": "Lydia",
    "linda": "Linda",
    "linnea": "Linnea",
}

DEFAULT_CALENDARS = {
    "elias": ["calendar.eliasfutis", "calendar.elias_golf", "calendar.elias_koris"],
    "amanda": ["calendar.amandafutis"],
    "lydia": ["calendar.lydiafutis", "calendar.lyyli_voimistely"],
    "linda": ["calendar.lunat"],
    "linnea": ["calendar.nune_voimisteou"],
}
