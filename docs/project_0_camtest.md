# Project 0 — 환경 구축 및 카메라 검증

프로젝트 1번(LED 자율 제어) 착수 전, 하드웨어 경로를 실제로 확인한 기록.
결론부터: **액추에이터 경로는 완성, 인지(카메라) 경로는 하드웨어 교체 필요.**

---

## 1. 현재 확보된 것

### 1.1 액추에이터 경로 — ✅ 동작 확인

```
Jetson Orin Nano ──USB CDC ACM──> Arduino Uno R3 ──> LED (13번 핀)
                  /dev/ttyACM0
                  115200 baud
```

| 구성 요소 | 상태 |
|---|---|
| 스케치 (`arduino/led_blink/led_blink.ino`) | 플래싱 완료, 플래시 16% / RAM 10% |
| 호스트 제어기 (`host/blink.py`) | pyserial, 전 명령 왕복 검증 |
| 시리얼 프로토콜 | `BLINK` / `ON` / `OFF` / `INT <ms>` / `STATE` / `PING` |
| 툴체인 | `arduino-cli` 1.5.1 (`~/.local/bin`, sudo 불필요) |

검증 내역 — 정상 명령, 경계값 거부(`INT 5` → `ERR interval must be >= 10`),
미지 명령 거부(`BOGUS` → `ERR unknown command`), 육안 점멸 시퀀스까지 확인.

**설계 원칙 (이후 전체 아키텍처에 적용):**
점멸 타이밍은 **아두이노가 소유**하고(`millis()` 기반, rollover 안전),
호스트는 `INT 100` 같은 **의도만** 전송한다. 호스트가 매번 ON/OFF를 보내면
USB 지연과 리눅스 스케줄링 때문에 타이밍이 무너지기 때문이다.
→ **느린 판단 루프(AI)와 빠른 제어 루프(MCU)의 분리**는 여기서 이미 증명됐다.

### 1.2 연산 / AI 스택

```
Jetson Orin Nano Super 8GB / L4T R36.5.2 (JetPack 6) / CUDA 12.6
ollama       :11434   qwen3.5:9b, bge-m3 (임베딩)
llama-server :8083    bge-reranker-v2-m3-Q8_0
```

둘 다 `127.0.0.1` 바인딩. 현재 구성은 **텍스트·임베딩 전용**이며
**비전 모델(VLM)이 없다** — 프로젝트 1번의 핵심 공백.

### 1.3 시스템 상태

디스크 14%(383G 여유), 온도 47~48°C, 팬 25%, 스로틀링 없음, OOM 0건,
I/O·파일시스템 오류 0건. 자원 여유 충분.

---

## 2. 카메라 — ✅ 해결 (IMX219 로 교체)

### 2.0 최종 상태 (2026-09-16)

IMX219 모듈로 교체하고 `Camera IMX219 Dual` 오버레이를 적용해 **정상 동작**한다.

```
imx219 9-0010: tegracam sensor driver:imx219_v2.0.6
tegra-capture-vi: subdev imx219 9-0010 bound      ← 오류 없이 바인딩
```

실촬영 검증 (워밍업 30프레임 후, 1280x720):

| | mean | std | 건전성 검사 |
|---|---|---|---|
| 워밍업 없이 첫 프레임 | 22.7 | 9.7 | 통과 (어둡지만 평탄하지 않음) |
| 워밍업 후 | 92.9 | 71.5 | 통과 |

**읽는 경로는 Argus 다. cv2/V4L2 가 아니다** — ADR-0006 참조.

```python
from perception import open_source
with open_source("argus:0", width=1280, height=720) as src:
    obs = src.read()
```

아래는 여기에 도달하기까지의 기록이며, IMX708 이 연결됐던 시점의 내용이다.

### 2.1 (당시) 결론

연결된 모듈은 **IMX708 (Raspberry Pi Camera Module 3)** 이며,
**JetPack이 이 센서를 지원하지 않는다.**

센서에게 직접 물어서 확인한 값:

```
i2ctransfer -y -f 9 w2@0x1a 0x00 0x16 r2   →   0x07 0x08
                                                 └─ 0x0708 = IMX708
```

| 항목 | 결과 |
|---|---|
| `nv_imx708.ko` | 없음 |
| IMX708 디바이스 트리 오버레이 | 없음 |
| JetPack 제공 센서 | ar0234, imx185, **imx219**, imx274, imx318, imx390, **imx477**, ov5693 |

### 2.2 가장 위험한 함정 — `/dev/video0`이 생겨도 작동이 아니다

IMX708은 IMX477과 **i2c 주소 `0x1a`를 공유**한다. 그래서
`Camera IMX477 Dual` 오버레이를 올리면 imx477 드라이버가 무언가를 발견하고

