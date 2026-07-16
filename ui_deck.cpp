#include "ui_deck.h"

#include <Arduino.h>
#include <string.h>

#include "actions.h"
#include "serial_proto.h"

// --- palette ---
static const uint32_t COL_BG = 0x0D0D0F;
static const uint32_t COL_SURFACE = 0x1A1A1F;
static const uint32_t COL_CUT = 0xC9A227;
static const uint32_t COL_DANGER = 0xE85D4C;
static const uint32_t COL_TRANSPORT = 0x2A4A6A;
static const uint32_t COL_OK = 0x4CAF50;
static const uint32_t COL_MUTED = 0x6B6B70;
static const uint32_t COL_TEXT = 0xF0F0F2;
static const uint32_t COL_BTN = 0x2A2A32;
static const uint32_t COL_TOOL = 0x3A3A42;
static const uint32_t COL_SAVE = 0x2A5A3A;
static const uint32_t COL_COLOR = 0x5A3A6A;

static lv_obj_t *s_lbl_status = nullptr;
static lv_obj_t *s_lbl_last = nullptr;
static lv_obj_t *s_lbl_play = nullptr;
static lv_obj_t *s_btn_play = nullptr;
static lv_obj_t *s_lbl_play_btn = nullptr;

enum TransportState : uint8_t { TR_STOP = 0, TR_PLAY = 1, TR_REV = 2 };
static TransportState s_transport = TR_STOP;
static uint32_t s_play_pulse_ms = 0;

static uint32_t s_last_cmd_ms = 0;
static uint32_t s_ack_until_ms = 0;
static const uint32_t kDebounceMs = 200;
static const uint32_t kAckFlashMs = 800;

static void set_status(const char *txt, uint32_t color) {
  if (!s_lbl_status) {
    return;
  }
  lv_label_set_text(s_lbl_status, txt);
  lv_obj_set_style_text_color(s_lbl_status, lv_color_hex(color), 0);
}

static void set_last(const char *action_id) {
  if (!s_lbl_last) {
    return;
  }
  char buf[48];
  snprintf(buf, sizeof(buf), "Last: %s", action_id);
  lv_label_set_text(s_lbl_last, buf);
}

static void refresh_transport_ui() {
  if (s_lbl_play) {
    if (s_transport == TR_PLAY) {
      lv_label_set_text(s_lbl_play, "PLAYING");
      lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(COL_OK), 0);
    } else if (s_transport == TR_REV) {
      lv_label_set_text(s_lbl_play, "REV");
      lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(0xFFAB40), 0);
    } else {
      lv_label_set_text(s_lbl_play, "STOP");
      lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(COL_MUTED), 0);
    }
  }

  if (s_btn_play && s_lbl_play_btn) {
    if (s_transport == TR_PLAY) {
      lv_obj_set_style_bg_color(s_btn_play, lv_color_hex(COL_OK), 0);
      lv_label_set_text(s_lbl_play_btn, "PAUSE");
    } else if (s_transport == TR_REV) {
      lv_obj_set_style_bg_color(s_btn_play, lv_color_hex(0xFFAB40), 0);
      lv_label_set_text(s_lbl_play_btn, "PLAY / PAUSE");
    } else {
      lv_obj_set_style_bg_color(s_btn_play, lv_color_hex(COL_TRANSPORT), 0);
      lv_label_set_text(s_lbl_play_btn, "PLAY / PAUSE");
    }
  }
}

static void note_transport_from_action(const char *action_id) {
  if (strcmp(action_id, ACTION_PLAY) == 0) {
    // Space toggles play/pause in Resolve
    if (s_transport == TR_STOP || s_transport == TR_REV) {
      s_transport = TR_PLAY;
    } else {
      s_transport = TR_STOP;
    }
  } else if (strcmp(action_id, ACTION_JK_STOP) == 0) {
    s_transport = TR_STOP;
  } else if (strcmp(action_id, ACTION_JK_FWD) == 0) {
    s_transport = TR_PLAY;
  } else if (strcmp(action_id, ACTION_JK_BACK) == 0) {
    s_transport = TR_REV;
  } else {
    return;
  }
  s_play_pulse_ms = millis();
  refresh_transport_ui();
}

