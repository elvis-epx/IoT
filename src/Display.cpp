#include "stdio.h"
#ifndef UNDER_TEST
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#endif

#include "Display.h"
#include "Elements.h"
#include "Constants.h"
#include "Console.h"

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define SCREEN_ADDRESS 0x3C

#ifndef UNDER_TEST
static Adafruit_SSD1306 hw(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire);
#endif

Display::Display()
{
    row2_phase = 1;
    row3_phase = 1;
    next_update = Timeout(1 * SECONDS);
    next_row2_update = Timeout(5 * SECONDS);
    next_row3_update = Timeout(5 * SECONDS);

#ifndef UNDER_TEST
    ok = hw.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS);
    if (ok) {
        hw.setTextSize(1);
        hw.setTextColor(SSD1306_WHITE);
        hw.cp437(true);
    }
#else
    ok = true;
#endif

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

    if (!next_row2_update.pending()) {
        ++row2_phase;
        if (row2_phase > 3) {
            row2_phase = 1;
        }
    }

    if (!next_row3_update.pending()) {
        ++row3_phase;
        if (row3_phase > 4) {
            row3_phase = 1;
        }
    }

    char msg0[30];
    char msg1[30];
    char msg2[30];
    char msg3[30];
    char *msg[4];
    msg[0] = msg0; msg[1] = msg1; msg[2] = msg2; msg[3] = msg3;

    sprintf(msg[0], "%s", sm->cur_state_name());

    const char *err = levelmeter->failure_detected() ? "E " : "";
    sprintf(msg[1], "%s%.0f%% + %.0fL", err, levelmeter->level_pct(), flowmeter->volume());

    if (row2_phase == 1) {
        double rate = flowmeter->rate(FLOWRATE_LONG);
        if (rate >= 0) {
            sprintf(msg[2], "%.1fL/min x 30m", rate);
        } else {
            row2_phase = 2;
        }
    }
    if (row2_phase == 2) {
        double rate = flowmeter->rate(FLOWRATE_SHORT);
        if (rate >= 0) {
            sprintf(msg[2], "%.1fL/min x 2m", rate);
        } else {
            row2_phase = 3;
        }
    }
    if (row2_phase == 3) {
        double rate = flowmeter->rate(FLOWRATE_INSTANT);
        if (rate >= 0) {
            sprintf(msg[2], "%.1fL/min x 10s", rate);
        } else {
            sprintf(msg[2], "...");
        }
    }

    if (row3_phase == 1) {
        millis_to_hms(now(), msg[3]);
    }
    if (row3_phase == 2) {
        if (pump->is_running()) {
            double volume = flowmeter->volume();
            double exp_volume = flowmeter->expected_volume() + 0.0001;
            sprintf(msg[3], "Efficiency %.0f%%",
                    100 * volume / exp_volume);
        } else {
            row3_phase = 3;
        }
    }
    if (row3_phase == 3) {
        sprintf(msg[3], "WiFi %s", mqtt->wifi_status());
    }
    if (row3_phase == 4) {
        sprintf(msg[3], "MQTT %s", mqtt->mqtt_status());
    }

    show(msg);
}

void Display::show(char **msg)
{
#ifdef UNDER_TEST
    printf("\033[s");
    printf("\033[44m");
    printf("\033[97m");
    printf("\033[1;60H");
    printf("  %-20s  ", "");
    printf("\033[2;60H");
    printf("  %-20s  ", msg[0]);
    printf("\033[3;60H");
    printf("  %-20s  ", msg[1]);
    printf("\033[4;60H");
    printf("  %-20s  ", msg[2]);
    printf("\033[5;60H");
    printf("  %-20s  ", msg[3]);
    printf("\033[6;60H");
    printf("  %-20s  ", "");
    printf("\033[u");
    fflush(stdout);
#else
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
    console_print(msg[0]);
    console_print(" || ");
    console_print(msg[1]);
    console_print(" || ");
    console_print(msg[2]);
    console_print(" || ");
    console_println(msg[3]);
#endif
}
