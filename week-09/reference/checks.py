"""Check public market-data fields without modifying the caller's records."""

from datetime import datetime, timezone
import math

FIELDS = ("time", "open", "high", "low", "close", "volume", "turnover")
NUMERIC_FIELDS = FIELDS[1:]


def validate_bars(rows):
    """Return new, UTC-normalized records sorted by time, or raise ValueError."""
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a non-empty list of bar records")
    result = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"row {index}: expected a record")
        missing = [name for name in FIELDS if name not in row]
        if missing:
            raise ValueError(f"row {index}: missing fields {', '.join(missing)}")
        try:
            if not isinstance(row["time"], str):
                raise ValueError
            instant = datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
            if instant.tzinfo is None or instant.utcoffset() is None:
                raise ValueError
            instant = instant.astimezone(timezone.utc)
        except (TypeError, ValueError):
            raise ValueError(f"row {index}: time must include a timezone") from None
        if instant in seen:
            raise ValueError(f"row {index}: duplicate time {instant.isoformat()}")
        seen.add(instant)
        normalized = {"time": instant.isoformat().replace("+00:00", "Z")}
        for name in NUMERIC_FIELDS:
            try:
                if isinstance(row[name], bool):
                    raise ValueError
                value = float(row[name])
            except (TypeError, ValueError, OverflowError):
                raise ValueError(f"row {index}: {name} must be a finite number") from None
            if not math.isfinite(value):
                raise ValueError(f"row {index}: {name} must be a finite number")
            normalized[name] = value
        if any(normalized[name] <= 0 for name in ("open", "high", "low", "close")):
            raise ValueError(f"row {index}: prices must be positive")
        if not (normalized["low"] <= normalized["open"] <= normalized["high"]
                and normalized["low"] <= normalized["close"] <= normalized["high"]):
            raise ValueError(f"row {index}: open and close must lie between low and high")
        if normalized["volume"] < 0 or normalized["turnover"] < 0:
            raise ValueError(f"row {index}: volume and turnover must be non-negative")
        result.append(normalized)
    return sorted(result, key=lambda row: row["time"])
