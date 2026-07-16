#include "serial_proto.h"

static SerialProtoStatusCb s_status_cb = nullptr;
static char s_rx_line[128];
static size_t s_rx_len = 0;

void serial_proto_set_status_cb(SerialProtoStatusCb cb) {
  s_status_cb = cb;
}

void serial_proto_begin(uint32_t baud) {
  Serial.begin(baud);
  delay(200);
  Serial.println();
  Serial.println("STAT:READY");
}

void serial_proto_send_cmd(const char *action_id) {
  if (!action_id || !action_id[0]) {
    return;
  }
  Serial.print("CMD:");
  Serial.println(action_id);
}

static void handle_rx_line(const char *line) {
  if (!line || !line[0]) {
    return;
  }
  if (strncmp(line, "ACK:", 4) == 0 || strncmp(line, "ERR:", 4) == 0 ||
      strncmp(line, "STAT:", 5) == 0) {
    if (s_status_cb) {
      s_status_cb(line);
    }
  }
}

void serial_proto_loop() {
  while (Serial.available() > 0) {
    const char c = (char)Serial.read();
    if (c == '\r') {
      continue;
    }
    if (c == '\n') {
      s_rx_line[s_rx_len] = '\0';
      handle_rx_line(s_rx_line);
      s_rx_len = 0;
      continue;
    }
    if (s_rx_len + 1 < sizeof(s_rx_line)) {
      s_rx_line[s_rx_len++] = c;
    } else {
      s_rx_len = 0;
    }
  }
}
