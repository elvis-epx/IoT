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
	void update_pub_data();
	void pub_data();
	void do_pub_data(const char *topic, const char *value) const;

	bool override_on_switch;
	bool override_off_switch;

	char **pub_values;
	int *pub_pending;
	Timestamp last_pub_update;
	Timestamp last_general_pub;
};

#endif
