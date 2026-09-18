# 준비 — 부품과 배선

## 부품 목록

| 항목 | 사양 | 비고 |
|---|---|---|
| Jetson Orin Nano | **8GB**, JetPack 6 (L4T R36.5) | 4GB 모델은 VLM 을 올릴 수 없다 |
| microSD / NVMe | 64GB 이상 | 모델 파일이 약 3GB |
| CSI 카메라 | **IMX219** 또는 IMX477 | ⚠️ 아래 주의 |
| CSI 케이블 | **22핀**, Jetson 용 | ⚠️ 아래 주의 |
| Arduino Uno R3 | 정품/호환 | USB 케이블 포함 |
| RGB LED | 5mm, **공통 애노드/캐소드 확인** | ⚠️ 아래 주의 |
| 저항 | **220~330Ω × 3개** | ⚠️ 아래 주의 |
| 브레드보드·점퍼선 | | |

## ⚠️ 부품 선택에서 실제로 막혔던 것

교재를 만드는 과정에서 실제로 시간을 잃은 지점이다. 학습자에게 미리 알린다.

### 1. Raspberry Pi Camera Module 3 (IMX708) 은 쓸 수 없다

JetPack 에 드라이버가 없다. 더 나쁜 것은 **IMX477 과 i2c 주소(0x1a)를 공유**해서,
IMX477 오버레이를 올리면 `/dev/video0` 이 생기고 캡처까지 성공한다는 점이다.
그런데 모든 픽셀 값이 같다.

**살 것:** IMX219(Camera Module v2 계열) 또는 IMX477(HQ Camera).
**사지 말 것:** Camera Module 3, IMX708 이 들어간 모듈.

### 2. 라즈베리파이용 케이블은 맞지 않을 수 있다

Orin Nano 커넥터는 **22핀**이다. Pi 4 이하의 카메라 케이블은 **15핀**이라 물리적으로
들어가도 접점이 닿지 않는다. Pi 5 용 22핀 케이블도 핀 배치가 다를 수 있다.

**살 것:** "Jetson Nano/Orin 용" 으로 명시된 케이블.

### 3. RGB LED 의 극성을 확인하라

**공통 애노드**면 핀이 LOW 일 때 켜진다. 즉 `analogWrite(pin, 255)` 가 **끈다.**
구분법: `RGB 255 255 255` 를 보냈는데 꺼지면 공통 애노드다.

### 4. 저항은 채널마다 하나씩

공통 단자에 저항 하나만 달면 세 다이가 전류를 나눠 갖고, 순방향 전압이 낮은
다이가 이긴다(적 > 녹 > 청). `RGB 255 255 0`(노랑)이 **순수 빨강**으로 나온다.

**배선:** R·G·B **각 다리에** 220~330Ω 을 하나씩. 공통 단자에는 저항을 두지 않는다.

## 배선

```
Arduino Uno                RGB LED (공통 애노드 기준)
  pin  9 ──[220Ω]──────── B
  pin 10 ──[220Ω]──────── R
  pin 11 ──[220Ω]──────── G
  5V     ─────────────── 공통(가장 긴 다리)
```

공통 캐소드 모듈이면 공통 다리를 **GND** 에 연결하고, 펌웨어의
`COMMON_ANODE` 를 `false` 로 바꾼다.

**9·10·11 을 쓰는 이유:** Uno 의 PWM 핀은 3, 5, 6, 9, 10, 11 뿐이다.
12번에 연결하면 `analogWrite` 가 on/off 2단계로 퇴화해 중간색이 나오지 않는다.

## 소프트웨어 준비

```bash
# 1. dialout 그룹 (시리얼 포트 접근)
sudo usermod -aG dialout $USER && sudo reboot

# 2. GUI 끄기 — VLM 을 올리려면 필수 (가용 2.3GiB → 6.4GiB)
sudo systemctl set-default multi-user.target && sudo reboot

# 3. arduino-cli (sudo 불필요)
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh \
  | BINDIR=~/.local/bin sh
arduino-cli core update-index && arduino-cli core install arduino:avr

# 4. 파이썬 패키지
pip3 install --user pyserial pytest

# 5. 저장소
git clone <이 저장소> && cd led_blinking_by_AI
make test        # 카메라·아두이노 없이도 통과해야 한다
```

마지막 줄이 중요하다. **하드웨어가 하나도 없어도 테스트가 통과**해야 한다.
통과하지 않으면 하드웨어 문제가 아니라 환경 문제다.
