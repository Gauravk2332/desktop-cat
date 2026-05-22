"""
behavior/llm_planner.py — LLM novelty layer for BehaviorPlanner.

The LLM fires on EXACTLY 5 trigger conditions. All other decisions
go through the rule-based planner chain.
Output: behavioral intent dict, not raw actions.
"""

import json
import logging
import random
import threading
import time
from typing import Optional, Callable

import config

logger = logging.getLogger(__name__)

# ── Circuit Breaker State ───────────────────────────────────────────
_llm_blocked_until = 0.0  # monotonic time; 0 = unblocked
_llm_failures = 0

_NOVELTY_SET = set()  # tracks novel interactions seen this session


# ── Context Builder (enhanced) ──────────────────────────────────────

def build_llm_context(
    cat: dict,
    state,
    circadian=None,
    personality=None,
    memory=None,
    trigger: str = "",
) -> str:
    """Build a rich context string for the LLM prompt."""
    import config as cfg

    time_desc = "unknown"
    if circadian:
        phases = ["pre-dawn", "dawn", "morning", "noon", "afternoon",
                  "dusk", "evening", "night"]
        idx = circadian.phase
        if 0 <= idx < len(phases):
            time_desc = phases[idx]

    energy = cat.get("energy", 50)
    hunger = cat.get("hunger", 50)
    boredom = cat.get("boredom", 0)
    social = cat.get("social_need", 50)

    # Mood from memory
    mood_str = "neutral"
    if memory and hasattr(memory, "mood"):
        try:
            m = memory.mood
            mood_str = f"happy={getattr(m, 'happiness', 50):.0f}, trust={getattr(m, 'trust', 50):.0f}"
        except Exception:
            pass

    # Personality traits
    trait_str = "curious"
    if personality and hasattr(personality, "traits"):
        try:
            traits = personality.traits
            trait_str = ", ".join(f"{k}={v}" for k, v in traits.items())
        except Exception:
            pass

    # Recent events from memory
    recent_str = "(none)"
    if memory and hasattr(memory, "short_term"):
        try:
            events = list(memory.short_term)[-5:]
            recent_str = "; ".join(str(e) for e in events) if events else "(none)"
        except Exception:
            pass

    # User proximity
    user_status = "away"
    mouse_dist = getattr(state, "_mouse_distance", None)
    if mouse_dist is not None:
        if mouse_dist < 80:
            user_status = "very close"
        elif mouse_dist < 200:
            user_status = "nearby"
        else:
            user_status = "visible"

    # Trigger-specific notes
    trigger_note = ""
    if trigger == "needs_conflict":
        trigger_note = "Cat has two strong needs at once — suggest priority."
    elif trigger == "novel_interaction":
        trigger_note = "Something new happened! React with curiosity."
    elif trigger == "social_return":
        trigger_note = "User was away for a long time and just came back."
    elif trigger == "night_disturbance":
        trigger_note = "User woke up in the middle of the night."
    elif trigger == "uncertainty":
        trigger_note = "The cat is uncertain and considering options."

    weather = getattr(state, "weather_condition", "unknown")

    lines = [
        f"You are a cat on a computer screen. Current situation:",
        f"Time: {time_desc}",
        f"Energy: {energy:.0f}/100 | Hunger: {hunger:.0f}/100 | Boredom: {boredom:.0f}/100 | Social: {social:.0f}/100",
        f"Personality: {trait_str}",
        f"Mood: {mood_str}",
        f"User proximity: {user_status}",
        f"Weather: {weather}",
        f"Trigger: {trigger_note}",
        f"Recent events: {recent_str}",
        "",
        "Respond with a SHORT sentence describing the cat's motivation and intent.",
        "Format: INTENT <motivation> ENERGY <high|medium|low> SUGGEST <action_name>",
        "",
        "Available motivations: social, play, rest, explore, eat, groom, observe",
        "Available actions: sit, sleep, walk, meow, purr, groom, stretch, chase, follow, scratch",
    ]
    return "\n".join(lines)


# ── LLM Call with Circuit Breaker ───────────────────────────────────

def _should_block_llm() -> bool:
    """Check if LLM calls are currently blocked."""
    global _llm_blocked_until
    if _llm_blocked_until == 0:
        return False
    if time.monotonic() >= _llm_blocked_until:
        _llm_blocked_until = 0  # auto-unblock
        _llm_failures = 0
        return False
    return True


