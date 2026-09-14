# CSI camera bring-up on this Jetson Orin Nano

Record of what has been verified, so the same ground is not re-covered.

Board: p3767 (Orin Nano module) + p3768 carrier, L4T R36.5.2 (JetPack 6).
CSI connectors are **22-pin**, confirmed by the jetson-io menu label
("Configure Jetson 22pin CSI Connector").

## RESOLVED: the sensor is an IMX708, which JetPack does not support

Root cause, confirmed by reading the sensor's own ID register over i2c while it was
powered and clocked:

```
i2ctransfer -y -f 9 w2@0x1a 0x00 0x16 r2   ->   0x07 0x08
```

`0x0708` is the **IMX708** — the Raspberry Pi **Camera Module 3**. This board's stock
JetPack ships no driver for it:

| | |
|---|---|
| `nv_imx708.ko` | absent |
| imx708 device tree overlays | none |
| modules.alias entries | none |
| Sensors JetPack does ship | ar0234, imx185, imx219, imx274, imx318, imx390, imx477, ov5693, hawk_owl |

IMX708 shares i2c address `0x1a` with the IMX477, so applying the **Camera IMX477 Dual**
overlay makes the imx477 driver find *something* there. It logs
`invalid sensor model id: 31`, binds anyway, and creates `/dev/video0` — but the IMX477
register sequences do not configure an IMX708, so every captured frame is flat: a
3840x2160 RG10 buffer where all 8.3M samples equal exactly 4100.

**A working `/dev/video0` is therefore not proof of a working camera here.** Check the
pixel data.

## How the earlier dead end resolved

Everything before this pointed at the cable, wrongly. The reasoning error: a manual
`i2cdetect` scan runs with the sensor unpowered and its INCK clock stopped, and these
sensors answer i2c only while clocked. An empty scan therefore cannot distinguish "no
camera attached" from "camera attached but no matching overlay loaded" — which is
exactly the situation that held. The cable and both modules were fine all along.

The lesson for next time: identify the sensor *first*, by applying any overlay that
powers the right i2c address and then reading register 0x0016, rather than inferring
from scans.

## Options

1. **Use a supported module.** Camera Module v2 (IMX219) or HQ Camera (IMX477) work with
   the stock overlays and no extra software.
2. **Third-party IMX708 driver.** Arducam and others publish out-of-tree IMX708 drivers
   and overlays for Jetson; they install as a kernel module package, not a custom kernel
   build. Verify the vendor supports L4T R36.5 / JetPack 6 before buying into this.
3. **USB webcam.** Enumerates as `/dev/video0` with no overlay and no reboot.

## Reference: the state when it was failing

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

## Ruled out: the cam0-rst GPIO hog

`bus@0/gpio@2200000/camera-control-output-low` is hogged `output-low` with
`label = "cam0-rst"`, which looks like the sensor being held in reset. It is not the
bug: decompiling the overlay (`dtc -I dtb -O dts`) shows NVIDIA defines this hog inside
the shipped overlay itself, on DT pin 59, while the sensor nodes take their reset from
DT pins 62 (CAM0) and 160 (CAM1). Different lines, intentional design.

Caveat on the reset experiment above: IMX219 needs its INCK (24 MHz) clock running
before it will answer i2c at all. Driving the reset line high by hand without enabling
that clock is therefore not a clean negative — it is weak evidence, not proof.

## The 22-pin trap

Raspberry Pi Camera v2 / HQ modules ship with a **15-pin** ribbon. It slides into
the Orin Nano's 22-pin connector and looks seated, but no contact is made. A
15-to-22-pin adapter cable is required. Counting the contacts on the Jetson end
of the cable settles this in seconds.

Orientation on the 22-pin connector: silver contacts face **down** (toward the
PCB), blue stiffener up. Check both ends — some cables are not symmetric.

## Tried: a Raspberry Pi 5 cable (22-pin) — still fails

Fitting a Pi 5 camera cable changed nothing: both ports still NACK with -121. The Pi 5
end is 22-pin and mates mechanically with this board, so this is now a signal-assignment
question, not a geometry one. A cable that works on a Pi 5 is wired for the Pi's 22-pin
pinout, which is not necessarily the pinout this connector expects. Buy a ribbon sold
specifically for Jetson (Arducam / Waveshare list them as "Jetson Nano/Orin 15-to-22-pin
camera cable") rather than reusing a Raspberry Pi one.

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
