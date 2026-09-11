/*
 * led_blink — Arduino Uno R3 LED blinker driven over USB serial.
 *
 * The host (Jetson) talks to this sketch over /dev/ttyACM0 at 115200 baud.
 * Blinking is non-blocking (millis()-based) so serial commands stay responsive.
 *
 * Commands (newline-terminated, case-insensitive):
 *   BLINK      resume blinking
 *   ON         hold the LED on
 *   OFF        hold the LED off
 *   INT <ms>   set blink half-period in milliseconds (>= 10)
 *   STATE      report current mode and interval
 *   PING       -> PONG   (liveness check)
 *
 * Every command is answered with a single line so the host can confirm it.
 */

const uint8_t LED_PIN = LED_BUILTIN;   // pin 13 on the Uno
const unsigned long BAUD = 115200;
const unsigned long MIN_INTERVAL = 10;

enum Mode { MODE_BLINK, MODE_ON, MODE_OFF };

Mode mode = MODE_BLINK;
unsigned long interval = 500;          // half-period: 500ms on, 500ms off
unsigned long lastToggle = 0;
bool ledOn = false;
String line;

void setLed(bool on) {
  ledOn = on;
  digitalWrite(LED_PIN, on ? HIGH : LOW);
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  setLed(false);
  line.reserve(32);
  Serial.begin(BAUD);
  while (!Serial) { ; }              // Uno returns immediately; harmless elsewhere
  Serial.println(F("READY led_blink"));
  lastToggle = millis();
}

void reportState() {
  Serial.print(F("STATE "));
  Serial.print(mode == MODE_BLINK ? F("BLINK") : (mode == MODE_ON ? F("ON") : F("OFF")));
  Serial.print(F(" interval="));
  Serial.println(interval);
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;
  cmd.toUpperCase();

  if (cmd == F("PING")) {
    Serial.println(F("PONG"));
  } else if (cmd == F("BLINK")) {
    mode = MODE_BLINK;
    lastToggle = millis();
    Serial.println(F("OK BLINK"));
  } else if (cmd == F("ON")) {
    mode = MODE_ON;
    setLed(true);
    Serial.println(F("OK ON"));
  } else if (cmd == F("OFF")) {
    mode = MODE_OFF;
    setLed(false);
    Serial.println(F("OK OFF"));
  } else if (cmd == F("STATE")) {
    reportState();
  } else if (cmd.startsWith(F("INT "))) {
    long ms = cmd.substring(4).toInt();
    if (ms < (long)MIN_INTERVAL) {
      Serial.println(F("ERR interval must be >= 10"));
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
    } else if (line.length() < 31) {
      line += c;
    }
  }

  if (mode == MODE_BLINK) {
    unsigned long now = millis();
    if (now - lastToggle >= interval) {   // unsigned math survives millis() rollover
      lastToggle = now;
      setLed(!ledOn);
    }
  }
}
