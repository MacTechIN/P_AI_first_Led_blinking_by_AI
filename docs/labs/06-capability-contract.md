# 모듈 5 — 역량 계약

**소요** 약 90분   **선행** 모듈 4   **슬라이스** VS-4   **ADR** 0010

## 목표

액추에이터를 **코드가 아니라 데이터로** 선언하고, 새 장치를 **코드 수정 0줄**로
추가할 수 있다. 그리고 왜 그것이 미학이 아니라 요구사항인지 설명할 수 있다.

## 1. 문제 인식

모듈 4 까지의 구조를 보자.

```python
@dataclass
class LedCommand:          # ← LED 전용 자료형
    mode: str
    rgb: tuple[int, int, int]
    ...
```

서보를 붙이려면 **자료형·정책·액추에이터를 모두 고쳐야 한다.** 그 순간 정의서의
"프로그램 불필요" 와 "액추에이터 구성은 사용자가 입력" 이 깨진다.

## 2. 선언 읽기

`capabilities/led_main.json`:

```json
{
  "id": "led_main",
  "kind": "rgb_led",
  "description": "RGB LED on the Arduino. Use it to show what the camera sees.",
  "transport": {"type": "serial", "port": "/dev/ttyACM0"},
  "commands": {
    "on": {
      "description": "Light the LED in a colour and hold it",
      "wire": "RGB {r} {g} {b}\nLEVEL {level}\nON",
      "args": {
        "r": {"type": "int", "min": 0, "max": 255},
        "level": {"type": "int", "min": 0, "max": 255, "default": 200}
      }
    }
  }
}
```

**`wire` 템플릿이 핵심이다.** 이것이 없으면 장치마다 파이썬 어댑터가 필요하고,
"선언만 추가" 가 거짓이 된다.

## 3. 하나의 선언에서 셋이 나온다

```python
from control.capability import Registry
r = Registry.load()

print(r.describe())                        # ① 모델이 읽는 프롬프트
print(len(r.tool_schema()["oneOf"]))       # ② 강제할 JSON 스키마
call = r.validate({"device": "led_main", "command": "on",
                   "args": {"r": 255, "g": 0, "b": 0, "level": 200}})
print(r.render(call))                      # ③ 전송 문자열
```

**예상:**
```
- led_main (rgb_led): RGB LED on the Arduino...
    on(r int 0..255, g int 0..255, b int 0..255, level int 0..255) — ...
3
['RGB 255 0 0', 'LEVEL 200', 'ON']
```

### 왜 하나에서 뽑는가

모듈 4 에서 계약을 **두 곳**에 적었더니 갈라졌고 응답의 80%가 조용히 거부됐다.
여기서는 **적을 곳이 하나뿐이라 갈라질 수 없다.** 규율이 아니라 구조로 푼 것이다.

## 4. 핵심 실습 — 코드 0줄로 장치 추가

**먼저 파이썬 파일의 해시를 기록한다.**

```bash
md5sum control/*.py host/vs4_demo.py | md5sum
```

**선언 파일 하나만 만든다.**

```bash
cat > capabilities/buzzer.json <<'JSON'
{
  "id": "buzzer",
  "kind": "buzzer",
  "description": "NOT WIRED YET — declaration only. Piezo buzzer for alerts.",
  "status": "planned",
  "transport": {"type": "null"},
  "commands": {
    "beep": {
      "description": "Beep at a frequency for a duration",
      "wire": "BEEP {hz} {ms}",
      "args": {
        "hz": {"type": "int", "min": 100, "max": 5000},
        "ms": {"type": "int", "min": 10, "max": 2000, "default": 200}
      }
    }
  }
}
JSON
```

**해시를 다시 확인한다.**

```bash
md5sum control/*.py host/vs4_demo.py | md5sum      # 동일해야 한다
python3 -c "
import sys; sys.path.insert(0,'.')
from control.capability import Registry, ContractActuator
r = Registry.load()
print('장치', sorted(r.devices))
print('스키마 옵션', len(r.tool_schema()['oneOf']))
call = r.validate({'device':'buzzer','command':'beep','args':{'hz':1000}})
print(call.describe(), '→', ContractActuator(r).apply(call))
"
```

