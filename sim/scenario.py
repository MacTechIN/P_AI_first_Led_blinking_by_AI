"""S-2 — 장면 대본. 실습 과제를 **코드가 아니라 선언으로** 바꾼다.

역량 계약(VS-4)과 같은 생각이다. 팀마다 다른 과제를 주려고 파이썬을 복사하기
시작하면 금세 네 벌의 다른 코드가 생긴다. 대본은 JSON 한 장이고, 거기에
**기대 출력까지 함께 적는다** — 그래서 장면이 곧 골든셋이 된다.

    {"name": "basics", "seconds": 24,
     "events": [{"t": 0, "card": "red"}, {"t": 8, "card": "green"}],
     "expect": [{"at": 4, "color": "red"}, {"at": 12, "color": "green"}]}

대본이 쓸 수 있는 것은 셋뿐이다. 더 늘리고 싶을 때마다 "이것이 30분 안에
가르칠 개념인가" 를 먼저 묻는다.

| 키 | 뜻 |
|---|---|
| `card` | 색지를 바꾼다. 색 이름이나 `[r,g,b]`, `null` 이면 치운다 |
| `light` | 조명 배율. 1.0 이 기본, 0.4 면 어둡다 |
| `move` | 물체가 `from` 에서 `to` 까지 `over` 초에 걸쳐 지나간다 |
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from control.evaluate import matches

from .world import SimWorld

CARDS: dict[str, tuple[int, int, int]] = {
    "red": (220, 40, 40),
    "orange": (230, 130, 30),
    "yellow": (225, 215, 50),
    "green": (40, 190, 70),
    "cyan": (40, 200, 200),
    "blue": (50, 70, 215),
    "purple": (150, 60, 200),
}
NO_CARD = (30, 30, 34)


class ScenarioError(ValueError):
    """대본이 잘못됐다."""


def _rgb(value: Any, where: str) -> tuple[int, int, int]:
    if value is None:
        return NO_CARD
    if isinstance(value, str):
        if value not in CARDS:
            raise ScenarioError(f"{where}: 모르는 색 {value!r} (가능: {', '.join(CARDS)})")
        return CARDS[value]
    if isinstance(value, list) and len(value) == 3:
        return (int(value[0]), int(value[1]), int(value[2]))
    raise ScenarioError(f"{where}: 색은 이름이나 [r,g,b] 여야 한다: {value!r}")


@dataclass(frozen=True)
class Expectation:
    at: float
    expect: dict[str, Any]
    note: str = ""


@dataclass
class Scenario:
    """시간에 따라 장면을 움직이고, 그 시각에 무엇이 맞는지 알고 있다."""

    name: str
    seconds: float
    events: list[dict[str, Any]] = field(default_factory=list)
    expect: list[Expectation] = field(default_factory=list)
    expect_tape: list[Expectation] = field(default_factory=list)
    """**모델 자신의 답**을 고정하는 기대. 기록 재생(S-4)일 때만 검사한다.

    따로 두는 이유가 있다. `expect` 의 color·zone 은 규칙 기반 특징에서 나오므로
    모델이 무엇을 답하든 통과한다 — 실제로 **빈 기록으로도 3/3 통과**했다.
    폴백이 모델을 완전히 가리기 때문이다(ADR-0009 와 같은 일). 모델을 검사하려면
    모델의 출력을 직접 적어야 한다.
    """

    note: str = ""

    def apply(self, world: SimWorld, t: float) -> None:
        """시각 t 의 장면을 world 에 반영한다. 지나간 사건을 순서대로 적용한다."""
        world.mover = None
        for ev in self.events:
            if ev["t"] > t:
                break
            if "card" in ev:
                world.card_rgb = _rgb(ev["card"], f"{self.name} t={ev['t']}")
            if "light" in ev:
                world.light = float(ev["light"])
            if "move" in ev:
                m = ev["move"]
                over = float(m.get("over", 1.0)) or 1.0
                frac = min(max((t - ev["t"]) / over, 0.0), 1.0)
                x = float(m["from"]) + (float(m["to"]) - float(m["from"])) * frac
                world.mover = (_rgb(m.get("colour", "yellow"), self.name), x)

    def due(self, t0: float, t1: float) -> list[Expectation]:
        """(t0, t1] 구간에 검사할 기대. 스텝 사이에 끼어도 빠뜨리지 않는다."""
        return [e for e in self.expect if t0 < e.at <= t1]

    def due_tape(self, t0: float, t1: float) -> list[Expectation]:
        return [e for e in self.expect_tape if t0 < e.at <= t1]

    def describe(self) -> str:
        tape = f" (+기록 {len(self.expect_tape)})" if self.expect_tape else ""
        return (f"{self.name} · {self.seconds:.0f}초 · "
                f"사건 {len(self.events)} · 기대 {len(self.expect)}{tape}")


def _parse(raw: dict[str, Any], name: str) -> Scenario:
    if "seconds" not in raw:
        raise ScenarioError(f"{name}: seconds 가 필요하다")

    # 정렬보다 검사가 먼저다. 순서를 먼저 잡으면 t 없는 사건이 KeyError 로
    # 터져 **실습 중에** 처음 드러난다. 대본의 오류는 읽는 순간 걸려야 한다.
    events = list(raw.get("events", []))
    for ev in events:
        if "t" not in ev:
            raise ScenarioError(f"{name}: 모든 사건에 t 가 필요하다")
        if not ({"card", "light", "move"} & set(ev)):
            raise ScenarioError(f"{name} t={ev['t']}: card · light · move 중 하나가 필요하다")
        where = f"{name} t={ev['t']}"
        if "card" in ev:
            _rgb(ev["card"], where)                      # 색 이름도 지금 확인한다
        if "move" in ev:
            m = ev["move"]
            if "from" not in m or "to" not in m:
                raise ScenarioError(f"{where}: move 에는 from 과 to 가 필요하다")
            _rgb(m.get("colour", "yellow"), where)
    events.sort(key=lambda e: e["t"])
    def _expectations(key: str) -> list[Expectation]:
        out = [Expectation(float(e["at"]), {k: v for k, v in e.items()
                                            if k not in ("at", "note")},
                           e.get("note", ""))
               for e in raw.get(key, [])]
        for e in out:
            if not e.expect:
                raise ScenarioError(f"{name} at={e.at}: 기대할 값이 비어 있다")
        return out

    return Scenario(raw.get("name", name), float(raw["seconds"]), events,
                    _expectations("expect"), _expectations("expect_tape"),
                    raw.get("note", ""))


def load(path: str | Path) -> Scenario:
    p = Path(path)
    if not p.is_file():
        raise ScenarioError(f"대본이 없다: {p}")
    try:
        raw = json.loads(p.read_text())
    except ValueError as e:
        raise ScenarioError(f"{p}: JSON 오류 {e}") from e
    return _parse(raw, p.stem)


def load_all(directory: str | Path = "scenarios") -> dict[str, Scenario]:
    d = Path(directory)
    if not d.is_dir():
        raise ScenarioError(f"대본 디렉터리가 없다: {d}")
    out = {}
    for p in sorted(d.glob("*.json")):
        s = load(p)
        out[s.name] = s
    if not out:
        raise ScenarioError(f"{d}: 대본이 하나도 없다")
    return out


def observe(result: Any, policy: Any = None) -> dict[str, Any]:
    """한 스텝을 기대와 맞춰 볼 수 있는 요약으로.

    `vlm_*` 는 **모델이 직접 한 말**이다. color·zone 은 규칙 기반 특징이라
    모델이 무엇을 답하든 바뀌지 않는다 — 둘을 섞으면 모델을 검사한다고
    착각하게 된다 (S-4 에서 빈 기록이 9/9 통과했던 이유).
    """
    from control.direction import zone_of

    f = result.features
    d = getattr(policy, "last_decision", None)
    return {
        "color": f.color,
        "zone": zone_of(f.centroid_x) if f.centroid_x is not None else None,
        "action": result.command.mode,
        "vlm_action": d.action if d else None,
        "vlm_colour": d.colour if d else None,
    }


def check(expectation: Expectation, got: dict[str, Any]) -> bool:
    """부분 일치. 골든셋과 같은 규칙을 쓴다 — 적어둔 필드만 본다."""
    return matches(expectation.expect, got)
