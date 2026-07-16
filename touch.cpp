/*******************************************************************************
 * GT911 + PCA9557 V3.0 — CrowPanel 7"
 *
 * Reset touch solo via PCA9557 (wiki Elecrow).
 * Lettura GT911 in I2C puro — evita TAMC_GT911::begin()/reset() con INT/RST=-1
 * che causa: gpio_set_level(226) GPIO output gpio_num error.
 ******************************************************************************/

#include "touch.h"

#include <Wire.h>

#include "config.h"
#include "LovyanGFX_Driver.h"

extern LGFX lcd;

// GT911 su questa board riporta già coordinate display (0,0 = top-left).
// La map invertita Elecrow (800→0 / 480→0) sposta l'hitbox in alto sul bottone.
#define TOUCH_MAP_X1 0
#define TOUCH_MAP_X2 800
#define TOUCH_MAP_Y1 0
#define TOUCH_MAP_Y2 480

#define PCA9557_ADDR       0x19
#define PCA9557_REG_OUTPUT 0x01
#define PCA9557_REG_CONFIG 0x03

#define GT911_ADDR_5D      0x5D
#define GT911_ADDR_14      0x14
#define GT911_REG_PRODUCT  0x8140
#define GT911_REG_STATUS   0x814E
#define GT911_REG_POINT1   0x814F

int touch_last_x = 0;
int touch_last_y = 0;

static uint8_t s_gt_addr = 0;

static void pca9557_write(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(PCA9557_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static uint8_t pca9557_read(uint8_t reg) {
  Wire.beginTransmission(PCA9557_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)PCA9557_ADDR, (uint8_t)1);
  if (Wire.available()) {
    return Wire.read();
  }
  return 0xFF;
}

static bool pca9557_v3_touch_timing() {
  Wire.beginTransmission(PCA9557_ADDR);
  if (Wire.endTransmission() != 0) {
    Serial.println("[WARN] PCA9557 @0x19 assente — skip V3 timing");
    return false;
  }

  pca9557_write(PCA9557_REG_CONFIG, 0xFF);
  delay(10);

  uint8_t cfg = pca9557_read(PCA9557_REG_CONFIG);
  cfg &= ~0x03;  // IO0, IO1 output
  pca9557_write(PCA9557_REG_CONFIG, cfg);

  uint8_t out = pca9557_read(PCA9557_REG_OUTPUT);
  out &= ~0x03;  // IO0 LOW, IO1 LOW
  pca9557_write(PCA9557_REG_OUTPUT, out);
  delay(20);

  out |= 0x01;  // IO0 HIGH (power)
  pca9557_write(PCA9557_REG_OUTPUT, out);
  delay(100);

  cfg = pca9557_read(PCA9557_REG_CONFIG);
  cfg |= 0x02;  // IO1 INPUT (release reset)
  pca9557_write(PCA9557_REG_CONFIG, cfg);

  Serial.println("[OK] PCA9557 V3 touch timing");
  return true;
}

static bool gt911_write8(uint16_t reg, uint8_t val) {
  Wire.beginTransmission(s_gt_addr);
  Wire.write((uint8_t)(reg >> 8));
  Wire.write((uint8_t)(reg & 0xFF));
  Wire.write(val);
  return Wire.endTransmission() == 0;
}

static bool gt911_read_block(uint16_t reg, uint8_t *buf, uint8_t len) {
  Wire.beginTransmission(s_gt_addr);
  Wire.write((uint8_t)(reg >> 8));
  Wire.write((uint8_t)(reg & 0xFF));
  if (Wire.endTransmission(false) != 0) {
    return false;
  }
  uint8_t n = Wire.requestFrom((uint8_t)s_gt_addr, len);
  if (n != len) {
    return false;
  }
  for (uint8_t i = 0; i < len; i++) {
    buf[i] = Wire.read();
  }
  return true;
}

static bool gt911_probe(uint8_t addr) {
  s_gt_addr = addr;
  uint8_t id[4] = {0};
  if (!gt911_read_block(GT911_REG_PRODUCT, id, 4)) {
    return false;
  }
  // Product ID tipico "911" ASCII
  if (id[0] == '9' && id[1] == '1' && id[2] == '1') {
    return true;
  }
  // Alcuni chip rispondono comunque con dati validi
  return (id[0] != 0x00 && id[0] != 0xFF);
}

static bool gt911_find() {
  if (gt911_probe(GT911_ADDR_5D)) {
    Serial.println("[OK] GT911 @0x5D");
    return true;
  }
  if (gt911_probe(GT911_ADDR_14)) {
    Serial.println("[OK] GT911 @0x14");
    return true;
  }
  Serial.println("[ERR] GT911 non trovato (0x5D/0x14)");
  s_gt_addr = 0;
  return false;
}

void touch_init() {
  Wire.begin(TOUCH_SDA, TOUCH_SCL);
  Wire.setClock(400000);

  pca9557_v3_touch_timing();
  delay(50);

  if (!gt911_find()) {
    // Retry dopo altro delay (power rail)
    delay(200);
    gt911_find();
  }
}

bool touch_has_signal() {
  return s_gt_addr != 0;
}

bool touch_touched() {
  if (s_gt_addr == 0) {
    return false;
  }

  uint8_t status = 0;
  if (!gt911_read_block(GT911_REG_STATUS, &status, 1)) {
    return false;
  }

  uint8_t n = status & 0x0F;
  if (n == 0 || n > 5) {
    if (status & 0x80) {
      gt911_write8(GT911_REG_STATUS, 0);
    }
    return false;
  }

  uint8_t pt[8] = {0};
  if (!gt911_read_block(GT911_REG_POINT1, pt, 8)) {
    return false;
  }

  // Clear buffer ready flag
  gt911_write8(GT911_REG_STATUS, 0);

  uint16_t raw_x = (uint16_t)pt[1] | ((uint16_t)pt[2] << 8);
  uint16_t raw_y = (uint16_t)pt[3] | ((uint16_t)pt[4] << 8);

  touch_last_x = map((int)raw_x, TOUCH_MAP_X1, TOUCH_MAP_X2, 0, (int)lcd.width() - 1);
  touch_last_y = map((int)raw_y, TOUCH_MAP_Y1, TOUCH_MAP_Y2, 0, (int)lcd.height() - 1);

  if (touch_last_x < 0) touch_last_x = 0;
  if (touch_last_y < 0) touch_last_y = 0;
  if (touch_last_x >= (int)lcd.width()) touch_last_x = lcd.width() - 1;
  if (touch_last_y >= (int)lcd.height()) touch_last_y = lcd.height() - 1;

  return true;
}

bool touch_released() {
  return true;
}
