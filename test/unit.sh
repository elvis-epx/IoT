#!/bin/bash

make clean
make
for script in unit/*.sh; do
	sh $script || exit 1
done
echo > unit.sim
