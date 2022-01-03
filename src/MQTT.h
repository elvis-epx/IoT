#ifndef __MQTT_H
#define __MQTT_H

class MQTT {
public:
	MQTT();
	~MQTT();

	void eval();

	bool override_on_state() const;
	bool override_off_state() const;
private:
	bool override_on_switch;
	bool override_off_switch;
};

#endif
