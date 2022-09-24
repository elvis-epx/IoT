#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"
#include "LogDebug.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else

#ifdef ESP8266
#include <ESP8266WiFi.h>
#else
#include <WiFi.h>
#endif
#include <PubSubClient.h>
#include "Credentials.h"

WiFiClient wifi;
PubSubClient mqttimpl(wifi);
static const char *mqtt_id = "H2OControl";

#endif

#define TOP "stat/H2OControl/"
#define TOP_CMND "cmnd/H2OControl/"
#define LOGDEBUG_TOPIC "tele/H2OControl/logdebug"

static const char *sub_onswitch = TOP_CMND "OverrideOn";
static const char *sub_offswitch = TOP_CMND "OverrideOff";

static const char* pub_topics[] = {
			TOP "State", TOP "Level1", TOP "LevelErr", TOP "Level2",
			TOP "FlowInst", TOP "FlowShort", TOP "FlowLong",
			TOP "Uptime", TOP "Efficiency",
			0};

static const int TOPIC_STATE = 0;
static const int TOPIC_LEVEL1 = 1;
static const int TOPIC_LEVELERR = 2;
static const int TOPIC_LEVEL2 = 3;
static const int TOPIC_FLOWI = 4;
static const int TOPIC_FLOWS = 5;
static const int TOPIC_FLOWL = 6;
static const int TOPIC_UPTIME = 7;
static const int TOPIC_EFF = 8;

MQTT::MQTT()
{
	override_on_switch = false;
	override_off_switch = false;
	last_pub_update = now() - (1 * MINUTES);
	last_general_pub = now() - (60 * MINUTES);
	last_mqtt_check = now() - (30 * SECONDS);
	last_wifi_check = now() - (60 * SECONDS);
    wifi_connection_logged = false;

	size_t count = 0;
	while (pub_topics[count++]);
	pub_values = (char**) calloc(count + 1, sizeof(char*));
	pub_pending = (int*) calloc(count, sizeof(int));
	for (size_t i = 0; i < count ; ++i) {
		pub_values[i] = strdup("Undefined");
		pub_pending[i] = 1;
	}

	init_mqttimpl();
}

void mqttimpl_trampoline2(const char* topic, const uint8_t* bpayload, unsigned int length)
{
	char *payload = (char*) malloc(length + 1);
	memcpy(payload, bpayload, length);
	payload[length] = 0;
	mqtt->sub_data_event(topic, payload, length);
	free(payload);
}

#ifndef UNDER_TEST
void mqttimpl_trampoline(char* topic, uint8_t* bpayload, unsigned int length)
{
	mqttimpl_trampoline2(topic, bpayload, length);
}
#endif

void MQTT::init_mqttimpl()
{
#ifndef UNDER_TEST
	mqttimpl.setServer(BROKER_MQTT, BROKER_PORT);
	mqttimpl.setCallback(mqttimpl_trampoline);
#endif
}

const char *MQTT::mqtt_status()
{
    static char tmp[31];
#ifndef UNDER_TEST
    if (mqttimpl.connected()) {
        sprintf(tmp, "conn");
    } else {
        sprintf(tmp, "disconn %d", mqttimpl.state());
    }
#else
    sprintf(tmp, "connected");
#endif
    return tmp;
}

void MQTT::chk_mqttimpl()
{
	Timestamp Now = now();
	if ((Now - last_mqtt_check) < (1 * MINUTES)) {
		return;
	}
	last_mqtt_check = Now;

#ifndef UNDER_TEST
	if (!mqttimpl.connected()) {
		Log::d("Connecting MQTT");
		if (mqttimpl.connect(mqtt_id)) {
			Log::d("MQTT connection up");
			mqttimpl.subscribe(sub_onswitch);
			mqttimpl.subscribe(sub_offswitch);
			// force full republish
			last_general_pub = Now - (30 * MINUTES);
		} else {
			Log::d("MQTT connection failed");
			Log::d("MQTT state", mqttimpl.state());
		}
	}
#endif
}

void MQTT::eval_mqttimpl()
{
#ifndef UNDER_TEST
	mqttimpl.loop();
#endif
}

