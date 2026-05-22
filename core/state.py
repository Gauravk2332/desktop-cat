"""
core/state.py — Central CatState dataclass.

Pure data. Zero logic. Shared by reference across all modules.
"""

from dataclasses import dataclass, field


@dataclass
class CatState:
    # ── Vital needs (0-100) ──
    energy: float = 80.0
    hunger: float = 20.0
    boredom: float = 0.0

    # ── State machine ──
    state: str = "SIT"               # SIT | WALK | SLEEP | GO_HOME | WANDER
    cat_x: float = 0.0               # screen X position of cat center
    cat_y: float = 0.0               # screen Y position of cat base
    facing: bool = True              # True = right, False = left

    # ── Walk internals ──
    walk_duration: float = 0.0
    walk_elapsed: float = 0.0
    walk_pause: bool = False
    walk_pause_start: float = 0.0  # monotonic time when pause started
    walk_accel: float = 1.0
    walk_frame: int = 0
    walk_accum: float = 0.0

    # ── Wander internals ──
    wander_duration: float = 0.0     # how long this wander leg lasts
    wander_elapsed: float = 0.0
    wander_cooldown: float = 0.0     # seconds until next wander session
    wander_session_count: int = 0    # legs per wander session

    # ── Home / Bed ──
    at_home: bool = False            # cat is on/near the bed
    home_cooldown: float = 0.0       # seconds until next random home visit
    home_linger: float = 0.0         # countdown: sit near bed after waking

    # ── Animations ──
    tail_phase: float = 0.0
    breath_phase: float = 0.0
    blinking: bool = False
    blink_timer: float = 0.0
    next_blink: float = 2.0
    sleep_breath: float = 0.0
    deep_sleep: bool = False
    zzz_particles: list = field(default_factory=list)

    # ── Reactions ──
    reaction_type: str | None = None
    reaction_timer: float = 0.0
    purr_vibrate: float = 0.0
    mouth_open: float = 0.0
    consecutive_pets: int = 0

    # ── Eye tracking ──
    eye_target: tuple = (0.0, 0.0)
    eye_current: tuple = (0.0, 0.0)

    # ── Mouse / context ──
    mouse_pos: tuple = (0.0, 0.0)
    mouse_near: bool = False
    last_interaction: float = 0.0

    # ── Persistence ──
    save_accum: float = 0.0

    # ── Screen geometry (set once at startup) ──
    screen_width: int = 1920
    screen_height: int = 1080

    # ── Expression system ──
    expression: dict = field(default_factory=lambda: dict(
        ew=4, eh=4, pw=2.5, ph=2.5, px=0, py=0
    ))
    expr_target: dict = field(default_factory=lambda: dict(
        ew=4, eh=4, pw=2.5, ph=2.5, px=0, py=0
    ))
    expr_timeout: float = 0.0
    blush_alpha: float = 0.0
    blush_target: float = 0.0
    pupil_dilation: float = 0.5
