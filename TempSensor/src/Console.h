/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __CONSOLE_H
#define __CONSOLE_H

void console_setup();
void console_eval();
void console_print(const char *);
void console_print(char);
void console_println(const char *);
void console_println();

#endif
