#ifndef __MQTT_H
#define __MQTT_H

class MQTT {
public:
	MQTT();
	~MQTT();
	bool override_on_state() const;
	bool override_off_state() const;
};

#endif
