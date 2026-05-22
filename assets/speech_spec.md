# Speech Bubble — Phase 2D Implementation Spec

## 1. Bubble Types & Moods

Text for each state/mood. Text is randomly selected from its pool on trigger.

| Mood | Texts (max 15 chars) | Mood Icon (top cell) |
|------|----------------------|---------------------|
| `bored` | "zzz...", "yawwwn", "pet me?" | 💤 |
| `happy` | "purrrr~", "nyaa~", "😊" | 😊 |
| `hungry` | "feed me.", "hungry...", "🍣" | 🍣 |
| `alert` | "!?", "who's there?", "👀" | 👀 |
| `sleepy` | "💤", "zzz...", "don't wanna" | 💤 |
| `playful` | "pounce!", "hehe", "🎯" | 🎯 |
| long-idle | "hello?", "still there?", "👋" | 👋 |

### Trigger Conditions

- **State transitions**: On entering any mood state, display one random text from that mood's pool.
- **Idle check**: Every idle check cycle (every 30s of no interaction), if cat has been idle > 120s, show a `long-idle` bubble. Cooldown 60s between idle bubbles.
- **Proximity**: Mouse cursor within 60px of cat head → show (mood-relevant or `happy` if petting). Cooldown 15s after dismiss.
- **Priority override**: See §4.5 in creative brief.

---

## 2. Bubble Visual Design

Two-cell layout, pixel-modern aesthetic (not retro blocky).

### Layout

```
┌──────────────────────┐
│  [mood emoji] 24×24  │  ← top cell (30px tall)
├──────────────────────┤
│  [text, max 15 chars] │  ← bottom cell (20px tall)
└─────────┬────────────┘
          │ tail        ← 10px base, 8px height
          ▼
        cat head
```

### Specs

| Property | Value |
|----------|-------|
| Total size | ~140 × 50px (wider if text is shorter — min 100px) |
| Top cell height | 30px (emoji centered) |
| Bottom cell height | 20px (text centered) |
| Corner radius | 4px (all four corners) |
| Background | `#2A2A2A` with alpha 200/255 — semi-transparent warm dark |
| Border | none |
| Text color | `#E0E0E0` |
| Emoji size | 16px (centered in 24×24 area) |
| Font | Segoe UI, 10pt |
| Max text length | 15 characters |
| Text alignment | centered horizontally + vertically |

### Tail

