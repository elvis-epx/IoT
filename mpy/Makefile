.SUFFIXES: .tst
.PHONY: src clean clean-coverage

PORT := $(shell cat serial.txt)

all: scr

clean: clean-coverage
	rm -rf `find . -name __pycache__` `find . -name tmppiggy` `find . -name espnow_packets`

scr:
	screen /dev/$(PORT) 115200

clean-coverage:
	python3-coverage erase
	rm -rf htmlcov/
	rm -f *.tst

test: h2o_disp.tst h2o_fails.tst justrun.tst justrun_e.tst justrun_h.tst justrun_r.tst justrun_sc.tst justrun_sm.tst tnowp.tst tnowc.tst justrun_sw.tst lan.tst mqttf.tst mqttf2.tst mqttf3.tst netnow.tst ota.tst otae.tst otafail.tst relay_disp.tst sensormf1.tst sensormf2.tst sw_tests.tst sw_tests2.tst sw_tests3.tst testsub.tst watchdog.tst wifi.tst
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

report:
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

# tests

h2o_disp.tst: testsuite/h2o_disp/script
	./runtest h2o_disp
	touch h2o_disp.tst

h2o_fails.tst: testsuite/h2o_fails/script
	./runtest h2o_fails
	touch h2o_fails.tst

justrun.tst: testsuite/justrun/script
	./runtest justrun
	touch justrun.tst

justrun_e.tst: testsuite/justrun_e/script
	./runtest justrun_e
	touch justrun_e.tst

justrun_h.tst: testsuite/justrun_h/script
	./runtest justrun_h
	touch justrun_h.tst

justrun_r.tst: testsuite/justrun_r/script
	./runtest justrun_r
	touch justrun_r.tst

justrun_sc.tst: testsuite/justrun_sc/script
	./runtest justrun_sc
	touch justrun_sc.tst

justrun_sm.tst: testsuite/justrun_sm/script
	./runtest justrun_sm
	touch justrun_sm.tst

tnowp.tst: testsuite/tnowp/script
	./runtest tnowp
	touch tnowp.tst

tnowc.tst: testsuite/tnowc/script
	./runtest tnowc
	touch tnowc.tst

justrun_sw.tst: testsuite/justrun_sw/script
	./runtest justrun_sw
	touch justrun_sw.tst

lan.tst: testsuite/lan/script
	./runtest lan
	touch lan.tst

mqttf.tst: testsuite/mqttf/script
	./runtest mqttf
	touch mqttf.tst

mqttf2.tst: testsuite/mqttf2/script
	./runtest mqttf2
	touch mqttf2.tst

mqttf3.tst: testsuite/mqttf3/script
	./runtest mqttf3
	touch mqttf3.tst

netnow.tst: testsuite/netnow/script
	./runtest netnow
	touch netnow.tst

ota.tst: testsuite/ota/script
	./runtest ota
	touch ota.tst

otae.tst: testsuite/otae/script
	./runtest otae
	touch otae.tst

otafail.tst: testsuite/otafail/script
	./runtest otafail
	touch otafail.tst

relay_disp.tst: testsuite/relay_disp/script
	./runtest relay_disp
	touch relay_disp.tst

sensormf1.tst: testsuite/sensormf1/script
	./runtest sensormf1
	touch sensormf1.tst

sensormf2.tst: testsuite/sensormf2/script
	./runtest sensormf2
	touch sensormf2.tst

sw_tests.tst: testsuite/sw_tests/script
	./runtest sw_tests
	touch sw_tests.tst

sw_tests2.tst: testsuite/sw_tests2/script
	./runtest sw_tests2
	touch sw_tests2.tst

sw_tests3.tst: testsuite/sw_tests3/script
	./runtest sw_tests3
	touch sw_tests3.tst

testsub.tst: testsuite/testsub/script
	./runtest testsub
	touch testsub.tst

watchdog.tst: testsuite/watchdog/script
	./runtest watchdog
	touch watchdog.tst

wifi.tst: testsuite/wifi/script
	./runtest wifi
	touch wifi.tst
