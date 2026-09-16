# Arduino Uno LED blinker. Requires arduino-cli on PATH (~/.local/bin).
FQBN  ?= arduino:avr:uno
PORT  ?= /dev/ttyACM0
SKETCH = arduino/led_blink

.PHONY: build flash monitor run clean

build:
	arduino-cli compile --fqbn $(FQBN) $(SKETCH)

flash: build
	arduino-cli upload -p $(PORT) --fqbn $(FQBN) $(SKETCH)

monitor:
	arduino-cli monitor -p $(PORT) --config baudrate=115200

run:
	./host/blink.py --port $(PORT)

clean:
	rm -rf $(SKETCH)/build

# --- Python (인지 계층 외) ---
.PHONY: test lint
test:
	python3 -m pytest tests/ -q

lint:
	python3 -m compileall -q perception host
