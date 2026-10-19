"""S-5 시험 — 큐가 직렬인가, 그리고 **남의 코드가 터져도 장비가 사는가**."""

import json
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "host"))
from rig_worker import run_job  # noqa: E402

from sim.submission import load_policy  # noqa: E402

from sim.queue import claim, finish, pending_jobs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def submit(queue: Path, team: str, policy: str, *, scenario="basics",
           seconds=2.0, fps=5.0) -> dict:
    (queue / "pending").mkdir(parents=True, exist_ok=True)
    jid = f"2026-01-01T00-00-{len(pending_jobs(queue)):02d}_{team}"
    spec = {"id": jid, "team": team, "policy": policy, "scenario": scenario,
            "seconds": seconds, "fps": fps, "submitted": "t"}
    (queue / "pending" / f"{jid}.json").write_text(json.dumps(spec))
    return spec


def write_policy(tmp: Path, name: str, body: str) -> str:
    p = tmp / f"{name}.py"
    p.write_text(body)
    return str(p)


GOOD = """
from control.policy import MirrorColorPolicy
def build(): return MirrorColorPolicy()
"""
BOOM = """
from control.policy import Policy
class B(Policy):
    def decide(self, features, observation=None):
        raise RuntimeError("학생 코드가 터졌다")
def build(): return B()
"""
NOT_A_POLICY = "def build(): return '정책 아님'"
NO_BUILD = "x = 1"
OUT_OF_RANGE = """
from control.policy import Policy
from control.commands import LedCommand
class I(Policy):
    def decide(self, features, observation=None):
        return LedCommand("on", rgb=(999, 0, 0))
def build(): return I()
"""


# --- 큐 ---


def test_jobs_are_claimed_oldest_first(tmp_path):
    q = tmp_path / "q"
    submit(q, "A", "x")
    submit(q, "B", "x")
    first = claim(q)
    assert "_A" in first.name
    assert len(pending_jobs(q)) == 1          # 집힌 것은 대기에서 빠진다
    assert "_B" in claim(q).name
    assert claim(q) is None


def test_a_claimed_job_cannot_be_claimed_twice(tmp_path):
    """작업자가 둘이어도 같은 작업을 두 번 돌리지 않는다."""
    q = tmp_path / "q"
    submit(q, "A", "x")
    assert claim(q) is not None
    assert claim(q) is None


def test_finish_moves_the_job_out_of_running(tmp_path):
    q = tmp_path / "q"
    submit(q, "A", "x")
    job = claim(q)
    done = finish(job, q)
    assert done.exists() and not job.exists()
    assert done.parent.name == "done"


# --- 제출물 적재 ---


def test_a_submission_without_build_is_refused(tmp_path):
    with pytest.raises(ValueError, match="build"):
        load_policy(write_policy(tmp_path, "nobuild", NO_BUILD))


def test_a_submission_that_returns_the_wrong_type_is_refused(tmp_path):
    with pytest.raises(ValueError, match="Policy"):
        load_policy(write_policy(tmp_path, "wrong", NOT_A_POLICY))


# --- 작업 실행 ---


def run(tmp_path, body, **kw):
    spec = {"id": "t", "team": "T", "policy": write_policy(tmp_path, "p", body),
            "scenario": kw.pop("scenario", "basics"), "seconds": 2.0, "fps": 5.0}
    return run_job(spec, real=False, port="", source_spec="",
                   runs_dir=str(tmp_path / "runs"))


def test_a_good_submission_produces_its_artifacts(tmp_path):
    report = run(tmp_path, GOOD)
    out = tmp_path / "runs" / "t"
    assert report["error"] is None
    assert report["steps"] == 10
    assert (out / "report.json").is_file()
    assert (out / "timings.csv").is_file()
    assert (out / "commands.log").is_file()
    assert report["latency_ms"]["decide"] >= 0.0


def test_a_crashing_submission_is_recorded_not_propagated(tmp_path):
    """남의 코드가 터져도 작업자는 다음 팀을 받아야 한다."""
    report = run(tmp_path, BOOM)
    assert "학생 코드가 터졌다" in report["error"]
    assert (tmp_path / "runs" / "t" / "report.json").is_file()


def test_an_out_of_range_command_never_reaches_the_device(tmp_path):
    """호스트 계약이 먼저 막는다. 진짜 경계는 펌웨어지만(ADR-0003) 여기서도 잡힌다."""
    report = run(tmp_path, OUT_OF_RANGE)
    assert "0~255" in report["error"]
    assert report["commands"] == 0


def test_an_unknown_scenario_fails_cleanly(tmp_path):
    report = run(tmp_path, GOOD, scenario="없는대본")
    assert "모르는 대본" in report["error"]


def test_the_shipped_example_policy_runs(tmp_path):
    spec = {"id": "ex", "team": "example",
            "policy": str(ROOT / "teams" / "example" / "policy.py"),
            "scenario": "basics", "seconds": 2.0, "fps": 5.0}
    report = run_job(spec, real=False, port="", source_spec="",
                     runs_dir=str(tmp_path / "runs"))
    assert report["error"] is None
    assert report["policy_name"] == "MirrorColorPolicy"