static void fire_action(const char *action_id) {
  if (!action_id || !action_id[0]) {
    return;
  }

  const uint32_t now = millis();
  if (now - s_last_cmd_ms < kDebounceMs) {
    return;
  }

  s_last_cmd_ms = now;
  serial_proto_send_cmd(action_id);
  set_last(action_id);
  set_status("USB: CMD sent", 0xFFAB40);
  note_transport_from_action(action_id);
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
                          uint32_t bg, lv_coord_t w, lv_coord_t h) {
  lv_obj_t *btn = lv_btn_create(parent);
  lv_obj_set_size(btn, w, h);
  lv_obj_set_style_bg_color(btn, lv_color_hex(bg), 0);
  lv_obj_set_style_bg_color(btn, lv_color_lighten(lv_color_hex(bg), 30), LV_STATE_PRESSED);
  lv_obj_set_style_radius(btn, 8, 0);
  lv_obj_set_style_shadow_width(btn, 0, 0);
  lv_obj_add_event_cb(btn, on_action_btn, LV_EVENT_CLICKED, (void *)action_id);

  lv_obj_t *lbl = lv_label_create(btn);
  lv_label_set_text(lbl, label);
  lv_obj_set_style_text_font(lbl, &lv_font_montserrat_20, 0);
  lv_obj_set_style_text_color(lbl, lv_color_hex(COL_TEXT), 0);
  lv_obj_center(lbl);
  return btn;
}

static void style_tab_btns(lv_obj_t *tabview) {
  lv_obj_t *btns = lv_tabview_get_tab_btns(tabview);
  lv_obj_set_style_bg_color(btns, lv_color_hex(COL_SURFACE), 0);
  lv_obj_set_style_text_font(btns, &lv_font_montserrat_16, 0);
  lv_obj_set_style_text_color(btns, lv_color_hex(COL_MUTED), 0);
  lv_obj_set_style_text_color(btns, lv_color_hex(COL_TEXT), LV_PART_ITEMS | LV_STATE_CHECKED);
  lv_obj_set_style_bg_color(btns, lv_color_hex(COL_CUT), LV_PART_ITEMS | LV_STATE_CHECKED);
  lv_obj_set_style_border_width(btns, 0, 0);
}

static void build_tab_cut(lv_obj_t *tab) {
  lv_obj_set_style_bg_color(tab, lv_color_hex(COL_BG), 0);
  lv_obj_clear_flag(tab, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *b;
  b = make_btn(tab, "CUT", ACTION_CUT, COL_CUT, 752, 100);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 12);

  b = make_btn(tab, "UNDO", ACTION_UNDO, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 128);

  b = make_btn(tab, "REDO", ACTION_REDO, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 128);

  b = make_btn(tab, "RIPPLE DEL", ACTION_RIPPLE_DEL, COL_DANGER, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 128);

  b = make_btn(tab, "DEL", ACTION_DEL, COL_DANGER, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 216);

  b = make_btn(tab, "SPLIT", ACTION_SPLIT, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 216);

  b = make_btn(tab, "SAVE", ACTION_SAVE, COL_SAVE, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 216);
}

static void build_tab_transport(lv_obj_t *tab) {
  lv_obj_set_style_bg_color(tab, lv_color_hex(COL_BG), 0);
  lv_obj_clear_flag(tab, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *b;
  b = make_btn(tab, "J", ACTION_JK_BACK, COL_TRANSPORT, 240, 100);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 12);

  b = make_btn(tab, "K", ACTION_JK_STOP, COL_TRANSPORT, 240, 100);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 12);

  b = make_btn(tab, "L", ACTION_JK_FWD, COL_TRANSPORT, 240, 100);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 12);

  s_btn_play = make_btn(tab, "PLAY / PAUSE", ACTION_PLAY, COL_TRANSPORT, 752, 88);
  lv_obj_align(s_btn_play, LV_ALIGN_TOP_MID, 0, 128);
  s_lbl_play_btn = lv_obj_get_child(s_btn_play, 0);

  b = make_btn(tab, "FIT", ACTION_FIT, COL_BTN, 368, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 232);

  b = make_btn(tab, "SNAP", ACTION_SNAP, COL_BTN, 368, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 232);

  refresh_transport_ui();
}

