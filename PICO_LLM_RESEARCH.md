# Pico LLM Research — Desktop Cat Decision Engine

**Date**: 2026-05-22
**Context**: Replace state machine with local LLM on Windows 11 (i7-12700, 32GB RAM, integrated GPU only)

---

## 1. Recommendation: Phi-4-mini (3.8B) Q4_K_M

**Winner**: `phi4-mini` via Ollama (2.5GB model file)

| Criterion | Phi-4-mini | Llama 3.2 3B | Qwen2.5-7B | Gemma-3-4b |
|-----------|-------------|--------------|-------------|------------|
| Model size (Q4) | **2.5 GB** | 2.0 GB | 4.5 GB | 2.8 GB |
| Quality / reasoning | **Excellent** (best-in-class for 3B) | Good | Better | Good |
| CPU speed (est. i7-12700) | **15-20 tok/s** | 20-25 tok/s | 8-12 tok/s | 12-18 tok/s |
| First-token latency | **~400-600ms** | ~300-500ms | ~800-1200ms | ~500-700ms |
| Structured output | **JSON via system prompt** | Good | Good | Good |
| 128K context | ✅ | ✅ (128K) | ✅ (32K) | ✅ (8K) |
| Function calling | ✅ built-in | ❌ | ✅ | ❌ |

### Why Phi-4-mini over alternatives

1. **Versus Llama 3.2 3B**: Llama 3.2 3B is lighter and slightly faster, but Phi-4-mini has markedly better reasoning quality for the decision-making task. The cat's actions need to feel intentional, not random. Phi-4-mini's training focus on synthetic reasoning data (math, logic, decision chains) makes it naturally suited for a "given these inputs, pick one action" task.

2. **Versus Qwen2.5-7B**: Qwen2.5-7B has better general quality, but at 4.5GB it consumes more RAM and is significantly slower on CPU (8-12 tok/s vs 15-20). The quality gap for a single-action-output task is negligible. The extra context (128K vs 32K) of Phi-4-mini is irrelevant for ~500 token windows. The 2GB RAM savings matter.

3. **Versus Gemma-3-4b**: Comparable size/speed, but Gemma-3 has a more restrictive license and weaker structured output compliance in benchmarks.

4. **Versus Mistral-7B / DeepSeek-Coder-1.3B**: Mistral-7B is overkill (4.5GB, slower). DeepSeek-Coder-1.3B is too specialized and weak at general decision-making.

### Fallback model

If Phi-4-mini proves too slow for sub-500ms decisions, switch to **Llama 3.2 3B** (Q4_K_M, ~2.0GB). It's the next best option with lower latency.

---

## 2. Ollama on Windows — Installation & Service Setup

### 2.1 Install Ollama

**Method A — PowerShell (silent, no GUI):**
```powershell
# Run as Administrator
irm https://ollama.com/install.ps1 | iex
```

**Method B — Offline installer:**
Download `OllamaSetup.exe` from https://ollama.com/download/windows
Run silently: `OllamaSetup.exe /S`

Installs to: `C:\Users\<User>\AppData\Local\Programs\Ollama\`

### 2.2 Run as a Background Service (survives logoff)

Ollama on Windows does NOT install itself as a Windows Service by default. It runs as a user-level background process that terminates on logoff.

**Option A — NSSM (free, recommended):**
```powershell
# Install nssm from https://nssm.cc/download
# Create service:
nssm install Ollama "C:\Users\<User>\AppData\Local\Programs\Ollama\ollama.exe" "serve"
nssm set Ollama AppNoConsole 1
nssm start Ollama

# Verify:
nssm status Ollama
```

**Option B — Task Scheduler (free, built-in):**
Create a task that runs `ollama.exe serve` at system startup, with "Run whether user is logged on or not" and "Run with highest privileges".

**Option C — AlwaysUp (paid, $49):**
Third-party tool that wraps any exe as a Windows service. Works, but unnecessary when NSSM does the same for free.

### 2.3 Verify service is running

```powershell
curl http://localhost:11434/
# Should return "Ollama is running"

curl http://localhost:11434/api/tags
# Lists installed models
```

### 2.4 Pull the model

```powershell
ollama pull phi4-mini
# Downloads ~2.5GB

