# 모듈 0 — 하드웨어는 "있다" 와 "동작한다" 가 다르다

**소요** 약 90분   **선행** 없음   **슬라이스** Project 0

## 목표

장치가 인식되었다는 신호와 실제로 동작한다는 증거를 **구분**할 수 있다.
그리고 구분이 안 될 때 **무엇을 재야 하는지** 설계할 수 있다.

## 1. 카메라 연결과 첫 확인

CSI 카메라는 **핫플러그가 안 된다.** 전원을 끄고 연결한 뒤 부팅한다.

```bash
ls /dev/video*
```

**예상:** `No such file or directory`

아직 오버레이를 설정하지 않았으므로 정상이다. 커널이 CSI 포트를 보지도 않는 상태다.

```bash
i2cdetect -l | grep -E 'i2c-(9|10)'
```

**예상:** 아무것도 안 나오거나 `NVIDIA SOC i2c adapter` 만.
카메라용 i2c 버스가 **아직 존재하지 않는다.**

> **이 시점의 교훈:** 케이블을 다시 꽂아도 소용없다. 커널이 그 포트를 프로브하도록
> 설정하지 않았기 때문이다. 증상만 보고 케이블을 의심하면 몇 시간을 잃는다.

## 2. 오버레이 설정

```bash
sudo /opt/nvidia/jetson-io/config-by-hardware.py -l
```

**예상 출력:**
```
Header 2: Jetson 22pin CSI Connector
  Available hardware modules:
  1. Camera IMX219 Dual
  2. Camera IMX219-A
  ...
```

헤더 번호(`2`)를 반드시 지정한다. 생략하면 40핀 헤더로 가서 실패한다.

```bash
sudo /opt/nvidia/jetson-io/config-by-hardware.py -n 2="Camera IMX219 Dual"
sudo reboot
```

## 3. 프로브 결과 읽기

```bash
journalctl -k -b | grep -iE 'imx219|probe of'
```

**성공했을 때:**
```
imx219 9-0010: tegracam sensor driver:imx219_v2.0.6
tegra-capture-vi: subdev imx219 9-0010 bound
```

**실패했을 때 (자주 보게 될 것):**
```
imx219 9-0010: imx219_board_setup: error during i2c read probe (-121)
imx219: probe of 9-0010 failed with error -121
```

`-121` 은 `EREMOTEIO`, **i2c NACK** — 센서가 응답하지 않았다는 뜻이다.
드라이버는 정상이고, 버스도 정상이고, **아무도 대답하지 않은 것**이다.

## 4. 핵심 실습 — "동작한다" 를 증명하기

`/dev/video0` 이 생겼다고 끝이 아니다. **사진을 찍어 픽셀을 본다.**

```bash
gst-launch-1.0 -q nvarguscamerasrc num-buffers=60 ! \
  'video/x-raw(memory:NVMM),width=1280,height=720' ! \
  nvvidconv ! jpegenc ! multifilesink location=/tmp/f_%03d.jpg
```

```python
import cv2
from perception import assert_frame_sane, frame_stats
img = cv2.cvtColor(cv2.imread("/tmp/f_059.jpg"), cv2.COLOR_BGR2RGB)
print(frame_stats(img))
assert_frame_sane(img)
```

**정상:** `{'min': 0, 'max': 255, 'mean': 87.5, 'std': 61.5}` — 예외 없음

**고장난 카메라의 실제 기록:**
```
{'min': 4100, 'max': 4100, 'mean': 4100, 'std': 0.0}
FrameHealthError: constant frame: 모든 픽셀이 4100
```

장치 노드도 있었고, 드라이버도 바인딩됐고, 캡처도 성공했다. **그런데 사진이 없다.**

### 왜 그런 일이 생기나

연결된 센서가 IMX708 인데 IMX477 과 i2c 주소(0x1a)를 공유한다. IMX477 드라이버가
"뭔가 있네" 하고 바인딩하지만, 레지스터 시퀀스가 맞지 않아 센서가 아무것도 내보내지
않는다. 드라이버는 `invalid sensor model id: 31` 이라는 경고를 찍고 **그대로 진행한다.**

## 5. 센서 정체를 직접 확인하는 법

추측하지 말고 칩에게 물어본다. **스트리밍 중에만 응답한다** — 센서는 INCK 클럭이
공급될 때만 i2c 에 답하기 때문이다.

```bash
# 터미널 1: 스트림을 유지해 센서에 전원·클럭 공급
gst-launch-1.0 nvarguscamerasrc num-buffers=900 ! fakesink

# 터미널 2: 칩 ID 레지스터 읽기
i2ctransfer -y -f 9 w2@0x1a 0x00 0x16 r2
```

| 응답 | 센서 |
|---|---|
| `0x02 0x19` | IMX219 (주소 0x10) |
| `0x04 0x77` | IMX477 |
| `0x07 0x08` | **IMX708 — JetPack 미지원** |

## 의도된 실패 실습

1. **틀린 오버레이 올리기**: IMX219 카메라에 `Camera IMX477 Dual` 을 적용하고
   재부팅. `-121` 이 나오는 것을 확인한다.
2. **스캔으로 판정해보기**: 스트리밍 없이 `i2cdetect -y -r 9` 를 실행한다.
   아무것도 안 나온다. **"카메라 없음" 과 "오버레이 불일치" 를 구별하지 못한다** —
   이것이 진단을 오래 헤매게 만든 원인이었다.

## 연습 문제

1. `/dev/video0` 이 존재하는데 카메라가 고장났음을 증명하는 **가장 짧은 절차**를 쓰시오.
2. `-121` 과 `invalid sensor model id` 는 각각 무엇이 어디까지 정상임을 뜻하는가?
3. 이 모듈의 교훈을 소프트웨어 장애에 적용한다면? (힌트: 서버가 `/health` 에 ok)

## 교훈

> **장치 노드는 드라이버가 만든다. 센서가 만드는 게 아니다.**
> 존재·바인딩·캡처 성공은 모두 증거가 아니다. **출력을 직접 재라.**
