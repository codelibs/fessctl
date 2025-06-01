import base64
from datetime import datetime, timezone
from typing import Optional


def to_utc_iso8601(epoch_millis: Optional[int | str]) -> str:
    if epoch_millis is None:
        return "-"
    dt = datetime.fromtimestamp(int(epoch_millis) / 1000, tz=timezone.utc)
    return dt.isoformat(timespec="seconds").replace("+00:00", "Z")


def encode_to_urlsafe_base64(text: str) -> str:
    """
    Converts the specified string to a UTF-8 byte array,
    performs URL-safe Base64 encoding, and returns the result as a string.
    """
    byte_data = text.encode('utf-8')
    encoded_bytes = base64.urlsafe_b64encode(byte_data)
    return encoded_bytes.decode('utf-8')