/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef __TIMESTAMP_H
#define __TIMESTAMP_H

#include "stdint.h"

typedef int64_t Timestamp;

Timestamp now();
#define SECONDS 1000
#define MINUTES 60000

#endif
