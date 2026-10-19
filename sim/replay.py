"""S-4 — VLM 기록·재생. 교실에서 GPU 하나를 스무 명이 나눠 쓰지 않는 법.

실물 서버는 `--parallel 1` 이라 동시 요청을 받지 못한다. 그래서 **실습 전에 한
번** 실제 모델에게 물어 답을 받아 두고, 수강생 노트북은 그 표를 읽는다.

얻는 것이 셋이다.

1. **동시에 실습할 수 있다.** 서버도 GPU 도 필요 없다.
2. **결정적이다.** 같은 장면에 늘 같은 답이 오므로 골든셋 채점이 재현된다.
3. **진짜 모델의 답이다.** 그럴듯하게 지어낸 응답이 아니라 Qwen2.5-VL 이
   실제로 한 말이고, 틀린 답도 틀린 채로 들어 있다.

## 무엇을 열쇠로 쓰는가

프레임을 그대로 해싱할 수 없다. 센서 노이즈 때문에 **같은 장면도 두 번 다시
같은 바이트가 아니다.** 그래서 8×6 으로 줄인 색 썸네일을 열쇠로 쓰고, 가장
가까운 것을 찾는다. 노이즈는 축소 평균에서 거의 사라지고 색은 남는다.

거리가 임계를 넘으면 **답하지 않는다** (`action: "none"`). 느슨하게 맞춰 주면
본 적 없는 장면에도 아무 답이나 내놓게 되는데, 그것은 모르면서 아는 척하는
것이고 이 교재가 가장 경계하는 것이다. `stats["misses"]` 가 그 횟수를 센다.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from control.vlm import VlmClient, VlmError, validate

THUMB = (6, 8)
"""썸네일 크기 (세로, 가로). 작을수록 노이즈에 둔하고 장면 구분에도 둔해진다."""

DEFAULT_TOLERANCE = 0.02
"""열쇠가 같다고 볼 거리. 실측해서 정한 값 — `docs/tech/notes/vlm-tape.md` 참조."""


def thumbprint(image: np.ndarray) -> np.ndarray:
    """프레임을 8×6 색 썸네일로. 노이즈에 견디고 색에는 민감하다."""
    h, w = image.shape[:2]
    ys = np.linspace(0, h, THUMB[0] + 1).astype(int)
    xs = np.linspace(0, w, THUMB[1] + 1).astype(int)
    out = np.empty((THUMB[0], THUMB[1], 3), dtype=np.float32)
    for i in range(THUMB[0]):
        for j in range(THUMB[1]):
            out[i, j] = image[ys[i]:ys[i + 1], xs[j]:xs[j + 1]].mean(axis=(0, 1))
    return (out / 255.0).ravel()


def distance(a: np.ndarray, b: np.ndarray) -> float:
    """썸네일 사이의 평균 절대 거리 (0~1)."""
    return float(np.abs(a - b).mean())


@dataclass
class Entry:
    key: np.ndarray
    decision: dict[str, Any]
    latency_ms: float
    note: str = ""


@dataclass
class Tape:
    """기록된 (장면 → 응답) 표. JSON 한 장이다."""

    entries: list[Entry] = field(default_factory=list)
    source: str = ""
    model: str = ""

    def add(self, image: np.ndarray, decision: dict[str, Any],
            latency_ms: float, note: str = "") -> None:
        self.entries.append(Entry(thumbprint(image), decision, latency_ms, note))

    def nearest(self, image: np.ndarray) -> tuple[Entry | None, float]:
        if not self.entries:
            return None, 1.0
        key = thumbprint(image)
        best = min(self.entries, key=lambda e: distance(key, e.key))
        return best, distance(key, best.key)

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({
            "source": self.source,
            "model": self.model,
            "thumb": list(THUMB),
            "entries": [
                {"key": [round(float(v), 4) for v in e.key],
                 "decision": e.decision,
                 "latency_ms": round(e.latency_ms, 1),
                 "note": e.note}
                for e in self.entries
            ],
        }, ensure_ascii=False, indent=1))

    @classmethod
    def load(cls, path: str | Path) -> "Tape":
        p = Path(path)
        if not p.is_file():
            raise VlmError(f"기록이 없다: {p}")
        raw = json.loads(p.read_text())
        if tuple(raw.get("thumb", THUMB)) != THUMB:
            raise VlmError(f"{p}: 썸네일 크기가 다르다 {raw.get('thumb')} != {list(THUMB)}")
        tape = cls(source=raw.get("source", ""), model=raw.get("model", ""))
        for item in raw["entries"]:
            tape.entries.append(Entry(
                np.asarray(item["key"], dtype=np.float32),
                item["decision"],
                float(item.get("latency_ms", 0.0)),
                item.get("note", ""),
            ))
        return tape

    def describe(self) -> str:
        lat = [e.latency_ms for e in self.entries]
        avg = sum(lat) / len(lat) if lat else 0.0
        return (f"{len(self.entries)}건 · 평균 {avg:.0f}ms"
                + (f" · {self.model}" if self.model else ""))


class RecordingVlmClient(VlmClient):
    """실제 클라이언트 앞에 세워 두고 오가는 것을 적는다."""

    def __init__(self, inner: VlmClient, tape: Tape | None = None,
                 *, note: str = "") -> None:
        super().__init__(endpoint=inner.endpoint)
        self.inner = inner
        self.tape = tape or Tape(model=getattr(inner, "model", ""))
        self.note = note

    def ask(self, image: Any) -> tuple[dict[str, Any], float, str]:
        decision, latency, raw = self.inner.ask(image)
        self.tape.add(image, decision, latency, self.note)
        return decision, latency, raw


class ReplayVlmClient(VlmClient):
    """표에서 답한다. 서버도 GPU 도 없이.

    지연까지 재현한다. 그래야 비동기 구조(ADR-0008)가 왜 필요한지 그대로 보인다.
    """

    def __init__(self, tape: Tape, *, tolerance: float = DEFAULT_TOLERANCE,
                 speed: float = 1.0) -> None:
        super().__init__(endpoint="tape://replay")
        self.tape = tape
        self.tolerance = tolerance
        self.speed = speed
        """지연 배속. 1.0 이면 기록된 그대로, 0 이면 즉시 (시험용)."""
        self.stats = {"hits": 0, "misses": 0}

    def ask(self, image: Any) -> tuple[dict[str, Any], float, str]:
        entry, dist = self.tape.nearest(image)
        if entry is None or dist > self.tolerance:
            self.stats["misses"] += 1
            # 본 적 없는 장면이다. 지어내지 않고 "모르겠다" 를 돌려준다.
            decision = validate({"action": "none", "colour": None,
                                 "reason": f"기록에 없는 장면 (거리 {dist:.3f})"})
            return decision, 0.0, json.dumps(decision, ensure_ascii=False)

        self.stats["hits"] += 1
        if self.speed > 0:
            time.sleep(entry.latency_ms / 1000.0 / self.speed)
        return (entry.decision, entry.latency_ms,
                json.dumps(entry.decision, ensure_ascii=False))
