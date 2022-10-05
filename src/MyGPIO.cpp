#include "MyGPIO.h"
#include "Elements.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else

#include <Arduino.h>
#include <MCP23017.h>

#define MCP23017_ADDR 0x20

MCP23017 mcp = MCP23017(MCP23017_ADDR);

static void IRAM_ATTR pulse_trampoline()
{
    gpio->pulse();
}

#endif

#define FLOWMETER_PIN 14

// note: inverted pump logic bit. This is because the 3V3 relay we use
// is like that - turns ON when input is grounded. So we need to raise
// the pin to 1 to turn it OFF. We had two options:
//
// a) use the NC (Normally Closed) contacts of relay, which would be opened
// as soon as the controller + I/O multiplexer are turned on (the initial
// state of I/O multiplexer pins is 0).
// b) use the NO (Normally Open) contacts of relay, set the relay control
// signal to 1 as soon as possible at startup
//
// We prefer the solution (b) so the controller falls back to "Off" when
// turned off. The potential disavantage is a brief Off-On-Off commutation
// at startup, but we took care to make it fast so the relay won't switch
// (only the LED indicator blinks briefly).

static const uint32_t PUMP_BIT = 0x01;

MyGPIO::MyGPIO()
{
    pulses = 0;
    // note: inverted pump logic bit
    output_bitmap = 0 | PUMP_BIT;

#ifndef UNDER_TEST
    i2c_begin();
    mcp.init();

    // high bits = input. Third parameter is pullup and all-1 by default
    mcp.portMode(MCP23017Port::A, 0);
    mcp.writeRegister(MCP23017Register::GPIO_A, 0 | PUMP_BIT); // reset
    mcp.portMode(MCP23017Port::B, 0b11111111);
    mcp.writeRegister(MCP23017Register::GPIO_B, 0); // reset
    // flow meter
    pinMode(FLOWMETER_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(FLOWMETER_PIN), pulse_trampoline, RISING);
#endif
    write_output(output_bitmap, ~0);
}

uint32_t MyGPIO::read_level_sensors()
{
    return read() & 0b11111;
}

uint32_t MyGPIO::read()
{
    uint32_t bitmap = 0;
#ifdef UNDER_TEST
    std::ifstream f;
    f.open("gpio.sim");
    f >> bitmap;
    f.close();
#else
    bitmap = mcp.readPort(MCP23017Port::B);
#endif
    return bitmap;
}

void MyGPIO::write_pump(bool state)
{
    // note: inverted pump logic bit
    write_output(state ? 0 : ~0, PUMP_BIT);
}

void MyGPIO::write_output(uint32_t bitmap, uint32_t bitmask)
{
    output_bitmap = (output_bitmap & ~bitmask) | (bitmap & bitmask);
#ifdef UNDER_TEST
    std::ofstream f;
    f.open("gpio2.sim");
    f << output_bitmap;
    f.close();
#else
    mcp.writePort(MCP23017Port::A, output_bitmap);
#endif
}

void MyGPIO::pulse()
{
    // Flow meter pulse
    // do as little as possible, since it may be called
    // by an interrupt handler
    ++pulses;
}

void MyGPIO::eval()
{
#ifdef UNDER_TEST
    int qty = 0;
    std::ifstream f;
    f.open("pulses.sim");
    if (f.is_open()) {
        f >> qty;
        std::remove("pulses.sim");
    }
    f.close();
    while (qty-- > 0) {
        pulse();
    }
#endif
    if (pulses > 0) {
        flowmeter->pulse(pulses);
        pulses = 0;
    }
}
