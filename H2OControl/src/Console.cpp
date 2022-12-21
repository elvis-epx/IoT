/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifdef UNDER_TEST
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include "Serial.h"
#else
#include <Arduino.h>
#endif
#include "CLI.h"
#include "Console.h"

static size_t ring_len = 0;
static size_t ring_pos = 0;
#define ring_cap 512
static char ring_buf[ring_cap];

void console_setup()
{
    Serial.begin(115200);
    Serial.println("Setup");
}

void console_eval()
{
#ifdef UNDER_TEST
    Serial.eval();
#endif
    if (Serial.available() > 0) {
        int c = Serial.read();
        cli_type(c);
    }

    size_t max_write = Serial.availableForWrite();
    size_t to_write = (ring_len > max_write) ? max_write : ring_len; 
    if (! to_write) {
        return;
    }
    
    if ((ring_pos + to_write) >= ring_cap) {
        to_write = ring_cap - ring_pos;
    }
    Serial.write((const uint8_t*) ring_buf + ring_pos, to_write);
    ring_len -= to_write;
    ring_pos += to_write;
    ring_pos = ring_pos % ring_cap;
}

void serial_print(const char *msg)
{
    size_t j = strlen(msg);
    for (size_t i = 0; i < j && ring_len < ring_cap; ++i) {
        ring_buf[(ring_pos + ring_len) % ring_cap] = msg[i];
        ring_len += 1;
    }
}

static void platform_print(const char *msg)
{
    serial_print(msg);
}

void console_print(const char *msg) {
    platform_print(msg);
}

void console_print(char c) {
    char msg[] = {c, 0};
    platform_print(msg);
}

void console_println(const char *msg) {
    platform_print(msg);
    platform_print("\r\n");
}

void console_println() {
    platform_print("\r\n");
}