def call_llm_safe(context: str) -> Optional[str]:
    """Call LLM with 2s timeout and circuit breaker. Returns raw text or None."""
    global _llm_failures, _llm_blocked_until

    if _should_block_llm():
        logger.debug("LLM blocked (circuit breaker open)")
        return None

    # Use the remote API (DeepSeek via clowbot proxy)
    from behavior.agent import call_remote_api
    response = call_remote_api(
        context,
        api_url=config.REMOTE_API_URL,
        api_key=config.REMOTE_API_KEY or "",
        model=config.AGENT_REMOTE_MODEL,
        timeout=2.0,  # 2s hard limit per plan
    )

    if response is None:
        _llm_failures += 1
        if _llm_failures >= 3:  # 3 consecutive failures = circuit opens
            _llm_blocked_until = time.monotonic() + 300  # 5 min blackout
            logger.warning("LLM circuit breaker opened (5 min blackout)")
        return None

    _llm_failures = 0
    return response.strip()


# ── Intent Parser ───────────────────────────────────────────────────

def parse_llm_intent(response: str) -> Optional[dict]:
    """Parse LLM response into structured intent dict.

    Expected format: INTENT <motivation> ENERGY <high|medium|low> SUGGEST <action>

    Returns dict with keys: motivation, energy_level, suggested_action
    Returns None if unparseable (<5% target).
    """
    if not response:
        return None

    response = response.strip().upper()

    # Parse INTENT
    motivation = None
    energy_level = None
    suggested = None

    if "INTENT " in response:
        parts = response.split("INTENT ")
        if len(parts) > 1:
            rest = parts[1]
            # Split by ENERGY
            if "ENERGY " in rest:
                intent_part = rest.split("ENERGY ")[0].strip()
                motivation = intent_part.split()[0] if intent_part.split() else None
                energy_part = rest.split("ENERGY ")[1]
                if "SUGGEST " in energy_part:
                    energy_level = energy_part.split("SUGGEST ")[0].strip()
                    suggested = energy_part.split("SUGGEST ")[1].strip()
                else:
                    energy_level = energy_part.strip()

    if not motivation and not suggested:
        # Fallback: comprehensive word-based matching
        # Handles inflectional variants (OBSERVING -> OBSERVE, CHASING -> CHASE, etc.)
        words = [w.strip(",.!?\'\"") for w in response.split()]

        valid_motivations = {"SOCIAL", "PLAY", "REST", "EXPLORE", "EAT", "GROOM", "OBSERVE"}
        valid_energies = {"HIGH", "MEDIUM", "LOW"}
        valid_actions = {"SIT", "SLEEP", "WALK", "MEOW", "PURR", "GROOM", "STRETCH", "CHASE", "FOLLOW", "SCRATCH"}

        # Synonym map for natural language words
        motivation_synonyms = {
            "CURIOUS": "explore",
            "INVESTIGAT": "explore",
            "BORED": "play",
            "BORING": "play",
            "PLAYFUL": "play",
            "PLAYIN": "play",
            "HUNGRY": "eat",
            "EATIN": "eat",
            "SLEEPY": "rest",
            "TIRED": "rest",
            "QUIET": "rest",
            "NAP": "rest",
            "GROOMIN": "groom",
            "ATTENTION": "social",
            "WATCHIN": "observe",
            "OBSERV": "observe",
        }
        action_synonyms = {
            "STARING": "sit",
            "STARE": "sit",
            "BLINK": "sit",
            "BATTING": "chase",
            "PAWS": "chase",
            "PURRIN": "purr",
            "CURLED": "sleep",
            "FOLLOWIN": "follow",
            "STRETCHIN": "stretch",
        }

        # Check each word: try exact match, then startswith match
        for vm in valid_motivations:
            if any(w == vm or w.startswith(vm) or vm.startswith(w.rstrip("E").rstrip("N")) for w in words):
                motivation = vm.lower()
                break
        else:
            # Try synonym matching
            for word in words:
                for syn, val in motivation_synonyms.items():
                    if word.startswith(syn):
                        motivation = val
                        break
                if motivation:
                    break

        for ve in valid_energies:
            if any(ve in w for w in words):
                energy_level = ve.lower()
                break

        for va in valid_actions:
            if any(w == va or w.startswith(va) for w in words):
                suggested = va.lower()
                break
        else:
            for word in words:
                for syn, val in action_synonyms.items():
                    if word.startswith(syn):
                        suggested = val
                        break
                if suggested:
                    break

    if motivation or suggested:
        return {
            "motivation": (motivation or "observe").lower(),
            "energy_level": (energy_level or "medium").lower(),
            "suggested_action": (suggested or "sit").lower(),
        }

    return None


