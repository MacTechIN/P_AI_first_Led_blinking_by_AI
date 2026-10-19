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

    def poll(self) -> None:
        """매 스텝 불린다. 명령이 바뀌지 않아도.

        `ControlLoop` 은 명령이 **바뀔 때만** 구동한다(ADR-0007). 정지한 장면에서는
        아무것도 나가지 않고, 워치독이 켜져 있으면 **호스트가 멀쩡한데도 트립한다.**
        시뮬레이터에 워치독을 넣고 나서야 드러났다 — 워치독이 기본으로 꺼져 있어
        지금껏 아무도 밟지 않았을 뿐이다.

        그래서 살아 있다는 신호를 보낼 자리가 따로 필요하다. 기본은 아무것도
        하지 않는다.
        """

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

    def __init__(self, port: str = "/dev/ttyACM0", *, verbose: bool = False,
                 keepalive_ms: int = 0) -> None:
        import sys
        import time
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
        from blink import Arduino

        self._ard = Arduino(port, verbose=verbose)
        self._last: LedCommand | None = None
        self.keepalive_ms = keepalive_ms
        """0 이면 끔. 워치독을 켠 장치에서는 **워치독 주기보다 짧게** 둬야 한다.

        `PING` 을 쓴다 — 워치독을 먹이지만 트립은 풀지 않는 명령이다. 트립을
        푸는 것은 출력을 구동하는 명령뿐이어야 한다 (펌웨어 주석 참조).
        """
        self._last_sent = time.monotonic()

    def apply(self, cmd: LedCommand) -> None:
        import time

        for line in self._diff(cmd):
            self._ard.send(line)
        self._last = cmd
        self._last_sent = time.monotonic()

    def poll(self) -> None:
        """워치독이 켜져 있으면 살아 있다는 신호를 보낸다."""
        if not self.keepalive_ms:
            return
        import time

        now = time.monotonic()
        if (now - self._last_sent) * 1000.0 >= self.keepalive_ms:
            self._ard.send("PING")
            self._last_sent = now

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
