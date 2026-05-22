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
WALK_SPEED     = 80.0   # px/s
WALK_ACCEL_TIME = 0.4   # seconds to reach full speed
WALK_DURATION_MIN = 0.5

# ─── States ───────────────────────────────────────────────────────────────
STATE_SIT     = "SIT"
STATE_WALK    = "WALK"
STATE_SLEEP   = "SLEEP"
STATE_GO_HOME = "GO_HOME"
STATE_WANDER  = "WANDER"

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


# ─── Animation Timing ─────────────────────────────────────────────────────
BLINK_INTERVAL_MIN = 2.0
BLINK_INTERVAL_MAX = 6.0
BLINK_DURATION     = 0.10
