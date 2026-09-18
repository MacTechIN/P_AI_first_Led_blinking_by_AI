/*
 * rgb_led — Arduino Uno R3 RGB LED driver, commanded over USB serial.
 *
 * The host (Jetson) talks to this sketch over /dev/ttyACM0 at 115200 baud.
 * Blinking is non-blocking (millis()-based) so serial commands stay responsive.
 *
 * WIRING / PWM CAVEAT
 *   B = pin 9   (PWM)
 *   R = pin 10  (PWM)
 *   G = pin 11  (PWM)
 *
 * The module is COMMON ANODE: each cathode leg is driven by its pin while the
 * common leg sits at +5V, so a LOW pin lights the channel and a HIGH pin blanks
 * it. analogWrite() values are therefore inverted on the way out. This was
 * established by photographing the LED: RGB 255 255 255 went dark and
 * RGB 255 0 0 glowed cyan, both of which only make sense inverted.
 * Set COMMON_ANODE to false for a common-cathode module.
 *
 * All three are PWM, so every channel is 256-level and mixed colours are
 * reproducible. Only pins 3,5,6,9,10,11 are PWM on the Uno: blue was first
 * wired to 12, where analogWrite() collapses to on/off at the 128 threshold
 * and partial blue (purple, cyan, warm white) came out wrong. BLUE_IS_PWM
 * reports the current wiring so the host can tell which case it is in.
 *
 * Commands (newline-terminated, case-insensitive):
 *   RGB <r> <g> <b>  set colour, each 0-255
 *   ON               show the colour
 *   OFF              blank the LED
 *   BLINK            blink the colour on/off
 *   INT <ms>         blink half-period, 10-5000
 *   LEVEL <n>        master brightness 0-255, scales all channels
 *   WATCHDOG <ms>    0 disables; otherwise blank the LED if no command arrives
 *                    within that window (10-60000)
 *   STATE            report mode, interval, level, colour, flags
 *   PING             -> PONG (also feeds the watchdog)
 *
 * Ranges are enforced here as well as host-side: the host check is a
 * convenience, this one is the boundary a model cannot cross (ADR-0003).
 */

const uint8_t RED_PIN = 10;    // PWM
const uint8_t GREEN_PIN = 11;  // PWM
const uint8_t BLUE_PIN = 9;    // PWM (was 12, which is not PWM — see caveat)
const uint8_t MIRROR_PIN = LED_BUILTIN;

const bool COMMON_ANODE = true;  // LOW lights the channel — see header

// Per-channel gains, out of 255. The module shares ONE current-limiting resistor
// on its common leg, so the three dies compete for a fixed current and the
// lowest forward-voltage die wins: red beats green beats blue. Measured
// directly -- commanding RGB 255 255 0 (yellow) photographed as pure red, and
// red had to drop to ~120 before green appeared at all. These gains hold the
// stronger dies back so mixtures land near their intended hue.
//
// This is a workaround, not a fix. The hardware fix is one resistor per channel
// (220-330R on each of R, G, B) instead of one on the common leg; with that,
// set all three gains to 255.
const uint8_t GAIN_R = 120;
const uint8_t GAIN_G = 200;
const uint8_t GAIN_B = 255;
const bool BLUE_IS_PWM = (BLUE_PIN == 3 || BLUE_PIN == 5 || BLUE_PIN == 6 ||
                          BLUE_PIN == 9 || BLUE_PIN == 10 || BLUE_PIN == 11);

const unsigned long BAUD = 115200;
const unsigned long MIN_INTERVAL = 10;
const unsigned long MAX_INTERVAL = 5000;
const uint8_t MAX_LEVEL = 255;
const unsigned long MIN_WATCHDOG = 10;
const unsigned long MAX_WATCHDOG = 60000;

enum Mode { MODE_BLINK, MODE_ON, MODE_OFF };

Mode mode = MODE_ON;
unsigned long interval = 500;
unsigned long lastToggle = 0;
uint8_t level = MAX_LEVEL;
uint8_t red = 0, green = 0, blue = 0;
bool lit = false;
String line;

// Watchdog. Off by default: an LED left glowing harms nothing, and the blink
// and colour-cycle demos deliberately set a state and stop talking. A device
// that can damage itself or its surroundings -- a servo, a stepper -- must
// enable it at startup, because a host that dies mid-motion otherwise leaves
// the mechanism driving into its end stop.
unsigned long watchdogMs = 0;
unsigned long lastCommand = 0;
bool watchdogTripped = false;

// Duty as the LED sees it: 0 = dark, 255 = full, regardless of wiring polarity.
void driveChannel(uint8_t pin, uint16_t duty) {
  analogWrite(pin, COMMON_ANODE ? 255 - duty : duty);
}

// Requested value -> actual duty, after master level and per-channel gain.
uint16_t dutyFor(uint8_t value, uint8_t gain) {
  return (uint32_t)value * level / 255 * gain / 255;
}

void writeChannels(bool on) {
  lit = on;
  driveChannel(RED_PIN, on ? dutyFor(red, GAIN_R) : 0);
  driveChannel(GREEN_PIN, on ? dutyFor(green, GAIN_G) : 0);
  driveChannel(BLUE_PIN, on ? dutyFor(blue, GAIN_B) : 0);
  digitalWrite(MIRROR_PIN, on && (red || green || blue) ? HIGH : LOW);
}

void setup() {
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(MIRROR_PIN, OUTPUT);
  writeChannels(false);
  line.reserve(48);
  Serial.begin(BAUD);
  while (!Serial) { ; }
  lastCommand = millis();
  Serial.print(F("READY rgb_led blue_pwm="));
  Serial.print(BLUE_IS_PWM ? 1 : 0);
  Serial.print(F(" common_anode="));
  Serial.println(COMMON_ANODE ? 1 : 0);
  lastToggle = millis();
}

