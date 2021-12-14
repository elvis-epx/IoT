CFLAGS=-DDEBUG -DUNDER_TEST -fsanitize=undefined -fstack-protector-strong -fstack-protector-all -std=c++1y -Wall -g -O0 -fprofile-arcs -ftest-coverage -fno-elide-constructors
OBJ=StateMachine.o H2OStateMachine.o FakeArduino.o Pump.o LevelMeter.o FlowMeter.o Timestamp.o GPIO.o

all: test

clean:
	rm -rf *.o test *.gcda *.gcno *.info out *.dSYM *.log *.val *.gcov

.cpp.o: *.h
	gcc $(CFLAGS) -c $<

test: test.cpp $(OBJ) *.h
	gcc $(CFLAGS) -o test test.cpp $(OBJ) -lstdc++
