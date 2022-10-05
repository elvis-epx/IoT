#ifndef __MCP23017_H
#define __MCP23017_H

class MCP23017Port {
public:
    static const int A = 0;
    static const int B = 1;
};

class MCP23017Register {
public:
    static const int GPIO_A = 0;
    static const int GPIO_B = 1;
};

class MCP23017 {
public:
    MCP23017(int addr);
    void init();
    void portMode(int, int);
    void writeRegister(int, int);
    uint32_t readPort(int);
    void writePort(int, uint32_t);

    void sim_pulses();
    void (*sim_pulse_cb)();
};

#endif
