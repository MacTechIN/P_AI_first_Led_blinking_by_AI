# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hardware context

Host is an **NVIDIA Jetson Orin Nano Super Developer Kit** (Ubuntu 22.04, aarch64, L4T kernel
5.15.x-tegra). The LED is **not** driven by Jetson GPIO — it is driven by an **Arduino Uno R3**
connected over USB (`/dev/ttyACM0`, USB ID `2341:0043`, CDC ACM). So the architecture is
host → USB serial → microcontroller, not `Jetson.GPIO`.

## Layout

```
arduino/rgb_led/rgb_led.ino       sketch: RGB LED driver + serial command parser
host/blink.py                     Jetson-side controller (pyserial) that sends commands
perception/                       L2 perception: frame sources + health checks (µ1.4)
control/                          L1/L3: features, policies, actuators, control loop (VS-2)
host/vs2_demo.py                  VS-2 end-to-end demo (camera colour -> LED)
host/verify_rgb.py                closed-loop colour check: commanded vs photographed
tests/                            pytest suite; runs without a camera attached
Makefile                          build / flash / monitor wrappers around arduino-cli
docs/project_difinition.md        project definition (source of requirements)
docs/development_plan.md          vertical-slice plan; start here for what to build next
docs/project_0_camtest.md         environment bring-up + camera investigation record
docs/tech/adr/                    architecture decision records
docs/research.md                  placeholder for Physical AI research notes
```

## Commands

```bash
make build      # compile sketch (no board needed)
make flash      # compile + upload to /dev/ttyACM0
make monitor    # raw serial monitor at 115200
make run        # run the host controller
make test       # pytest (camera-dependent tests skip themselves)

./host/blink.py --interval 100   # fast blink
./host/blink.py --on             # hold LED on
./host/blink.py --pattern sos    # host-timed pattern
./host/blink.py --repl           # interactive prompt
./host/vs2_demo.py --steps 30 --lock      # VS-2 loop on real hardware
./host/vs2_demo.py --policy rule          # blink-rate encoding instead of mirroring
./host/verify_rgb.py --level 40 --lock    # commanded vs photographed colour
./host/vs2_demo.py --source synthetic --dry-run   # no hardware at all
```

Override the port with `PORT=/dev/ttyACM1 make flash`.

## Serial protocol

115200 baud, newline-terminated ASCII, one reply line per command. The sketch prints
`READY led_blink` after reset. Commands: `BLINK`, `ON`, `OFF`, `INT <ms>` (10-5000),
`LEVEL <n>` (0-255, PWM brightness), `STATE`, `PING` → `PONG`.

RGB LED on **B=9, R=10, G=11** (all PWM), plus `RGB <r> <g> <b>`. Pin 13 mirrors on/off.
Range limits are enforced in firmware as well as in `control/commands.py` — the host check
is a convenience, firmware is the boundary a model cannot cross (ADR-0003).

Two hardware quirks are compensated in firmware, both established by photographing the
LED (see `docs/tech/notes/rgb-led-calibration.md`):

- **Common anode**: a LOW pin lights the channel, so duties are inverted on the way out.
  Before this, `RGB 255 0 0` glowed cyan and `RGB 255 255 255` went dark.
- **One shared current-limiting resistor**: the dies compete for a fixed current and the
  lowest-forward-voltage one wins (red beats green beats blue), so `RGB 255 255 0` came
  out pure red. `GAIN_R/G/B` hold the stronger dies back. The real fix is a resistor per
  channel; with that wiring, set all three gains to 255.

Two constraints worth knowing before debugging serial issues:

- **Opening the port resets the Uno** (DTR toggle). The bootloader runs first, so anything
  sent in the first ~2s is lost. `host/blink.py` waits for the `READY` banner instead of
  sleeping blindly — keep that behavior in any new host code.
- **Only one process may hold the port.** `make monitor` and `blink.py` cannot run at once,
  and an open monitor will make `make flash` fail.

Re-sending an identical `BLINK` resets the blink phase and looks like a stutter, so
`ControlLoop` actuates only when the command changes. That is a correctness requirement,
not an optimisation. `MirrorColorPolicy` additionally holds its output with hysteresis —
without it, sensor noise alone produced 18 commands in 20 still frames (ADR-0007).

Blink timing lives on the Arduino (`millis()`-based, rollover-safe) so it is unaffected by
host scheduling. `--pattern` is the deliberate exception: it is timed host-side.

## Local VLM

`llama.cpp` is built from source with CUDA (`~/llama.cpp`, sm_87) and the models live in
`~/models`. Qwen2.5-VL-7B Q4_K_M runs, but with almost no headroom — see
`docs/tech/notes/vlm-on-orin-nano.md` before changing any flag:

```bash
~/llama.cpp/build/bin/llama-server -m ~/models/Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf \
  --mmproj ~/models/mmproj-Qwen2.5-VL-7B-Instruct-Q8_0.gguf \
  -ngl 99 -c 2048 -b 2048 -ub 512 --parallel 1 -ctk q8_0 -ctv q8_0 --port 8080
```

- **The GUI must stay off** (`multi-user.target`). With GNOME running there is 2.3 GiB
  free instead of 6.4 GiB, and nothing fits.
- `--parallel 1` matters: the default allocates four KV slots and the server then dies on
  the first request.
- Images must be resized (768x432 works). A 1280x720 frame overflows the batch and aborts
  on `GGML_ASSERT(n_tokens_all <= cparams.n_batch)`.
- **`/health` returning ok does not mean it works.** The server reports `model loaded`
  even when the vision buffer failed to allocate. Send a real request to find out.
- Inference is 2.2-2.9 s, against a 34.6 ms control loop, so the VLM never runs inside
  that loop (ADR-0008).

## Toolchain

`arduino-cli` (1.5.x) and `gh` are installed **per-user** in `~/.local/bin` — not via apt,
because `sudo` requires an interactive password in this environment. `arduino:avr` core and
`pyserial` (`pip3 install --user`) are installed. Prefer this no-sudo install pattern for any
further tooling.

## Environment gotchas

- The user account must be in the **`dialout`** group to open `/dev/ttyACM0`; otherwise every
  serial operation fails with `Permission denied`. Group changes need a re-login or reboot.
- **The CSI camera works: an IMX219 under the `Camera IMX219 Dual` overlay.** Read it
  with `open_source("argus:0")`, never with cv2/V4L2 — `/dev/video0` carries RG10 Bayer
  that only the Tegra ISP can develop, and this system's cv2 is built without GStreamer.
  See ADR-0006.
- An earlier module was a Raspberry Pi Camera Module 3 (IMX708), which JetPack does not
  support. It shares i2c address `0x1a` with the IMX477, so that overlay bound to it and
  created a `/dev/video0` whose every sample was 4100. **A present `/dev/video0` is not
  proof of a working camera — check the pixel data** (`perception.assert_frame_sane`).
  The identification procedure is in `docs/project_0_camtest.md`.
- `/dev/media0` and a running `nvargus-daemon` exist on this board even with **no sensor
  attached**, so neither is evidence of a working camera. Verify with an actual capture
  (`gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! fakesink`). CSI cameras are not
  hot-pluggable and need a reboot.
- `dmesg` is not readable as a normal user here; use `/var/log/syslog` and `/var/log/kern.log`.

The user communicates in Korean.