# Verify:
ollama list
# Should show phi4-mini:latest
```

---

## 3. Expected Inference Latency

### Key metric for this use case: Time-to-First-Token + 1 generation token

Since the cat only outputs a single action (e.g., `{"action": "sleep"}`), total latency = **prompt evaluation time** + **1 token generation time**.

### Benchmark-based estimates for i7-12700 (CPU-only)

**Reference data**: Llama 3.1 8B Q4_K_M on AMD EPYC 9354 (32 cores, 3.8 GHz) achieved:
- 14.2 tok/s generation, 380ms p50 first-token latency for 512-token prompt
- 5.1 GB peak RAM

**i7-12700 estimate** (8 P-cores + 4 E-cores, AVX2, DDR4/DDR5):

| Model | Tokens/sec | First-token (500 ctx) | Total per decision | Peak RAM |
|-------|-----------|----------------------|-------------------|----------|
| Phi-4-mini Q4_K_M | **15-20 tok/s** | **400-600ms** | **~450-650ms** | **~2.5 GB** |
| Llama 3.2 3B Q4_K_M | 20-25 tok/s | 300-500ms | ~350-550ms | ~2.0 GB |
| Qwen2.5-7B Q4_K_M | 8-12 tok/s | 800-1200ms | ~900-1300ms | ~4.5 GB |

**Verdict**: Phi-4-mini hits the sub-second target for the decision loop. The first call after idle (cold start) adds 500-1500ms for model loading from disk — see Section 5 for mitigation.

### Optimization tips for speed

1. **Set `num_thread` to physical core count**: 8 threads (P-cores) for i7-12700. More causes cache thrashing.
2. **Set `num_ctx` to 2048**: Don't waste CPU on unused context.
3. **Avoid streaming**: Use `"stream": false` for single-action output. Saves serialization overhead.
4. **Pre-load model at startup** (see Section 5).

---

## 4. Context Window Budget

### Estimated per-request context

| Component | Tokens |
|-----------|--------|
| System prompt (cat personality, JSON schema) | ~200 |
| Current state (time, weather, energy, hunger, boredom, proximity) | ~100 |
| Recent action history (last 5-10 actions) | ~200 |
| User input / trigger | ~50 |
| **Total budget** | **~550 tokens** |

### Recommendation

- **Set `num_ctx`: 2048** — comfortable headroom for history and persona
- No need for long context; Phi-4-mini's 128K is irrelevant here but free

---

## 5. Memory Constraints & Model Management

### RAM budget (i7-12700, 32GB)

| Component | RAM |
|-----------|-----|
| Windows 11 | ~4-6 GB |
| Cat app + Python runtime | ~0.5 GB |
| Ollama service overhead | ~0.3 GB |
| **Phi-4-mini Q4_K_M (resident)** | **~2.5 GB** |
| Other background apps | ~2 GB |
| **Total** | **~10 GB** |
| **Available headroom** | **~22 GB** |

No RAM concerns at all. Even running the 7B model leaves headroom.

### Keep-alive strategy

**Default**: Ollama unloads a model 5 minutes after the last request.

**Cat app needs**: Model stays resident permanently (decisions can be seconds apart).

**Solution — set keep_alive to -1 (infinite):**
```python
# In Python request:
payload = {
    "model": "phi4-mini",
    "messages": [...],
    "keep_alive": -1,  # Pin in RAM forever
    "stream": False,
    "options": {"num_thread": 8, "num_ctx": 2048}
}
```

**Or set environment variable**: `OLLAMA_KEEP_ALIVE=-1` in the service config (NSSM or system-wide).

**Verification:**
```powershell
curl http://localhost:11434/api/ps
# Should show phi4-mini with expires_at: "0001-01-01T00:00:00Z" (pinned)
```

### Cold start mitigation

1. Pre-load model at service startup:
```powershell
# In service startup script, after Ollama starts:
curl -s -X POST http://localhost:11434/api/generate -d "{\"model\": \"phi4-mini\", \"prompt\": \"\", \"keep_alive\": -1}" > $null
```

2. In the cat app, send a warm-up request during startup (discard result). First real decision will then be hot (~500ms instead of 2-3s).

---

## 6. Python API Reference

### Recommended: Direct REST API (no extra dependencies beyond `requests`)

```python
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"

