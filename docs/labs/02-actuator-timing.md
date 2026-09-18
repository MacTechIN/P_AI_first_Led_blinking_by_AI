# 모듈 1 — 액추에이터와 타이밍 소유권

**소요** 약 120분   **선행** 모듈 0   **슬라이스** VS-0   **ADR** 0001, 0003

## 목표

호스트와 MCU 중 **누가 타이밍을 소유해야 하는지** 스스로 판단할 수 있다.
그리고 안전 한계를 어디에 두어야 하는지 설명할 수 있다.

## 1. 첫 연결

```bash
ls -l /dev/ttyACM0
```

**권한 거부가 나면** `dialout` 그룹 문제다 (모듈 00 준비 참조).
`crw-rw---- root dialout` 이고 `id` 에 dialout 이 없으면 그것이 원인이다.

```bash
make flash          # 컴파일 + 업로드
```

**예상:** `스케치는 프로그램 저장 공간 6852 바이트(21%)를 사용`

## 2. 핵심 실습 — 두 가지 방식으로 점멸시키기

같은 LED 를 **두 방식**으로 깜빡이고 비교한다. 이것이 이 모듈의 전부다.

### (a) 호스트가 타이밍을 쥔다

```python
import sys, time; sys.path.insert(0, 'host')
from blink import Arduino
with Arduino('/dev/ttyACM0', verbose=False) as a:
    a.send("RGB 255 0 0"); a.send("LEVEL 120")
    for _ in range(50):              # 호스트가 매번 켜고 끈다
        a.send("ON");  time.sleep(0.05)
        a.send("OFF"); time.sleep(0.05)
```

**관찰:** 100ms 주기에서 **눈에 띄게 불규칙하다.** 가끔 길게 켜지거나 건너뛴다.

### (b) MCU 가 타이밍을 쥔다

```python
with Arduino('/dev/ttyACM0', verbose=False) as a:
    a.send("RGB 255 0 0"); a.send("LEVEL 120")
    a.send("INT 50"); a.send("BLINK")    # 의도만 전달
    time.sleep(5)
```

**관찰:** 완벽하게 균일하다. 호스트는 명령 3개만 보내고 아무것도 하지 않는다.

### 왜 (a) 가 떨리나

호스트 주도는 두 가지에 노출된다.

- **USB CDC 왕복 지연** — 명령 하나마다 왕복이 필요하다
- **리눅스 스케줄러 지터** — `time.sleep(0.05)` 는 정확히 50ms 가 아니다

아두이노의 `millis()` 루프는 둘 다와 무관하다.

> **이것이 Physical AI 의 핵심 긴장이다.** AI 판단은 초 단위, 물리 제어는 밀리초
> 단위다. 하나의 루프에 묶으면 둘 다 망가진다. 모듈 4 에서 같은 원리를 VLM 에
> 다시 적용한다.

## 3. 프로토콜 설계 읽기

`arduino/rgb_led/rgb_led.ino` 를 열고 다음을 확인한다.

```cpp
if (mode == MODE_BLINK) {
  unsigned long now = millis();
  if (now - lastToggle >= interval) {   // 부호 없는 뺄셈 — rollover 안전
    lastToggle = now;
    writeChannels(!lit);
  }
}
```

`millis()` 는 약 50일마다 0으로 되돌아간다. `now - lastToggle` 을 **부호 없는
연산**으로 하면 되돌아가도 차이가 정확히 나온다. `now > lastToggle + interval`
로 썼다면 50일마다 멈춘다.

## 4. 안전 한계는 어디에 두는가

호스트에서 범위를 검사하는데도 펌웨어가 또 검사한다.

```bash
python3 -c "
import sys; sys.path.insert(0,'host')
from blink import Arduino
with Arduino('/dev/ttyACM0', verbose=False) as a:
    print(a.send('INT 5'))
    print(a.send('LEVEL 300'))
"
```

**예상:**
```
ERR interval must be 10-5000
ERR level must be 0-255
```

**왜 두 번 검사하나.** 호스트 검사는 우회할 수 있다 — 다른 프로그램이 포트를 열고
아무 문자열이나 보낼 수 있다. 모듈 4 에서 AI 가 명령을 만들기 시작하면 이것이
더 중요해진다. **펌웨어는 모델이 넘을 수 없는 경계다.**

## 5. RGB LED 의 함정 두 가지

교재를 만들며 실제로 만난 것이다. 학습자도 만날 가능성이 높다.

### (a) 공통 애노드 — 논리가 반대

```bash
python3 -c "
import sys; sys.path.insert(0,'host')
from blink import Arduino
with Arduino('/dev/ttyACM0', verbose=False) as a:
    a.send('RGB 255 255 255'); a.send('ON')
"
```

**꺼지면 공통 애노드다.** 핀이 HIGH 일 때 전압차가 없어 소등된다.
`rgb_led.ino` 의 `COMMON_ANODE` 를 맞게 설정한다.

### (b) 공통 저항 — 색이 섞이지 않는다

```bash
python3 -c "
import sys, time; sys.path.insert(0,'host')
from blink import Arduino
with Arduino('/dev/ttyACM0', verbose=False) as a:
    a.send('LEVEL 120')
    for rgb in ['255 255 0', '255 0 255', '0 255 255']:
        a.send(f'RGB {rgb}'); a.send('ON'); time.sleep(2)
"
```

**노랑·자홍이 빨강으로, 청록이 초록으로 보이면** 공통 단자에 저항이 하나뿐이다.
세 다이가 고정된 전류를 나눠 갖고 **순방향 전압이 낮은 쪽이 이긴다** (적 < 녹 < 청).

확인 실험:
```bash
python3 -c "
import sys, time; sys.path.insert(0,'host')
from blink import Arduino
with Arduino('/dev/ttyACM0', verbose=False) as a:
    a.send('LEVEL 120')
    for r in (255, 120, 60, 0):
        a.send(f'RGB {r} 255 0'); a.send('ON')
        print(f'R={r}'); time.sleep(2)
"
```
빨강을 줄일수록 초록이 드러나면 확정이다. **해결: 채널마다 저항 하나씩.**

## 의도된 실패 실습

1. **rollover 버그 심기**: 비교식을 `now > lastToggle + interval` 로 바꾸고
   `lastToggle` 을 큰 값으로 초기화해 멈추는 것을 확인한다.
2. **펌웨어 검사 제거**: `INT` 의 범위 검사를 지우고 `INT 1` 을 보낸다.
   점멸이 아니라 깜박임으로 보이지 않게 된다.
3. **같은 BLINK 반복 전송**: 0.3초마다 `BLINK` 를 다시 보낸다.
   **점멸 위상이 리셋되어 끊겨 보인다** — 모듈 3 의 "변화 시에만 전송" 이 왜
   최적화가 아니라 정확성 문제인지 미리 체험한다.

## 연습 문제

1. 호스트 주도 점멸이 떨리는 두 원인을 쓰고, 각각을 없앨 방법을 제시하시오.
2. 호스트가 타이밍을 쥐는 것이 **오히려 맞는** 경우는? (힌트: `--pattern sos`)
3. 범위 검사를 호스트에만 두면 생길 수 있는 사고를 하나 서술하시오.

## 교훈

> **타이밍은 MCU 가 소유하고, 호스트는 의도만 보낸다.**
> 느린 판단과 빠른 제어를 분리하라 — 이 원칙은 모듈 3(이력)과 모듈 4(비동기)에서
> 다른 얼굴로 다시 나타난다.