- **Shape**: Isosceles triangle, 10px base width, 8px height.
- **Position**: Bottom-center of bubble, pointing down toward the cat's head.
- **Color**: Same as bubble background (`#2A2A2A` at alpha 200).
- **Facing-based offset**:
  - Cat facing **right**: tail centered, no x-offset (bubble is roughly above head).
  - Cat facing **left**: tail offset +4px right from center (cat's head is to the left, bubble wants pointer toward it).
  - If cat is near screen top (`cat.y < 60`): flip bubble below cat. Tail points **up** (rotated 180°, same dimensions).

### Shadow

- None on the bubble itself (transparency + dark bg provides depth). Let the cat's shadow on the ground handle depth cues.

---

## 3. Implementation (Python API)

Add to the cat state object in the main state class:

```python
# In state class __init__
self.speech = {
    "text": None,          # Current displayed text (str or None)
    "emoji": None,         # Current mood emoji (str or None)
    "timer": 0.0,          # Remaining display time in seconds
    "fading": False,       # True during fade-out
    "opacity": 1.0,        # 0.0 → 1.0
    "queue": [],           # List of {"text": str, "emoji": str, "duration": float}
}
self.speech_timer = 0.0   # Cooldown/proximity timer for trigger management
self.speech_queue = []     # Secondary queue for queued messages (see priority)
```

### Cycle Logic (per tick)

```python
# Called each frame (TICK_MS ~50ms)
def update_speech(dt):
    s = state.speech

    # No active speech, check queue
    if s["text"] is None and s["queue"]:
        next_msg = s["queue"].pop(0)
        s["text"] = next_msg["text"]
        s["emoji"] = next_msg["emoji"]
        s["timer"] = next_msg["duration"]
        s["fading"] = False
        s["opacity"] = 0.0  # Will fade in over 0.3s
        s["timer"] += 0.3   # Account for fade-in time

    # Active speech
    if s["text"] is not None:
        if s["timer"] > 0:
            s["timer"] -= dt

            # Fade-in phase (first 0.3s)
            if s["opacity"] < 1.0 and not s["fading"]:
                s["opacity"] = min(1.0, s["opacity"] + dt / 0.3)

            # Transition to fade-out
            if s["timer"] <= 0.5 and not s["fading"]:
                s["fading"] = True

            # Fade-out phase (last 0.5s)
            if s["fading"]:
                s["opacity"] = max(0.0, s["opacity"] - dt / 0.5)

            # Fully faded out — clear
            if s["timer"] <= 0 and s["opacity"] <= 0:
                s["text"] = None
                s["emoji"] = None
                s["timer"] = 0.0
                s["fading"] = False
                s["opacity"] = 0.0
```

### State Transition Hook

```python
def on_state_transition(new_mood: str):
    """Called when cat transitions to a new mood."""
    mood_data = SPEECH_MOODS.get(new_mood)
    if not mood_data:
        return

    # Pick random text + emoji from the mood's pool
    text = random.choice(mood_data["texts"])
    emoji = mood_data["emoji"]

    # If current speech is higher priority, queue this one
    if state.speech["text"] is not None:
        if MOOD_PRIORITY.get(new_mood, 1) > MOOD_PRIORITY.get(current_mood, 1):
            # High priority — interrupt
            state.speech["fading"] = True
            state.speech["timer"] = min(state.speech["timer"], 0.15)  # Quick fade
        elif MOOD_PRIORITY.get(new_mood, 1) >= MOOD_PRIORITY.get(current_mood, 1):
            # Queue it
            state.speech["queue"].append({
                "text": text, "emoji": emoji, "duration": SPEECH_DURATION
            })
            return  # Don't trigger now
        else:
            return  # Lower priority, drop
```

### Drawing Function

```python
def draw_speech_bubble(painter, cat_x, cat_y, cat_facing_right):
    s = state.speech
    if s["text"] is None:
        return

    painter.setOpacity(s["opacity"])

    # Bubble dimensions
    bubble_w = 140
    top_h = 30    # emoji cell
    bot_h = 20    # text cell
    total_h = top_h + bot_h

    # Position: 20px above cat head, centered
    bx = cat_x - bubble_w // 2
    by = cat_y - total_h - 20  # 20px above cat head

    # Flip below if near top edge
    if by < 5:
        by = cat_y + 50  # below cat head

    # Clip bx to screen bounds (keep 5px margin)
    bx = max(5, min(bx, SCREEN_W - bubble_w - 5))

    # Tail direction
    tail_dir = -1 if cat_facing_right else 1  # not needed, using visual offset

    # --- Draw bubble background ---
    path = QPainterPath()
    path.addRoundedRect(bx, by, bubble_w, total_h, 4, 4)
    painter.fillPath(path, QColor(42, 42, 42, 200))

    # --- Draw divider line ---
    painter.setPen(QPen(QColor(60, 60, 60, 200), 1))
    painter.drawLine(bx + 4, by + top_h, bx + bubble_w - 4, by + top_h)

    # --- Draw emoji ---
    painter.setFont(QFont("Segoe UI", 12))
    painter.setPen(QColor(224, 224, 224))
    emoji_rect = QRectF(bx, by, bubble_w, top_h)
    painter.drawText(emoji_rect, Qt.AlignCenter, s["emoji"] or "")

    # --- Draw text ---
    painter.setFont(QFont("Segoe UI", 10))
    text_rect = QRectF(bx, by + top_h, bubble_w, bot_h)
    painter.drawText(text_rect, Qt.AlignCenter, s["text"])

    # --- Draw tail ---
    tail_center_x = bx + bubble_w // 2
    tail_top_y = by + total_h
    tail_bottom_y = tail_top_y + 8

    if by < cat_y:  # Normal: tail points down
        tail_points = QPolygonF([
            QPointF(tail_center_x, tail_bottom_y),
            QPointF(tail_center_x - 5, tail_top_y),
            QPointF(tail_center_x + 5, tail_top_y),
        ])
    else:  # Flipped: tail points up
        tail_points = QPolygonF([
            QPointF(tail_center_x, tail_top_y),
            QPointF(tail_center_x - 5, tail_bottom_y),
            QPointF(tail_center_x + 5, tail_bottom_y),
        ])

    painter.setBrush(QColor(42, 42, 42, 200))
    painter.setPen(Qt.NoPen)
    painter.drawPolygon(tail_points)

    painter.setOpacity(1.0)
```

---

## 4. Trigger Points Summary

| Trigger | Where | Duration | Priority |
|---------|-------|----------|----------|
| State transition | `on_state_transition()` | 3.0s | High (interrupts) |
| Idle check (>120s idle) | `idle_check()` cycle | 3.0s | Normal |
| Proximity (mouse within 60px) | `mouse_move_event()` | 3.0s | Normal |
| On pet | `pet_handler()` | 3.0s | High |
| On toy interaction | toy state machine handlers | 3.0s | Normal |
| On API feed | `api_feed_handler()` | 3.0s | High |

### Constants (add to `config.py`)

```python
# Speech bubble
SPEECH_BUBBLE_W = 140
SPEECH_CELL_TOP_H = 30
SPEECH_CELL_BOT_H = 20
SPEECH_ABOVE_GAP = 20
SPEECH_BELOW_GAP = 50
SPEECH_FADE_IN = 0.3       # seconds
SPEECH_DISPLAY = 3.0       # base seconds (add 0.5s per 5 chars beyond 5)
SPEECH_FADE_OUT = 0.5      # seconds
SPEECH_MAX_CHARS = 15
SPEECH_QUEUE_MAX = 5       # max queued messages
SPEECH_IDLE_COOLDOWN = 60  # seconds between idle bubbles
SPEECH_IDLE_THRESHOLD = 120  # seconds idle before "hello?"
SPEECH_PROXIMITY_RADIUS = 60  # px
SPEECH_PROXIMITY_COOLDOWN = 15  # seconds
```

### Mood Priority

```python
MOOD_PRIORITY = {
    "hungry": 3,    # highest
    "alert": 3,
    "playful": 2,
    "happy": 2,
    "bored": 1,
    "sleepy": 0,
    "long-idle": 1,
}
```

---

## 5. Edge Cases

1. **Very short messages** (e.g., "😊"): Min bubble width 100px, still uses 2-cell layout.
2. **Queue overflow**: If queue exceeds 5, drop lowest-priority pending items. Never drop hungry/alert.
3. **Rapid state flips**: Only trigger on *state entry* (once per transition), not every tick.
4. **Cat moving**: Bubble follows cat position each frame (redrawn at cat's current x,y).
5. **Screen edge collision**: bx is clamped to [5, screen_w - bubble_w - 5]; flip below if y < 5.
6. **Empty emoji/text**: If emoji is None, collapse top cell to 10px (emoji hidden, divider hidden). If text is None, collapse bottom cell to 0px.
7. **Multi-cat**: Each cat instance has its own `state.speech` dict. Bubble draws independently per cat.
