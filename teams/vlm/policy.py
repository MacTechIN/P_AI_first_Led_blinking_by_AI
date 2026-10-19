"""기록해 둔 실제 VLM 응답으로 판단하는 정책 (S-4 의 표를 쓴다).

`tapes/` 의 기록을 **전부 합쳐** 하나로 쓴다. 가장 가까운 장면을 찾는 방식이라
여러 대본의 기록이 한 표에 섞여 있어도 된다.

숨은 세트는 기록에 없다. 그래서 모델은 `none` 을 돌려주고 폴백이 답한다 —
**기록은 본 것만 안다.** 리더보드의 폴백 칸이 그것을 숫자로 보여준다.
"""

from pathlib import Path

from control.policy import MirrorColorPolicy, Policy
from control.vlm import VlmPolicy
from sim.replay import ReplayVlmClient, Tape

TAPES = Path(__file__).resolve().parents[2] / "tapes"


def build() -> Policy:
    merged = Tape(source="merged", model="")
    for p in sorted(TAPES.glob("*.json")):
        t = Tape.load(p)
        merged.entries.extend(t.entries)
        merged.model = merged.model or t.model
    return VlmPolicy(ReplayVlmClient(merged, speed=0.0),
                     fallback=MirrorColorPolicy(), min_interval_s=0.0).start()
