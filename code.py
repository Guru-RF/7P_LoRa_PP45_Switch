import time

import adafruit_rfm9x
import board
import busio
from digitalio import DigitalInOut, Direction
from microcontroller import watchdog as w
from watchdog import WatchDogMode

import config


def purple(data):
    stamp = time.time()
    return "\x1b[38;5;104m[" + str(stamp) + "] " + data + "\x1b[0m"


def yellow(data):
    return "\x1b[38;5;220m" + data + "\x1b[0m"


def red(data):
    return "\x1b[1;5;31m -- " + data + "\x1b[0m"


# our version
VERSION = "RF.Guru_8P_Switch_LoRa 0.1"

pp1 = DigitalInOut(board.GP23)
pp1.direction = Direction.OUTPUT
pp1.value = config.port1
time.sleep(config.delay)

pp2 = DigitalInOut(board.GP22)
pp2.direction = Direction.OUTPUT
pp2.value = config.port2
time.sleep(config.delay)

pp3 = DigitalInOut(board.GP14)
pp3.direction = Direction.OUTPUT
pp3.value = config.port3
time.sleep(config.delay)

pp4 = DigitalInOut(board.GP13)
pp4.direction = Direction.OUTPUT
pp4.value = config.port4
time.sleep(config.delay)

pp5 = DigitalInOut(board.GP1)
pp5.direction = Direction.OUTPUT
pp5.value = config.port5
time.sleep(config.delay)

pp6 = DigitalInOut(board.GP3)
pp6.direction = Direction.OUTPUT
pp6.value = config.port6
time.sleep(config.delay)

pp7 = DigitalInOut(board.GP2)
pp7.direction = Direction.OUTPUT
pp7.value = config.port7
time.sleep(config.delay)

ports = {
    "1": pp1,
    "2": pp2,
    "3": pp3,
    "4": pp4,
    "5": pp5,
    "6": pp6,
    "7": pp7,
}

print(red(config.name + " -=- " + VERSION))

# Lora Stuff
RADIO_FREQ_MHZ = 868.000
CS = DigitalInOut(board.GP21)
RESET = DigitalInOut(board.GP20)
spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP8)
rfm9x = adafruit_rfm9x.RFM9x(
    spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False, crc=True
)
rfm9x.tx_power = 5

# configure watchdog
w.timeout = 5
w.mode = WatchDogMode.RESET
w.feed()

while True:
    msg = yellow("Waiting for LoRa packet ...")
    print(f"{msg}\r", end="")
    packet = rfm9x.receive(w, with_header=True, timeout=10)

    if packet is not None:
        # print(packet)
        if packet[:3] == (b"<\xaa\x01"):
            rawdata = bytes(packet[3:]).decode("utf-8")
            try:
                name, setport, intstate = rawdata.split("/", 3)
            except:
                name = "unknown"
                setport = "0"
                
            print(
                purple(
                    "PORT REQ: Name: "
                    + name
                    + " Port: "
                    + setport
                    + " State: "
                    + intstate
                )
            )

            if name == config.name:
                try:
                    if int(intstate) == 1:
                        if ports[str(int(setport))].value == False:
                            ports[str(int(setport))].value = True
                    else:
                        if ports[str(int(setport))].value == True:
                            ports[str(int(setport))].value = False
                except:
                        print(
                            purple(
                                "PORT REQ: Error"
                            )
                        )
            else:
                print(
                    yellow("Received another switch port req packet: " + str(rawdata))
                )
        else:
            print(yellow("Received an unknown packet: " + str(packet)))
