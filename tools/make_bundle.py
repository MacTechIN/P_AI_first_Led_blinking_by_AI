#!/usr/bin/env python3
"""학생용 오프라인 꾸러미를 만든다.

    ./tools/make_bundle.py --wheels <휠 디렉터리> --out dist/

교실에 네트워크가 없으므로 **USB 로 건네는 것이 전부여야 한다.** 그래서
시뮬레이터에 필요한 것만 담고, numpy 휠을 함께 넣는다. OpenCV 는 넣지 않는다 —
`control/colour.py` 가 numpy 로 대신하므로 50MB 를 아낀다.
"""

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PACKAGES = ["sim", "control", "perception"]
DATA = ["scenarios", "tapes", "teams"]
HOST = ["sim_demo.py", "scenario_check.py", "leaderboard.py", "promote_case.py"]
DOCS = {
    "docs/labs/08-fault-clinic.md": "docs/08-fault-clinic.md",
    "docs/labs/STUDENT.md": "MANUAL.md",      # 학생이 따라 하는 본문
}


def copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
        "__pycache__", "*.pyc", ".pytest_cache"))


def build(out: Path, wheels: Path | None) -> Path:
    stage = out / "pai-sim"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    for name in PACKAGES + DATA:
        copy_tree(ROOT / name, stage / name)

    (stage / "host").mkdir()
    for name in HOST:
        shutil.copyfile(ROOT / "host" / name, stage / "host" / name)

    for src, dst in DOCS.items():
        target = stage / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / src, target)

    shutil.copyfile(ROOT / "tools" / "START.py", stage / "START.py")
    shutil.copyfile(ROOT / "tools" / "START.bat", stage / "START.bat")
    shutil.copyfile(ROOT / "tools" / "README-학생용.md", stage / "README.md")

    if wheels and wheels.is_dir():
        copy_tree(wheels, stage / "wheels")
        n = len(list((stage / "wheels").glob("*.whl")))
        print(f"  휠 {n}개 포함")
    else:
        print("  휠 없음 — 학생 컴퓨터에 numpy 가 이미 있어야 합니다")

    archive = out / "pai-sim.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(out))
    return archive


def main() -> None:
    p = argparse.ArgumentParser(description="학생용 오프라인 꾸러미")
    p.add_argument("--out", default="dist")
    p.add_argument("--wheels", help="numpy 휠이 든 디렉터리")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    archive = build(out, Path(args.wheels) if args.wheels else None)

    size = archive.stat().st_size / 1e6
    print(f"\n{archive}  ({size:.0f} MB)")
    print(f"{out / 'pai-sim'}/  (압축 전)")
    print("\nUSB 에 넣어 돌리고, 학생은 이것만 치면 됩니다:")
    print("  python3 START.py")


if __name__ == "__main__":
    main()
