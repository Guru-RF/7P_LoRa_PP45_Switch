#!/bin/bash

DIR="/Volumes/RPI-RP2"
if [ -d "$DIR" ]; then
  echo "Installing firmwire to pico in ${DIR}..."
  cd /tmp
  wget https://downloads.circuitpython.org/bin/raspberry_pi_pico/en_US/adafruit-circuitpython-raspberry_pi_pico-en_US-8.0.4.uf2
  cp adafruit-circuitpython-raspberry_pi_pico-en_US-8.0.4.uf2 /Volumes/RPI-RP2
  echo "Sleeping 40 seconds for firmware to install"
  cd -
  sleep 40
fi

DIR="/Volumes/CIRCUITPY"
if [ -d "$DIR" ]; then
  echo "Installing software in ${DIR}..."
  cp -r lib /Volumes/CIRCUITPY
  cp *.py /Volumes/CIRCUITPY
  cp localcounter /Volumes/CIRCUITPY
  cp remotecounter /Volumes/CIRCUITPY
  diskutil unmount /Volumes/CIRCUITPY
  echo "done"
fi

DIR="/Volumes/LORA4PSW"
if [ -d "$DIR" ]; then
  echo "Updating software in ${DIR}..."
  cp -r lib /Volumes/LORA4PSW
  cp *.py /Volumes/LORA4PSW
  echo "done"
fi
