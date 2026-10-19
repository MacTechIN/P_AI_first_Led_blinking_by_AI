"""이력을 없앤 정책. **정확도는 같고 전송만 늘어난다.**

색을 더 민감하게 따라가면 좋아 보인다. 정확도 숫자만 보면 실제로 같다.
전송 횟수 칸을 함께 보기 전까지는 무엇이 나빠졌는지 알 수 없다 (ADR-0007).
"""

from control.policy import MirrorColorPolicy, Policy


def build() -> Policy:
    return MirrorColorPolicy(hue_step=1, level_step=1)
