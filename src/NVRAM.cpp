/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2020 PU5EPX
 */

#include <stdlib.h>
#include "NVRAM.h"
#ifdef UNDER_TEST
#include <string.h>
#include "Preferences.h"
#else
#include <Preferences.h>
#endif

extern Preferences prefs;

static const char* chapter = "H2OControl";

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

char *arduino_nvram_load(const char *key)
{
	char *candidate = (char*) calloc(sizeof(char), 65);
	prefs.begin(chapter);
	// len includes \0
	size_t len = prefs.getString(key, candidate, 65);
	prefs.end();

	if (len <= 1) {
		strcpy(candidate, "None");
	}
	return candidate;
}
