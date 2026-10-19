"""모듈 6 §4 — 결정 로그가 **재현에 필요한 것을 빠짐없이** 남기는가."""

import json
from pathlib import Path

import numpy as np

from control.commands import LedCommand
from control.decisionlog import DecisionLog, promote
from control.evaluate import load_cases
from control.features import SceneFeatures
from control.loop import StepResult
from control.vlm import VlmDecision
from perception.types import Observation

FEAT = SceneFeatures("red", 0.0, 0.5, 200.0, 120.0, 0.5, (255, 0, 0))


def step(seq=1, changed=True, with_frame=True):
    obs = None
    if with_frame:
        rng = np.random.default_rng(seq)
        img = rng.integers(0, 255, (48, 64, 3), dtype=np.uint8)
        obs = Observation(image=img, source_id="t", seq=seq, timestamp=0.0)
    return StepResult(FEAT, LedCommand("on", rgb=(255, 0, 0)), {"capture": 1.0},
                      seq, changed, obs)


def decision(seq=0):
    return VlmDecision(action="on", colour="red", reason="빨강", latency_ms=2814.0,
                       observed_seq=seq, observed_at=0.0, raw="{}")


def test_a_decision_records_which_frame_it_was_about(tmp_path):
    """비동기라 지금 프레임이 아니다. 몇 프레임 늦었는지가 남아야 한다."""
    log = DecisionLog(tmp_path)
    entry = log.record(step(seq=7), decision(seq=4))
    assert entry["decision"]["observed_seq"] == 4
    assert entry["lag_frames"] == 3


def test_the_frame_itself_is_saved(tmp_path):
    log = DecisionLog(tmp_path)
    entry = log.record(step(seq=3), decision())
    assert "frame" in entry
    assert (Path(tmp_path) / entry["frame"]).is_file()


def test_without_a_frame_nothing_can_be_promoted(tmp_path):
    """프레임이 없으면 다시 물어볼 수 없다. 사례가 될 수 없다."""
    log = DecisionLog(tmp_path)
    log.record(step(with_frame=False), decision())
    assert promote(log.entries(), tmp_path, tmp_path / "g") == []


def test_entries_round_trip_as_jsonl(tmp_path):
    log = DecisionLog(tmp_path)
    log.record(step(seq=1), decision())
    log.record(step(seq=2), decision())
    entries = log.entries()
    assert len(entries) == 2 and entries[1]["seq"] == 2
    assert all(json.dumps(e) for e in entries)


# --- 승격 ---


def test_a_promoted_moment_becomes_a_loadable_golden_case(tmp_path):
    log = DecisionLog(tmp_path / "log")
    log.record(step(seq=5), decision(), note="현장에서 이상했던 순간")
    cases = promote(log.entries(), tmp_path / "log", tmp_path / "golden")
    assert len(cases) == 1
    loaded = load_cases(tmp_path / "golden")       # 평가가 그대로 읽는다
    assert loaded[0].expect == {"action": "on", "colour": "red"}
    assert "이상했던" in loaded[0].note


def test_fields_decide_what_is_being_defended(tmp_path):
    """적지 않은 필드의 회귀는 조용히 통과한다 — 2/5 가 5/5 가 되던 그 일."""
    log = DecisionLog(tmp_path / "log")
    log.record(step(), decision())
    loose = promote(log.entries(), tmp_path / "log", tmp_path / "loose",
                    fields=("colour",))
    assert loose[0]["expect"] == {"colour": "red"}     # action 은 자유
    strict = promote(log.entries(), tmp_path / "log", tmp_path / "strict",
                     fields=("action", "colour"))
    assert set(strict[0]["expect"]) == {"action", "colour"}


def test_a_step_without_a_model_decision_is_still_logged(tmp_path):
    """폴백이 답한 순간도 기록된다. 다만 사례로는 승격되지 않는다."""
    log = DecisionLog(tmp_path)
    entry = log.record(step(), None)
    assert "decision" not in entry
    assert promote([entry], tmp_path, tmp_path / "g") == []
