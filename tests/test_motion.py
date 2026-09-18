"""예제 2 시험 — 움직임 검출. 카메라 없이 전부 검증한다."""

import time

import numpy as np
import pytest

from control import ALARM_HUE, CALM_HUE, MotionDetector, MotionPolicy, SceneFeatures
from control.features import hue_to_rgb
from perception import SyntheticSource, patch


def frame(seed=0, shape=(240, 320, 3)):
    return np.random.default_rng(seed).integers(0, 256, shape, dtype=np.uint8)


def obs(image, seq=0):
    from perception import Observation

    return Observation(image=image, source_id="test", seq=seq)


# --- 검출기 ---


def test_first_frame_has_no_score():
    """비교 대상이 없을 때 0 을 돌려주면 '변화 없음' 으로 오해된다."""
    assert MotionDetector().score(frame()) is None


def test_identical_frames_score_zero():
    d = MotionDetector()
    f = frame()
    d.score(f)
    assert d.score(f) == 0.0


def test_different_frames_score_high():
    d = MotionDetector()
    d.score(frame(0))
    assert d.score(frame(1)) > 5.0


def test_reset_clears_history():
    d = MotionDetector()
    d.score(frame())
    d.reset()
    assert d.score(frame()) is None


def test_small_change_scores_below_large_change():
    d = MotionDetector()
    base = np.full((240, 320, 3), 100, dtype=np.uint8)
    nudged = base.copy(); nudged[:10, :10] = 140
    flipped = np.full((240, 320, 3), 200, dtype=np.uint8)
    d.score(base); small = d.score(nudged)
    d.reset(); d.score(base); large = d.score(flipped)
    assert small < large


# --- 정책 ---


def test_calm_when_nothing_moves():
    p = MotionPolicy(threshold=1.0)
    f = frame()
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f))
    cmd = p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f, 1))
    assert cmd.mode == "on" and cmd.rgb == hue_to_rgb(CALM_HUE)


def test_alarms_on_change():
    p = MotionPolicy(threshold=1.0)
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(0)))
    cmd = p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(1), 1))
    assert cmd.mode == "blink" and cmd.rgb == hue_to_rgb(ALARM_HUE)


def test_alarm_holds_after_motion_stops():
    """사람이 잠깐 멈출 때마다 경보가 꺼지면 쓸모가 없다."""
    p = MotionPolicy(threshold=1.0, hold_s=5.0)
    f = frame(1)
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(0)))
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f, 1))
    cmd = p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f, 2))
    assert cmd.mode == "blink", "움직임이 멈춰도 유지돼야 한다"


def test_alarm_releases_after_hold_expires():
    p = MotionPolicy(threshold=1.0, hold_s=0.05)
    f = frame(1)
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(0)))
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f, 1))
    time.sleep(0.08)
    cmd = p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(f, 2))
    assert cmd.mode == "on", "유지 시간이 지나면 풀려야 한다"


def test_threshold_is_respected():
    quiet = MotionPolicy(threshold=999.0)
    quiet.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(0)))
    cmd = quiet.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(1), 1))
    assert cmd.mode == "on", "임계값이 높으면 경보가 나면 안 된다"


def test_output_stays_within_the_firmware_contract():
    p = MotionPolicy(threshold=0.0)
    p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(0)))
    cmd = p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(1), 1))
    assert 10 <= cmd.interval_ms <= 5000 and 0 <= cmd.level <= 255


def test_stats_track_triggers():
    p = MotionPolicy(threshold=1.0)
    for i in range(4):
        p.decide(SceneFeatures(None, None, 0, 0, 100, None), obs(frame(i), i))
    assert p.stats["frames"] == 4 and p.stats["triggers"] >= 3


def test_works_without_an_observation():
    """관측이 없으면 마지막 상태를 유지하고 죽지 않는다."""
    p = MotionPolicy()
    assert p.decide(SceneFeatures(None, None, 0, 0, 100, None), None).mode == "on"
