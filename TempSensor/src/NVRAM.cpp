/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2020 PU5EPX
 */

#include <stdlib.h>
#ifdef UNDER_TEST
#include <string.h>
#endif
#include <Preferences.h>
#include "NVRAM.h"
#include "Constants.h"

extern Preferences prefs;

static const char* chapter = NVRAM_CHAPTER;

void arduino_nvram_clear_all()
{
    prefs.begin(chapter, false);
    prefs.clear();
    prefs.end();
}

void arduino_nvram_save(const char *key, const char *value)
{
    prefs.begin(chapter, false);
    prefs.putString(key, value);
    prefs.end();
}

void arduino_nvram_load(StrBuf& candidate, const char *key)
{
    candidate.reserve(65);
    prefs.begin(chapter);
    // len includes \0
    size_t len = prefs.getString(key, candidate.hot_str(), 65);
    prefs.end();

    if (len <= 1) {
        candidate.update("None");
    }
}