static void build_tab_tools(lv_obj_t *tab) {
  lv_obj_set_style_bg_color(tab, lv_color_hex(COL_BG), 0);
  lv_obj_clear_flag(tab, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *b;
  b = make_btn(tab, "SELECT A", ACTION_SELECT_TOOL, COL_TOOL, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 12);

  b = make_btn(tab, "TRIM T", ACTION_TRIM_TOOL, COL_TOOL, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 12);

  b = make_btn(tab, "BLADE B", ACTION_BLADE_TOOL, COL_TOOL, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 12);

  b = make_btn(tab, "IN (I)", ACTION_MARK_IN, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 100);

  b = make_btn(tab, "OUT (O)", ACTION_MARK_OUT, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 100);

  b = make_btn(tab, "MARK +", ACTION_MARKER_ADD, COL_BTN, 240, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 100);

  b = make_btn(tab, "INSERT", ACTION_INSERT, COL_TRANSPORT, 180, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 188);

  b = make_btn(tab, "OVERWRITE", ACTION_OVERWRITE, COL_TRANSPORT, 180, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 208, 188);

  b = make_btn(tab, "REPLACE", ACTION_REPLACE, COL_TRANSPORT, 180, 72);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 400, 188);

  b = make_btn(tab, "M PREV", ACTION_MARKER_PREV, COL_TOOL, 90, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -108, 188);

  b = make_btn(tab, "M NEXT", ACTION_MARKER_NEXT, COL_TOOL, 90, 72);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 188);
}

static void build_tab_color(lv_obj_t *tab) {
  lv_obj_set_style_bg_color(tab, lv_color_hex(COL_BG), 0);
  lv_obj_clear_flag(tab, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *b;
  b = make_btn(tab, "→ COLOR PAGE", ACTION_PAGE_COLOR, COL_COLOR, 752, 64);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 8);

  b = make_btn(tab, "SERIAL +", ACTION_COLOR_ADD_SERIAL, COL_COLOR, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 88);

  b = make_btn(tab, "PARALLEL +", ACTION_COLOR_ADD_PARALLEL, COL_COLOR, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 88);

  b = make_btn(tab, "LAYER +", ACTION_COLOR_ADD_LAYER, COL_COLOR, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 88);

  b = make_btn(tab, "BYPASS NODE", ACTION_COLOR_BYPASS_NODE, COL_BTN, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_LEFT, 16, 184);

  b = make_btn(tab, "BYPASS ALL", ACTION_COLOR_BYPASS_ALL, COL_DANGER, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_MID, 0, 184);

  b = make_btn(tab, "RESET NODE", ACTION_COLOR_RESET_NODE, COL_BTN, 240, 80);
  lv_obj_align(b, LV_ALIGN_TOP_RIGHT, -16, 184);
}

static void build_tab_pages(lv_obj_t *tab) {
  lv_obj_set_style_bg_color(tab, lv_color_hex(COL_BG), 0);
  lv_obj_clear_flag(tab, LV_OBJ_FLAG_SCROLLABLE);

  struct PageBtn {
    const char *label;
    const char *id;
  };
  static const PageBtn pages[] = {
      {"MEDIA", ACTION_PAGE_MEDIA},     {"CUT", ACTION_PAGE_CUT},
      {"EDIT", ACTION_PAGE_EDIT},       {"FUSION", ACTION_PAGE_FUSION},
      {"COLOR", ACTION_PAGE_COLOR},     {"FAIRLIGHT", ACTION_PAGE_FAIRLIGHT},
      {"DELIVER", ACTION_PAGE_DELIVER},
  };

  const lv_coord_t w = 180;
  const lv_coord_t h = 72;
  const lv_coord_t gap = 12;
  const lv_coord_t x0 = 16;
  const lv_coord_t y0 = 16;

  for (unsigned i = 0; i < sizeof(pages) / sizeof(pages[0]); i++) {
    const unsigned col = i % 4;
    const unsigned row = i / 4;
    lv_obj_t *b = make_btn(tab, pages[i].label, pages[i].id, COL_BTN, w, h);
    lv_obj_set_pos(b, x0 + (lv_coord_t)col * (w + gap), y0 + (lv_coord_t)row * (h + gap));
  }
}

