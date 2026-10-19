"""S-5 — 파일 한 장이 작업 하나. 디렉터리 세 개가 큐 전체다.

    queue/pending/   제출됨
    queue/running/   한 번에 하나만
    queue/done/      끝남

`os.rename` 이 원자적이라는 성질 하나로 선점을 처리한다. 작업자가 둘이어도
같은 작업을 두 번 집지 않는다 — 다만 **장비가 하나이므로 작업자도 하나다.**
큐를 쓰는 이유가 병렬 처리가 아니라 **직렬화**라는 점이 요점이다.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

QUEUE = "queue"
RUNS = "runs"


def PENDING(root: str | Path = QUEUE) -> Path:
    return Path(root) / "pending"


def RUNNING(root: str | Path = QUEUE) -> Path:
    return Path(root) / "running"


def DONE(root: str | Path = QUEUE) -> Path:
    return Path(root) / "done"


def job_id(team: str) -> str:
    stamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    safe = "".join(c for c in team if c.isalnum() or c in "-_") or "anon"
    return f"{stamp}_{safe}"


def pending_jobs(root: str | Path = QUEUE) -> list[Path]:
    """제출 순서대로. 파일명이 곧 시각이라 정렬이 곧 FIFO 다."""
    d = PENDING(root)
    return sorted(d.glob("*.json")) if d.is_dir() else []


def claim(root: str | Path = QUEUE) -> Path | None:
    """가장 오래된 작업을 집는다. 집히면 다른 작업자는 집을 수 없다."""
    running = RUNNING(root)
    running.mkdir(parents=True, exist_ok=True)
    for job in pending_jobs(root):
        target = running / job.name
        try:
            os.rename(job, target)          # 원자적 — 경쟁에서 한 쪽만 이긴다
        except OSError:
            continue                        # 다른 작업자가 먼저 집었다
        return target
    return None


def finish(job: Path, root: str | Path = QUEUE) -> Path:
    done = DONE(root)
    done.mkdir(parents=True, exist_ok=True)
    target = done / job.name
    os.rename(job, target)
    return target
