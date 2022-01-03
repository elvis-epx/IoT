#ifndef __MQTT_H
#define __MQTT_H

#include "Timestamp.h"

class MQTT {
public:
	MQTT();
	~MQTT();

	void eval();

	bool override_on_state() const;
	bool override_off_state() const;
private:
	void sub_data_event(const char *topic, const char *payload, unsigned int length);
	void update_pub_data();
	void pub_data();
	void do_pub_data(const char *topic, const char *value) const;
#ifndef UNDER_TEST
	void init_wifi();
	void init_mqttimpl();
	void chk_mqttimpl();
	void chk_wifi();
	void eval_mqttimpl();
	Timestamp last_wifi_check;
	Timestamp last_mqtt_check;
#endif

	bool override_on_switch;
	bool override_off_switch;

	char **pub_values;
	int *pub_pending;
	Timestamp last_pub_update;
	Timestamp last_general_pub;

#ifndef UNDER_TEST
friend void mqttimpl_trampoline(char* topic, uint8_t* payload, unsigned int length);
#endif
};

#endif
