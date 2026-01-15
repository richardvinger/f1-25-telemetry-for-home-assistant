"""Constants for the F1 25 Telemetry integration."""

from typing import Final

DOMAIN: Final = "f1_25_telemetry"
CONF_PORT: Final = "port"
CONF_FORWARD_ENABLED: Final = "forward_enabled"
CONF_FORWARD_IP: Final = "forward_ip"
CONF_FORWARD_PORT: Final = "forward_port"

DEFAULT_PORT: Final = 20777

# Detailed Packet IDs from spec
PACKET_ID_MOTION = 0
PACKET_ID_SESSION = 1
PACKET_ID_LAP_DATA = 2
PACKET_ID_EVENT = 3
PACKET_ID_PARTICIPANTS = 4
PACKET_ID_CAR_SETUPS = 5
PACKET_ID_CAR_TELEMETRY = 6
PACKET_ID_CAR_STATUS = 7
PACKET_ID_FINAL_CLASSIFICATION = 8
PACKET_ID_LOBBY_INFO = 9
PACKET_ID_CAR_DAMAGE = 10
PACKET_ID_SESSION_HISTORY = 11
PACKET_ID_TYRE_SETS = 12
PACKET_ID_MOTION_EX = 13
PACKET_ID_TIME_TRIAL = 14
PACKET_ID_LAP_POSITIONS = 15

# New Participant Packet
PACKET_ID_PARTICIPANTS = 4

# Device ID for persistent grouping
DEVICE_ID = "f1_25_telemetry_device"
# Packet Sizes (Bytes) for sanity checking
PACKET_HEADER_SIZE = 29
PACKET_SIZES = {
    PACKET_ID_MOTION: 1349,
    PACKET_ID_SESSION: 753,
    PACKET_ID_LAP_DATA: 1285,
    PACKET_ID_EVENT: 45,
    PACKET_ID_PARTICIPANTS: 1284,
    PACKET_ID_CAR_SETUPS: 1133,
    PACKET_ID_CAR_TELEMETRY: 1352,
    PACKET_ID_CAR_STATUS: 1239,
    PACKET_ID_FINAL_CLASSIFICATION: 1042,
    PACKET_ID_LOBBY_INFO: 954,
    PACKET_ID_CAR_DAMAGE: 1041,
    PACKET_ID_SESSION_HISTORY: 1460,
    PACKET_ID_TYRE_SETS: 231,
    PACKET_ID_MOTION_EX: 273,
}

# Weather IDs
WEATHER_CLEAR = 0
WEATHER_LIGHT_CLOUD = 1
WEATHER_OVERCAST = 2
WEATHER_LIGHT_RAIN = 3
WEATHER_HEAVY_RAIN = 4
WEATHER_STORM = 5

WEATHER_MAP = {
    WEATHER_CLEAR: "sunny",
    WEATHER_LIGHT_CLOUD: "partlycloudy",
    WEATHER_OVERCAST: "cloudy",
    WEATHER_LIGHT_RAIN: "rainy",
    WEATHER_HEAVY_RAIN: "pouring",
    WEATHER_STORM: "lightning-rainy",
}

# Safety Car Status
SAFETY_CAR_NONE = 0
SAFETY_CAR_FULL = 1
SAFETY_CAR_VIRTUAL = 2
SAFETY_CAR_FORMATION_LAP = 3

SAFETY_CAR_STATUS_MAP = {
    SAFETY_CAR_NONE: "No Safety Car",
    SAFETY_CAR_FULL: "Safety Car",
    SAFETY_CAR_VIRTUAL: "Virtual Safety Car",
    SAFETY_CAR_FORMATION_LAP: "Formation Lap",
}

# FIA Flags
FIA_FLAG_UNKNOWN = -1
FIA_FLAG_NONE = 0
FIA_FLAG_GREEN = 1
FIA_FLAG_BLUE = 2
FIA_FLAG_YELLOW = 3
FIA_FLAG_RED = 4 # Not explicitly in list 559 but 193 mentions red flags