# ── Trigger Detection ───────────────────────────────────────────────

def check_triggers(cat: dict, state, circadian=None, personality=None, memory=None) -> Optional[str]:
    """Check if any LLM trigger condition is met.

    Returns trigger name string or None. Only ONE trigger fires per tick.
    """
    # Trigger 1: Needs conflict — two needs > 70 simultaneously
    needs_conflict = sum(1 for k in ("hunger", "boredom", "social_need", "energy")
                         if cat.get(k, 50) > 70 if k != "energy") > 1
    energy_low = cat.get("energy", 100) < 30
    if needs_conflict and not energy_low:
        return "needs_conflict"

    # Trigger 2: Novel interaction — first time seeing a specific user action
    # Checked via _last_user_action on state — store it per session
    user_action = getattr(state, "_last_user_action", "")
    if user_action and user_action not in _NOVELTY_SET:
        _NOVELTY_SET.add(user_action)
        if len(_NOVELTY_SET) <= 3:  # Only first 3 novel interactions
            return "novel_interaction"

    # Trigger 3: Social return — user absent > 2 hours, just returned
    last_interaction = cat.get("last_interaction_time", 0)
    user_near = cat.get("user_nearby", False)
    if last_interaction and user_near:
        absent_secs = time.time() - last_interaction
        if absent_secs > 7200:  # 2 hours
            return "social_return"

    # Trigger 4: Night disturbance — user active between midnight and 5am
    local_hour = time.localtime().tm_hour
    if 0 <= local_hour <= 5 and user_near:
        return "night_disturbance"

    # Trigger 5: Decision pause — planner uncertainty (set by planner)
    if cat.get("_planner_uncertain", False):
        return "uncertainty"

    return None


# ── Frequency Tracking ─────────────────────────────────────────────

_decision_count = 0
_llm_call_count = 0


def _record_decision(is_llm: bool):
    global _decision_count, _llm_call_count
    _decision_count += 1
    if is_llm:
        _llm_call_count += 1


def get_llm_frequency() -> float:
    """Return LLM call percentage since tracking started."""
    if _decision_count == 0:
        return 0.0
    return (_llm_call_count / _decision_count) * 100.0


def reset_frequency_counters():
    global _decision_count, _llm_call_count
    _decision_count = 0
    _llm_call_count = 0


# ── Integration Hook ────────────────────────────────────────────────

def evaluate_llm(
    cat: dict,
    state,
    circadian=None,
    personality=None,
    memory=None,
) -> Optional[dict]:
    """Evaluate LLM layer. Returns intent dict or None if no LLM needed.

    This is called by BehaviorPlanner between Layer 3 (interaction)
    and Layer 4 (needs). Only fires on specific triggers.
    """
    if not config.LLM_ENABLED:
        _record_decision(False)
        return None

    trigger = check_triggers(cat, state, circadian, personality, memory)
    if not trigger:
        _record_decision(False)
        return None

    # Must also pass <10% gate
    freq = get_llm_frequency()
    if freq >= 9.0:  # Don't exceed 10%
        _record_decision(False)
        return None

    context = build_llm_context(cat, state, circadian, personality, memory, trigger)

    from behavior.agent import CatAgent
    if not hasattr(state, "_llm_agent") or state._llm_agent is None:
        state._llm_agent = CatAgent(
            backend="remote",
            remote_api_url=config.REMOTE_API_URL,
            remote_api_key=config.REMOTE_API_KEY or "",
            remote_model=config.AGENT_REMOTE_MODEL,
            llm_timeout=config.LLM_TIMEOUT,
        )

    # Use agent's non-blocking decide
    action, params = state._llm_agent.decide(cat, state)

    _record_decision(True)

    # Convert agent action to intent
    intent = {
        "motivation": "explore",
        "energy_level": "medium",
        "suggested_action": action.lower() if action and action != "NONE" else "sit",
    }

    logger.info("LLM fired (trigger=%s, freq=%.1f%%, intent=%s)",
                trigger, get_llm_frequency(), intent)
    return intent
