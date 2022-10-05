#include <stdio.h>
#include "Adafruit_SSD1306.h"

Adafruit_SSD1306::Adafruit_SSD1306(int pw, int ph, class Wire*)
{
    for (int i = 0; i < ph / 16; ++i) {
        StrBuf line;
        line.reserve(pw / 4);
        data.push_back(line);
    }
    clearDisplay();
}

bool Adafruit_SSD1306::begin(int, int)
{
    clearDisplay();
    return true;
}

void Adafruit_SSD1306::setCursor(int pixel_x, int pixel_y)
{
    x = pixel_x / 4;
    y = pixel_y / 16;
}

void Adafruit_SSD1306::write(char c)
{
    data[y].hot_str()[x] = c;
    x += 1;
}

void Adafruit_SSD1306::clearDisplay()
{
    for (size_t i = 0; i < data.count(); ++i) {
        setCursor(0, i * 16);
        for (size_t j = 0; j < data[i].length(); ++j) {
            write(' ');
        }
    }
}

void Adafruit_SSD1306::setTextColor(int) {}
void Adafruit_SSD1306::setTextSize(int) {}
void Adafruit_SSD1306::cp437(bool) {}

void Adafruit_SSD1306::display()
{
    printf("\033[s");
    printf("\033[44m");
    printf("\033[97m");
    printf("\033[1;60H");
    printf("  %-20s  ", "");
    printf("\033[2;60H");
    printf("  %-20s  ", data[0].c_str());
    printf("\033[3;60H");
    printf("  %-20s  ", data[1].c_str());
    printf("\033[4;60H");
    printf("  %-20s  ", data[2].c_str());
    printf("\033[5;60H");
    printf("  %-20s  ", data[3].c_str());
    printf("\033[6;60H");
    printf("  %-20s  ", "");
    printf("\033[u");
    fflush(stdout);
}
