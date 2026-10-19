"""제출 정책의 본보기.

제출물은 `Policy` 하나를 돌려주는 `build()` 가 있는 파이썬 파일이다. 그 외의
약속은 없다. 큐는 이 함수를 부르고, 나머지는 평소의 제어 루프와 똑같다.

    def build() -> Policy
"""

from control.policy import MirrorColorPolicy, Policy


def build() -> Policy:
    """본 색을 LED 에 그대로 띄운다. 이력은 기본값 그대로."""
    return MirrorColorPolicy()
