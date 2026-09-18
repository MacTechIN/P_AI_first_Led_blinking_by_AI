# 모듈 4 — 온디바이스 AI 판단

**소요** 약 180분 (빌드 포함)   **선행** 모듈 3   **슬라이스** VS-3   **ADR** 0008, 0009

## 목표

로컬 VLM 을 올려 판단을 맡기되, **느린 판단이 빠른 제어를 막지 않게** 만들 수 있다.
그리고 모델 출력이 하드웨어에 닿기까지 무엇을 통과해야 하는지 설계할 수 있다.

## 1. 메모리 예산 재기

**이것이 이 모듈의 첫 관문이다.** 추측하면 안 된다.

```bash
free -h
```

| 상태 | 가용 |
|---|---|
| GNOME 데스크톱 실행 중 | **2.3 GiB** |
| GUI 끔 (`multi-user.target`) | **6.4 GiB** |

**GUI 를 끄지 않으면 아무것도 올라가지 않는다.**

## 2. llama.cpp CUDA 빌드

```bash
git clone --depth 1 https://github.com/ggml-org/llama.cpp.git
cd llama.cpp
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87 -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
```

`87` 은 Orin 의 compute capability(sm_87)다. `-j4` 인 이유: nvcc 가 메모리를
많이 써서 6코어 전부 쓰면 OOM 위험이 있다.

**소요:** Orin Nano 에서 약 30분. CUDA 템플릿 인스턴스화 구간(26~30%)이 가장 느리다.

## 3. 핵심 실습 — 7B 와 3B 중 무엇을 쓸 것인가

직관은 "큰 게 좋다" 고 말한다. **재보면 다르다.**

```bash
# 두 모델 받기
cd ~/models
BASE=https://huggingface.co/ggml-org
curl -fLO $BASE/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf
curl -fLO $BASE/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main/mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf
```

### 반드시 이렇게 재야 한다

**모델만 띄워놓고 재면 틀린 답이 나온다.** 제어 루프와 카메라를 **함께 돌리면서** 잰다.

```bash
# 터미널 1
~/llama.cpp/build/bin/llama-server -m ~/models/Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf \
  -ngl 99 -c 4096 -b 4096 -ub 512 --parallel 1 -ctk q8_0 -ctv q8_0 --port 8080

# 터미널 2
./host/vs2_demo.py --steps 60 --lock

# 터미널 3: 동시에 추론 요청
```

**실제 결과:**

| | 7B Q4 | **3B Q4** |
|---|---|---|
| 서버만 | 가용 530MB | 가용 2187MB |
| + 카메라 + 루프 | 가용 393MB | 가용 1974MB |
| **+ 추론 요청** | **서버 사망, 스왑 3.7GB 전소** | **6/6 성공** |
| 색 판별 | 측정 불가 | **6/6 정확** |
| 평균 지연 | 2200~2900ms | **943ms** |

**3B 가 타협이 아니다.** 더 빠르고, 정확도는 같고, 유일하게 동작한다.
이 작업에서 7B 의 추가 용량은 아무 이득이 없다.

> **적재 성공과 운용 가능은 다른 문제다.** 그 차이는 **추론 중 연산 버퍼**
> (약 700MB)에서 갈린다.

## 4. 함정: `/health` 가 ok 라고 동작하는 게 아니다

```
srv load_model: loaded multimodal model
srv llama_server: model loaded          ← 이것이 찍혀도
srv llama_server: listening on ...      ← 포트가 열려도
```
비전 버퍼 할당이 이미 실패했을 수 있다. **실제 요청을 보내야 안다.**
모듈 0 의 `/dev/video0` 과 정확히 같은 함정이다.

## 5. 플래그 하나하나가 중요하다

| 플래그 | 없으면 |
|---|---|
| `--parallel 1` | 슬롯 4개 × 컨텍스트 4096 → KV 캐시 4배 → **첫 요청에서 사망** |
| `-ub 512` | 마이크로배치가 커지며 연산 버퍼 813MB 요구 → 적재 실패 |
| `-c 4096` | **줄이면 오히려 깨진다** — 이미지 토큰이 배치에 안 들어감 |
| 이미지 768×432 | 1280×720 은 `GGML_ASSERT(n_tokens_all <= n_batch)` 로 abort |

