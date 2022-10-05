#!/bin/bash

. unit/defs.sh

nvram_nomqtt
runme

cli "!help"
sleep 2
cli "!ssid None"
sleep 2
cli "!ssid"
sleep 2
cli "!ssid foo"
sleep 2
cli "!ssid fooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
sleep 5
cli "!ssid"
sleep 2
cli "!password None"
sleep 2
cli "!password"
sleep 2
cli "!password barrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"
sleep 5
cli "!password bar"
sleep 2
cli "!password"
sleep 2
cli "!mqtt 1.2.3.4"
sleep 2
cli "!mqtt 1.2.3.44444444444444444444444444444444444444444444444444444444444444444444444444444444444"
sleep 5
cli "!mqtt"
sleep 2
cli "!mqtt None"
sleep 2
cli "!mqtt"
sleep 2
cli "!mqttport 70000"
sleep 2
cli "!mqttport 1234"
sleep 2
cli "!mqttport"
sleep 2
cli "!mqttport None"
sleep 2
cli "!mqttport"
sleep 2
cli "!status"
sleep 2
cli "!defconfig"
sleep 2
cli "!deffconfig"
sleep 2
cli "!moo"
sleep 2
cli "!moo\boo"
sleep 2
cli "asjdlfkajslfajskljsflsjlskdfjdlskfjsdjkasdlfslfasdlfkajslfkasjflasjflkasdjfdlasjfadslfjdslfjasdlfjsdlfadsfadlskfjadslfasdfjkasdfaldsjfasdlfjadslkfadskfjadslfajsflkasdjflasdfasdkfasdlfjasdlfjasdlfkasdjflasjfaskfjdaslkfjasdlkfdjaslfjadskfladskfjasdlfadjsklfjflkasdjfladsjfaldksfjasdlfjsklfadsjlfasjfaldskfadlskfdajslfasdjfladsjfsadlkfjasdlfdjalfdkajsfladfjasdlfajdsfkladsfjladsjkfadslfjadslfkasdjfalsdfjkasdlfjasdflasdkjfalsdjfasdlkjfadslfjadsfladsjfadslkfjasljsadlfjasdladsjfalsdkfjasdlfjdaslfkadjslfdasjfldasjkflakdsfjaslfjadsflkasdfjdsalkfdasasljfkdakljsflasfdaslfkadsjlfdsajflkdsajfdsalf"
sleep 15
cli "!restart"
sleep 5
