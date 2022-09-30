#include <iostream>
#include <fstream>
#include <map>
#include <string>
#include <string.h>
#include "Preferences.h"

// Emulation of Arduino ESP32 Preferences class

static std::map<std::string,std::string> nvram;
static bool initialized = false;

static void init()
{
    initialized = true;
    
    std::ifstream f;
    f.open("nvram.sim");
    if (f.is_open()) {
        char key[80];
        char value[80];
        while (f) {
            f.getline(key, 80);
            f.getline(value, 80);
            printf("\nNVRAM %s = %s\n", key, value);
            nvram[key] = value;
        }
        std::remove("nvram.sim");
    }
    f.close();
}

void Preferences::begin(const char*)
{
    if (! initialized) {
        init();
    }
}

void Preferences::begin(const char*, bool)
{
    if (! initialized) {
        init();
    }
}

void Preferences::end()
{
}

void Preferences::clear()
{
	nvram.clear();
}

size_t Preferences::getString(const char* key, char* value, size_t maxlen)
{
	if (nvram.find(key) == nvram.end() || maxlen == 0) {
		return 0;
	}

	const std::string bvalue = nvram[key];
	if (bvalue.empty()) {
		value[0] = 0;
		return 1;
	}

	size_t i = bvalue.length() + 1; // with \0
	if (i > maxlen) {
		i = maxlen;
	}
	memcpy(value, bvalue.c_str(), i);

	return i;
}

void Preferences::putString(const char* key, const char* value)
{
	nvram[key] = value;
}
