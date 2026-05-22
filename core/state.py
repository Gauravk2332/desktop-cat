"""
core/state.py — Central CatState dataclass.

Pure data. Zero logic. Shared by reference across all modules.
Multi-cat: per-cat state lives in state.cats list. Backward-compatible
properties on CatState read/write cats[0] so single-cat code still works.
"""

import random
from dataclasses import dataclass, field


class CatProxy:
    """Wrapper around a cat dict providing attribute-style access.

    Allows drawing functions that expect `state.facing`, `state.tail_phase`
    to work with cat dicts via `cat_proxy.facing`, `cat_proxy.tail_phase`.
    Falls through to the original dict for __getitem__ access.
    """
    __slots__ = ('_cat',)

    def __init__(self, cat_dict: dict):
        self._cat = cat_dict

    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        # Handle aliases like cat_x → x, cat_y → y
        if name == 'cat_x' or name == 'x':
            return self._cat.get('x', 0.0)
        if name == 'cat_y' or name == 'y':
            return self._cat.get('y', 0.0)
        if name in self._cat:
            return self._cat[name]
        raise AttributeError(f"CatProxy has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        if name == '_cat':
            super().__setattr__(name, value)
        elif name in ('cat_x', 'x'):
            self._cat['x'] = value
        elif name in ('cat_y', 'y'):
            self._cat['y'] = value
        elif name in self._cat:
            self._cat[name] = value
        else:
            self._cat[name] = value

    def __getitem__(self, key):
        return self._cat[key]

    def __setitem__(self, key, value):
        self._cat[key] = value

    def get(self, key, default=None):
        return self._cat.get(key, default)


# ── Speech bubble mood pools ──
SPEECH_MOODS = {
    "bored": {
        "texts": ["zzz...", "yawwwn", "pet me?", "so bored..."],
        "emoji": "💤",
    },
    "happy": {
        "texts": ["purrrr~", "nyaa~", "😊", "hehe"],
        "emoji": "😊",
    },
    "hungry": {
        "texts": ["feed me.", "hungry...", "🍣", "snack?"],
        "emoji": "🍣",
    },
    "alert": {
        "texts": ["!?", "who's there?", "👀", "hm?"],
        "emoji": "👀",
    },
    "sleepy": {
        "texts": ["💤", "zzz...", "don't wanna", "sleepy..."],
        "emoji": "💤",
    },
    "playful": {
        "texts": ["pounce!", "hehe", "🎯", "again!", "c'mere!"],
        "emoji": "🎯",
    },
    "long-idle": {
        "texts": ["hello?", "still there?", "👋", "miss me?"],
        "emoji": "👋",
    },
}


def default_cat_dict(cat_id: int, coat: int = 0,
                      x: float = 500.0, y: float = 700.0) -> dict:
    """Create a default per-cat state dict."""
    return {
        "id": cat_id,
        "x": x,
        "y": y,
        "state": "SIT",
        "facing": True,
        "coat": coat,
        "energy": 80.0,
        "hunger": 20.0,
        "boredom": 0.0,
        "at_home": False,
        "home_cooldown": 0.0,
        "home_linger": 0.0,
        "walk_duration": 0.0,
        "walk_elapsed": 0.0,
        "walk_pause": False,
        "walk_pause_start": 0.0,
        "walk_accel": 1.0,
        "walk_frame": 0,
        "walk_accum": 0.0,
        "wander_duration": 0.0,
        "wander_elapsed": 0.0,
        "wander_cooldown": 0.0,
        "wander_session_count": 0,
        "wander_vx": 1.0,
        "wander_vy": 0.0,
        "tail_phase": 0.0,
        "breath_phase": 0.0,
        "blinking": False,
        "blink_timer": 0.0,
        "next_blink": 2.0,
        "sleep_breath": 0.0,
        "deep_sleep": False,
        "zzz_particles": [],
        "reaction_type": None,
        "reaction_timer": 0.0,
        "purr_vibrate": 0.0,
        "mouth_open": 0.0,
        "consecutive_pets": 0,
        "eye_target": (0.0, 0.0),
        "eye_current": (0.0, 0.0),
        "hearts": [],
        "last_interaction": 0.0,
        "speech": {
            "text": None, "emoji": None, "timer": 0.0,
            "fading": False, "opacity": 0.0, "queue": [],
        },
        "speech_cooldown": 0.0,
        "speech_idle_timer": 0.0,
        "expression": {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0},
        "expr_target": {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0},
        "expr_timeout": 0.0,
        "blush_alpha": 0.0,
        "blush_target": 0.0,
        "pupil_dilation": 0.5,
        "toy_target": None,
        "toy_timer": 0.0,
        "toy_active": False,
        "toy_type": None,
        "chase_timeout": 0.0,
        "hut_index": cat_id,
    }


# ── Per-cat field names (for backward-compat aliasing) ──
_CAT_FIELDS = [
    "energy", "hunger", "boredom",
    "state", "facing",
    "walk_duration", "walk_elapsed", "walk_pause", "walk_pause_start",
    "walk_accel", "walk_frame", "walk_accum",
    "wander_duration", "wander_elapsed", "wander_cooldown",
    "wander_session_count", "wander_vx", "wander_vy",
    "at_home", "home_cooldown", "home_linger",
    "tail_phase", "breath_phase", "blinking", "blink_timer", "next_blink",
    "sleep_breath", "deep_sleep", "zzz_particles",
    "reaction_type", "reaction_timer", "purr_vibrate", "mouth_open",
    "consecutive_pets",
    "eye_target", "eye_current",
    "hearts",
    "last_interaction",
    "speech", "speech_cooldown", "speech_idle_timer",
    "expression", "expr_target", "expr_timeout",
    "blush_alpha", "blush_target", "pupil_dilation",
    "toy_target", "toy_timer", "toy_active", "toy_type", "chase_timeout",
]
# Aliases: legacy names → new cat dict key (for special cases like cat_x/cat_y)
_CAT_FIELD_ALIAS = {
    "cat_x": "x",
    "cat_y": "y",
}


@dataclass
class CatState:
    # ── Multi-cat state ──
    cats: list = field(default_factory=lambda: [default_cat_dict(0)])

    # ── Mouse / context (shared) ──
    mouse_pos: tuple = (0.0, 0.0)
    mouse_near: bool = False

    # ── Click-through state (toggled by Controls) ──
    click_through: bool = True

    # ── Persistence ──
    save_accum: float = 0.0

    # ── Screen geometry (set once at startup) ──
    screen_width: int = 1920
    screen_height: int = 1080

    # ── Weather (shared) ──
    weather_condition: str = "cloudy"
    weather_temp: int = 25
    weather_last_fetch: float = 0.0
    weather_fetch_timer: float = 0.0

    # ── Smart Needs (shared) ──
    afk_timer: float = 0.0
    feed_cycle_index: int = 0

    # ── Engine tracking (shared) ──
    deep_sleep_all: bool = False

    # ── Backward-compatible properties ────────────────────────────────

    def _get(self, field: str):
        """Get field from cats[0], handling aliases."""
        key = _CAT_FIELD_ALIAS.get(field, field)
        if not self.cats:
            return None
        return self.cats[0].get(key)

    def _set(self, field: str, value):
        """Set field on cats[0], handling aliases."""
        key = _CAT_FIELD_ALIAS.get(field, field)
        if self.cats:
            self.cats[0][key] = value

    @property
    def cat_x(self) -> float:
        return self.cats[0]["x"] if self.cats else 0.0

    @cat_x.setter
    def cat_x(self, v: float):
        if self.cats:
            self.cats[0]["x"] = v

    @property
    def cat_y(self) -> float:
        return self.cats[0]["y"] if self.cats else 0.0

    @cat_y.setter
    def cat_y(self, v: float):
        if self.cats:
            self.cats[0]["y"] = v


# Dynamically create backward-compatible properties for all per-cat fields.
def _make_property(field: str):
    """Factory to create a backward-compatible property for a cat field."""
    key = _CAT_FIELD_ALIAS.get(field, field)

    def getter(self):
        if not self.cats:
            if field == "hearts":
                return []
            if field == "speech":
                return {"text": None, "emoji": None, "timer": 0.0,
                        "fading": False, "opacity": 0.0, "queue": []}
            if field == "zzz_particles":
                return []
            if field in ("expression", "expr_target"):
                return {"ew": 4, "eh": 4, "pw": 2.5, "ph": 2.5, "px": 0, "py": 0}
            if field in ("eye_target", "eye_current"):
                return (0.0, 0.0)
            return None
        return self.cats[0].get(key)

    def setter(self, value):
        if self.cats:
            self.cats[0][key] = value

    return property(getter, setter)


# Install backward-compatible properties on CatState
for _field in _CAT_FIELDS:
    setattr(CatState, _field, _make_property(_field))

# Explicitly handle fields where we want the alias names on the class
for _alias, _target in _CAT_FIELD_ALIAS.items():
    if _alias not in ("cat_x", "cat_y"):
        setattr(CatState, _alias, _make_property(_alias))


# ── Multi-cat management methods (attached post-definition) ──

def _add_cat(self, coat: int = 0, x: float = None, y: float = None) -> int:
    """Add a new cat. Returns cat ID, or -1 if at max cats."""
    import config as _cfg
    if len(self.cats) >= _cfg.MAX_CATS:
        return -1

    cat_id = len(self.cats)
    if x is None:
        if self.cats:
            last_x = self.cats[-1]["x"]
            x = last_x + random.uniform(_cfg.CAT_SPAWN_OFFSET_MIN,
                                        _cfg.CAT_SPAWN_OFFSET_MAX)
        else:
            x = float(self.screen_width // 2)
        x = max(50.0, min(x, float(self.screen_width - 50)))

    if y is None:
        y = float(self.screen_height - _cfg.CAT_BASELINE)

    cat = default_cat_dict(cat_id, coat, x, y)
    cat["hut_index"] = cat_id
    self.cats.append(cat)
    return cat_id


def _remove_cat(self, cat_id: int) -> bool:
    """Remove cat by id. Cannot remove cat 0 (minimum 1 cat)."""
    if cat_id == 0 or cat_id >= len(self.cats):
        return False
    self.cats.pop(cat_id)
    # Reassign hut indices
    for i, c in enumerate(self.cats):
        c["hut_index"] = i
    return True


CatState.add_cat = _add_cat
CatState.remove_cat = _remove_cat