FIA_FLAG_MAP = {
    FIA_FLAG_UNKNOWN: "Unknown",
    FIA_FLAG_NONE: "None",
    FIA_FLAG_GREEN: "Green",
    FIA_FLAG_BLUE: "Blue",
    FIA_FLAG_YELLOW: "Yellow",
    FIA_FLAG_RED: "Red",
}

# ERS Deploy Modes
ERS_MODE_NONE = 0
ERS_MODE_MEDIUM = 1
ERS_MODE_HOTLAP = 2
ERS_MODE_OVERTAKE = 3

ERS_MODE_MAP = {
    ERS_MODE_NONE: "None",
    ERS_MODE_MEDIUM: "Medium",
    ERS_MODE_HOTLAP: "Hotlap",
    ERS_MODE_OVERTAKE: "Overtake",
}

# Tyre Compounds (Visual)
TYRE_COMPOUND_SOFT = 16
TYRE_COMPOUND_MEDIUM = 17
TYRE_COMPOUND_HARD = 18
TYRE_COMPOUND_INTER = 7
TYRE_COMPOUND_WET = 8

TYRE_COMPOUND_MAP = {
    TYRE_COMPOUND_SOFT: "Soft",
    TYRE_COMPOUND_MEDIUM: "Medium",
    TYRE_COMPOUND_HARD: "Hard",
    TYRE_COMPOUND_INTER: "Inter",
    TYRE_COMPOUND_WET: "Wet",
}

# Session Types (Partial list relative to interest)
SESSION_TYPE_UNKNOWN = 0
SESSION_TYPE_P1 = 1
SESSION_TYPE_P2 = 2
SESSION_TYPE_P3 = 3
SESSION_TYPE_SHORT_P = 4
SESSION_TYPE_Q1 = 5
SESSION_TYPE_Q2 = 6
SESSION_TYPE_Q3 = 7
SESSION_TYPE_SHORT_Q = 8
SESSION_TYPE_OSQ = 9
SESSION_TYPE_R = 10
SESSION_TYPE_R2 = 11
SESSION_TYPE_R3 = 12
SESSION_TYPE_TIME_TRIAL = 13

SESSION_TYPE_MAP = {
    SESSION_TYPE_UNKNOWN: "Unknown",
    SESSION_TYPE_P1: "Practice 1",
    SESSION_TYPE_P2: "Practice 2",
    SESSION_TYPE_P3: "Practice 3",
    SESSION_TYPE_SHORT_P: "Short Practice",
    SESSION_TYPE_Q1: "Qualifying 1",
    SESSION_TYPE_Q2: "Qualifying 2",
    SESSION_TYPE_Q3: "Qualifying 3",
    SESSION_TYPE_SHORT_Q: "Short Qualifying",
    SESSION_TYPE_OSQ: "One-Shot Qualifying",
    SESSION_TYPE_R: "Race",
    SESSION_TYPE_R2: "Race 2",
    SESSION_TYPE_R3: "Race 3",
    SESSION_TYPE_TIME_TRIAL: "Time Trial",
}

# Track IDs mapping (2025 spec)
TRACK_MAP = {
    0: "Melbourne",
    1: "Paul Ricard",
    2: "Shanghai",
    3: "Sakhir (Bahrain)",
    4: "Catalunya",
    5: "Monaco",
    6: "Montreal",
    7: "Silverstone",
    8: "Hockenheim",
    9: "Hungaroring",
    10: "Spa",
    11: "Monza",
    12: "Singapore",
    13: "Suzuka",
    14: "Abu Dhabi",
    15: "Texas",
    16: "Brazil",
    17: "Austria",
    18: "Sochi",
    19: "Mexico",
    20: "Baku",
    21: "Sakhir Short",
    22: "Silverstone Short",
    23: "Texas Short",
    24: "Suzuka Short",
    25: "Hanoi",
    26: "Zandvoort",
    27: "Imola",
    28: "Portimao",
    29: "Jeddah",
    30: "Miami",
    31: "Las Vegas",
    32: "Losail",
}
