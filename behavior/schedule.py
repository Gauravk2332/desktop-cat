"""
behavior/schedule.py — Owner schedule detection.

Tracks user activity across 24 hourly slots with a 7-day rolling average
for predicting peak activity times. Used to make the cat pre-active before
the owner is likely to interact.
"""

import json
import logging
import os
import tempfile

import config

logger = logging.getLogger(__name__)


class OwnerSchedule:
    """Track user activity across 24 hourly slots. 7-day rolling average."""

    def __init__(self):
        # hourly_activity[hour] = list of last 7 days' activity levels (0.0-1.0)
        self.hourly_activity: dict[int, list[float]] = {h: [] for h in range(24)}
        self.persist_file = config.SCHEDULE_FILE
        self._load()

    def record_activity(self, hour: int, level: float) -> None:
        """Record activity level for a given hour (0.0-1.0)."""
        if hour < 0 or hour > 23:
            return
        daily = self.hourly_activity.setdefault(hour, [])
        daily.append(min(1.0, level))
        # Keep only last 7 days
        if len(daily) > 7:
            daily.pop(0)
        self._save()

    def get_average(self, hour: int) -> float:
        """Return average activity for a given hour across 7 days."""
        daily = self.hourly_activity.get(hour, [])
        if not daily:
            return 0.0
        return sum(daily) / len(daily)

    def predict_active_hour(self) -> int:
        """Return the hour with highest average user activity."""
        best_hour = 12  # default noon
        best_avg = -1.0
        for h in range(24):
            daily = self.hourly_activity.get(h, [])
            if not daily:
                continue
            avg = sum(daily) / len(daily)
            if avg > best_avg:
                best_avg = avg
                best_hour = h
        return best_hour

    def predict_pre_active_time(self) -> float:
        """Return hours until cat should be pre-active (30min before peak)."""
        peak = self.predict_active_hour()
        return max(0.0, peak - 0.5)  # 30 min before peak

    def _load(self):
        """Load schedule from disk."""
        try:
            if os.path.exists(self.persist_file):
                with open(self.persist_file, "r") as f:
                    data = json.load(f)
                    self.hourly_activity = {
                        int(k): v for k, v in data.get("hourly", {}).items()
                    }
        except (json.JSONDecodeError, OSError, PermissionError) as e:
            logger.warning("Failed to load schedule %s: %s", self.persist_file, e)

    def _save(self):
        """Save schedule to disk atomically."""
        try:
            data = {
                "hourly": {
                    str(h): v for h, v in self.hourly_activity.items()
                }
            }
            os.makedirs(os.path.dirname(self.persist_file), exist_ok=True)
            fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.persist_file))
            with os.fdopen(fd, "w") as f:
                json.dump(data, f)
            os.replace(tmp, self.persist_file)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to save schedule %s: %s", self.persist_file, e)