**컨텍스트를 줄이는 것이 늘 이득이 아니다.** 직관과 반대다.

## 6. 핵심 실습 — 비동기 분리

```
제어 루프 한 스텝:  34 ms
VLM 판단:         1000~3000 ms      ← 30~85배
```

동기로 부르면 루프가 **1 fps 이하**로 떨어진다. 그래서 작업 스레드에서 돌리고
`decide()` 는 **가장 최근에 완성된 명령을 즉시 반환**한다.

```bash
./host/vs2_demo.py --policy vlm --steps 400 --lock
```

**예상:**
```
  decide        0.0 ms          ← 판단이 루프를 막지 않는다
  합계         33.3 ms   30.0 fps
  VLM {'requests': 5, 'ok': 4, 'failed': 0, 'none': 1}
```

로그에서 구조가 보인다 — 처음 몇 스텝은 **폴백**(규칙 정책)이 답하고,
VLM 판단이 도착하면 그때 바뀐다.

**폴백이 없으면:** 첫 판단이 올 때까지 LED 가 죽어 있고, VLM 이 죽으면 영영 멈춘다.

## 7. 모델에게 "모르겠다" 는 출구를 줘라

응답 스키마에 `"none"` 을 **합법적인 출력**으로 넣는다.

```json
{"action": {"enum": ["on", "blink", "off", "none"]}}
```

**실제로 바로 값어치를 했다.** 어두운 장면에서 모델이 색을 지어내지 않고
`none` 에 *"The image is too dark, blurred, or ambiguous"* 라고 답했다.

그리고 `none` 은 **직전 명령을 유지**한다. "판단 못 함" 과 "꺼라" 는 다른 말이다.

> 출구를 주지 않으면 모델은 **반드시 지어낸다.**

## 8. 핵심 실습 — 계약이 갈라지면 조용히 죽는다

스키마와 검증기가 같은 계약을 **두 번** 적고 있었다.

```
스키마:  colour 는 선택
검증기:  on/blink 에는 colour 필수
모델:    action="blink", colour 생략    ← 스키마를 따랐다
결과:    5회 중 4회 거부
```

**검증기는 옳았다.** 틀린 것은 계약이다.

가장 위험했던 점: **아무것도 고장나 보이지 않았다.** 폴백이 30 fps 를 유지해서
화면상 정상이었고, `policy.stats` 의 `failed: 4` 를 보지 않았다면 놓쳤을 것이다.

```python
print(policy.stats)    # {'requests': 5, 'ok': 0, 'failed': 4, ...}
```

**폴백은 증상을 가린다. 통계를 함께 봐라.**

## 의도된 실패 실습

1. **스키마 되돌리기**: `RESPONSE_SCHEMA["required"]` 에서 `"colour"` 를 빼고
   실행한다. **80% 거부를 재현**하고, 화면상으로는 멀쩡해 보이는 것을 확인한다.
2. **동기 호출하기**: `VlmPolicy.decide` 를 블로킹으로 바꾸고 fps 를 잰다.
3. **`none` 없애기**: 스키마에서 `"none"` 을 빼고 어두운 장면을 비춘다.
   모델이 무엇을 답하는지 본다.
4. **`--parallel 1` 빼기**: 서버가 적재는 되고 첫 요청에서 죽는 것을 확인한다.

## 연습 문제

1. "7B 가 올라간다" 는 주장을 반증하려면 무엇을 어떻게 재야 하는가?
2. 폴백이 있어서 좋은 점과 위험한 점을 각각 서술하시오.
3. `none` 이 직전 명령을 유지하는 것과 `off` 를 보내는 것의 차이가
   실제 기계에서 어떤 사고로 이어질 수 있는가?

## 교훈

> **느린 판단과 빠른 제어를 분리한다** (모듈 1 의 타이밍 소유권과 같은 원리).
> **모델 출력은 검증을 통과해야 하드웨어에 닿는다.**
> **계약은 한 곳에만 적는다** — 모듈 5 가 이것을 구조로 해결한다.
