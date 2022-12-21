#!/bin/bash

for script in unit/[0-9]*.sh; do
    echo
    echo ===
    echo $script
    echo ===
    bash $script || exit 1
done
echo > unit.sim
