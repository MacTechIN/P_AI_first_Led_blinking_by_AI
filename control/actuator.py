"""액추에이터 — 명령을 실제 장치로 보낸다.

`LedCommand` 만 받고 시리얼 문법은 여기에 가둔다. VS-4 에서 이 클래스가
역량 계약의 구현체가 된다.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .commands import LedCommand


class Actuator(ABC):
    @abstractmethod
    def apply(self, cmd: LedCommand) -> None: ...

    def close(self) -> None:
        pass

    def __enter__(self) -> "Actuator":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class NullActuator(Actuator):
    """아무것도 구동하지 않고 기록만 한다. 하드웨어 없는 시험용."""

    def __init__(self) -> None:
        self.history: list[LedCommand] = []

    def apply(self, cmd: LedCommand) -> None:
        self.history.append(cmd)

    @property
    def last(self) -> LedCommand | None:
        return self.history[-1] if self.history else None


class SerialLedActuator(Actuator):
    """아두이노 LED. 바뀐 것만 보낸다.

    매번 전체 명령을 보내면 시리얼이 붐비고, 무엇보다 같은 `BLINK` 를 반복
    전송하면 펌웨어가 위상을 리셋해 점멸이 끊겨 보인다. 그래서 직전 명령과
    비교해 달라진 부분만 보낸다.
    """

    def __init__(self, port: str = "/dev/ttyACM0", *, verbose: bool = False) -> None:
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
        from blink import Arduino

        self._ard = Arduino(port, verbose=verbose)
        self._last: LedCommand | None = None

    def apply(self, cmd: LedCommand) -> None:
        for line in self._diff(cmd):
            self._ard.send(line)
        self._last = cmd

    def _diff(self, cmd: LedCommand) -> list[str]:
        if self._last is None:
            return cmd.to_wire()

        lines: list[str] = []
        if cmd.rgb != self._last.rgb:
            r, g, b = cmd.rgb
            lines.append(f"RGB {r} {g} {b}")
        if cmd.level != self._last.level:
            lines.append(f"LEVEL {cmd.level}")
        if cmd.mode == "blink":
            if cmd.interval_ms != self._last.interval_ms:
                lines.append(f"INT {cmd.interval_ms}")
            if self._last.mode != "blink":
                lines.append("BLINK")
        elif cmd.mode != self._last.mode:
            lines.append(cmd.mode.upper())
        return lines

    def close(self) -> None:
        self._ard.close()

    def describe(self) -> dict[str, Any]:
        return {"type": "SerialLedActuator", "last": self._last}
