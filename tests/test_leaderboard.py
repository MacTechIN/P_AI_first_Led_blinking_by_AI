"""S-6 시험 — 숨은 세트가 **공개 세트가 못 보는 것**을 보는가."""

from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
from leaderboard import grade  # noqa: E402

from sim.scenario import load_all  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = str(ROOT / "scenarios")
HIDDEN = str(ROOT / "scenarios" / "hidden")


def team(name: str) -> Path:
    return ROOT / "teams" / name / "policy.py"


# --- 세트 자체 ---


def test_the_hidden_set_is_separate_from_the_public_one():
    """숨은 대본이 공개 쪽에 섞여 있으면 숨은 것이 아니다."""
    pub = set(load_all(PUBLIC))
    hid = set(load_all(HIDDEN))
    assert hid and not (pub & hid)


def test_the_hidden_expectations_are_correct():
    """기대가 틀려 있으면 성실한 정책이 떨어진다. 그건 채점이 아니라 사고다."""
    r = grade(team("example"), HIDDEN)
    assert r["passed"] == r["total"] > 0


# --- 숨은 세트가 잡아내는 것 ---


def test_a_policy_tuned_to_the_public_set_passes_it_and_fails_the_hidden_one():
    pub = grade(team("tuned"), PUBLIC)
    hid = grade(team("tuned"), HIDDEN)
    assert pub["passed"] == pub["total"]              # 공개는 만점
    assert hid["passed"] < hid["total"]               # 숨은 세트에서 무너진다


def test_accuracy_alone_would_have_ranked_the_chatty_policy_first():
    """정확도는 같고 전송만 늘어난다. 한 칸만 보면 알 수 없다 (ADR-0007)."""
    honest = grade(team("example"), PUBLIC)
    chatty = grade(team("chatty"), PUBLIC)
    assert chatty["passed"] == honest["passed"]
    assert chatty["commands"] >= honest["commands"] * 3


# --- S-6 에서 고친 것 ---


def test_the_expectations_check_the_policy_not_just_perception():
    """`color` 만 보면 정책이 무엇을 하든 통과한다 — 과적합 정책이 실제로 통과했다.

    그래서 `cmd_colour` 와 `action` 을 기대에 넣었다. 둘이 빠지면 이 시험이
    먼저 깨진다.
    """
    keys = set()
    for sc in load_all(HIDDEN).values():
        for e in sc.expect:
            keys |= set(e.expect)
    assert "cmd_colour" in keys
    assert "action" in keys


def test_a_recorded_tape_does_not_generalise_to_unseen_scenes():
    """기록은 본 것만 안다. 숨은 세트에서 모델은 거의 입을 다문다."""
    pub = grade(team("vlm"), PUBLIC)
    hid = grade(team("vlm"), HIDDEN)
    assert pub["model"] is not None and hid["model"] is not None
    assert hid["model"] < pub["model"]
    assert hid["passed"] < hid["total"]


def test_grade_reports_every_axis():
    r = grade(team("example"), PUBLIC)
    for k in ("passed", "total", "commands", "steps", "ms", "model"):
        assert k in r
    assert r["steps"] > 0 and r["ms"] > 0
