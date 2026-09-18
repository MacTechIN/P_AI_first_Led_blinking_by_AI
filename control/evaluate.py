"""µ6.3 — 골든셋 평가. 정책이 나빠졌는지 자동으로 안다.

프롬프트를 고치거나 모델을 바꾸거나 임계값을 만지면 무언가는 좋아지고 무언가는
나빠진다. 눈으로 보면 좋아진 것만 보인다. 그래서 **이미지와 기대 출력의 쌍**을
모아두고 매번 전부 돌린다.

골든셋은 `<디렉터리>/cases.json` 에 선언한다:

    [{"image": "red_led.jpg", "expect": {"colour": "red"}},
     {"image": "dark.jpg",    "expect": {"action": "none"}}]

기대값은 **부분 일치**다. 적어둔 필드만 검사하므로, 판단의 일부만 고정하고
나머지는 자유롭게 둘 수 있다.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import numpy as np


class GoldenError(ValueError):
    """골든셋 정의가 잘못됐다."""


@dataclass(frozen=True)
class Case:
    name: str
    image: Path
    expect: dict[str, Any]
    note: str = ""


@dataclass(frozen=True)
class CaseResult:
    case: Case
    got: dict[str, Any] | None
    passed: bool
    latency_ms: float
    error: str = ""

    def describe(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        if self.error:
            return f"  {mark}  {self.case.name:24s} 오류: {self.error[:44]}"
        diff = ", ".join(
            f"{k}={self.got.get(k)!r}(기대 {v!r})"
            for k, v in self.case.expect.items()
            if self.got.get(k) != v
        )
        detail = diff if diff else json.dumps(self.got, ensure_ascii=False)[:48]
        return f"  {mark}  {self.case.name:24s} {self.latency_ms:6.0f}ms  {detail}"


@dataclass
class Report:
    results: list[CaseResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def ok(self) -> bool:
        return self.total > 0 and self.passed == self.total

    def summary(self) -> str:
        if not self.results:
            return "사례가 없다"
        lat = [r.latency_ms for r in self.results if r.latency_ms > 0]
        avg = sum(lat) / len(lat) if lat else 0.0
        return (f"{self.passed}/{self.total} 통과"
                + (f"  평균 {avg:.0f}ms" if avg else ""))

    def failures(self) -> list[CaseResult]:
        return [r for r in self.results if not r.passed]


def load_cases(directory: str | Path) -> list[Case]:
    path = Path(directory)
    manifest = path / "cases.json"
    if not manifest.is_file():
        raise GoldenError(f"골든셋 정의가 없다: {manifest}")
    try:
        raw = json.loads(manifest.read_text())
    except ValueError as e:
        raise GoldenError(f"{manifest}: JSON 오류 {e}") from e
    if not isinstance(raw, list) or not raw:
        raise GoldenError(f"{manifest}: 비어 있지 않은 배열이어야 한다")

    cases = []
    for i, item in enumerate(raw):
        if "image" not in item or "expect" not in item:
            raise GoldenError(f"{manifest}[{i}]: image 와 expect 가 필요하다")
        img = path / item["image"]
        if not img.is_file():
            raise GoldenError(f"{manifest}[{i}]: 이미지가 없다 {img}")
        cases.append(Case(item.get("name") or item["image"], img,
                          item["expect"], item.get("note", "")))
    return cases


def matches(expect: dict[str, Any], got: dict[str, Any] | None) -> bool:
    """부분 일치. 기대에 적힌 필드만 본다."""
    if got is None:
        return False
    return all(got.get(k) == v for k, v in expect.items())


def run(cases: list[Case], ask: Callable[[np.ndarray], dict[str, Any]]) -> Report:
    """각 사례의 이미지를 `ask` 에 넣고 기대와 대조한다.

    `ask` 는 이미지를 받아 판단 dict 를 돌려주는 무엇이든 될 수 있다 —
    VLM 클라이언트든, 규칙 정책이든, 시험용 가짜든. 평가는 정책 종류를 모른다.
    """
    import cv2

    report = Report()
    for case in cases:
        img = cv2.imread(str(case.image), cv2.IMREAD_COLOR)
        if img is None:
            report.results.append(
                CaseResult(case, None, False, 0.0, f"이미지를 읽지 못했다"))
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        t0 = time.perf_counter()
        try:
            got = ask(rgb)
        except Exception as e:                       # 정책이 무엇이든 평가는 계속된다
            report.results.append(CaseResult(
                case, None, False, (time.perf_counter() - t0) * 1000,
                f"{type(e).__name__}: {e}"))
            continue
        ms = (time.perf_counter() - t0) * 1000
        report.results.append(CaseResult(case, got, matches(case.expect, got), ms))
    return report
