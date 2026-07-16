/**
 * ESP32-DaVinci — CrowPanel 7" Resolve deck (USB serial shortcuts)
 *
 * Tools: ESP32S3 Dev Module | USB CDC Disabled | Flash 4MB | PSRAM OPI | Huge APP
 *
 * Libraries: LovyanGFX ≥1.2.9 (with esp32 core 3.x), lvgl 8.3.11
 * Copy lv_conf.h to Arduino/libraries/lv_conf.h
 *
 * Mac: python3 bridge/resolve_bridge.py
 * Docs: README.md and docs/
 */

#include "config.h"
#include "LovyanGFX_Driver.h"
#include "touch.h"
#include "lvgl_port.h"
#include "serial_proto.h"
#include "ui_deck.h"

LGFX lcd;

static void on_host_status(const char *line) {
  ui_deck_on_host_line(line);
}

static void backlight_on() {
  pinMode(TFT_BL, OUTPUT);
  digitalWrite(TFT_BL, LOW);
  delay(500);
  digitalWrite(TFT_BL, HIGH);
}

void setup() {
  serial_proto_begin(115200);
  serial_proto_set_status_cb(on_host_status);

  Serial.println("========== ESP32-DaVinci v" FW_VERSION " ==========");
  Serial.printf("PSRAM: %s (%u)\n", psramFound() ? "YES" : "NO", ESP.getPsramSize());

  pinMode(38, OUTPUT);
  digitalWrite(38, LOW);

  lcd.begin();
  lcd.fillScreen(TFT_BLACK);
  delay(100);
  backlight_on();

  touch_init();
  lvgl_port_init(lcd);
  ui_deck_create();

  Serial.println("[OK] UI deck + USB serial ready");
  Serial.println("    Mac: python3 bridge/resolve_bridge.py");
}

void loop() {
  lvgl_port_loop();
  serial_proto_loop();
  ui_deck_loop();
  delay(5);
}