const char *MQTT::wifi_status()
{
    static char tmp[31];
#ifndef UNDER_TEST
    if (WiFi.status() == WL_CONNECTED) {
        sprintf(tmp, "%s", WiFi.localIP().toString().c_str());
    } else {
        sprintf(tmp, "disconn");
    }
#else
    sprintf(tmp, "connected");
#endif
    return tmp;
}

void MQTT::chk_wifi()
{
	Timestamp Now = now();
	if ((Now - last_wifi_check) < (1 * MINUTES)) {
		return;
	}
	last_wifi_check = Now;

#ifndef UNDER_TEST
	if (WiFi.status() == WL_CONNECTED) {
        if (!wifi_connection_logged) {
		    Log::d("WiFi up, IP is ", WiFi.localIP().toString().c_str());
            wifi_connection_logged = true;
        }
		return;
	}
    wifi_connection_logged = false;
	Log::d("Connecting to WiFi...");
	WiFi.begin(SSID, PASSWORD);
#endif
}

MQTT::~MQTT()
{
	for (size_t i = 0; pub_values[i]; ++i) {
		free(pub_values[i]);
	}
	free(pub_values);
	free(pub_pending);
}

bool MQTT::override_on_state() const
{
	return override_on_switch;
}


bool MQTT::override_off_state() const
{
	return override_off_switch;
}

void MQTT::sub_data_event(const char *topic, const char *payload, unsigned int length)
{
	if (strcmp(topic, sub_onswitch) == 0) {
		if (strncasecmp(payload, "On", length) == 0) {
			override_on_switch = 1;
		} else if (strncasecmp(payload, "1", length) == 0) {
			override_on_switch = 1;
		} else if (strncasecmp(payload, "Off", length) == 0) {
			override_on_switch = 0;
		} else if (strncasecmp(payload, "0", length) == 0) {
			override_on_switch = 0;
		}
	} else if (strcmp(topic, sub_offswitch) == 0) {
		if (strncasecmp(payload, "On", length) == 0) {
			override_off_switch = 1;
		} else if (strncasecmp(payload, "1", length) == 0) {
			override_off_switch = 1;
		} else if (strncasecmp(payload, "Off", length) == 0) {
			override_off_switch = 0;
		} else if (strncasecmp(payload, "0", length) == 0) {
			override_off_switch = 0;
		}
	}
}

void MQTT::eval()
{
#ifdef UNDER_TEST
	// simulate receiving MQTT commands
	std::ifstream f;
	int x = 0;
	f.open("mqtt.sim");
	if (f.is_open()) {
		f >> x;
		std::remove("mqtt.sim");
	}
	f.close();
	if (x == 1) {
		mqttimpl_trampoline2(sub_onswitch, (uint8_t*) ((random() % 2) ? "On" : "1"), 2);
	} else if (x == 2) {
		mqttimpl_trampoline2(sub_onswitch, (uint8_t*) ((random() % 2) ? "Off" : "0"), 3);
	} else if (x == 3) {
		mqttimpl_trampoline2(sub_offswitch, (uint8_t*) ((random() % 2) ? "on" : "1"), 2);
	} else if (x == 4) {
		mqttimpl_trampoline2(sub_offswitch, (uint8_t*) ((random() % 2) ? "off" : "0"), 3);
	}
#endif
	chk_wifi();
	chk_mqttimpl();
	eval_mqttimpl();

	update_pub_data();
	pub_data();
}

