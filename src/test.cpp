#include "H2OStateMachine.h"
#include <unistd.h>

int main()
{
	H2OStateMachine sm;
	sm.start();
	for (int i = 0; i < 100; ++i) {
		sleep(1);
		sm.eval();
	}
}
