
from datetime import datetime, timezone



def make_naive_utc(dt: datetime | str | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt