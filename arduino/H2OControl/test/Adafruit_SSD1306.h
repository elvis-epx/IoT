#ifndef _ADAFRUIT_SSD1306_H
#define _ADAFRUIT_SSD1306_H

#define SSD1306_SWITCHCAPVCC 0
#define SSD1306_WHITE 0

#include <Vector.h>
#include <StrBuf.h>

class Adafruit_SSD1306 {
public:
    Adafruit_SSD1306(int, int, class Wire*);
    bool begin(int, int);
    void setCursor(int, int);
    void write(char);
    void clearDisplay();
    void display();
    void setTextColor(int);
    void setTextSize(int);
    void cp437(bool);
private:
    int x, y;
    Vector<StrBuf> data;
};

#endif
