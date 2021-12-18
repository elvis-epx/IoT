#!/bin/bash

make clean
make
for script in unit/[0-9]*.sh; do
	bash $script || exit 1
done
echo > unit.sim
