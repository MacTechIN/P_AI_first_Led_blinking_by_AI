"""S-2 시험 — 장면 대본이 과제를 선언으로 바꾸는가, 그리고 **무엇을 못 잡는가**."""

import json

import pytest

from sim import build_rig
from sim.scenario import ScenarioError, load, load_all
from sim.world import SimWorld

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
from scenario_check import play  # noqa: E402


# --- 선언의 정합성 ---


def test_shipped_scenarios_load():
    names = set(load_all("scenarios"))
    assert {"basics", "dusk", "sweep"} <= names


@pytest.mark.parametrize("raw,msg", [
    ({"events": []}, "seconds"),
    ({"seconds": 5, "events": [{"card": "red"}]}, "t 가 필요"),
    ({"seconds": 5, "events": [{"t": 0}]}, "card · light · move"),
    ({"seconds": 5, "events": [{"t": 0, "card": "무지개"}]}, "모르는 색"),
    ({"seconds": 5, "expect": [{"at": 1}]}, "비어 있다"),
])
def test_broken_scenarios_are_refused(tmp_path, raw, msg):
    """잘못된 대본은 실습 중이 아니라 읽는 순간 걸려야 한다."""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ScenarioError, match=msg):
        load(p)


# --- 시간에 따라 장면이 움직인다 ---


def test_events_apply_in_order_of_time():
    s = load("scenarios/basics.json")
    w = SimWorld()
    s.apply(w, 0.0)
    red = w.card_rgb
    s.apply(w, 9.0)
    assert w.card_rgb != red          # 8초에 초록으로 바뀐다


def test_light_dims_the_scene():
    s = load("scenarios/dusk.json")
    w = SimWorld(clock=lambda: 0.0)
    s.apply(w, 1.0)
    bright = w.render(0).mean()
    s.apply(w, 20.0)
    assert w.render(0).mean() < bright * 0.5


def test_mover_crosses_the_frame():
    s = load("scenarios/sweep.json")
    w = SimWorld()
    s.apply(w, 3.0)
    left = w.mover[1]
    s.apply(w, 19.0)
    assert w.mover[1] > left + 0.3


def test_expectations_between_steps_are_not_missed():
    """기대 시각이 스텝 사이에 끼어도 검사된다."""
    s = load("scenarios/basics.json")
    assert len(s.due(3.9, 4.1)) == 1
    assert s.due(4.1, 4.2) == []


# --- 대본이 곧 골든셋 ---


def test_every_shipped_scenario_passes_on_a_healthy_rig():
    """대본의 기대가 실제로 맞는 값이어야 한다. 틀린 기대는 실습을 망친다."""
    for name, s in load_all("scenarios").items():
        passed, failed = play(s, verbose=False, fps=5)
        assert failed == 0, f"{name}: {failed}개 불일치"
        assert passed == len(s.expect)


def test_a_broken_roi_is_caught_by_the_scenarios():
    total_failed = sum(play(s, fault="stale-roi", verbose=False, fps=5)[1]
                       for s in load_all("scenarios").values())
    assert total_failed >= 5


def test_the_scenarios_do_not_catch_a_chattering_policy():
    """**대본은 적어둔 것만 지킨다.**

    `no-hysteresis` 는 명령을 쏟아내지만 화면에 보이는 것은 그대로다. 기대가
    전송 빈도를 적지 않았으므로 전부 통과한다 — 골든셋에서 action 을 적지
    않았을 때 2/5 가 5/5 가 됐던 것과 같은 일이다.

    통과한다는 사실 자체를 고정해 둔다. 나중에 전송 빈도를 기대에 넣으면
    이 시험이 먼저 깨지고, 그때 비로소 대본이 그것을 지키기 시작한다.
    """
    for s in load_all("scenarios").values():
        assert play(s, fault="no-hysteresis", verbose=False, fps=5)[1] == 0
