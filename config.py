"""
config.py — ALL constants for the desktop cat.
Single source of truth. Every import reads from here.
No runtime changes. All values are final per session.
"""

import os
from PyQt6.QtGui import QColor, QFont

DEBUG = False  # Set True for verbose logging during development

# ─── Debug ──────────────────────────────────────────────────────────────
# DEBUG is at top, after imports

# ─── Window (full-screen overlay) ──────────────────────────────────────
CAT_BASELINE = 20        # px above screen bottom for cat base

# ─── Timing ───────────────────────────────────────────────────────────────
TICK_MS = 50
TICK_S = TICK_MS / 1000.0     # 0.05

SAVE_INTERVAL = 30.0          # Persist state every N seconds
IDLE_SLEEP_DELAY = 120.0      # System-idle seconds before deep sleep

# ─── Needs Rates (per second) ─────────────────────────────────────────────
ENERGY_DRAIN_ACTIVE  = 0.02
ENERGY_DRAIN_SIT     = 0.003
ENERGY_RECHARGE_SLEEP = 0.08
HUNGER_DRAIN         = 0.003
BOREDOM_INCREASE_SIT = 0.005

# ─── Movement ─────────────────────────────────────────────────────────────
WALK_SPEED      = 80.0   # px/s
WALK_ACCEL_TIME = 0.4   # seconds to reach full speed
WALK_DURATION_MIN = 0.5

# ─── 2D Movement ────────────────────────────────────────────────────────────
CAT_MIN_Y_FRACTION = 0.35   # cat won't go above this fraction of screen height

# ─── States ───────────────────────────────────────────────────────────────
STATE_SIT     = "SIT"
STATE_WALK    = "WALK"
STATE_SLEEP   = "SLEEP"
STATE_GO_HOME = "GO_HOME"
STATE_WANDER  = "WANDER"
STATE_CHASE   = "CHASE"
STATE_PLAY    = "PLAY"

# ─── Wander behavior ──────────────────────────────────────────────────────
WANDER_DURATION_MIN = 2.0     # min seconds per wander walk
WANDER_DURATION_MAX = 5.0     # max seconds per wander walk
WANDER_BASE_CHANCE  = 0.002   # per-tick base chance to wander when sitting
WANDER_COOLDOWN     = 45.0    # seconds between wander sessions
WANDER_OFFSET      = 60      # px from screen edges (don't hug walls)
WANDER_TURN_CHANCE  = 0.01   # per-tick chance to reverse direction

# ─── Paths ────────────────────────────────────────────────────────────────
STATE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "Nova", "desktop-cat"
)
STATE_PATH = os.path.join(STATE_DIR, "state.json")

# ─── HTTP API ─────────────────────────────────────────────────────────────
API_PORT = 18789

# ─── Hut / Home (screen-relative) ─────────────────────────────────────────
HUT_WIDTH     = 60    # total hut width in px
HUT_HEIGHT    = 55    # total hut height in px
HUT_ROOF_OVERHANG = 6   # roof extends past walls
HUT_DOOR_W    = 22    # door opening width
HUT_DOOR_H    = 30    # door opening height
HUT_DOOR_FLOOR = 6    # floor/threshold height below door
HUT_PADDING_RIGHT = 20
HUT_PADDING_BOTTOM = 48
HOME_TOLERANCE = 2.0    # px near-enough when arriving

HOME_ENERGY_THRESHOLD  = 40.0  # energy below this → go home
HOME_NAP_MIN_ENERGY    = 60.0  # wake from home nap when energy reaches this
HOME_LINGER_DURATION   = 8.0   # seconds to sit near hut after waking
HOME_VISIT_COOLDOWN    = 90.0  # min seconds between home visits
HOME_BOREDOM_THRESHOLD = 70.0  # boredom above this → go home nap

# ─── Colors ───────────────────────────────────────────────────────────────
C_BODY      = QColor(0x7C, 0x8E, 0x9E)   # steel gray-blue (Russian Blue)
C_BELLY     = QColor(0xD4, 0xD9, 0xDE)   # light warm gray
C_SHADOW    = QColor(0, 0, 0, 25)        # translucent black
C_PAW       = QColor(0xCC, 0xD5, 0xDC)   # paw pads — muted pink-gray

C_INNER_EAR = QColor(0xFF, 0xB8, 0xC6)   # soft pink inner ear
C_NOSE      = QColor(0xFF, 0x94, 0x94)   # soft coral pink
C_WHISKER   = QColor(0xA8, 0xB0, 0xB8)   # light gray

C_EYE_WHITE  = QColor(0xFF, 0xFF, 0xFF)  # pure white sclera
C_IRIS       = QColor(0x6B, 0xA3, 0xD6)  # soft blue iris
C_PUPIL      = QColor(0x1A, 0x1A, 0x1A)  # near-black
C_CLOSED_EYE = QColor(0x5C, 0x4A, 0x3D)  # warm brown for closed-eye arc
C_BLUSH      = QColor(0xFF, 0xCD, 0xD2, 100)

# Hut
HUT_INTERIOR_COLOR = QColor(0x1A, 0x1A, 0x1A, 200)  # dark
HUT_WALL_COLOR = QColor(0xD4, 0xA5, 0x74)         # warm wood brown
HUT_ROOF_COLOR = QColor(0xB8, 0x7A, 0x4A)          # darker brown
HUT_ACCENT_COLOR = QColor(0xE8, 0xD5, 0xC0)        # light trim
C_Z_BADGE   = QColor(0xCC, 0xCC, 0xCC, 200)

# Effects
C_ZZZ = QColor(0xBB, 0xBB, 0xBB, 180)
ZZZ_FONT = QFont("Segoe UI", 9)