```
imx477 9-001a: invalid sensor model id: 31
tegra-capture-vi: subdev imx477 9-001a bound      ← 바인딩 성공
```

**`/dev/video0`을 만들어낸다.** 포맷 조회도 되고(3840×2160 RG10 @30fps),
프레임 캡처도 성공한다. 그런데 IMX477용 레지스터 시퀀스가 IMX708을 설정하지
못하므로 **픽셀이 전부 같은 값**이다:

```
샘플 수 8,294,400 (3840×2160)
min = max = mean = 4100        ← 완전한 평탄 화면
```

> **`/dev/video0`의 존재는 카메라 동작의 증거가 아니다. 픽셀 값을 반드시 검사하라.**
> 이 검사는 개발 계획 µ1.3에서 자동화한다.

### 2.3 소거된 변수 (재조사 불필요)

| 변수 | 판정 | 근거 |
|---|---|---|
| 오버레이 설정 | 정상 | `extlinux.conf`에 적용 확인, 양쪽 포트 프로브 |
| 드라이버 | 정상 | `imx219_v2.0.6` / `imx477_v2.0.6` 로드·프로브 |
| CSI/VI 파이프라인 | 정상 | `nvcsi`, `tegra-capture-vi`, `vi0/vi1` 바인딩 |
| i2c mux | 정상 | dual 오버레이에서 채널 분리 확인 (chan_id 0/1) |
| 포트 CAM0/CAM1 | 정상 | dual 오버레이로 동시 프로브 |
| 케이블 | **정상** | 최종적으로 CAM0에서 i2c 응답 성공 |
| 카메라 모듈 | **정상** | 라즈베리파이에서 동작 확인 |
| `cam0-rst` GPIO hog | 정상 설계 | 오버레이 역컴파일 결과 NVIDIA 의도 |

### 2.4 진단 중 범한 오류 (같은 함정 반복 방지)

한동안 **케이블을 범인으로 지목했으나 틀렸다.**

원인: 수동 `i2cdetect` 스캔은 센서의 전원과 **INCK(24MHz) 클럭이 꺼진 상태**에서
실행되는데, 이 센서들은 클럭이 공급되어야만 i2c에 응답한다. 따라서 빈 스캔은

- "카메라가 연결되지 않음" 과
- "카메라는 있으나 맞는 오버레이가 없음"

을 **구별하지 못한다.** 실제 상황은 후자였다.

> **교훈: 센서 식별을 먼저 하라.** 해당 i2c 주소에 전원을 넣는 오버레이를
> 아무거나 올린 뒤 레지스터 `0x0016`을 읽는 것이, 스캔 결과로 추론하는 것보다
> 빠르고 확실하다.

### 2.5 선택지

| 방안 | 비용 | 소요 | 비고 |
|---|---|---|---|
| **USB 웹캠** | 낮음 | 즉시 | 오버레이·재부팅 불필요. **개발 즉시 진행 가능** |
| **IMX219** (Camera v2) | 중 | 배송 | 기존 오버레이로 바로 동작. CSI 대역폭 활용 |
| **IMX477** (HQ Camera) | 중상 | 배송 | 화질 우수, 렌즈 교체형 |
| 서드파티 IMX708 드라이버 | 시간 | 불확실 | L4T R36.5 지원 여부 사전 확인 필수 |

**권장: USB 웹캠으로 즉시 착수 + IMX219 병행 확보.**
인지 계층을 인터페이스로 추상화해 두면(µ1.4) 나중에 CSI로 교체할 때
상위 계층 수정이 필요 없다.

---

## 3. 유용한 명령

```bash
# 카메라 실체 확인 (존재 확인만으로 불충분)
ls /dev/video*
journalctl -k -b | grep -iE 'imx|probe of'
v4l2-ctl -d /dev/video0 --list-formats-ext

# 센서 정체 확인 (스트리밍 중에만 응답)
v4l2-ctl -d /dev/video0 --stream-mmap --stream-count=900 --stream-to=/dev/null &
i2ctransfer -y -f 9 w2@0x1a 0x00 0x16 r2     # 0x0219 / 0x0477 / 0x0708

# 오버레이 변경 (TUI 없이)
sudo /opt/nvidia/jetson-io/config-by-hardware.py -l
sudo /opt/nvidia/jetson-io/config-by-hardware.py -n 2="Camera IMX219 Dual"
#                                                   └ 헤더 2 = 22pin CSI

# 액추에이터
make flash && ./host/blink.py --repl
```

---

## 4. 다음 단계

개발 계획은 `docs/development_plan.md` 참조.
**임계 경로는 카메라 확보 하나**이며, 그 외 모든 슬라이스는
가짜 프레임(fake frame source)으로 병행 개발 가능하도록 설계했다.
