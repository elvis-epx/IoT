PORT := $(shell cat serial.txt)

all: scr

clean: clean-coverage
	rm -rf `find . -name __pycache__` `find . -name tmppiggy`

scr:
	screen /dev/$(PORT) 115200

clean-coverage:
	python3-coverage erase
	rm -rf htmlcov/

test: clean-coverage
	./runtests
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

report:
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html

test2:
	./runtest ota
	python3-coverage combine || echo
	python3-coverage html
	xdg-open htmlcov/index.html
