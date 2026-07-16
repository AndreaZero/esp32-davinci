/**
 * ESP32-DaVinci v0.1 — CrowPanel 7" → DaVinci Resolve (USB serial macros)
 *
 * Tools: ESP32S3 Dev Module | USB CDC Disabled | Flash 4MB | PSRAM OPI | Huge APP
 * (stesse impostazioni di esp32-sony)
 *
 * Librerie: LovyanGFX ≥1.1.16, lvgl 8.3.11
 * lv_conf.h in sketch (+ libraries/lv_conf.h se già usato per Sony)
 *
 * Mac: avvia bridge/resolve_bridge.py sulla porta seriale del panel.
 * Docs: docs/
 */

#include "config.h"
#include "LovyanGFX_Driver.h"
#include "touch.h"
#include "lvgl_port.h"
#include "actions.h"
#include "serial_proto.h"

LGFX lcd;

static lv_obj_t *s_lbl_status = nullptr;
static lv_obj_t *s_lbl_last = nullptr;
static uint32_t s_last_cmd_ms = 0;
static const uint32_t kDebounceMs = 200;

static void ui_set_status(const char *txt, uint32_t color) {
  if (!s_lbl_status) {
    return;
  }
  lv_label_set_text(s_lbl_status, txt);
  lv_obj_set_style_text_color(s_lbl_status, lv_color_hex(color), 0);
}

static void ui_set_last(const char *action_id) {
  if (!s_lbl_last) {
    return;
  }
  char buf[64];
  snprintf(buf, sizeof(buf), "Last: %s", action_id);
  lv_label_set_text(s_lbl_last, buf);
}

static void on_host_status(const char *line) {
  if (!line) {
    return;
  }
  if (strncmp(line, "ACK:", 4) == 0) {
    ui_set_status(line, 0x4CAF50);
  } else if (strncmp(line, "ERR:", 4) == 0) {
    ui_set_status(line, 0xE85D4C);
  } else {
    ui_set_status(line, 0xFFAB40);
  }
}

static void fire_action(const char *action_id) {
  const uint32_t now = millis();
  if (now - s_last_cmd_ms < kDebounceMs) {
    return;
  }
  s_last_cmd_ms = now;

  serial_proto_send_cmd(action_id);
  ui_set_last(action_id);
  ui_set_status("USB: CMD sent", 0xFFAB40);
}

static void on_action_btn(lv_event_t *e) {
  if (lv_event_get_code(e) != LV_EVENT_CLICKED) {
    return;
  }
  const char *id = (const char *)lv_event_get_user_data(e);
  if (id) {
    fire_action(id);
  }
}

static lv_obj_t *make_btn(lv_obj_t *parent, const char *label, const char *action_id,
                          lv_color_t bg, lv_coord_t w, lv_coord_t h) {
  lv_obj_t *btn = lv_btn_create(parent);
  lv_obj_set_size(btn, w, h);
  lv_obj_set_style_bg_color(btn, bg, 0);
  lv_obj_set_style_radius(btn, 8, 0);
  lv_obj_add_event_cb(btn, on_action_btn, LV_EVENT_CLICKED, (void *)action_id);

  lv_obj_t *lbl = lv_label_create(btn);
  lv_label_set_text(lbl, label);
  lv_obj_set_style_text_font(lbl, &lv_font_montserrat_20, 0);
  lv_obj_center(lbl);
  return btn;
}

static void ui_create() {
  lv_obj_t *scr = lv_scr_act();
  lv_obj_set_style_bg_color(scr, lv_color_hex(0x0D0D0F), 0);
  lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);

  lv_obj_t *title = lv_label_create(scr);
  lv_label_set_text(title, "ESP32-DaVinci");
  lv_obj_set_style_text_color(title, lv_color_hex(0xF0F0F2), 0);
  lv_obj_set_style_text_font(title, &lv_font_montserrat_28, 0);
  lv_obj_align(title, LV_ALIGN_TOP_LEFT, 24, 16);

  s_lbl_status = lv_label_create(scr);
  lv_label_set_text(s_lbl_status, "USB: waiting bridge");
  lv_obj_set_style_text_color(s_lbl_status, lv_color_hex(0xFFAB40), 0);
  lv_obj_set_style_text_font(s_lbl_status, &lv_font_montserrat_20, 0);
  lv_obj_align(s_lbl_status, LV_ALIGN_TOP_RIGHT, -24, 22);

  s_lbl_last = lv_label_create(scr);
  lv_label_set_text(s_lbl_last, "Last: —");
  lv_obj_set_style_text_color(s_lbl_last, lv_color_hex(0x6B6B70), 0);
  lv_obj_align(s_lbl_last, LV_ALIGN_TOP_LEFT, 24, 64);

  lv_obj_t *b;

  b = make_btn(scr, "CUT  (Cmd+B)", ACTION_CUT, lv_color_hex(0xC9A227), 360, 88);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 24, 110);

  b = make_btn(scr, "PLAY / PAUSE", ACTION_PLAY, lv_color_hex(0x2A4A6A), 360, 88);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -24, 110);

  b = make_btn(scr, "UNDO", ACTION_UNDO, lv_color_hex(0x2A2A32), 170, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 24, 220);

  b = make_btn(scr, "REDO", ACTION_REDO, lv_color_hex(0x2A2A32), 170, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 210, 220);

  b = make_btn(scr, "RIPPLE DEL", ACTION_RIPPLE_DEL, lv_color_hex(0xE85D4C), 360, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -24, 220);

  b = make_btn(scr, "IN (I)", ACTION_MARK_IN, lv_color_hex(0x3A3A42), 170, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 24, 310);

  b = make_btn(scr, "OUT (O)", ACTION_MARK_OUT, lv_color_hex(0x3A3A42), 170, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 210, 310);

  b = make_btn(scr, "SAVE", ACTION_SAVE, lv_color_hex(0x2A5A3A), 360, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -24, 310);

  b = make_btn(scr, "PING", ACTION_PING, lv_color_hex(0x3A2A2A), 140, 56);
  lv_obj_align(b, LV_ALIGN_BOTTOM_LEFT, 24, -24);
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
  ui_create();

  Serial.println("[OK] UI+USB serial ready");
  Serial.println("    Mac: python3 bridge/resolve_bridge.py");
}

void loop() {
  lvgl_port_loop();
  serial_proto_loop();
  delay(5);
}
