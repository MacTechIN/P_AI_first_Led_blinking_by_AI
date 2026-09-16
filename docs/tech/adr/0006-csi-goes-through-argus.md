# ADR-0006 — CSI 카메라는 Argus 를 경유한다 (V4L2 아님)

상태: 채택   날짜: 2026-09-16   슬라이스: VS-1 (µ1.2)

## 배경
IMX219 가 정상 인식된 뒤 `V4L2Source`(cv2.VideoCapture) 로 읽으려 했으나
프레임을 얻지 못하고 멈췄다.

## 결정
Jetson CSI 카메라는 **`nvarguscamerasrc` + python-gi Gst appsink** 로 읽는다.
USB 웹캠은 기존 `V4L2Source` 를 그대로 쓴다. 상위는 `open_source("argus:0")`
와 `open_source("v4l2:0")` 의 차이만 보며 인터페이스는 동일하다 (ADR-0004).

## 근거
1. **CSI 의 `/dev/video0` 은 RG10(10비트 Bayer) 원시 데이터다.**
   디베이어·자동노출·화이트밸런스는 Tegra ISP 의 몫이고, 그 경로가 Argus 다.
   cv2 는 이 포맷을 처리하지 못한다.
2. **이 시스템의 cv2 는 GStreamer 없이 빌드됐다** (`getBuildInformation()` →
   `GStreamer: NO`). 따라서 `cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)`
   우회로도 막혀 있다. python-gi 의 Gst 1.20.3 은 사용 가능하다.

## 대안과 기각 사유
- **`gst-launch ! fdsink` 파이프**: nvarguscamerasrc 가 stdout 에 진단 문구를
  섞어 프레임 바이트를 오염시킨다. 실측으로 640x480x3 프레임 3장에
  1277 바이트가 초과 수신됐다. 기각.
- **cv2 재빌드(GStreamer 포함)**: 빌드 시간과 유지 부담이 크고, gi 로 이미
  해결된다. 기각.
- **원시 Bayer 를 직접 디베이어**: ISP 가 하는 자동노출·화이트밸런스까지
  구현해야 한다. 기각.

## 부수 결정 — 워밍업 필수
Argus 자동노출은 수렴에 시간이 걸린다. 실측:

| 프레임 | mean | std | 판정 |
|---|---|---|---|
| 1번째 | 22.7 | 9.7 | 거의 검은 화면 |
| 60번째 | 87.5 | 61.5 | 정상 노출 |

`DEFAULT_WARMUP = 30` 프레임을 버린다.

**중요: 워밍업은 건전성 검사(ADR-0005)를 대신하지 않는다.** 첫 프레임도
어두울 뿐 평탄하지는 않아 검사를 통과한다. 두 장치는 서로 다른 실패를 막는다.
검사는 "센서가 설정되지 않음"을, 워밍업은 "노출이 수렴하지 않음"을 막는다.

## 결과
- `perception/argus.py` 추가. `gi` 는 지연 import 하므로 합성 소스만 쓰는
  환경에서는 요구되지 않는다.
- `appsink max-buffers=1 drop=true` 로 항상 최신 프레임을 준다.
  제어 루프에는 밀린 프레임보다 최신 프레임이 맞다.