**예상:**
```
장치 ['buzzer', 'led_main', 'servo_pointer']
스키마 옵션 6
buzzer.beep(hz=1000 ms=200) → ['BEEP 1000 200']
```

기본값(`ms=200`)이 채워지고, 전송 문자열까지 만들어졌다. **파이썬은 한 글자도
바뀌지 않았다.**

## 5. 계약이 막는 것들

```python
from control.capability import ContractError
for bad in [
    {"device": "laser", "command": "fire"},
    {"device": "buzzer", "command": "explode"},
    {"device": "buzzer", "command": "beep", "args": {"hz": 99999}},
    {"device": "buzzer", "command": "beep", "args": {"hz": 1000, "volume": 11}},
]:
    try:
        r.validate(bad); print("❌ 통과됨:", bad)
    except ContractError as e:
        print("✅", str(e)[:60])
```

**모델이 지어낸 장치·명령·인자·범위가 전부 막힌다.** 이것이 환각이 하드웨어에
닿지 않게 하는 관문이다.

## 6. 실물보다 선언이 먼저일 때

`servo_pointer` 는 **아직 물리적으로 없다.** 선언에 그렇게 적혀 있다.

```json
"status": "planned",
"transport": {"type": "null"}
```

`planned` 인데 전송로가 `null` 이 아니면 **적재 시점에 거부**한다.
실물 없는 장치가 살아 있는 포트로 명령을 보내는 사고를 구조로 막는다.

```bash
python3 -c "
import sys, json, tempfile, pathlib; sys.path.insert(0,'.')
from control.capability import Registry, ContractError
d = pathlib.Path(tempfile.mkdtemp())
(d/'ghost.json').write_text(json.dumps({
  'id':'ghost','kind':'servo','status':'planned',
  'transport':{'type':'serial','port':'/dev/ttyACM0'},
  'commands':{'go':{'wire':'GO','args':{}}}}))
try: Registry.load(d)
except ContractError as e: print('✅ 거부:', e)
"
```

> 모듈 0 의 `/dev/video0`, 모듈 4 의 `model loaded` 와 같은 원칙이다.
> **선언이 적재된다고 동작하는 게 아니다.**

## 7. 종단 실행

```bash
./host/vs4_demo.py --rounds 4
```

**예상:**
```
  [0] led_main.on(r=255 g=0 b=0 level=255)   4215ms  → ['RGB 255 0 0', 'LEVEL 255', 'ON']
결과: {'ok': 4, 'violation': 0, 'failed': 0}
```

모델이 **자동 생성된 스키마**에서 장치·명령·인자를 골랐고, 계약 검증을 통과해
실제 LED 로 나갔다.

### 관찰할 비용

계약 스키마가 복잡해지며 지연이 늘었다: **1.3초 → 4.1초.** `oneOf` 분기가 많아진
탓으로 보인다. 장치가 더 늘면 재검토가 필요하다 — 가르칠 때 함께 짚을 지점이다.

## 의도된 실패 실습

1. **`wire` 없애기**: 선언에서 `wire` 를 지우고 적재한다. 왜 거부되는지,
   그리고 없다면 무엇을 코드로 써야 했을지 생각한다.
2. **선언 범위를 펌웨어보다 넓게**: `level` 의 `max` 를 1000 으로 바꾸고
   `LEVEL 500` 을 보낸다. **펌웨어가 막는 것**을 확인한다 (ADR-0003).
3. **모델에게 원시 문자열 생성 허용**: 스키마를 자유 문자열로 바꾸고 무엇이
   나오는지 본다. 왜 위험한지 체감한다.

## 연습 문제

1. `wire` 템플릿이 없다면 "장치 추가에 코드가 필요 없다" 가 왜 거짓이 되는가?
2. 선언에 범위를 적었는데도 펌웨어에 또 적는 이유는? 선언은 데이터인데도 왜?
3. 모듈 4 의 계약 분기 사고를 이 구조가 **구조적으로** 막는 이유를 설명하시오.

## 교훈

> **역량은 코드가 아니라 데이터로 선언한다.** 하나의 선언에서 스키마·검증기·
> 전송이 모두 파생되면 갈라질 수 없다.
> 그리고 **경계는 여전히 펌웨어다** — 선언도 틀릴 수 있다.
