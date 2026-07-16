#pragma once

// Forza lv_conf.h dello sketch prima di lvgl (evita silent-fail Arduino)
#include "lv_conf.h"
#define LV_CONF_SKIP

#include <lvgl.h>
#include "LovyanGFX_Driver.h"

bool lvgl_port_init(LGFX &lcd);
void lvgl_port_loop();
