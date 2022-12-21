PORT=/dev/ttyUSB0
# PORT=/dev/cu.usbserial-146160

all: scr

h2o: h2o_boot.cop h2o_main.cop h2o_config.cop h2olib uumqtt third epx

weather: weather_boot.cop weather_main.cop weather_config.cop weatherlib uumqtt third epx

relay: relay_boot.cop relay_main.cop relay_config.cop relaylib uumqtt third epx

h2olib: lib/h2o/service.ucop lib/h2o/sensor.ucop lib/h2o/actuator.ucop lib/h2o/__init__.ucop

weatherlib: lib/weather/service.ucop lib/weather/sensor.ucop lib/weather/__init__.ucop

relaylib: lib/relay/service.ucop lib/relay/actuator.ucop lib/relay/__init__.ucop

uumqtt: lib/uumqtt/__init__.ucop lib/uumqtt/simple2.ucop lib/uumqtt/errno.ucop

epx: lib/epx/__init__.ucop lib/epx/config.ucop lib/epx/mqtt.ucop lib/epx/net.ucop lib/epx/watchdog.ucop lib/epx/loop.ucop lib/epx/ota.ucop

third: lib/third/__init__.ucop lib/third/bme280.ucop lib/third/hdc1080.ucop lib/third/mcp23017.ucop lib/third/ssd1306.ucop

clean: clean-coverage
	rm -rf *.cop *.fcop *.txtup `find . -name '*.ucop'` `find . -name '*.sim'` `find . -name __pycache__` `find . -name tmppiggy`

scr:
	screen $(PORT) 115200	

h2o_config.cop: h2o_config.txt
	pyboard.py -d $(PORT) -f cp $< :config.txt
	touch $@

h2o_boot.cop: h2o_boot.py
	pyboard.py -d $(PORT) -f cp $< :boot.py
	touch $@

h2o_main.cop: h2o_main.py
	pyboard.py -d $(PORT) -f cp $< :main.py
	touch $@

weather_config.cop: weather_config.txt
	pyboard.py -d $(PORT) -f cp $< :config.txt
	touch $@

weather_boot.cop: weather_boot.py
	pyboard.py -d $(PORT) -f cp $< :boot.py
	touch $@

weather_main.cop: weather_main.py
	pyboard.py -d $(PORT) -f cp $< :main.py
	touch $@

relay_config.cop: relay_config.txt
	pyboard.py -d $(PORT) -f cp $< :config.txt
	touch $@

relay_boot.cop: relay_boot.py
	pyboard.py -d $(PORT) -f cp $< :boot.py
	touch $@

relay_main.cop: relay_main.py
	pyboard.py -d $(PORT) -f cp $< :main.py
	touch $@

%.cop: %.py
	pyboard.py -d $(PORT) -f cp $< :$<
	touch $@

%.ucop: %.py lib.fcop uumqtt.fcop epx.fcop third.fcop weather.fcop relay.fcop h2o.fcop
	pyboard.py -d $(PORT) -f cp $< :/$<
	touch $@

lib.fcop:
	pyboard.py -d $(PORT) -f mkdir :/lib
	touch $@

h2o.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/h2o
	touch $@

weather.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/weather
	touch $@

relay.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/relay
	touch $@

epx.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/epx
	touch $@

third.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/third
	touch $@

uumqtt.fcop: lib.fcop
	pyboard.py -d $(PORT) -f mkdir :/lib/uumqtt
	touch $@

clean-coverage:
	python3-coverage erase
	rm -rf htmlcov/

test: clean-coverage
	./runtests
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

test2: clean-coverage
	./runtest justrun_h
	./runtest h2o_disp
	./runtest h2o_fails
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

.SUFFIXES: .py .cop .ucop .fcop .txt
