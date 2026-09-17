"""액추에이터 명령 — 검증은 여기서 한 번, 펌웨어에서 또 한 번 (ADR-0003).

호스트 검증은 편의다. 잘못된 명령을 빨리 잡아 디버깅을 쉽게 한다.
**경계를 지키는 최후 방어선은 펌웨어**이며, 이 값들은 펌웨어 상수와 일치해야 한다.
VS-4 에서 이 정의가 역량 계약(capability contract)의 씨앗이 된다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MIN_INTERVAL_MS = 10
"""펌웨어의 MIN_INTERVAL 과 일치. led_blink.ino 참조."""

MAX_INTERVAL_MS = 5000
MIN_LEVEL = 0
MAX_LEVEL = 255
"""펌웨어의 MAX_LEVEL 과 일치."""

Mode = Literal["off", "on", "blink"]


class CommandError(ValueError):
    """명령이 계약을 위반했다."""


@dataclass(frozen=True)
class LedCommand:
    """LED 에 보낼 의도. 타이밍 자체가 아니라 **의도**다 (ADR-0001)."""

    mode: Mode = "off"
    rgb: tuple[int, int, int] = (255, 255, 255)
    interval_ms: int = 500
    level: int = 255

    def __post_init__(self) -> None:
        if self.mode not in ("off", "on", "blink"):
            raise CommandError(f"알 수 없는 mode: {self.mode!r}")
        if len(self.rgb) != 3:
            raise CommandError(f"rgb 는 3개 값이어야 한다: {self.rgb!r}")
        for name, v in zip("rgb", self.rgb):
            if not MIN_LEVEL <= v <= MAX_LEVEL:
                raise CommandError(f"{name} 는 0~255 여야 한다: {v}")
        if not MIN_INTERVAL_MS <= self.interval_ms <= MAX_INTERVAL_MS:
            raise CommandError(
                f"interval_ms 는 {MIN_INTERVAL_MS}~{MAX_INTERVAL_MS} 여야 한다: "
                f"{self.interval_ms}"
            )
        if not MIN_LEVEL <= self.level <= MAX_LEVEL:
            raise CommandError(
                f"level 은 {MIN_LEVEL}~{MAX_LEVEL} 여야 한다: {self.level}"
            )

    def to_wire(self) -> list[str]:
        """시리얼 프로토콜 문장들. 순서가 중요하다 — 모드 전환 전에 파라미터를 세운다."""
        r, g, b = self.rgb
        lines = [f"RGB {r} {g} {b}", f"LEVEL {self.level}"]
        if self.mode == "blink":
            lines += [f"INT {self.interval_ms}", "BLINK"]
        else:
            lines.append(self.mode.upper())
        return lines

    def describe(self) -> str:
        if self.mode == "off":
            return "off"
        colour = "#%02x%02x%02x" % self.rgb
        if self.mode == "blink":
            return f"blink {self.interval_ms}ms {colour} @{self.level}"
        return f"on {colour} @{self.level}"
