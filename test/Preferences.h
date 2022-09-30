#ifndef __PREFERENCES_H
#define __PREFERENCES_H

#include <cstdint>

struct Preferences {
	static void begin(const char*);
	static void begin(const char*, bool);
	static void end();
	static size_t getString(const char*, char*, size_t);
	static void putString(const char*, const char*);
	static void clear();
};

#endif // __PREFERENCES_H
