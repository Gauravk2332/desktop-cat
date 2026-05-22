"""
behavior/agent.py — LLM-powered cat agent.

Replaces the hardcoded state machine with a local LLM that decides
what the cat should do moment-to-moment. Falls back to simple rules
if the LLM is unavailable.

Architecture:
  build_context()  →  call_llm()  →  parse_action()  →  engine.execute()

Supports:
  - Ollama (local, default)
  - Remote API (DeepSeek/OpenAI-compatible)
  - Rule-based fallback (no LLM dependency)
"""

import json
import logging
import math
import random
import threading
import time
from typing import Optional

logger = logging.getLogger(__name__)


# ─── Personality Prompt ──────────────────────────────────────────────

SYSTEM_PROMPT = """You are a cat named Whiskers living on a computer screen.
You have a strong personality:
- Curious but easily bored — investigate new things then lose interest
- Affectionate on YOUR terms — enjoy pets but walk away when done
- Proud and independent — do what you want, when you want
- Playful when energetic — chase things, bat at objects
- Sleepy when tired — curl up anywhere cozy
- React to the user — slow blink to show trust, purr when happy
- Get grumpy when hungry or over-petted

Choose ONE action based on your current state and the user's behavior.
Respond with EXACTLY one line: ACTION <name> [params]

Available actions (choose the best single one):
  SIT              — sit in place, relax
  WALK x y         — walk to screen coordinates (0-1536, 0-816)
  SLEEP            — curl up and nap
  PURR             — purr contentedly
  MEOW             — meow (greeting, plaintive, happy)
  GROOM            — clean your fur
  STRETCH          — stretch your body
  CHASE            — chase after the cursor
  FOLLOW           — follow the user's cursor slowly
  PLAYTOY          — bat at a toy
  HOME             — go to your bed
  IGNORE           — do nothing for a moment
  SLOWBLINK        — slow blink at the user (trust signal)
  SCRATCH          — scratch at something

Examples:
  ACTION SIT
  ACTION WALK 300 500
  ACTION MEOW greeting
  ACTION CHASE
  ACTION SLOWBLINK"""


# ─── Context Builder ─────────────────────────────────────────────────

def build_context(cat: dict, state) -> str:
    """Build a human-readable context string for the LLM."""
    # Cat state
    energy = cat.get("energy", 50)
    hunger = cat.get("hunger", 50)
    boredom = cat.get("boredom", 0)
    cat_state = cat.get("state", "SIT")
    at_home = cat.get("at_home", False)
    x, y = cat.get("x", 500), cat.get("y", 400)

    # Time of day
    t = time.localtime()
    hour = t.tm_hour
    if hour < 6:
        time_desc = "late night"
    elif hour < 12:
        time_desc = "morning"
    elif hour < 14:
        time_desc = "midday"
    elif hour < 18:
        time_desc = "afternoon"
    elif hour < 22:
        time_desc = "evening"
    else:
        time_desc = "night"

    # User proximity — if state has mouse tracking info
    mouse_dist = getattr(state, "_mouse_distance", None)
    if mouse_dist is not None:
        if mouse_dist < 80:
            proximity = "very close (user is petting)"
        elif mouse_dist < 200:
            proximity = "nearby"
        elif mouse_dist < 500:
            proximity = "within sight"
        else:
            proximity = "far away"
    else:
        proximity = "unknown"

    # AFK detection
    last_interaction = cat.get("last_interaction", 0)
    afk_secs = time.time() - last_interaction if last_interaction else 999
    if afk_secs > 300:
        user_status = f"user AFK for {int(afk_secs//60)}m"
    elif afk_secs > 60:
        user_status = f"user idle for {int(afk_secs//60)}m"
    else:
        user_status = "user is active"

    # Recent action history (last 5) — stored on cat dict by engine
    raw_history = cat.get("_action_history", [])
    history = [h[0] if isinstance(h, (list, tuple)) else h for h in raw_history[-5:]]
    history_str = "\n".join(history) if history else "(no recent actions)"

    # Weather (if available)
    weather_str = "unknown"
    if hasattr(state, "weather_condition"):
        weather_str = state.weather_condition or "unknown"

    lines = [
        f"Time: {t.tm_hour:02d}:{t.tm_min:02d} ({time_desc})",
        f"Position: ({int(x)}, {int(y)})",
        f"State: {cat_state} {'(at home/bed)' if at_home else ''}",
        f"Energy: {energy:.0f}% | Hunger: {hunger:.0f}% | Boredom: {boredom:.0f}%",
        f"User: {user_status} | Proximity: {proximity}",
        f"Weather: {weather_str}",
        "",
        "Recent actions:",
        history_str,
    ]
    return "\n".join(lines)


