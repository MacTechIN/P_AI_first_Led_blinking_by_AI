# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Hardware context

Host is an **NVIDIA Jetson Orin Nano Super Developer Kit** (Ubuntu 22.04, aarch64, L4T kernel
5.15.x-tegra). The LED is **not** driven by Jetson GPIO — it is driven by an **Arduino Uno R3**
connected over USB (`/dev/ttyACM0`, USB ID `2341:0043`, CDC ACM). So the architecture is
host → USB serial → microcontroller, not `Jetson.GPIO`.

## Layout

```
arduino/led_blink/led_blink.ino   sketch: non-blocking blink + serial command parser
host/blink.py                     Jetson-side controller (pyserial) that sends commands
Makefile                          build / flash / monitor wrappers around arduino-cli
docs/research.md                  placeholder for Physical AI research notes
```

## Commands

```bash
make build      # compile sketch (no board needed)
make flash      # compile + upload to /dev/ttyACM0
make monitor    # raw serial monitor at 115200
make run        # run the host controller

./host/blink.py --interval 100   # fast blink
./host/blink.py --on             # hold LED on
./host/blink.py --pattern sos    # host-timed pattern
./host/blink.py --repl           # interactive prompt
```

Override the port with `PORT=/dev/ttyACM1 make flash`.

## Serial protocol

115200 baud, newline-terminated ASCII, one reply line per command. The sketch prints
`READY led_blink` after reset. Commands: `BLINK`, `ON`, `OFF`, `INT <ms>` (>= 10),
`STATE`, `PING` → `PONG`.

Two constraints worth knowing before debugging serial issues:

- **Opening the port resets the Uno** (DTR toggle). The bootloader runs first, so anything
  sent in the first ~2s is lost. `host/blink.py` waits for the `READY` banner instead of
  sleeping blindly — keep that behavior in any new host code.
- **Only one process may hold the port.** `make monitor` and `blink.py` cannot run at once,
  and an open monitor will make `make flash` fail.

Blink timing lives on the Arduino (`millis()`-based, rollover-safe) so it is unaffected by
host scheduling. `--pattern` is the deliberate exception: it is timed host-side.

## Toolchain

`arduino-cli` (1.5.x) and `gh` are installed **per-user** in `~/.local/bin` — not via apt,
because `sudo` requires an interactive password in this environment. `arduino:avr` core and
`pyserial` (`pip3 install --user`) are installed. Prefer this no-sudo install pattern for any
further tooling.

## Environment gotchas

- The user account must be in the **`dialout`** group to open `/dev/ttyACM0`; otherwise every
  serial operation fails with `Permission denied`. Group changes need a re-login or reboot.
- No camera is guaranteed present. Verify with `v4l2-ctl --list-devices` and an actual capture
  attempt (`gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! fakesink`) — `/dev/media0` and a
  running `nvargus-daemon` exist on this board even with **no sensor attached**, so neither is
  evidence of a working camera. CSI cameras are not hot-pluggable and need a reboot.
- `dmesg` is not readable as a normal user here; use `/var/log/syslog` and `/var/log/kern.log`.

The user communicates in Korean.
