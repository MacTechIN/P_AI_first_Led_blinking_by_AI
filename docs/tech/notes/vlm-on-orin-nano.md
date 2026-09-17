# µ3.1 — Orin Nano 8GB 에서 VLM 실측 (2026-09-17)

VS-3 착수 전, **아키텍처를 바꿀 수 있는 유일한 미지수**였던 메모리 제약을 실측으로 해소한 기록.

## 결론

**Qwen2.5-VL-7B (Q4_K_M) 가 동작한다.** 단 여유가 거의 없다.

| | |
|---|---|
| 런타임 | llama.cpp (CUDA, sm_87) 직접 빌드 |
| 모델 | Qwen2.5-VL-7B-Instruct Q4_K_M **4.36 GB** |
| 비전 인코더 | mmproj Q8_0 **0.79 GB** |
| 색 판별 정확도 | **3/3** (빨강·초록·파랑 LED) |
| 추론 지연 | **2.2 ~ 2.9 초** (새 이미지) |
| 캐시 적중 시 | 0.24 초 (동일 이미지 재질의) |
| 이미지 인코딩 | 1.2 초 (768×432) |
| **잔여 메모리** | **100 MiB** ← 위험 수준 |

## 동작하는 설정

```bash
llama-server -m Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf \
             --mmproj mmproj-Qwen2.5-VL-7B-Instruct-Q8_0.gguf \
             -ngl 99 -c 2048 -b 2048 -ub 512 --parallel 1 \
             -ctk q8_0 -ctv q8_0 --host 127.0.0.1 --port 8080
```

**전제: GUI 를 꺼야 한다** (`systemctl set-default multi-user.target`).
GNOME 이 떠 있으면 가용이 2.3 GiB 여서 3B 조차 빠듯하다. GUI 를 끄면 6.4 GiB 다.

## 실패한 설정과 이유

| 설정 | 결과 | 원인 |
|---|---|---|
| 기본값 (슬롯 4개) | 첫 요청에서 크래시 | `n_slots=4` × `n_ctx=4096` 로 KV 캐시 4배. 적재는 "성공" 으로 보고하고 죽는다 |
| `-b 4096 -ub 4096` | 적재 실패 | 마이크로배치가 커지며 연산 버퍼 813 MiB 요구 |
| `-c 1024` | abort | `GGML_ASSERT(n_tokens_all <= n_batch)` — 이미지 토큰이 배치를 넘는다 |
| 1280×720 원본 | abort | 같은 이유. 768×432 로 줄이면 들어간다 |

**교훈 두 가지.**
`llama-server` 는 비전 버퍼 할당에 실패해도 `model loaded` 를 찍고 포트를 연다.
`/health` 가 ok 라고 해서 동작한다는 뜻이 아니다 — **실제 요청을 보내봐야 안다.**
그리고 컨텍스트를 줄이는 것이 늘 이득이 아니다. 이미지 토큰이 배치에 들어가야 하므로
`-c` 를 낮추면 오히려 깨진다.

## 이미지 크기의 딜레마

llama.cpp 가 경고한다:

```
Qwen-VL models require at minimum 1024 image tokens to function correctly on grounding task
```

- 너무 크면 → 배치 초과로 abort
- 너무 작으면 → 그라운딩 정확도 저하

768×432 에서 색 판별은 3/3 이었다. 물체 위치·방향 판단이 필요해지면 재검토해야 한다.

## VS-3 아키텍처에 대한 결정적 함의

| | 지연 |
|---|---|
| 제어 루프 (VS-2 실측) | **34.6 ms** |
| 규칙 정책 판단 | **0.0 ms** |
| **VLM 판단** | **2200 ~ 2900 ms** |

**VLM 은 제어 루프 안에 들어갈 수 없다.** 약 70~85배 느리다.

이는 ADR-0001 이 이미 정한 방향을 실측으로 확증한 것이다 —
**느린 정책 루프와 빠른 제어 루프를 분리**해야 한다. VS-3 의 VLM 정책은
제어 루프를 막지 않고 비동기로 돌며, 제어 루프는 마지막으로 받은 의도를
계속 유지한 채 28 fps 로 돈다. 타이밍은 여전히 MCU 가 소유한다.

## 권장

**운용은 3B 로, 7B 는 품질 상한 확인용으로.**
7B 의 잔여 100 MiB 는 카메라 파이프라인·제어 루프가 함께 도는 실제 운용에서
버티기 어렵다 (nvargus-daemon 만 160 MB 다). 3B 는 1.80 + 0.79 = 2.59 GB 로
3 GB 이상 여유가 남는다.

## 재현

```bash
# 빌드
cmake -B build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=87 -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4        # Orin Nano 에서 약 30분

# 단발 시험
llama-mtmd-cli -m <model> --mmproj <mmproj> -ngl 99 -c 4096 -b 4096 \
  -ctk q8_0 -ctv q8_0 --image scene.jpg -p "..."
```
