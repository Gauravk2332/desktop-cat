"""
config.py — ALL constants for the desktop cat.
Single source of truth. Every import reads from here.
No runtime changes. All values are final per session.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, List

from PyQt6.QtGui import QColor, QFont

DEBUG = False  # Set True for verbose logging during development

# ─── Debug ──────────────────────────────────────────────────────────────
# DEBUG is at top, after imports

# ─── Window (full-screen overlay) ──────────────────────────────────────
CAT_BASELINE = 20        # px above screen bottom for cat base

# ─── Timing ───────────────────────────────────────────────────────────────
TICK_MS = 30   # ~33fps — smoother movement updates
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
WALK_SPEED      = 55.0   # px/s — slower, more natural gait
WALK_ACCEL_TIME = 0.6   # seconds to reach full speed — gentler start/stop
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
API_PORT = 65432

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
C_SHADOW    = QColor(0, 0, 0, 25)        # translucent black

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
BLINK_INTERVAL_MIN = 10       # seconds
BLINK_INTERVAL_MAX = 20       # seconds
BLINK_DURATION     = 0.15     # seconds (150ms)
SHOW_BLINK_VISUAL  = True     # show horizontal bar over eye region during blink (placeholder)


# ─── Sprite Rendering ─────────────────────────────────────────────────────
SPRITE_SIZE = 400                     # px — native frame dimension
CAT_SIZE_DEFAULT = 120                 # px — default cat height on screen (60% of pre-sprite size)
CAT_SIZE_MIN = 120                     # px — minimum scaled size
CAT_SIZE_MAX = 350                     # px — maximum scaled size
SHADOW_OPACITY = 0.10                  # drop shadow opacity (0.0-1.0)
SILHOUETTE_SHADOW = True               # extra blur layer behind cat
CROSSFADE_MS = 200                     # transition crossfade duration
RENDERER_BACKEND = "sprite"             # "sprite" | "qpainter" (fallback)


# ─── Phase 1: Night Mode + LOD ─────────────────────────────────────────
NIGHT_MODE = False                       # enable night palette (engine sets dynamically)
NIGHT_DESATURATE = 0.20                  # 20% color desaturation at night
LOD_OUTLINE_THRESHOLD = 150              # px — below this size, add 1px outline
LOD_OUTLINE_COLOR = "#1a1a1a"           # dark outline for small sprites
LOD_OUTLINE_OPACITY = 0.5                # outline opacity


# ─── Multi-Pet ────────────────────────────────────────────────────────
MAX_CATS = 3                    # max number of cats (configurable)
DEFAULT_CATS = 1                # number of cats at fresh install
CAT_SPAWN_OFFSET_MIN = 20       # px offset range for new cats
CAT_SPAWN_OFFSET_MAX = 80
MULTI_HUT_GAP = 10              # px gap between huts


# ─── Coat Colors ─────────────────────────────────────────────────────────

@dataclass
class CoatColors:
    """Complete color specification for one cat coat."""
    name: str
    body: QColor
    belly: QColor
    stripe: Optional[QColor] = None
    nose: QColor = field(default_factory=lambda: QColor(0xFF, 0x94, 0x94))
    ear_inner: QColor = field(default_factory=lambda: QColor(0xFF, 0xB8, 0xC6))
    eye: QColor = field(default_factory=lambda: QColor(0x6B, 0xA3, 0xD6))
    pupil: QColor = field(default_factory=lambda: QColor(0x1A, 0x1A, 0x1A))
    whisker: QColor = field(default_factory=lambda: QColor(0xA8, 0xB0, 0xB8))
    paw_pads: QColor = field(default_factory=lambda: QColor(0xCC, 0xD5, 0xDC))
    chin_chest: Optional[QColor] = None
    stripe_style: str = "mackerel"  # "mackerel" | "solid" | "tuxedo" | "patch" | "point" | "none"
    has_forehead_m: bool = True


# Helper to build QColor from hex
_H = lambda h: QColor(h)

COAT_COLORS_STRUCTURED: List[CoatColors] = [
    CoatColors(name="Gray Tabby",
               body=QColor(0x7C, 0x8E, 0x9E),   # steel gray-blue
               belly=QColor(0xD4, 0xD9, 0xDE),   # light warm gray
               stripe=QColor(0x5A, 0x6B, 0x7A),
               paw_pads=QColor(0xCC, 0xD5, 0xDC),
               stripe_style="mackerel"),
    CoatColors(name="Orange Tabby",
               body=QColor(0xE8, 0x9B, 0x5D),   # warm ginger orange
               belly=QColor(0xFC, 0xE6, 0xC9),   # cream/light tan
               stripe=QColor(0xC4, 0x7A, 0x3C),  # darker orange-brown
               nose=QColor(0xF0, 0x80, 0x80),    # light coral
               ear_inner=QColor(0xFF, 0xB6, 0xC1),
               eye=QColor(0x4C, 0xAF, 0x50),     # green
               whisker=QColor(0xD4, 0xD4, 0xD4),
               paw_pads=QColor(0xD4, 0x95, 0x6A),
               chin_chest=QColor(0xFE, 0xFE, 0xFE),
               stripe_style="mackerel",
               has_forehead_m=True),
    CoatColors(name="Tuxedo",
               body=QColor(0x2F, 0x2F, 0x2F),    # near-black
               belly=QColor(0xFE, 0xFE, 0xFE),    # white
               stripe=None,
               nose=QColor(0x33, 0x33, 0x33),
               ear_inner=QColor(0x55, 0x55, 0x55),
               eye=QColor(0xE8, 0xD5, 0x3F),     # gold
               whisker=QColor(0xE0, 0xE0, 0xE0),
               paw_pads=QColor(0xFE, 0xFE, 0xFE),
               chin_chest=QColor(0xFE, 0xFE, 0xFE),
               stripe_style="tuxedo",
               has_forehead_m=False),
    CoatColors(name="Calico",
               body=QColor(0xFE, 0xFA, 0xF0),    # cream-white
               belly=QColor(0xFE, 0xFA, 0xF0),
               stripe=None,
               ear_inner=QColor(0xFF, 0xB6, 0xC1),
               eye=QColor(0x8B, 0xC3, 0x4A),     # green
               whisker=QColor(0xD4, 0xD4, 0xD4),
               paw_pads=QColor(0xFE, 0xFA, 0xF0),
               stripe_style="patch",
               has_forehead_m=False),
    CoatColors(name="Siamese",
               body=QColor(0xF5, 0xE6, 0xCC),    # cream
               belly=QColor(0xFA, 0xF0, 0xDD),
               stripe=None,
               nose=QColor(0x6B, 0x4E, 0x37),
               ear_inner=QColor(0x8B, 0x6E, 0x57),
               eye=QColor(0x4A, 0x90, 0xD9),     # blue
               whisker=QColor(0xF0, 0xF0, 0xF0),
               paw_pads=QColor(0x6B, 0x4E, 0x37),
               stripe_style="point",
               has_forehead_m=False),
    CoatColors(name="Solid Black",
               body=QColor(0x1A, 0x1A, 0x1A),    # true black
               belly=QColor(0x33, 0x33, 0x33),    # slightly lighter
               stripe=None,
               nose=QColor(0x44, 0x44, 0x44),
               ear_inner=QColor(0x55, 0x55, 0x55),
               eye=QColor(0xF0, 0xE6, 0x8C),     # yellow
               whisker=QColor(0xBB, 0xBB, 0xBB),
               paw_pads=QColor(0x44, 0x44, 0x44),
               stripe_style="none",
               has_forehead_m=False),
    CoatColors(name="Tortoiseshell",
               body=QColor(0x2F, 0x2F, 0x2F),    # dark base
               belly=QColor(0x4A, 0x3A, 0x2A),
               stripe=None,
               nose=QColor(0x80, 0x60, 0x60),
               ear_inner=QColor(0x8B, 0x6E, 0x57),
               eye=QColor(0xE8, 0xD5, 0x3F),     # gold
               whisker=QColor(0xBB, 0xBB, 0xBB),
               paw_pads=QColor(0x55, 0x44, 0x44),
               stripe_style="patch",
               has_forehead_m=False),
]

# Legacy aliases for backward compatibility
C_BODY      = COAT_COLORS_STRUCTURED[0].body
C_BELLY     = COAT_COLORS_STRUCTURED[0].belly
C_SHADOW    = QColor(0, 0, 0, 25)
C_PAW       = COAT_COLORS_STRUCTURED[0].paw_pads
C_INNER_EAR = COAT_COLORS_STRUCTURED[0].ear_inner
C_NOSE      = COAT_COLORS_STRUCTURED[0].nose
C_WHISKER   = COAT_COLORS_STRUCTURED[0].whisker

# Settings coat name → COAT_COLORS_STRUCTURED index
COAT_NAME_INDEX = {
    "russian_blue": 0,
    "orange_tabby": 1,
    "tuxedo": 2,
    "calico": 3,
    "siamese": 4,
    "black": 5,
    "tortoiseshell": 6,
    "ginger": 1,   # legacy alias for orange tabby
    "white": 5,     # legacy — closest to black (no white in structured)
}


def get_coat(index: int) -> CoatColors:
    """Get CoatColors by index, safe for out-of-range."""
    if 0 <= index < len(COAT_COLORS_STRUCTURED):
        return COAT_COLORS_STRUCTURED[index]
    return COAT_COLORS_STRUCTURED[0]



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
