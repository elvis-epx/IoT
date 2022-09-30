/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __NVRAM_H
#define __NVRAM_H

void arduino_nvram_clear_all();
char *arduino_nvram_load(const char*);
void arduino_nvram_save(const char*, const char *);

#endif
