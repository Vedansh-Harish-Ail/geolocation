LANDING_HIGHLIGHTS = [
    {
        "title": "Indoor Wayfinding",
        "description": "Provide instant step-by-step indoor directions to your destination.",
        "label": "01",
    },
    {
        "title": "Digital Directory",
        "description": "Maintain a live directory of campus departments, labs, and student services.",
        "label": "02",
    },
    {
        "title": "Safety Monitoring",
        "description": "Monitor campus safety alerts and emergency response zones from a central console.",
        "label": "03",
    },
    {
        "title": "Asset Management",
        "description": "Track important campus equipment and hardware infrastructure in real-time.",
        "label": "04",
    },
]

LANDING_METRICS = [
    {"value": "0", "label": "mapped destinations"},
    {"value": "24/7", "label": "system availability"},
]

OPERATIONS_PANELS = [
    {
        "title": "Asset Tracking Dashboard",
        "description": "Track device status, occupancy, maintenance, and movement alerts.",
        "href": "/ops/assets",
    },
    {
        "title": "Safety & Analytics Console",
        "description": "Monitor crowd hotspots, panic triggers, and emergency events.",
        "href": "/ops/safety",
    },
    {
        "title": "Hardware Configuration",
        "description": "Manage beacon inventory and signal calibration for indoor positioning.",
        "href": "/ops/hardware",
    },
]

DIRECTORY_SECTIONS = [
    {"id": "all", "name": "All Spaces"},
    {"id": "academic", "name": "Academic Buildings"},
    {"id": "library", "name": "Libraries"},
    {"id": "dining", "name": "Dining"},
    {"id": "admin", "name": "Administrative Offices"},
]

DIRECTORY_ENTRIES = []

ASSET_METRICS = [
    {"label": "Total Assets Tracked", "value": "0", "tone": "primary"},
    {"label": "Current Occupancy", "value": "0%", "tone": "teal"},
    {"label": "Active Alerts", "value": "0", "tone": "amber", "subtext": "System clear"},
]

ASSET_STATUS_SEGMENTS = [
    {"label": "Active", "value": 0, "color": "#2d8cff"},
    {"label": "In Transit", "value": 0, "color": "#ff8b3d"},
    {"label": "Maintenance", "value": 0, "color": "#f4c76a"},
]

SECURITY_ALERTS = []

ASSET_INVENTORY = []

SAFETY_PROTOCOLS = [
    "Trigger site-wide alert",
    "Activate evacuation routes",
]

SAFETY_EVENTS = []

PANIC_TRIGGERS = []

SAFETY_HEAT_ZONES = []

BEACON_INVENTORY = []

FIRMWARE_STATUS = {
    "version": "v1.0.0",
    "progress": 0,
    "signal_strength": 0,
    "calibration_offset": 0,
}
