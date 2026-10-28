"""S-4 시험 — 기록·재생이 서버를 대신할 수 있는가, 그리고 **무엇을 못 막는가**."""

import json
from pathlib import Path

import numpy as np
import pytest

from sim import SimSource, SimWorld, build_rig
from sim.replay import DEFAULT_TOLERANCE, ReplayVlmClient, Tape, distance, thumbprint
from sim.scenario import load_all

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
from scenario_check import play  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def frame(rgb=(220, 40, 40), seed=0):
    w = SimWorld(clock=lambda: 0.0, card_rgb=rgb)
    with SimSource(w, seed=seed) as s:
        return s.read().image


# --- 열쇠: 노이즈에 둔하고 색에 민감해야 한다 ---


def test_the_key_survives_sensor_noise():
    """같은 장면도 두 번 다시 같은 바이트가 아니다. 그래서 해시를 못 쓴다."""
    a, b = thumbprint(frame(seed=1)), thumbprint(frame(seed=2))
    assert distance(a, b) < DEFAULT_TOLERANCE / 5


@pytest.mark.parametrize("other", [(40, 190, 70), (50, 70, 215), (225, 215, 50)])
def test_the_key_separates_different_cards(other):
    d = distance(thumbprint(frame()), thumbprint(frame(other)))
    assert d > DEFAULT_TOLERANCE * 2


# --- 표 자체 ---


def test_tape_round_trips(tmp_path):
    t = Tape(source="시험", model="m")
    t.add(frame(), {"action": "on", "colour": "red", "reason": ""}, 950.0, "note")
    t.save(tmp_path / "t.json")
    back = Tape.load(tmp_path / "t.json")
    assert len(back.entries) == 1
    assert back.model == "m"
    assert back.entries[0].decision["colour"] == "red"


def test_a_tape_from_a_different_thumbnail_size_is_refused(tmp_path):
    p = tmp_path / "t.json"
    p.write_text(json.dumps({"thumb": [4, 4], "entries": []}), encoding="utf-8")
    with pytest.raises(Exception, match="썸네일 크기"):
        Tape.load(p)


# --- 재생 ---


def test_a_scene_it_never_saw_gets_none_not_a_guess():
    """모르면 모른다고 해야 한다. 느슨하게 맞춰 주면 지어내기 시작한다."""
    t = Tape()
    t.add(frame(), {"action": "on", "colour": "red", "reason": ""}, 10.0)
    c = ReplayVlmClient(t, speed=0)
    decision, _, _ = c.ask(frame((50, 70, 215)))       # 파랑은 기록에 없다
    assert decision["action"] == "none"
    assert c.stats["misses"] == 1 and c.stats["hits"] == 0


def test_a_recorded_scene_comes_back_verbatim():
    t = Tape()
    t.add(frame(), {"action": "blink", "colour": "red", "reason": "x"}, 2814.0)
    c = ReplayVlmClient(t, speed=0)
    decision, latency, _ = c.ask(frame(seed=9))        # 노이즈만 다른 프레임
    assert decision["colour"] == "red" and decision["action"] == "blink"
    assert latency == 2814.0                           # 지연까지 그대로
    assert c.stats["hits"] == 1


# --- 실제로 기록해 둔 표 ---


def test_the_shipped_tapes_are_from_the_real_model():
    """지어낸 응답이 아니라 Qwen2.5-VL 이 실제로 한 말이어야 한다."""
    for name in ("basics", "dusk", "sweep"):
        t = Tape.load(ROOT / "tapes" / f"{name}.json")
        assert t.entries
        assert "Qwen2.5-VL" in t.model
        assert all(e.latency_ms > 500 for e in t.entries)   # 실제 추론 시간


def test_replaying_the_scenarios_never_misses():
    """교실에서 빗나가면 모델이 입을 다문 것처럼 보인다."""
    for name, sc in load_all(ROOT / "scenarios").items():
        rig = build_rig(policy="tape", tape=ROOT / "tapes" / f"{name}.json",
                        tape_speed=0.0)
        now = 0.0
        rig.world.clock = lambda: now
        with rig.source:
            loop = rig.loop()
            rig.policy.start()
            for i in range(int(sc.seconds * 5)):
                now = i / 5.0
                sc.apply(rig.world, now)
                loop.step()
            rig.policy.stop()
        assert rig.policy.client.stats["misses"] == 0


def test_the_tape_is_load_bearing():
    """빈 기록이면 모델 기대가 떨어져야 한다.

    처음에는 떨어지지 않았다 — color·zone 이 규칙 기반 특징에서 나오고 폴백이
    모델을 완전히 가렸기 때문이다. 그래서 모델의 출력을 따로 적게 했다.
    """
    sc = load_all(ROOT / "scenarios")["basics"]
    assert sc.expect_tape, "모델을 검사하는 기대가 없다"

    good = play(sc, policy="tape", tape_dir=str(ROOT / "tapes"), verbose=False)
    assert good[1] == 0

    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        Tape().save(Path(tmp) / "basics.json")
        empty = play(sc, policy="tape", tape_dir=tmp, verbose=False)
    assert empty[1] == len(sc.expect_tape)


def test_rule_expectations_alone_would_not_have_noticed():
    """같은 빈 기록으로도 **규칙 기대는 전부 통과한다.** 그것이 문제였다."""
    sc = load_all(ROOT / "scenarios")["basics"]
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        Tape().save(Path(tmp) / "basics.json")
        passed, _ = play(sc, policy="tape", tape_dir=tmp, verbose=False)
    assert passed == len(sc.expect)
