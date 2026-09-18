"""µ2.3 — 종단 루프와 지연 측정.

단계별 시간을 따로 잰다. VS-3 에서 VLM 을 넣으면 판단(decide) 시간만 수백 배로
늘어날 텐데, 그때 어디가 비싼지 바로 보이게 하려는 것이다.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from perception import FrameSource

from .actuator import Actuator
from .commands import LedCommand
from .features import SceneFeatures, extract
from .policy import Policy


@dataclass(frozen=True)
class StepResult:
    features: SceneFeatures
    command: LedCommand
    timings_ms: dict[str, float]
    seq: int
    changed: bool

    @property
    def total_ms(self) -> float:
        return sum(self.timings_ms.values())

    def describe(self) -> str:
        t = self.timings_ms
        mark = "*" if self.changed else " "
        return (
            f"{mark}[{self.seq:04d}] {self.features.describe()}  →  "
            f"{self.command.describe()}   "
            f"({self.total_ms:.0f}ms = 촬영 {t['capture']:.0f} "
            f"+ 특징 {t['extract']:.0f} + 판단 {t['decide']:.0f} "
            f"+ 구동 {t['actuate']:.0f})"
        )


@dataclass
class ControlLoop:
    """인지 → 특징 → 판단 → 구동."""

    source: FrameSource
    policy: Policy
    actuator: Actuator
    _seq: int = field(default=0, init=False)
    _last: LedCommand | None = field(default=None, init=False)

    def step(self) -> StepResult:
        t: dict[str, float] = {}

        t0 = time.perf_counter()
        obs = self.source.read()
        t["capture"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        features = extract(obs.image)
        t["extract"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        command = self.policy.decide(features, obs)
        t["decide"] = (time.perf_counter() - t0) * 1000

        changed = command != self._last
        t0 = time.perf_counter()
        if changed:
            self.actuator.apply(command)
        t["actuate"] = (time.perf_counter() - t0) * 1000

        self._last = command
        result = StepResult(features, command, t, self._seq, changed)
        self._seq += 1
        return result

    def run(self, steps: int | None = None, *, on_step: Any = None) -> list[StepResult]:
        results: list[StepResult] = []
        n = 0
        while steps is None or n < steps:
            r = self.step()
            results.append(r)
            if on_step:
                on_step(r)
            n += 1
        return results


def summarize(results: list[StepResult]) -> dict[str, float]:
    """µ2.3 의 산출물 — VS-3 과 비교할 지연 수치."""
    if not results:
        return {}
    stages = results[0].timings_ms.keys()
    out = {
        f"{s}_ms": sum(r.timings_ms[s] for r in results) / len(results) for s in stages
    }
    totals = sorted(r.total_ms for r in results)
    out["total_ms"] = sum(totals) / len(totals)
    out["p95_ms"] = totals[int(len(totals) * 0.95) - 1] if totals else 0.0
    out["fps"] = 1000.0 / out["total_ms"] if out["total_ms"] else 0.0
    return out
