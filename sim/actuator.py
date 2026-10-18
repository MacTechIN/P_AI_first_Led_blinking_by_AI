"""S-1 — 가상 액추에이터.

`NullActuator` 는 명령을 삼킨다. 그래서 루프가 닫히지 않고, 수강생은 자기
정책이 무엇을 했는지 숫자로만 본다. `SimActuator` 는 명령을 **장면에 반영**해
다음 프레임에서 카메라가 결과를 보게 만든다.
"""

from __future__ import annotations

from typing import Any

from control.actuator import Actuator
from control.commands import LedCommand

from .world import SimWorld


class SimActuator(Actuator):
    """명령을 가상 현장에 적용한다. 전송 기록은 `NullActuator` 처럼 남긴다."""

    def __init__(self, world: SimWorld) -> None:
        self.world = world
        self.history: list[LedCommand] = []

    def apply(self, cmd: LedCommand) -> None:
        self.world.apply(cmd)
        self.history.append(cmd)

    @property
    def last(self) -> LedCommand | None:
        return self.history[-1] if self.history else None

    @property
    def wire_lines(self) -> int:
        """실제 배선이었다면 나갔을 시리얼 줄 수. 전송 빈도 실습에 쓴다."""
        return sum(len(c.to_wire()) for c in self.history)

    def describe(self) -> dict[str, Any]:
        return {
            "type": "SimActuator",
            "commands": len(self.history),
            "wire_lines": self.wire_lines,
            "last": self.last,
        }
