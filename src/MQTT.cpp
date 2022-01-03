#include "MQTT.h"
#include "Elements.h"
#include "Constants.h"

#ifdef UNDER_TEST

#include <iostream>
#include <fstream>

#else
#endif

#define TOP "H2OControl/"

static const char* pub_topics[] = {
			TOP "State", TOP "Level",
			TOP "FlowInst", TOP "FlowShort", TOP "FlowLong",
			TOP "Uptime", TOP "Efficiency",
			0};

static const int TOPIC_STATE = 0;
static const int TOPIC_LEVEL = 1;
static const int TOPIC_FLOWI = 2;
static const int TOPIC_FLOWS = 3;
static const int TOPIC_FLOWL = 4;
static const int TOPIC_UPTIME = 5;
static const int TOPIC_EFF = 6;

static void millis_to_hm(int64_t t, char *target)
{
	if (t < 0) {
		sprintf(target, "???");
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

	sprintf(target, "%dd %02dh %02dm", d, h, m);
}

MQTT::MQTT()
{
	override_on_switch = false;
	override_off_switch = false;
	last_pub_update = last_general_pub = 0;

	size_t count = 0;
	while (pub_topics[count++]);
	pub_values = (char**) calloc(count + 1, sizeof(char*));
	pub_pending = (int*) calloc(count, sizeof(int));
	for (size_t i = 0; i < count ; ++i) {
		pub_values[i] = strdup("Undefined");
		pub_pending[i] = 1;
	}

	// FIXME init WiFi, PubSub
	// FIXME configure sub to switches and callbacks
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
		override_on_switch = true;
	} else if (x == 2) {
		override_on_switch = false;
	} else if (x == 3) {
		override_off_switch = true;
	} else if (x == 4) {
		override_off_switch = false;
	}
#endif
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
	const char *err = levelmeter->failure_detected() ? "E " : "";
	sprintf(tmp, "%s%.0f%% + %.0fL", err, levelmeter->level_pct(), flowmeter->volume());

	if (strcmp(tmp, pub_values[TOPIC_LEVEL])) {
		free(pub_values[TOPIC_LEVEL]);
		pub_values[TOPIC_LEVEL] = strdup(tmp);
		pub_pending[TOPIC_LEVEL] = 1;
	}

	if (flowmeter->rate(FLOWRATE_INSTANT) < 0) {
		sprintf(tmp, "---");
	} else {
		sprintf(tmp, "%.1fL/min", flowmeter->rate(FLOWRATE_INSTANT));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWI])) {
		free(pub_values[TOPIC_FLOWI]);
		pub_values[TOPIC_FLOWI] = strdup(tmp);
		pub_pending[TOPIC_FLOWI] = 1;
	}

	if (flowmeter->rate(FLOWRATE_SHORT) < 0) {
		sprintf(tmp, "---");
	} else {
		sprintf(tmp, "%.1fL/min", flowmeter->rate(FLOWRATE_SHORT));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWS])) {
		free(pub_values[TOPIC_FLOWS]);
		pub_values[TOPIC_FLOWS] = strdup(tmp);
		pub_pending[TOPIC_FLOWS] = 1;
	}

	if (flowmeter->rate(FLOWRATE_LONG) < 0) {
		sprintf(tmp, "---");
	} else {
		sprintf(tmp, "%.1fL/min", flowmeter->rate(FLOWRATE_LONG));
	}

	if (strcmp(tmp, pub_values[TOPIC_FLOWL])) {
		free(pub_values[TOPIC_FLOWL]);
		pub_values[TOPIC_FLOWL] = strdup(tmp);
		pub_pending[TOPIC_FLOWL] = 1;
	}

	millis_to_hm(Now, tmp);

	if (strcmp(tmp, pub_values[TOPIC_UPTIME])) {
		free(pub_values[TOPIC_UPTIME]);
		pub_values[TOPIC_UPTIME] = strdup(tmp);
		pub_pending[TOPIC_UPTIME] = 1;
	}

	if (pump->is_running()) {
		double volume = flowmeter->volume();
		double exp_volume = flowmeter->expected_volume() + 0.0001;
		sprintf(tmp, "%.0f%%", 100 * volume / exp_volume);
	} else {
		sprintf(tmp, "---");
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
	if ((Now - last_general_pub) >= (30 * MINUTES)) {
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

void MQTT::do_pub_data(const char *topic, const char *value) const
{
#ifdef UNDER_TEST
	std::ofstream f;
	f.open("mqttpub.sim", std::ios_base::app);
	f << topic << " " << value << std::endl;
	f.close();
#else
	// FIXME publish in real device
#endif
}
