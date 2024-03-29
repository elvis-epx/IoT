#include "stdio.h"
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#include "Display.h"
#include "Elements.h"
#include "Constants.h"
#include "Console.h"

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C

static Adafruit_SSD1306 hw(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire);

Display::Display()
{
    row3_phase = 1;
    next_update = Timeout(1 * SECONDS);
    next_row3_update = Timeout(2 * SECONDS);

    ok = hw.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS);
    if (ok) {
        hw.setTextSize(1);
        hw.setTextColor(SSD1306_WHITE);
        hw.cp437(true);
    }

    const char *msg[] = {"", "", "", ""};
    show((char**) msg);
}

void Display::millis_to_hms(int64_t t, char *target)
{
    if (t < 0) {
        sprintf(target, "...");
        return;
    }
    t /= 1000;
    int32_t s = t % 60;
    t -= s;
    t /= 60;
    int32_t m = t % 60;
    t -= m;
    t /= 60;
    int32_t h = t % 24;
    t -= h;
    t /= 24;
    int32_t d = t;

    if (d > 0) {
        sprintf(target, "Uptime %d:%02d:%02d:%02d", d, h, m, s);
    } else if (h > 0) {
        sprintf(target, "Uptime %d:%02d:%02d", h, m, s);
    } else {
        sprintf(target, "Uptime %d:%02d", m, s);
    }
}

void Display::eval()
{
    if (next_update.pending()) {
        return;
    }

    if (!next_row3_update.pending()) {
        ++row3_phase;
        if (row3_phase > 2) {
            row3_phase = 1;
        }
    }

    char msg0[30];
    char msg1[30];
    char msg2[30];
    char msg3[30];
    char *msg[4];
    msg[0] = msg0; msg[1] = msg1; msg[2] = msg2; msg[3] = msg3;

    const char *err = levelmeter->failure_detected() ? "E " : "";
    sprintf(msg[0], "%s%.0f%% + %.0f" VOL_UNIT, err, levelmeter->level_pct(), flowmeter->volume());

    double rate = flowmeter->rate();
    sprintf(msg[1], "%.1f" VOL_UNIT "/min", rate);

    millis_to_hms(now(), msg[2]);
    
    if (row3_phase == 1) {
        sprintf(msg[3], "WiFi %s", mqtt->wifi_status());
    } else {
        sprintf(msg[3], "MQTT %s", mqtt->mqtt_status());
    }

    show(msg);
}

void Display::show(char **msg)
{
    if (ok) {
        hw.clearDisplay();
        hw.setCursor(0, 0 + 4);
        for (int i = 0; msg[0][i]; ++i) {
            hw.write(msg[0][i]);
        }
        hw.setCursor(0, 16 + 4);
        for (int i = 0; msg[1][i]; ++i) {
            hw.write(msg[1][i]);
        }
        hw.setCursor(0, 32 + 4);
        for (int i = 0; msg[2][i]; ++i) {
            hw.write(msg[2][i]);
        }
        hw.setCursor(0, 48 + 4);
        for (int i = 0; msg[3][i]; ++i) {
            hw.write(msg[3][i]);
        }
        hw.display();
    }

    /*
    console_print(msg[0]);
    console_print(" || ");
    console_print(msg[1]);
    console_print(" || ");
    console_print(msg[2]);
    console_print(" || ");
    console_println(msg[3]);
    */
}
