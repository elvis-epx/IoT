#include "MyGPIO.h"
#include "Elements.h"
#include "Constants.h"
#include "ArduinoBridge.h"
#ifdef UNDER_TEST
#define IRAM_ATTR
#endif
#include <MCP23017.h>

#define MCP23017_ADDR 0x20

MCP23017 mcp = MCP23017(MCP23017_ADDR);

static void IRAM_ATTR pulse_trampoline()
{
    gpio->pulse();
}

// About inverse pump logic bit. The 3V3 relay we use
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

    i2c_begin();
    mcp.init();

    // Port A = all output
    mcp.portMode(MCP23017Port::A, 0);
    mcp.writeRegister(MCP23017Register::GPIO_A, 0);
    // Port B = all input
    mcp.portMode(MCP23017Port::B, 0b11111111);
    mcp.writeRegister(MCP23017Register::GPIO_B, 0);
    // flow meter
    arduino_pinmode(FLOWMETER_PIN, INPUT_PULLUP);
#ifndef UNDER_TEST
    attachInterrupt(digitalPinToInterrupt(FLOWMETER_PIN), pulse_trampoline, RISING);
#else
    mcp.sim_pulse_cb = pulse_trampoline;
#endif
}

uint32_t MyGPIO::read_level_sensors()
{
    return read() & LEVEL_SENSOR_MASK;
}

uint32_t MyGPIO::read()
{
    uint32_t bitmap = 0;
    bitmap = mcp.readPort(MCP23017Port::B);
    return bitmap;
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
    mcp.sim_pulses();
#endif
    if (pulses > 0) {
        flowmeter->pulse(pulses);
        pulses = 0;
    }
}
