/*
 * LoRaMaDoR (LoRa-based mesh network for hams) project
 * Copyright (c) 2019 PU5EPX
 */

#ifndef UNDER_TEST
#include <Arduino.h>
#else
#include <stdio.h>
#endif
#include <stdlib.h>
#include "ArduinoBridge.h"
#include "NVRAM.h"
#include "CLI.h"
#include "Console.h"
#include "Elements.h"

#define cli_buf_cap 255
static char cli_buf[cli_buf_cap + 1];
static size_t cli_buf_len = 0;

// Wi-Fi network name (SSID) configuration
static void cli_parse_ssid(const char *candidate)
{
    if (strlen(candidate) > 64) {
        console_println("Maximum SSID length is 64.");
        return;
    }
    
    arduino_nvram_save("ssid", candidate);
    console_println("SSID saved, call !restart to apply");
}

static void cli_parse_ssid_empty()
{
    char *ssid = arduino_nvram_load("ssid");
    if (strcmp(ssid, "None") == 0) {
       console_println("Wi-Fi SSID is set to None.");
    } else {
        console_print("Wi-Fi SSID is '");
        console_print(ssid);
        console_println("'");
        console_println("Set SSID to None to disable Wi-Fi.");
    }
    free(ssid);
}

static void cli_parse_password(const char *candidate)
{
    if (strlen(candidate) > 64) {
        console_println("maximum password length is 64.");
        return;
    }
    
    arduino_nvram_save("password", candidate);
    console_println("Wi-Fi password saved, call !restart to apply");
}

static void cli_parse_password_empty()
{
    char *password = arduino_nvram_load("password");
    if (strcmp(password, "None") == 0) {
       console_println("Wi-Fi password is set to None.");
    } else {
        char tmp[40];
        sprintf(tmp, "Password has %d characters.", strlen(password));
        console_println("Wi-Fi password is set.");
        console_println(tmp);
        console_println("Set password to None for Wi-Fi network without password.");
    }
    free(password);
}

static void cli_parse_mqtt(const char *candidate)
{
    if (strlen(candidate) > 64) {
        console_println("Maximum MQTT broker length is 64.");
        return;
    }
    
    arduino_nvram_save("mqtt", candidate);
    console_println("MQTT broker saved, call !restart to apply");
}

static void cli_parse_mqttport(const char *candidate)
{
    int port = atoi(candidate);
    if (strcmp(candidate, "None") && (port <= 0 || port >= 65536)) {
        console_println("Invalid port number. Set a number 1..65535 or None");
        return;
    }
    
    arduino_nvram_save("mqttport", candidate);
    console_println("MQTT broker port saved, call !restart to apply");
}

static void cli_parse_mqtt_empty()
{
    char *mqtt = arduino_nvram_load("mqtt");
    if (strcmp(mqtt, "None") == 0) {
       console_println("MQTT broker is set to None.");
    } else {
        console_print("MQTT broker is '");
        console_print(mqtt);
        console_println("'");
        console_println("Set MQTT broker to None to disable MQTT service.");
    }
    free(mqtt);
}

static void cli_parse_mqttport_empty()
{
    char *mqttport = arduino_nvram_load("mqttport");
    if (strcmp(mqttport, "None") == 0) {
       console_println("MQTT broker port is None.");
    } else {
        console_print("MQTT broker port is '");
        console_print(mqttport);
        console_println("'");
    }
    free(mqttport);
}


// Print Wi-Fi status information
static void cli_status()
{
    console_println(mqtt->wifi_status());
    console_println(mqtt->mqtt_status());
}

static void cli_parse_help()
{
    console_println("Available commands:");
    console_println();
    console_println("!ssid [SSID]           Get/set Wi-Fi network (None to disable)");
    console_println("!password [PASSWORD]   Get/set Wi-Fi password (None if no password)");
    console_println("!mqtt [ADDRESS]        Get/set MQTT broker address (None to disable)");
    console_println("!mqttport [PORT]       Get/set MQTT broker port (None to disable)");
    console_println("!status                Show Wi-Fi/MQTT connection status");
    console_println("!defconfig             Reset all configurations saved in NVRAM");
    console_println("!restart               Restart controller");
    console_println();
}

// !command switchboard
static void cli_parse_meta()
{
    if (strncmp("!ssid ", cli_buf, 6) == 0 && strlen(cli_buf) >= 7) {
        cli_parse_ssid(cli_buf + 6);
    } else if (strncmp("!mqtt ", cli_buf, 6) == 0 && strlen(cli_buf) >= 7) {
        cli_parse_mqtt(cli_buf + 6);
    } else if (strncmp("!mqttport ", cli_buf, 10) == 0 && strlen(cli_buf) >= 11) {
        cli_parse_mqttport(cli_buf + 10);
    } else if (strncmp("!password ", cli_buf, 10) == 0 && strlen(cli_buf) >= 11) {
        cli_parse_password(cli_buf + 10);
    } else if (strcmp("!ssid", cli_buf) == 0) {
        cli_parse_ssid_empty();
    } else if (strcmp("!mqtt", cli_buf) == 0) {
        cli_parse_mqtt_empty();
    } else if (strcmp("!mqttport", cli_buf) == 0) {
        cli_parse_mqttport_empty();
    } else if (strcmp("!password", cli_buf) == 0) {
        cli_parse_password_empty();
    } else if (strcmp("!status", cli_buf) == 0) {
        cli_status();
    } else if (strcmp("!help", cli_buf) == 0) {
        cli_parse_help();
    } else if (strcmp("!restart", cli_buf) == 0) {
        console_println("Restarting...");
        arduino_restart();
    } else if (strcmp("!defconfig", cli_buf) == 0) {
        console_println("cleaning NVRAM...");
        arduino_nvram_clear_all();
        console_println("Call !restart to apply");
    } else {
        console_print("Unknown cmd: ");
        console_println(cli_buf);
    }
}

// Parse a command or packet typed in CLI
static void cli_parse()
{
    cli_parse_meta();
}

// ENTER pressed in CLI
static void cli_enter() {
    console_println();
    cli_parse();
    cli_buf_len = 0;
    cli_buf[0] = 0;
}

void cli_type(char c) {
    if (c == 13 || c == 10) {
        cli_enter();
    } else if (c == 8 || c == 127) {
        if (cli_buf_len > 0) {
            cli_buf[--cli_buf_len] = 0;
        }
        console_println();
        console_print(cli_buf);
    } else if (c < 32) {
        // ignore non-handled control chars
    } else if (cli_buf_len >= cli_buf_cap) {
        // full buffer
        return;
    } else {
        cli_buf[cli_buf_len++] = c;
        cli_buf[cli_buf_len] = 0;
        console_print(c);
    }
}
