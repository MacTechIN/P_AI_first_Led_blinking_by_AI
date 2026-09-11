#!/usr/bin/env python3
"""Drive the Arduino led_blink sketch from the Jetson over USB serial.

Examples:
    ./host/blink.py                      # blink at the sketch default (500ms)
    ./host/blink.py --interval 100       # fast blink
    ./host/blink.py --on                 # hold the LED on
    ./host/blink.py --pattern sos        # blink out SOS, then resume
    ./host/blink.py --repl               # type commands interactively
"""

import argparse
import sys
import time

try:
    import serial  # pyserial
except ImportError:
    sys.exit("pyserial is missing. Install it with: pip3 install --user pyserial")

DEFAULT_PORT = "/dev/ttyACM0"
BAUD = 115200
# Opening the port toggles DTR, which resets the Uno. The bootloader then waits
# before handing control to the sketch, so nothing sent before READY is seen.
RESET_WAIT = 2.0

# (on_ms, off_ms) pairs: dot, dash, gap
SOS = [(150, 150)] * 3 + [(450, 150)] * 3 + [(150, 150)] * 3


class Arduino:
    def __init__(self, port, baud=BAUD, timeout=1.0, verbose=True):
        self.verbose = verbose
        self.ser = serial.Serial(port, baud, timeout=timeout)
        self._wait_ready()

    def _wait_ready(self):
        deadline = time.time() + RESET_WAIT + 3.0
        self.ser.reset_input_buffer()
        while time.time() < deadline:
            line = self.ser.readline().decode(errors="replace").strip()
            if line.startswith("READY"):
                self._log(f"< {line}")
                return
        # Not fatal: the sketch may already have been running before we opened.
        self._log("! READY banner not seen; continuing anyway")

    def _log(self, msg):
        if self.verbose:
            print(msg)

    def send(self, cmd):
        """Send one command and return the Arduino's reply line."""
        self._log(f"> {cmd}")
        self.ser.write((cmd + "\n").encode())
        self.ser.flush()
        reply = self.ser.readline().decode(errors="replace").strip()
        if reply:
            self._log(f"< {reply}")
        return reply

    def close(self):
        self.ser.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def run_pattern(ard, pattern):
    """Blink a fixed on/off pattern from the host side."""
    for on_ms, off_ms in pattern:
        ard.send("ON")
        time.sleep(on_ms / 1000.0)
        ard.send("OFF")
        time.sleep(off_ms / 1000.0)


def repl(ard):
    print("Type commands (BLINK / ON / OFF / INT <ms> / STATE / PING). Ctrl-D to quit.")
    while True:
        try:
            cmd = input("arduino> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if cmd:
            ard.send(cmd)


def main():
    p = argparse.ArgumentParser(description="Blink an LED on an Arduino over serial.")
    p.add_argument("--port", default=DEFAULT_PORT, help=f"serial port (default: {DEFAULT_PORT})")
    p.add_argument("--interval", type=int, metavar="MS", help="blink half-period in ms")
    p.add_argument("--repl", action="store_true", help="interactive command prompt")
    p.add_argument("--pattern", choices=["sos"], help="blink a fixed pattern, then resume blinking")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--on", action="store_true", help="hold the LED on")
    mode.add_argument("--off", action="store_true", help="hold the LED off")
    args = p.parse_args()

    try:
        ard = Arduino(args.port)
    except serial.SerialException as e:
        sys.exit(
            f"Cannot open {args.port}: {e}\n"
            "If this is a permission error, add yourself to the dialout group:\n"
            "    sudo usermod -aG dialout $USER   (then log out and back in)"
        )

    with ard:
        ard.send("PING")
        if args.interval is not None:
            ard.send(f"INT {args.interval}")
        if args.on:
            ard.send("ON")
        elif args.off:
            ard.send("OFF")
        elif args.pattern == "sos":
            run_pattern(ard, SOS)
            ard.send("BLINK")
        else:
            ard.send("BLINK")

        if args.repl:
            repl(ard)
        else:
            ard.send("STATE")


if __name__ == "__main__":
    main()
