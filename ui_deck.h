#pragma once

#include "lv_conf.h"
#define LV_CONF_SKIP
#include <lvgl.h>

void ui_deck_create();
void ui_deck_on_host_line(const char *line);
void ui_deck_loop();  // ACK flash timeout
