#include <iostream>
#include <fstream>
#include "MCP23017.h"

MCP23017::MCP23017(int addr) {}
void MCP23017::init() {}
void MCP23017::portMode(int, int) {}
void MCP23017::writeRegister(int, int) {}

uint32_t MCP23017::readPort(int)
{
    uint32_t bitmap = 0;
    std::ifstream f;
    f.open("gpiomcpr.sim");
    f >> bitmap;
    f.close();
    return bitmap;
}

void MCP23017::writePort(int, uint32_t output_bitmap)
{
    std::ofstream f;
    f.open("gpiomcpw.sim");
    f << output_bitmap;
    f.close();
}

void MCP23017::sim_pulses()
{
    int qty = 0;
    std::ifstream f;
    f.open("pulses.sim");
    if (f.is_open()) {
        f >> qty;
        std::remove("pulses.sim");
    }
    f.close();
    while (qty-- > 0) {
        sim_pulse_cb();
    }
}
