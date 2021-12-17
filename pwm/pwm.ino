// PWM generator to test flow meter

void setup() {
	Serial.begin(9600);
	pinMode(11, OUTPUT);
}

void loop() {
	int val = analogRead(2);
	if (val <= 23) {
		digitalWrite(11, LOW);
		Serial.println("Off");
		delay(250);
		return;
	}
	int hz = 1 + (val - 23) / 3; // 0-333Hz
	long int wavelength = 1000000L / hz; // in µs
	long int half = wavelength / 2;
	Serial.print(hz);
	Serial.print(" Hz, ");
	Serial.println(wavelength);

	for (int i = 0; i < hz / 4; ++i) {
		digitalWrite(11, HIGH);
		if (half > 10000) {
			delay(half / 1000);
		} else {
			delayMicroseconds(half);
		}
		digitalWrite(11, LOW);
		if (half > 10000) {
			delay(half / 1000);
		} else {
			delayMicroseconds(half);
		}
	}
}
