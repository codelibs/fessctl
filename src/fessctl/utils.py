from datetime import datetime, timezone
from typing import Optional


def to_utc_iso8601(epoch_millis: Optional[int | str]) -> str:
    if epoch_millis is None:
        return "-"
    dt = datetime.fromtimestamp(int(epoch_millis) / 1000, tz=timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")