# ─── LLM Callers ─────────────────────────────────────────────────────

def call_ollama(context: str, host: str = "localhost:11434",
                model: str = "llama3.2:1b", timeout: float = 5.0) -> Optional[str]:
    """Call a local Ollama instance."""
    import urllib.request
    import urllib.error

    prompt = f"""[INST]<<SYS>>
{SYSTEM_PROMPT}
<</SYS>>

Current situation:
{context}

What do you do? Respond with EXACTLY one line: ACTION <name> [params][/INST]"""

    data = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.8,
            "num_predict": 30,
            "stop": ["\n"],
        }
    }).encode()

    req = urllib.request.Request(
        f"http://{host}/api/generate",
        data,
        {"Content-Type": "application/json"},
    )

    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        result = json.loads(resp.read())
        return result.get("response", "").strip()
    except (urllib.error.URLError, json.JSONDecodeError,
            OSError, TimeoutError) as e:
        logger.warning("Ollama call failed: %s", e)
        return None


def call_remote_api(context: str, api_url: str = "",
                    api_key: str = "", model: str = "deepseek-chat",
                    timeout: float = 10.0) -> Optional[str]:
    """Call a remote API (OpenAI-compatible)."""
    import urllib.request
    import urllib.error

    if not api_url:
        return None

    prompt = f"""[INST]<<SYS>>
{SYSTEM_PROMPT}
<</SYS>>

Current situation:
{context}

What do you do? Respond with EXACTLY one line: ACTION <name> [params][/INST]"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Current situation:\n{context}\n\nWhat do you do?"},
    ]

    data = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 30,
        "stop": ["\n"],
    }).encode()

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = urllib.request.urlopen(urllib.request.Request(api_url, data, headers), timeout=timeout)
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.warning("Remote API call failed: %s", e)
        return None


# ─── Action Parser ───────────────────────────────────────────────────

def parse_action(response: str) -> tuple:
    """Parse LLM response into (action_type, params).

    Returns (action_type, args_dict or None).
    """
    if not response:
        return ("NONE", None)

    response = response.strip().upper()

    # Strip common prefixes
    for prefix in ("ACTION ", "ACTION:"):
        if response.startswith(prefix):
            response = response[len(prefix):].strip()

    # Try to parse "NAME" or "NAME param1 param2"
    parts = response.split()
    if not parts:
        return ("NONE", None)

    action = parts[0]
    params = parts[1:] if len(parts) > 1 else []

    VALID_ACTIONS = {
        "SIT", "WALK", "SLEEP", "PURR", "MEOW", "GROOM",
        "STRETCH", "CHASE", "FOLLOW", "PLAYTOY", "HOME",
        "IGNORE", "SLOWBLINK", "SCRATCH", "NONE",
    }

    if action not in VALID_ACTIONS:
        logger.debug("Unknown action from LLM: %s", action)
        return ("NONE", None)

    if action == "WALK" and len(params) >= 2:
        try:
            return ("WALK", {"x": float(params[0]), "y": float(params[1])})
        except ValueError:
            return ("WALK", None)
    elif action == "MEOW" and params:
        return ("MEOW", {"type": params[0].lower()})

    return (action, None)


# ─── Rule-Based Fallback ─────────────────────────────────────────────

def rule_based_action(cat: dict, state) -> tuple:
    """Simple rule-based fallback when LLM is unavailable."""
    energy = cat.get("energy", 50)
    hunger = cat.get("hunger", 50)
    boredom = cat.get("boredom", 0)
    cat_state = cat.get("state", "SIT")

    # Critical needs override everything
    if energy < 15 and cat_state != "SLEEP":
        return ("HOME", None)
    if hunger > 80 and cat_state != "HOME":
        return ("HOME", None)

    # Bored → walk somewhere
    if boredom > 60 and cat_state in ("SIT",):
        return ("WALK", {"x": random.randint(100, 1400),
                          "y": random.randint(100, 700)})

    # Energetic → play
    if energy > 70 and boredom > 40 and cat_state in ("SIT",):
        return ("CHASE", None)

    # Tired → sleep
    if energy < 30 and cat_state not in ("SLEEP", "HOME"):
        return ("HOME", None)

    # Content → purr or groom
    if energy > 50 and hunger < 40 and cat_state == "SIT":
        return random.choice([("PURR", None), ("GROOM", None), ("SIT", None)])

    return ("SIT", None)


# ─── CatAgent Class ──────────────────────────────────────────────────

# ─── Non-Blocking Agent ────────────────────────────────────────────────

class CatAgent:
    """Decision-maker for a single cat, using LLM or fallback rules.

    **Non-blocking:** LLM calls run in a background thread so the frame
    loop is never blocked. If the thread is still running when a decision
    is requested, the last known action is returned immediately.

    Usage:
        agent = CatAgent(backend="ollama")
        action, params = agent.decide(cat, state)
        engine.execute_action(action, params)
    """

    def __init__(
        self,
        backend: str = "ollama",
        ollama_host: str = "localhost:11434",
        ollama_model: str = "llama3.2:1b",
        remote_api_url: str = "",
        remote_api_key: str = "",
        remote_model: str = "",
        decision_interval: float = 2.0,
        max_failures: int = 3,
        llm_timeout: float = 10.0,
    ):
        self.backend = backend
        self.ollama_host = ollama_host
        self.ollama_model = ollama_model
        self.remote_api_url = remote_api_url
        self.remote_api_key = remote_api_key
        self.remote_model = remote_model
        self.decision_interval = decision_interval
        self.llm_timeout = llm_timeout

        self._last_decision = 0.0
        self._last_action = ("SIT", None)
        self._consecutive_failures = 0
        self._max_failures_before_fallback = max_failures
        self._use_fallback = False

        # Background thread state
        self._thread = None
        self._thread_context = ""
        self._thread_result: Optional[str] = None  # None = not done
        self._thread_lock = threading.Lock()
        self._last_cat_in_sight = 0.0  # cats are fast, but not this fast

        logger.info("CatAgent initialized: backend=%s model=%s interval=%.1fs",
                     backend, ollama_model if backend == "ollama" else remote_model,
                     decision_interval)

    def _start_decision_thread(self, context: str):
        """Start a background thread for the LLM call."""
        def _worker():
            response = None
            if self.backend == "ollama":
                response = call_ollama(context, self.ollama_host,
                                       self.ollama_model, self.llm_timeout)
            elif self.backend == "remote":
                response = call_remote_api(context, self.remote_api_url,
                                           self.remote_api_key, self.remote_model,
                                           self.llm_timeout)
            with self._thread_lock:
                self._thread_result = response

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def decide(self, cat: dict, state) -> tuple:
        """Decide what action to take. Never blocks.

        Returns (action_type, params) — either a new decision from the
        background thread or the previous action.
        """
        now = time.time()

        # 1. Check if background thread finished
        if self._thread is not None:
            with self._thread_lock:
                if self._thread_result is not None:
                    response = self._thread_result
                    self._thread_result = None
                    self._thread = None

                    # Process LLM result
                    if response:
                        self._consecutive_failures = 0
                        self._use_fallback = False
                        action, params = parse_action(response)
                        self._last_action = (action, params)
                        return (action, params)
                    else:
                        # LLM call failed
                        self._consecutive_failures += 1
                        if self._consecutive_failures >= self._max_failures_before_fallback:
                            self._use_fallback = True
                            logger.info("Agent: falling back to rule-based (LLM unavailable)")
                        fallback = rule_based_action(cat, state)
                        self._last_action = fallback
                        return fallback

            # Thread still running — return last action
            return self._last_action

        # 2. Not time for a new decision yet
        if now - self._last_decision < self.decision_interval:
            return self._last_action

        self._last_decision = now

        # 3. Fallback mode — use rules (instant, no thread)
        if self._use_fallback:
            action, params = rule_based_action(cat, state)
            self._last_action = (action, params)
            return (action, params)

        # 4. Start background LLM call, return current action immediately
        context = build_context(cat, state)
        self._start_decision_thread(context)
        return self._last_action

    @property
    def is_using_fallback(self) -> bool:
        return self._use_fallback