static void build_header(lv_obj_t *parent) {
  lv_obj_t *hdr = lv_obj_create(parent);
  lv_obj_set_size(hdr, 800, 56);
  lv_obj_align(hdr, LV_ALIGN_TOP_MID, 0, 0);
  lv_obj_set_style_bg_color(hdr, lv_color_hex(COL_SURFACE), 0);
  lv_obj_set_style_border_width(hdr, 0, 0);
  lv_obj_set_style_radius(hdr, 0, 0);
  lv_obj_set_style_pad_all(hdr, 0, 0);
  lv_obj_clear_flag(hdr, LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t *title = lv_label_create(hdr);
  lv_label_set_text(title, "DaVinci");
  lv_obj_set_style_text_color(title, lv_color_hex(COL_TEXT), 0);
  lv_obj_set_style_text_font(title, &lv_font_montserrat_22, 0);
  lv_obj_align(title, LV_ALIGN_LEFT_MID, 16, 0);

  s_lbl_last = lv_label_create(hdr);
  lv_label_set_text(s_lbl_last, "Last: —");
  lv_obj_set_style_text_color(s_lbl_last, lv_color_hex(COL_MUTED), 0);
  lv_obj_set_style_text_font(s_lbl_last, &lv_font_montserrat_14, 0);
  lv_obj_align(s_lbl_last, LV_ALIGN_LEFT_MID, 140, 0);

  s_lbl_play = lv_label_create(hdr);
  lv_label_set_text(s_lbl_play, "STOP");
  lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(COL_MUTED), 0);
  lv_obj_set_style_text_font(s_lbl_play, &lv_font_montserrat_16, 0);
  lv_obj_align(s_lbl_play, LV_ALIGN_LEFT_MID, 280, 0);

  s_lbl_status = lv_label_create(hdr);
  lv_label_set_text(s_lbl_status, "USB: waiting");
  lv_obj_set_style_text_color(s_lbl_status, lv_color_hex(0xFFAB40), 0);
  lv_obj_set_style_text_font(s_lbl_status, &lv_font_montserrat_14, 0);
  lv_obj_align(s_lbl_status, LV_ALIGN_RIGHT_MID, -100, 0);

  lv_obj_t *ping = make_btn(hdr, "PING", ACTION_PING, 0x3A2A2A, 72, 40);
  lv_obj_align(ping, LV_ALIGN_RIGHT_MID, -8, 0);
}

void ui_deck_create() {
  lv_obj_t *scr = lv_scr_act();
  lv_obj_set_style_bg_color(scr, lv_color_hex(COL_BG), 0);
  lv_obj_set_style_bg_opa(scr, LV_OPA_COVER, 0);
  lv_obj_clear_flag(scr, LV_OBJ_FLAG_SCROLLABLE);

  build_header(scr);

  // Header 56 + tabview 424
  lv_obj_t *tv = lv_tabview_create(scr, LV_DIR_BOTTOM, 64);
  lv_obj_set_size(tv, 800, 424);
  lv_obj_align(tv, LV_ALIGN_BOTTOM_MID, 0, 0);
  lv_obj_set_style_bg_color(tv, lv_color_hex(COL_BG), 0);

  style_tab_btns(tv);

  lv_obj_t *tab_cut = lv_tabview_add_tab(tv, "CUT");
  lv_obj_t *tab_play = lv_tabview_add_tab(tv, "PLAY");
  lv_obj_t *tab_tools = lv_tabview_add_tab(tv, "TOOLS");
  lv_obj_t *tab_color = lv_tabview_add_tab(tv, "COL");
  lv_obj_t *tab_pages = lv_tabview_add_tab(tv, "PAGE");

  build_tab_cut(tab_cut);
  build_tab_transport(tab_play);
  build_tab_tools(tab_tools);
  build_tab_color(tab_color);
  build_tab_pages(tab_pages);
}

void ui_deck_on_host_line(const char *line) {
  if (!line) {
    return;
  }
  if (strncmp(line, "INFO:", 5) == 0) {
    return;  // ignored (live status removed)
  }
  if (strncmp(line, "ACK:", 4) == 0) {
    set_status(line, COL_OK);
    s_ack_until_ms = millis() + kAckFlashMs;
  } else if (strncmp(line, "ERR:", 4) == 0) {
    set_status(line, COL_DANGER);
    s_ack_until_ms = 0;
  } else if (strncmp(line, "STAT:", 5) == 0) {
    if (strcmp(line, "STAT:BRIDGE_OFF") == 0) {
      set_status("USB: bridge OFF", COL_DANGER);
      s_ack_until_ms = 0;
      return;
    }
    if (strcmp(line, "STAT:BRIDGE_ONLINE") == 0) {
      set_status("USB: ready", COL_OK);
      return;
    }
    set_status(line, 0xFFAB40);
  }
}

void ui_deck_loop() {
  if (s_ack_until_ms != 0 && (int32_t)(millis() - s_ack_until_ms) >= 0) {
    s_ack_until_ms = 0;
    set_status("USB: ready", COL_MUTED);
  }

  // Soft pulse on PLAYING / REV badge
  if (s_lbl_play && s_transport != TR_STOP) {
    const uint32_t phase = (millis() - s_play_pulse_ms) % 1000;
    const bool dim = phase > 500;
    if (s_transport == TR_PLAY) {
      lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(dim ? 0x2E7D32 : COL_OK), 0);
    } else {
      lv_obj_set_style_text_color(s_lbl_play, lv_color_hex(dim ? 0x8D6E00 : 0xFFAB40), 0);
    }
  }
}
