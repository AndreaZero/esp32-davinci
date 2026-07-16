#pragma once

#include <Arduino.h>

void serial_proto_begin(uint32_t baud = 115200);
void serial_proto_send_cmd(const char *action_id);
void serial_proto_loop();  // host → device lines (ACK/ERR/STAT/INFO)

using SerialProtoStatusCb = void (*)(const char *line);
void serial_proto_set_status_cb(SerialProtoStatusCb cb);
