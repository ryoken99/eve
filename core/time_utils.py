from __future__ import annotations

from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def lisbon_tz():
    try:
        return ZoneInfo("Europe/Lisbon")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=1), name="Europe/Lisbon-fallback")


def now_lisbon() -> datetime:
    return datetime.now(lisbon_tz())