# ─── Drawing Dimensions ───────────────────────────────────────────────────
HEAD_R        = 14
EAR_W         = 8
EAR_H         = 10
EAR_OFFSET    = 11
EYE_R         = 4
PUPIL_R       = 2.5
WHISKER_LEN   = 12

# ─── Speech Bubble ──────────────────────────────────────────────────────────
SPEECH_BUBBLE_W = 140
SPEECH_CELL_TOP_H = 30
SPEECH_CELL_BOT_H = 20
SPEECH_ABOVE_GAP = 20
SPEECH_BELOW_GAP = 50
SPEECH_FADE_IN = 0.3       # seconds
SPEECH_DISPLAY = 3.0       # base seconds
SPEECH_FADE_OUT = 0.5      # seconds
SPEECH_MAX_CHARS = 15
SPEECH_QUEUE_MAX = 5       # max queued messages
SPEECH_IDLE_COOLDOWN = 60  # seconds between idle bubbles
SPEECH_IDLE_THRESHOLD = 120  # seconds idle before "hello?"
SPEECH_PROXIMITY_RADIUS = 60  # px
SPEECH_PROXIMITY_COOLDOWN = 15  # seconds

MOOD_PRIORITY = {
    "hungry": 3,
    "alert": 3,
    "playful": 2,
    "happy": 2,
    "bored": 1,
    "sleepy": 0,
    "long-idle": 1,
}

# ─── Expression Targets ───────────────────────────────────────────────────
EXPR_NEUTRAL  = {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0}
EXPR_HAPPY     = {"ew": 5, "eh": 3,  "pw": 3,   "ph": 2,  "px": 0, "py": 1}
EXPR_SLEEPY    = {"ew": 3, "eh": 2,  "pw": 1.5, "ph": 1.5, "px": 0, "py": 1}
EXPR_ALERT     = {"ew": 6, "eh": 5,  "pw": 1.5, "ph": 3,  "px": 0, "py": 0}
EXPR_SQUINT    = {"ew": 4, "eh": 2,  "pw": 1.5, "ph": 1.5, "px": 0, "py": 0}
EXPR_ANGRY     = {"ew": 4, "eh": 4,  "pw": 2.5, "ph": 2.5, "px": 0, "py": -1,
                  "top_flat": True}
EXPR_SURPRISED = {"ew": 6, "eh": 6,  "pw": 2,   "ph": 2.5, "px": 0, "py": 0}

# ─── Utility ──────────────────────────────────────────────────────────────
def flip_x(x: float, facing: bool) -> float:
    """Flip x-coordinate based on facing direction."""
    return x if facing else -x


# ─── Toys ──────────────────────────────────────────────────────────────────
CHASE_SPEED_MULTIPLIER = 1.5
CHASE_REACH_DISTANCE = 30.0
CHASE_TIMEOUT = 2.0
PLAY_TOY_INTERVAL = 15.0
PLAY_TOY_DURATION = 5.0
PLAY_TOY_REACH_DISTANCE = 20.0

# ─── Animation Timing ─────────────────────────────────────────────────────
BLINK_INTERVAL_MIN = 2.0
BLINK_INTERVAL_MAX = 6.0
BLINK_DURATION     = 0.10


# ─── Multi-Pet ────────────────────────────────────────────────────────
MAX_CATS = 3                    # max number of cats (configurable)
DEFAULT_CATS = 1                # number of cats at fresh install
CAT_SPAWN_OFFSET_MIN = 20       # px offset range for new cats
CAT_SPAWN_OFFSET_MAX = 80
MULTI_HUT_GAP = 10              # px gap between huts


# ─── Coat Colors ─────────────────────────────────────────────────────────
COAT_COLORS = [
    # (body, belly, paw) - each is a QColor
    QColor(0x7C, 0x8E, 0x9E),  # 0: Russian Blue (default)
    QColor(0xF5, 0xDE, 0xB3),  # 1: Cream
    QColor(0x8B, 0x6F, 0x47),  # 2: Brown Tabby
    QColor(0x2F, 0x2F, 0x2F),  # 3: Black
    QColor(0xFF, 0xFF, 0xFF),  # 4: White
    QColor(0xD4, 0x7E, 0x6A),  # 5: Ginger
    QColor(0xA0, 0xA0, 0xA0),  # 6: Gray
]


# ─── Weather ──────────────────────────────────────────────────────────────────────────────
WEATHER_CITY = "Mumbai"             # Default city for wttr.in
WEATHER_CACHE_INTERVAL = 1800       # Seconds between fetches (30 min)
WEATHER_RETRIES = 3                  # Fetch retry count
WEATHER_RETRY_DELAY = 2.0           # Seconds between retries


# ─── Smart Needs: Time-of-Day Multipliers ──────────────────────────────────
# Each tuple: (start_hour, end_hour, multiplier)
# Applied to base drain rate: base_rate * tod_mul * weather_mul
NEED_TIME_MULTIPLIERS = {
    "energy": ((6, 12, 2.0), (22, 6, 0.5)),
    "hunger": ((7, 9, 1.5), (19, 21, 1.5)),
}


# ─── Smart Needs: AFK & Critical Thresholds ───────────────────────────────
AFK_BOREDOM_MULTIPLIER = 2.0
AFK_THRESHOLD = 300                 # Seconds without mouse interaction → AFK
HUNGER_URGENT_THRESHOLD = 80
ENERGY_CRITICAL_THRESHOLD = 20
BOREDOM_ERRATIC_THRESHOLD = 80
FEED_HUNGER_REDUCTION = 30          # Hunger reduced per Ctrl+F press
