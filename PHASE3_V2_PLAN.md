# Phase 3: Learning, Social Referencing & Mood Persistence

## Package Tasks

### Coder: Learning Systems
1. **Favorite Spot Learning** — Upgrade memory.py: visit counter, N=10 → favorite, 3× idle weight
2. **Owner Schedule Detection** — New behavior/schedule.py: 24h tracking, 7-day avg, active hour prediction
3. **Engine wiring** — Sleep zone selection uses favorites, pre-active prediction shifts cat behavior

### Muse: Social + Mood + Contagion + REM
4. **Mood Persistence** — Happiness (0-100), Trust (0-100) in state, persist JSON. Affects greeting frequency, approach distance
5. **Social Referencing** — Head turn → object → back → chirp. Duration 2-3s. Triggers on curiosity > 5 + user nearby
6. **Contagious Behavior** — 5s input rate window. Fast typing → tail swish, ear airplane
7. **Sleep REM Twitching** — 1-3 REM episodes during deep sleep, 0.5-1s paw kick + eye flutter

### Me: Integration tests + wiring
- Write full integration test suite for all 6 deliverables
- Stitch Coder + Muse modules into engine
- Verify exit criteria (Lens checklist)

## Sequence
1. Write integration tests
2. Coder + Muse build in parallel
3. Merge → full suite → Lens review
4. Deploy to gk-pc
