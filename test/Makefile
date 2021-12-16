CFLAGS=-DDEBUG -DUNDER_TEST -fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0 -fprofile-arcs -ftest-coverage -fno-elide-constructors
OBJ=StateMachine.o H2OStateMachine.o ArduinoBridge.o Pump.o LevelMeter.o FlowMeter.o Timestamp.o GPIO.o Display.o

all: test

clean:
	rm -rf *.o test *.gcda *.gcno *.info out *.dSYM *.log *.val *.gcov

.cpp.o: *.h
	gcc $(CFLAGS) -c $<

test: test.cpp $(OBJ) *.h
	gcc $(CFLAGS) -o test test.cpp $(OBJ) -lstdc++

recov:
	rm -f *.gcda

coverage: test
	rm -f *.info
	./test
	gcov test.cpp
	lcov -c --directory . --output-file main_coverage.info
	lcov -r main_coverage.info '*/test.cpp' -o main_coverage.info
	genhtml main_coverage.info --output-directory out
	xdg-open out/index.html
