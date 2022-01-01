// PWM generator to test flow meter

void setup() {
	Serial.begin(9600);
	pinMode(11, OUTPUT);
	pinMode(13, OUTPUT);
}

void loop() {
	int rval = analogRead(2);
	if (rval <= 23) {
		digitalWrite(11, LOW);
		digitalWrite(13, LOW);
		Serial.println("Off");
		delay(250);
		return;
	}
	double fval = (rval - 23) / 1000.0; // 23..1023 to 0..1
	fval = pow(fval, 2); // make the curve more exponential
	int hz = 1 + fval * 333; // 0..1 to 1..333Hz
	long int wavelength = 1000000L / hz; // in µs
	long int half = wavelength / 2;
	Serial.print(hz);
	Serial.print(" Hz, ");
	Serial.println(wavelength);

	for (long int i = 0; i < 250000; i += wavelength) {
		digitalWrite(11, HIGH);
		digitalWrite(13, HIGH);
		if (half > 10000) {
			delay(half / 1000);
		} else {
			delayMicroseconds(half);
		}
		digitalWrite(11, LOW);
		digitalWrite(13, LOW);
		if (half > 10000) {
			delay(half / 1000);
		} else {
			delayMicroseconds(half);
		}
	}
}