def decide_action(state: dict, history: list) -> dict:
    """
    Ask the model what the cat should do next.
    Returns a dict with at least {"action": "..."}.
    """
    system_prompt = f"""You are a desktop cat companion. Given your current state,
choose ONE action from: sleep, wake, walk, eat, drink, play, groom, meow, watch, explore.

Respond ONLY with a JSON object, no other text:
{{"action": "<action>", "reason": "<brief reason>"}}

Cat personality: curious but lazy. Prefers warm spots. Gets playful at night.
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # Add recent history
    for entry in history[-10:]:
        messages.append({"role": "user", "content": str(entry["state"])})
        messages.append({"role": "assistant", "content": json.dumps(entry["action"])})

    # Current state as the prompt
    messages.append({"role": "user", "content": json.dumps(state)})

    payload = {
        "model": "phi4-mini",
        "messages": messages,
        "stream": False,
        "keep_alive": -1,      # keep model resident
        "options": {
            "num_thread": 8,   # match physical cores on i7-12700
            "num_ctx": 2048,   # no need for more
            "temperature": 0.7 # some randomness for personality
        }
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=10)
        resp.raise_for_status()
        content = resp.json()["message"]["content"]

        # Parse JSON from response
        # Handle case where model wraps in markdown
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        return json.loads(content)

    except requests.exceptions.ConnectionError:
        return {"action": "sleep", "reason": "ollama_unavailable"}
    except (json.JSONDecodeError, KeyError) as e:
        return {"action": "sleep", "reason": f"parse_error: {str(e)}"}

# Usage:
state = {
    "energy": 75,
    "hunger": 30,
    "boredom": 60,
    "time": "14:30",
    "proximity": "near_desk",
    "weather": "sunny"
}
history = []  # List of past state+action pairs

action = decide_action(state, history)
print(action)  # {"action": "sleep", "reason": "midday_sun_spot"}
```

### Alternative: Ollama Python library

```python
import ollama

response = ollama.chat(
    model="phi4-mini",
    messages=[...],
    options={"num_thread": 8, "num_ctx": 2048},
    keep_alive=-1
)
```

The direct REST API is preferred — simpler dependency, more control over error handling.

### Key API endpoints used

| Endpoint | Purpose |
|----------|---------|
| `POST /api/chat` | Chat completion (recommended — supports system messages) |
| `POST /api/generate` | Simple text generation |
| `GET /api/tags` | List pulled models |
| `GET /api/ps` | Show models currently loaded in RAM |
| `POST /api/pull` | Download a model |

---

## 7. Crash Recovery & Error Handling

### Failure modes and mitigations

| Failure | Symptom | Mitigation |
|---------|---------|------------|
| Ollama service stopped | Connection refused on `:11434` | Cat process catches `ConnectionError`, falls back to basic state machine or deterministic action ("sleep") |
| Model not found | 404 from API | Auto-pull on first run: `ollama pull phi4-mini` |
| OOM (unlikely with 32GB) | Process killed | Set `num_ctx` conservatively (2048), monitor via `ollama ps` |
| GPU driver crash | N/A (CPU-only, no GPU risk) | — |
| Windows update reboot | Service stops | NSSM auto-restart; cat process retries connection every 5s |
| Long inference (>5s) | Cat freezes | Set HTTP timeout (10s). Use async/non-blocking call in main loop |

### Recommended architecture

```
[Cat main loop, ~1-2Hz]
    |
    ├── state = collect_state()       # sensor read, fast
    ├── if ollama_available:
    │       action = call_llm(state)  # async, 500ms typical
    │   else:
    │       action = fallback_fsm(state)  # deterministic
    │
    └── execute(action)               # animation, fast
```

The fallback FSM (current state machine) becomes the safety net rather than primary engine. This means the cat never freezes — it only gets smarter when Ollama is available.

### Startup sequence

1. Cat app starts → begins running fallback FSM immediately
2. Spawn background thread: check Ollama health, pull model if needed, warm up model
3. Once warm-up completes (~3-5s for first load), switch to LLM-driven mode
4. If LLM fails mid-session, fall back to FSM, retry in 30s

---

## 8. Alternatives Considered

### Windows-native options beyond Ollama

| Solution | Verdict |
|----------|---------|
| **llama.cpp directly** | Viable but more work. Same GGUF models. Slightly lower overhead (~0.1s faster) but loses Ollama's model management, keep-alive, and easy pulling. Not worth it. |
| **llama.cpp DirectML** | Could leverage Intel integrated GPU via DirectX 12. The i7-12700 has Intel UHD 770 iGPU. Real-world tests show only 1.5-2x speedup over CPU for small models on iGPU. Not transformative. Adds complexity. Skip. |
| **llama.cpp SYCL** | Intel SYCL backend for iGPUs. Experimental. Skip for now. |
| **ONNX Runtime** | Requires model conversion. Windows-native but far more complex setup. No keep-alive. Skip. |
| **GPT4All** | Windows-native, but less model choice and no keep-alive control. Skip. |

**Verdict**: Ollama is the right choice. The overhead vs raw llama.cpp is negligible (~50ms per call, acceptable for cat decisions). The benefits (model management, keep-alive, API, easy updates) far outweigh it.

### What about DirectML / Intel iGPU?

The i7-12700 has Intel UHD Graphics 770 (24 EUs). This is NOT a dedicated GPU. Benchmarks show:
- UHD 770 gives ~1.5-2x speedup over CPU-only for small models (3B-7B)
- But setting up DirectML or SYCL with Ollama adds complexity
- For a 500ms target, CPU-only achieves ~500ms. GPU acceleration isn't needed.

**Recommendation**: Start with CPU-only. If latency is too high, explore DirectML as a second step.

---

## 9. Summary Checklist for Gk

- [ ] Download/OllamaSetup.exe or run `irm https://ollama.com/install.ps1 | iex` on gk-pc
- [ ] Install NSSM and create Windows Service for `ollama.exe serve`
- [ ] Set `OLLAMA_KEEP_ALIVE=-1` environment variable in service config
- [ ] `ollama pull phi4-mini` (2.5GB download)
- [ ] Verify: `curl http://localhost:11434/api/ps` shows phi4-mini loaded
- [ ] Add `POST /api/chat` call to cat Python process as shown in Section 6
- [ ] Keep fallback FSM for crash recovery
- [ ] Pre-load model on service startup via empty-prompt curl
