"""발표 스크립트가 덱과 **어긋나지 않는가**.

슬라이드를 한 장 끼워 넣으면 그 뒤 번호가 전부 밀린다. 발표 중에 알아차리면
늦으므로 여기서 잡는다.
"""

import re
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "docs" / "lecture" / "presenter-script.md"
DECK = ROOT / "docs" / "lecture" / "deck" / "pai-deck.pptx"


def slide_count() -> int:
    with zipfile.ZipFile(DECK) as z:
        return sum(1 for n in z.namelist()
                   if re.match(r"ppt/slides/slide\d+\.xml$", n))


def scripted_slides() -> set[int]:
    """'### 12.' 또는 '### 51–53.' 형태의 제목에서 번호를 모은다."""
    out: set[int] = set()
    for line in SCRIPT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"### (\d+)(?:[–-](\d+))?\.", line)
        if m:
            lo = int(m.group(1))
            hi = int(m.group(2) or lo)
            out.update(range(lo, hi + 1))
    return out


def test_every_slide_has_a_line_in_the_script():
    missing = sorted(set(range(1, slide_count() + 1)) - scripted_slides())
    assert not missing, f"스크립트에 없는 슬라이드: {missing}"


def test_the_script_does_not_refer_to_slides_that_do_not_exist():
    extra = sorted(n for n in scripted_slides() if n > slide_count())
    assert not extra, f"덱에 없는 번호: {extra}"


def test_the_time_budget_adds_up_to_the_stated_total():
    """표의 누적이 105분으로 끝나야 한다. 틀리면 발표가 늦어진다."""
    text = SCRIPT.read_text(encoding="utf-8")
    # 마크다운 표의 구분선(|---|)이 아니라 **구획 구분선**에서 잘라야 한다.
    block = text.split("## 시간 배분")[1].split("\n---\n")[0]
    rows = re.findall(r"\|\s*(\d+)\s*분\s*\|\s*(\d+)\s*\|", block)
    assert rows, block
    spent = sum(int(a) for a, _ in rows)
    assert int(rows[-1][1]) == spent == 105, (rows, spent)


@pytest.mark.parametrize("figure", [
    "34.6",      # 종단 지연
    "3,306",     # 동기 호출 시 지연
    "7.4",       # 규칙 판단 시간
    "3/9",       # VLM 위치 판단
    "9/9",       # 규칙 위치 판단
    "0.300",     # 노이즈 바닥
    "0.601",     # 임계값
    "+0.02",     # 전역 밝기 상쇄
    "6/12",      # 12색 정확
    "2/5",       # 골든셋
    "32",        # 기권 측정
])
def test_the_headline_figures_appear_in_the_script(figure):
    """강사가 말할 숫자가 빠져 있으면 '대충' 말하게 된다."""
    assert figure in SCRIPT.read_text(encoding="utf-8"), f"{figure} 가 스크립트에 없다"


def test_the_autoexposure_direction_is_not_reversed():
    """3.2배는 자동보정을 **켰을 때** 신호가 왜곡되어 커진 값이다.

    처음 쓸 때 '고정하니 3.2배 커졌다' 로 적었다가 원 기록과 반대였다.
    발표 중에 거꾸로 말하면 그 장 전체가 무너진다.
    """
    text = SCRIPT.read_text(encoding="utf-8")
    assert "왜곡" in text
    assert "고정하자 신호가 **3.2배** 커졌" not in text
