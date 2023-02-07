all: test

test:
	python3-coverage erase
	rm -rf htmlcov/
	./runtest
	./runtest-alaw
	python3-coverage combine || echo 
	python3-coverage html
	xdg-open htmlcov/index.html
