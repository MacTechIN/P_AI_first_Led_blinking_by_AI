"""모듈 6 §4 — 결정 로그. **이상했던 순간을 다음 골든셋 사례로.**

비동기 판단은 늦게 도착한다(ADR-0008). 그래서 "LED 가 이상했다" 는 신고를
받았을 때, 그 순간 모델이 무엇을 보고 무엇이라 답했는지가 남아 있지 않으면
재현할 길이 없다. 남겨야 하는 것은 셋이다.

| 남기는 것 | 없으면 |
|---|---|
| 판단 (action · colour · reason) | 무엇이라 답했는지 모른다 |
| **근거 프레임** | 다시 물어볼 수 없다 |
| 관측 시각·순번 | 어느 프레임을 보고 내린 결정인지 모른다 |

로그는 JSONL 한 줄이 한 사건이고, 프레임은 옆에 JPEG 로 떨어진다. 그대로
`control.evaluate` 의 골든셋 형식으로 **승격**할 수 있다 — 그것이 이 모듈이
목표로 한 순환이다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_DIR = "decisions"


@dataclass
class DecisionLog:
    """판단과 그 근거 프레임을 함께 적는다."""

    directory: str | Path = DEFAULT_DIR
    save_frames: bool = True
    _n: int = 0

    def __post_init__(self) -> None:
        self.directory = Path(self.directory)
        (self.directory / "frames").mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "decisions.jsonl"

    def record(self, result: Any, decision: Any = None, *, note: str = "") -> dict:
        """한 스텝을 적는다. `decision` 이 없으면 명령만 남는다."""
        entry: dict[str, Any] = {
            "seq": result.seq,
            "command": result.command.describe(),
            "mode": result.command.mode,
            "rgb": list(result.command.rgb),
            "changed": result.changed,
            "features": {
                "color": result.features.color,
                "coverage": round(result.features.coverage, 4),
                "brightness": round(result.features.brightness, 2),
            },
            "note": note,
        }
        if decision is not None:
            entry["decision"] = {
                "action": decision.action,
                "colour": decision.colour,
                "reason": decision.reason,
                "latency_ms": round(decision.latency_ms, 1),
                "observed_seq": decision.observed_seq,
            }
            # 판단이 **어느 프레임을 보고** 내려졌는지. 비동기라 지금 프레임이 아니다.
            entry["lag_frames"] = result.seq - decision.observed_seq

        obs = getattr(result, "observation", None)
        if self.save_frames and obs is not None:
            name = f"{result.seq:06d}.jpg"
            if _write_jpeg(obs.image, self.directory / "frames" / name):
                entry["frame"] = f"frames/{name}"

        with self.path.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        self._n += 1
        return entry

    def entries(self) -> list[dict]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text().splitlines() if line]

    def __len__(self) -> int:
        return self._n


def _write_jpeg(image: Any, path: Path) -> bool:
    try:
        import cv2

        return bool(cv2.imwrite(str(path), cv2.cvtColor(image, cv2.COLOR_RGB2BGR)))
    except Exception:
        return False


def promote(entries: list[dict], source: str | Path, target: str | Path,
            *, fields: tuple[str, ...] = ("action", "colour")) -> list[dict]:
    """고른 사건을 골든셋 사례로 승격한다.

    `fields` 가 **무엇을 지키겠다는 선언**이다. 적지 않은 필드의 회귀는 조용히
    통과한다 — colour 만 적었을 때 5/5 였고 action 을 함께 적자 2/5 가 됐다.
    """
    import shutil

    src, dst = Path(source), Path(target)
    dst.mkdir(parents=True, exist_ok=True)
    cases = []
    for e in entries:
        if "frame" not in e:
            continue
        d = e.get("decision") or {}
        expect = {k: d[k] for k in fields if k in d}
        if not expect:
            continue
        name = Path(e["frame"]).name
        shutil.copyfile(src / e["frame"], dst / name)
        cases.append({
            "name": f"seq {e['seq']}",
            "image": name,
            "expect": expect,
            "note": e.get("note") or f"현장 기록에서 승격 · {e['command']}",
        })
    if cases:
        (dst / "cases.json").write_text(
            json.dumps(cases, ensure_ascii=False, indent=2) + "\n")
    return cases
