# CSI camera bring-up on this Jetson Orin Nano

Record of what has been verified, so the same ground is not re-covered.

Board: p3767 (Orin Nano module) + p3768 carrier, L4T R36.5.2 (JetPack 6).
CSI connectors are **22-pin**, confirmed by the jetson-io menu label
("Configure Jetson 22pin CSI Connector").

## Current state: sensor does not respond electrically

```
imx219  9-0010: imx219_board_setup: error during i2c read probe (-121)
imx219 10-0010: imx219_board_setup: error during i2c read probe (-121)
```

`-121` is `EREMOTEIO` — an I2C NACK. The bus is driven correctly and nothing
answers. A full 0x00-0x77 scan of both CSI buses returns zero devices.

## Verified working (do not re-investigate)

| Layer | Evidence |
|---|---|
| Overlay | `OVERLAYS /boot/tegra234-p3767-camera-p3768-imx219-dual.dtbo` in extlinux.conf |
| Device tree | `cam_i2cmux/i2c@0/rbpcv2_imx219_a@10` and `i2c@1/rbpcv2_imx219_c@10` both present |
| Driver | `imx219_v2.0.6` loads and probes both addresses |
| i2c mux | i2c-9 = chan_id 1, i2c-10 = chan_id 0 (channels distinct under the dual overlay) |
| CSI/VI | `nvcsi`, `tegra-capture-vi`, `vi0`/`vi1` all bind cleanly |
| Reset line | PJ.04 (gpiochip0 line 62) driven high manually — still no i2c response |

## Variables eliminated

- **Camera module** — two different modules produced byte-identical failures.
- **Port** — the dual overlay probes CAM0 and CAM1 simultaneously; both NACK.
- **Sensor identity** — an IMX477 would answer at 0x1a; nothing answers anywhere,
  so this is not a wrong-overlay problem.
- **Reset held low** — releasing PJ.04 by hand changed nothing.

Remaining suspect is the physical layer: cable pin count, orientation, or damage.

## Confirmed good on a Raspberry Pi

The module and cable were verified working on a Raspberry Pi. That eliminates a dead
sensor and a damaged ribbon — but it does **not** clear the cable, because a cable that
works on a Pi is a Pi cable. Pi 4 and earlier use a **15-pin** CSI connector; only the
Pi 5 / CM4 use 22-pin. A cable proven on a Pi 4 is therefore 15-pin, which is exactly
the failure mode below.

## The 22-pin trap

Raspberry Pi Camera v2 / HQ modules ship with a **15-pin** ribbon. It slides into
the Orin Nano's 22-pin connector and looks seated, but no contact is made. A
15-to-22-pin adapter cable is required. Counting the contacts on the Jetson end
of the cable settles this in seconds.

Orientation on the 22-pin connector: silver contacts face **down** (toward the
PCB), blue stiffener up. Check both ends — some cables are not symmetric.

## Useful commands

```bash
ls /dev/video*                                   # the goal
journalctl -k -b | grep imx219                   # probe result
i2cdetect -y -r 9 ; i2cdetect -y -r 10           # 0x10=IMX219, 0x1a=IMX477
i2cdetect -l | grep -E 'i2c-(9|10)'              # confirm mux channels differ
sudo /opt/nvidia/jetson-io/config-by-hardware.py -n "Camera IMX219 Dual"
```

The last one applies an overlay non-interactively; the exact name comes from the
dtbo itself (`strings <file>.dtbo | grep Camera`), avoiding the jetson-io TUI.

## Fallback

A USB webcam needs none of this — it enumerates as `/dev/video0` with no overlay
and no reboot.