void MQTT::update_pub_data()
{
	Timestamp Now = now();
	if ((Now - last_pub_update) < 1000) {
		return;
	}
	last_pub_update = Now;

	if (strcmp(sm->cur_state_name(), pub_values[TOPIC_STATE])) {
		free(pub_values[TOPIC_STATE]);
		pub_values[TOPIC_STATE] = strdup(sm->cur_state_name());
		pub_pending[TOPIC_STATE] = 1;
	}

	char tmp[30];

	sprintf(tmp, "%.0f", levelmeter->level_pct());

	if (strcmp(tmp, pub_values[TOPIC_LEVEL1])) {
		free(pub_values[TOPIC_LEVEL1]);
		pub_values[TOPIC_LEVEL1] = strdup(tmp);
		pub_pending[TOPIC_LEVEL1] = 1;
	}

	const char *err = levelmeter->failure_detected() ? "1" : "0";
	sprintf(tmp, "%s", err);

	if (strcmp(tmp, pub_values[TOPIC_LEVELERR])) {
		free(pub_values[TOPIC_LEVELERR]);
		pub_values[TOPIC_LEVELERR] = strdup(tmp);
		pub_pending[TOPIC_LEVELERR] = 1;
	}

	sprintf(tmp, "%.0f", flowmeter->volume());

	if (strcmp(tmp, pub_values[TOPIC_LEVEL2])) {
		free(pub_values[TOPIC_LEVEL2]);
		pub_values[TOPIC_LEVEL2] = strdup(tmp);
		pub_pending[TOPIC_LEVEL2] = 1;
	}

	if (flowmeter->rate(FLOWRATE_INSTANT) < 0) {
		sprintf(tmp, "0");
	} else {
		sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_INSTANT));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWI])) {
		free(pub_values[TOPIC_FLOWI]);
		pub_values[TOPIC_FLOWI] = strdup(tmp);
		pub_pending[TOPIC_FLOWI] = 1;
	}

	if (flowmeter->rate(FLOWRATE_SHORT) < 0) {
		sprintf(tmp, "0");
	} else {
		sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_SHORT));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWS])) {
		free(pub_values[TOPIC_FLOWS]);
		pub_values[TOPIC_FLOWS] = strdup(tmp);
		pub_pending[TOPIC_FLOWS] = 1;
	}

	if (flowmeter->rate(FLOWRATE_LONG) < 0) {
		sprintf(tmp, "0");
	} else {
		sprintf(tmp, "%.1f", flowmeter->rate(FLOWRATE_LONG));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWL])) {
		free(pub_values[TOPIC_FLOWL]);
		pub_values[TOPIC_FLOWL] = strdup(tmp);
		pub_pending[TOPIC_FLOWL] = 1;
	}

    sprintf(tmp, "%lld", Now / (1 * MINUTES));

	if (strcmp(tmp, pub_values[TOPIC_UPTIME])) {
		free(pub_values[TOPIC_UPTIME]);
		pub_values[TOPIC_UPTIME] = strdup(tmp);
		pub_pending[TOPIC_UPTIME] = 1;
	}

	if (pump->is_running()) {
		double volume = flowmeter->volume();
		double exp_volume = flowmeter->expected_volume() + 0.0001;
		sprintf(tmp, "%.0f", 100 * volume / exp_volume);
	} else {
		sprintf(tmp, "0");
	}

	if (strcmp(tmp, pub_values[TOPIC_EFF])) {
		free(pub_values[TOPIC_EFF]);
		pub_values[TOPIC_EFF] = strdup(tmp);
		pub_pending[TOPIC_EFF] = 1;
	}
}

void MQTT::pub_data()
{
	Timestamp Now = now();
	if (((Now - last_general_pub) >= (30 * MINUTES))) {
		for (int i = 0; pub_topics[i]; ++i) {
			pub_pending[i] = 1;
		}
		last_general_pub = Now;
	}

	for (int i = 0; pub_topics[i]; ++i) {
		if (! pub_pending[i]) {
			continue;
		}
		do_pub_data(pub_topics[i], pub_values[i]);
		pub_pending[i] = 0;
		// Do a single MQTT publish per cycle
		break;
	}
}

void MQTT::pub_logdebug(const char *msg)
{
	// do not call Log::d() here to avoid infinite loop
	do_pub_data(LOGDEBUG_TOPIC, msg);
}

void MQTT::do_pub_data(const char *topic, const char *value) const
{
	// do not call Log::d() here to avoid infinite loop
#ifdef UNDER_TEST
	std::ofstream f;
	f.open("mqttpub.sim", std::ios_base::app);
	f << topic << " " << value << std::endl;
	f.close();
#else
	mqttimpl.publish(topic, (const uint8_t*) value, strlen(value), true);
#endif
}
