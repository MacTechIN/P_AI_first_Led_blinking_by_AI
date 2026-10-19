"""제출된 정책 파일을 불러온다 (S-5·S-6 공용).

약속은 함수 하나뿐이다 — `build()` 가 `Policy` 를 돌려준다. 그 외에는 아무것도
요구하지 않는다.

처음에는 `host/rig_worker.py` 안에 있었는데, 채점기와 학생용 꾸러미가 같은 것을
필요로 했다. 실행기(host/)는 꾸러미마다 다르게 담기므로, **라이브러리는
라이브러리 자리에 있어야 한다.**
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

from control.policy import Policy


def load_policy(path: str | Path) -> Policy:
    p = Path(path)
    spec = importlib.util.spec_from_file_location(f"submitted_{p.stem}", p)
    if spec is None or spec.loader is None:
        raise ValueError(f"불러올 수 없다: {p}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "build"):
        raise ValueError(f"{p}: build() 가 없다")
    policy = module.build()
    if not isinstance(policy, Policy):
        raise ValueError(f"{p}: build() 가 Policy 를 돌려주지 않았다")
    return policy
