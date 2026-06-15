from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import socket
from typing import Any

from .channels import ANALOG_CHANNELS, DIGITAL_CHANNELS

TELNET_TIMEOUT = 5.0


class HargassnerError(Exception):
    """Raised when the Hargassner telnet stream cannot be parsed/read."""


def _parse_number(token: str) -> int | float | str:
    try:
        value = float(token)
    except ValueError:
        return token
    if value.is_integer():
        return int(value)
    return value


def _parse_digital_word(token: str) -> int:
    token = token.strip()
    if not token:
        return 0
    # The HV20 DAQ stream emits digital words as four-character hex-ish words
    # such as 0082, 4800, 008A. Use base 16 for stable bit mapping.
    try:
        return int(token, 16)
    except ValueError:
        return int(float(token))


@dataclass(slots=True)
class HargassnerFrame:
    raw: str
    analog: dict[int, int | float | str]
    digital_words: list[int]
    digital: dict[str, bool]
    received_at: datetime

    @property
    def available(self) -> bool:
        return bool(self.analog)


def parse_pm_frame(raw: str) -> HargassnerFrame:
    """Parse one `pm ...` line from the Hargassner HV20 telnet stream."""
    line = raw.strip().replace("\r", "")
    # Sometimes a socket read can contain multiple frames. Prefer the first full pm line.
    for candidate in line.split("\n"):
        candidate = candidate.strip()
        if candidate.startswith("pm "):
            line = candidate
            break
    parts = line.split()
    if not parts or parts[0] != "pm":
        raise HargassnerError(f"No pm frame found in: {raw[:80]!r}")

    analog_count = len(ANALOG_CHANNELS)
    expected_min = 1 + analog_count
    if len(parts) < expected_min:
        raise HargassnerError(
            f"Incomplete pm frame: got {len(parts) - 1} values, need at least {analog_count} analog values"
        )

    analog: dict[int, int | float | str] = {}
    for channel in ANALOG_CHANNELS:
        idx = channel["id"] + 1  # token 0 is "pm"; DAQ analog id 0 is token 1
        analog[channel["id"]] = _parse_number(parts[idx])

    digital_tokens = parts[1 + analog_count :]
    digital_words = [_parse_digital_word(tok) for tok in digital_tokens]
    digital: dict[str, bool] = {}
    for channel in DIGITAL_CHANNELS:
        word_index = channel["word"]
        bit = channel["bit"]
        word_value = digital_words[word_index] if word_index < len(digital_words) else 0
        digital[channel["key"]] = bool(word_value & (1 << bit))

    return HargassnerFrame(
        raw=line,
        analog=analog,
        digital_words=digital_words,
        digital=digital,
        received_at=datetime.now(timezone.utc),
    )


class HargassnerClient:
    def __init__(self, host: str, port: int = 23, timeout: float = TELNET_TIMEOUT) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def read_frame(self) -> HargassnerFrame:
        chunks: list[bytes] = []
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                # The boiler sends continuously on connect. A newline payload is harmless on this firmware,
                # but not required; stay read-only/passive.
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    text = b"".join(chunks).decode("ascii", errors="replace")
                    if "\n" in text and text.lstrip().startswith("pm"):
                        return parse_pm_frame(text)
                    if len(text) > 8192:
                        return parse_pm_frame(text)
        except (OSError, TimeoutError) as err:
            raise HargassnerError(f"Cannot read Hargassner telnet stream {self.host}:{self.port}: {err}") from err

        if not chunks:
            raise HargassnerError("No data received from Hargassner telnet stream")
        return parse_pm_frame(b"".join(chunks).decode("ascii", errors="replace"))


def frame_to_dict(frame: HargassnerFrame) -> dict[str, Any]:
    return {
        "raw": frame.raw,
        "analog": frame.analog,
        "digital_words": frame.digital_words,
        "digital": frame.digital,
        "received_at": frame.received_at.isoformat(),
    }
