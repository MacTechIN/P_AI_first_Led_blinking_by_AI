"""저장소에 딸려 오는 데이터를 **어디서 실행하든** 찾는다.

학생은 `~/led-blinking/host/sim_demo.py` 를 자기 홈에서 친다. 그때 `scenarios`
를 현재 디렉터리에서 찾으면 "대본 디렉터리가 없다" 로 끝난다 — 실제로 그랬다.

구분은 하나다.

| | 어디 기준인가 | 왜 |
|---|---|---|
| 저장소가 **주는 것** (대본·기록·팀·골든셋) | 저장소 | 어디서 실행해도 같은 것을 읽어야 한다 |
| 실행이 **만드는 것** (큐·결과·결정 로그) | 현재 디렉터리 | 만든 자리에 떨어지는 편이 낫다 |
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = str(ROOT / "scenarios")
HIDDEN = str(ROOT / "scenarios" / "hidden")
TAPES = str(ROOT / "tapes")
TEAMS = str(ROOT / "teams")
GOLDEN = str(ROOT / "golden")
