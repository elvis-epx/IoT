#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <sys/types.h>
#include <string>
#include <iostream>
#include <fstream>

#include "Serial.h"

SerialClass Serial;

static std::string readbuf;

void SerialClass::begin(int baud)
{
}

int SerialClass::available()
{
	return readbuf.length();
}	

int SerialClass::availableForWrite()
{
	return random() % 512;
}	

char SerialClass::read()
{
	char c = 0;
	if (!readbuf.empty()) {
		c = readbuf.at(0);
		readbuf.erase(0, 1);
	}
	return c;
}

void SerialClass::write(const uint8_t *data, int len)
{
	char *tmp = (char*) calloc(1, len + 1);
	memcpy(tmp, data, len);
	printf("%s", tmp);
	free(tmp);
}

void SerialClass::println(const char* data)
{
    write((const uint8_t*) data, strlen(data));
    write((const uint8_t*) "\n", 1);
}

void SerialClass::eval()
{
    // simulate receiving serial data
    std::ifstream f;
    f.open("serial.sim");
    if (f.is_open()) {
        std::string line;
        while (f) {
            std::getline(f, line);
            if (! line.empty()) {
                readbuf += line;
                readbuf += "\n";
            }
        }
        std::remove("serial.sim");
    }
    f.close();
}
