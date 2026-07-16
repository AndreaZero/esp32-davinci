#include "lvgl_port.h"

#include <esp_timer.h>

#include "config.h"
#include "touch.h"

static LGFX *s_lcd = nullptr;

// Buffer in SRAM (non PSRAM) — come esempio Elecrow; evita screen drift
static lv_disp_draw_buf_t s_draw_buf;
static lv_color_t s_buf1[SCREEN_WIDTH * SCREEN_HEIGHT / 15];
static lv_disp_drv_t s_disp_drv;
static lv_indev_drv_t s_indev_drv;

static void disp_flush(lv_disp_drv_t *disp, const lv_area_t *area, lv_color_t *color_p) {
  const uint32_t w = area->x2 - area->x1 + 1;
  const uint32_t h = area->y2 - area->y1 + 1;
  s_lcd->pushImageDMA(area->x1, area->y1, w, h, (lgfx::rgb565_t *)&color_p->full);
  lv_disp_flush_ready(disp);
}

static void touchpad_read(lv_indev_drv_t *indev, lv_indev_data_t *data) {
  (void)indev;
  if (touch_has_signal() && touch_touched()) {
    data->state = LV_INDEV_STATE_PR;
    data->point.x = touch_last_x;
    data->point.y = touch_last_y;
  } else {
    data->state = LV_INDEV_STATE_REL;
  }
}

static void lv_tick_cb(void *arg) {
  (void)arg;
  lv_tick_inc(1);
}

bool lvgl_port_init(LGFX &lcd) {
  s_lcd = &lcd;

  lv_init();

  lv_disp_draw_buf_init(&s_draw_buf, s_buf1, NULL,
                        SCREEN_WIDTH * SCREEN_HEIGHT / 15);

  lv_disp_drv_init(&s_disp_drv);
  s_disp_drv.hor_res = SCREEN_WIDTH;
  s_disp_drv.ver_res = SCREEN_HEIGHT;
  s_disp_drv.flush_cb = disp_flush;
  s_disp_drv.draw_buf = &s_draw_buf;
  lv_disp_drv_register(&s_disp_drv);

  lv_indev_drv_init(&s_indev_drv);
  s_indev_drv.type = LV_INDEV_TYPE_POINTER;
  s_indev_drv.read_cb = touchpad_read;
  lv_indev_drv_register(&s_indev_drv);

  const esp_timer_create_args_t tick_args = {
      .callback = &lv_tick_cb,
      .arg = nullptr,
      .dispatch_method = ESP_TIMER_TASK,
      .name = "lv_tick",
      .skip_unhandled_events = true,
  };
  esp_timer_handle_t tick_timer = nullptr;
  if (esp_timer_create(&tick_args, &tick_timer) == ESP_OK) {
    esp_timer_start_periodic(tick_timer, 1000);
  } else {
    Serial.println("[WARN] lv_tick timer failed");
  }

  Serial.println("[OK] LVGL ready");
  return true;
}

void lvgl_port_loop() {
  lv_timer_handler();
}