void reportState() {
  Serial.print(F("STATE "));
  Serial.print(mode == MODE_BLINK ? F("BLINK") : (mode == MODE_ON ? F("ON") : F("OFF")));
  Serial.print(F(" interval="));
  Serial.print(interval);
  Serial.print(F(" level="));
  Serial.print(level);
  Serial.print(F(" rgb="));
  Serial.print(red); Serial.print(',');
  Serial.print(green); Serial.print(',');
  Serial.print(blue);
  Serial.print(F(" blue_pwm="));
  Serial.print(BLUE_IS_PWM ? 1 : 0);
  Serial.print(F(" common_anode="));
  Serial.print(COMMON_ANODE ? 1 : 0);
  Serial.print(F(" watchdog="));
  Serial.print(watchdogMs);
  Serial.print(F(" tripped="));
  Serial.println(watchdogTripped ? 1 : 0);
}

// Parse "<a> <b> <c>" into three 0-255 values. Returns false on any bad field.
bool parseTriple(const String &s, long *out) {
  int start = 0;
  for (uint8_t i = 0; i < 3; i++) {
    while (start < (int)s.length() && s[start] == ' ') start++;
    if (start >= (int)s.length()) return false;
    int end = s.indexOf(' ', start);
    if (end < 0) end = s.length();
    String tok = s.substring(start, end);
    for (uint8_t k = 0; k < tok.length(); k++) {
      if (!isDigit(tok[k])) return false;   // reject signs and junk
    }
    out[i] = tok.toInt();
    if (out[i] < 0 || out[i] > 255) return false;
    start = end;
  }
  return true;
}

// The safe state. For this device that is dark; for a servo it would be a
// known-good position, and for a stepper, de-energised.
void enterSafeState() {
  watchdogTripped = true;
  mode = MODE_OFF;
  writeChannels(false);
  Serial.println(F("WATCHDOG tripped, entered safe state"));
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  cmd.toUpperCase();

  // Every command feeds the watchdog, but only a command that drives an output
  // clears the trip. Otherwise STATE -- the very command used to observe the
  // trip -- clears it first, and the flag can never be read. A tripped device
  // also *should* stay in its safe state until something explicitly commands
  // it back, rather than resuming because the host said hello.
  lastCommand = millis();

  if (cmd == F("PING")) {
    Serial.println(F("PONG"));
  } else if (cmd == F("BLINK")) {
    watchdogTripped = false;
    mode = MODE_BLINK;
    lastToggle = millis();
    Serial.println(F("OK BLINK"));
  } else if (cmd == F("ON")) {
    watchdogTripped = false;
    mode = MODE_ON;
    writeChannels(true);
    Serial.println(F("OK ON"));
  } else if (cmd == F("OFF")) {
    watchdogTripped = false;
    mode = MODE_OFF;
    writeChannels(false);
    Serial.println(F("OK OFF"));
  } else if (cmd == F("STATE")) {
    reportState();
  } else if (cmd.startsWith(F("RGB "))) {
    long v[3];
    if (!parseTriple(cmd.substring(4), v)) {
      Serial.println(F("ERR usage: RGB <r> <g> <b>, each 0-255"));
    } else {
      red = (uint8_t)v[0]; green = (uint8_t)v[1]; blue = (uint8_t)v[2];
      if (mode != MODE_OFF) writeChannels(true);
      Serial.print(F("OK RGB "));
      Serial.print(red); Serial.print(' ');
      Serial.print(green); Serial.print(' ');
      Serial.println(blue);
    }
  } else if (cmd.startsWith(F("LEVEL "))) {
    long n = cmd.substring(6).toInt();
    if (n < 0 || n > (long)MAX_LEVEL) {
      Serial.println(F("ERR level must be 0-255"));
    } else {
      level = (uint8_t)n;
      if (lit || mode == MODE_ON) writeChannels(true);
      Serial.print(F("OK LEVEL "));
      Serial.println(level);
    }
  } else if (cmd.startsWith(F("WATCHDOG "))) {
    long ms = cmd.substring(9).toInt();
    if (ms != 0 && (ms < (long)MIN_WATCHDOG || ms > (long)MAX_WATCHDOG)) {
      Serial.println(F("ERR watchdog must be 0 or 10-60000"));
    } else {
      watchdogMs = (unsigned long)ms;
      Serial.print(F("OK WATCHDOG "));
      Serial.println(watchdogMs);
    }
  } else if (cmd.startsWith(F("INT "))) {
    long ms = cmd.substring(4).toInt();
    if (ms < (long)MIN_INTERVAL || ms > (long)MAX_INTERVAL) {
      Serial.println(F("ERR interval must be 10-5000"));
    } else {
      interval = (unsigned long)ms;
      Serial.print(F("OK INT "));
      Serial.println(interval);
    }
  } else {
    Serial.print(F("ERR unknown command: "));
    Serial.println(cmd);
  }
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (line.length() > 0) { handleCommand(line); line = ""; }
    } else if (line.length() < 47) {
      line += c;
    }
  }

  // Watchdog is checked before anything else drives an output: a tripped
  // device must not keep blinking on its way to the safe state.
  if (watchdogMs > 0 && !watchdogTripped &&
      (millis() - lastCommand) >= watchdogMs) {
    enterSafeState();
  }

  if (mode == MODE_BLINK) {
    unsigned long now = millis();
    if (now - lastToggle >= interval) {   // unsigned math survives millis() rollover
      lastToggle = now;
      writeChannels(!lit);
    }
  }
}
