"""예제 3 시험 — 계약과 기권이 설계대로 동작하는가."""

import pytest

from control.commands import LedCommand
from control.features import SceneFeatures
from control.scene import (NO_ABSTAIN_SCHEMA, SCENE_SCHEMA, VERDICTS, SceneError,
                           ScenePolicy, try_rule, validate_scene)

EMPTY = SceneFeatures(None, None, 0.0, 0.0, 0.0, None)


def test_the_rule_attempt_is_deliberately_empty():
    """비어 있다는 사실이 예제 3 의 출발점이다. 채워지면 모델을 쓸 이유가 없다."""
    assert try_rule(EMPTY) is None
    assert "반례" in try_rule.__doc__


def test_schema_and_validator_agree_on_the_verdicts():
    """스키마와 검증기가 갈라지면 폴백이 그것을 가린다 (ADR-0009)."""
    assert set(SCENE_SCHEMA["properties"]["verdict"]["enum"]) == set(VERDICTS)


def test_abstention_is_part_of_the_contract():
    assert "uncertain" in VERDICTS
    assert "uncertain" not in NO_ABSTAIN_SCHEMA["properties"]["verdict"]["enum"]


@pytest.mark.parametrize("bad", [
    {"verdict": "매우 깔끔"}, {"verdict": None}, {}, "문자열", {"verdict": "unknown"},
])
def test_an_answer_outside_the_contract_is_refused(bad):
    with pytest.raises(SceneError):
        validate_scene(bad)


def test_the_no_abstain_schema_refuses_uncertain():
    """비교 측정용 스키마는 기권을 받지 않아야 비교가 성립한다."""
    with pytest.raises(SceneError):
        validate_scene({"verdict": "uncertain"}, ("tidy", "cluttered"))


def test_evidence_is_clipped_not_trusted():
    got = validate_scene({"verdict": "tidy", "evidence": "가" * 500})
    assert len(got["evidence"]) == 80


# --- 판정을 LED 로 ---


def test_uncertain_holds_the_previous_command():
    """모를 때 불을 끄면 '정돈됨' 신호와 구별되지 않는다."""
    p = ScenePolicy()
    lit = p.apply_verdict("cluttered")
    assert lit.mode == "blink"
    assert p.apply_verdict("uncertain") == lit        # 유지


def test_uncertain_before_any_verdict_leaves_the_led_off():
    assert ScenePolicy().apply_verdict("uncertain") == LedCommand("off")


def test_tidy_and_cluttered_are_distinguishable():
    p = ScenePolicy()
    tidy = p.apply_verdict("tidy")
    clut = p.apply_verdict("cluttered")
    assert tidy.mode == "on" and clut.mode == "blink"
    assert tidy.rgb != clut.rgb


def test_stability_counts_how_often_the_answer_repeated():
    """재현성은 정확도보다 먼저 재야 하는 값이다."""
    p = ScenePolicy()
    for v in ("cluttered", "cluttered", "tidy", "cluttered"):
        p.apply_verdict(v)
    assert p.stability == 0.75


def test_the_policy_itself_never_invents_a_judgement():
    """판정은 비동기로 바깥에서 온다. decide() 는 유지만 한다 (ADR-0008)."""
    p = ScenePolicy()
    assert p.decide(EMPTY) == LedCommand("off")
    p.apply_verdict("tidy")
    assert p.decide(EMPTY).mode == "on"
