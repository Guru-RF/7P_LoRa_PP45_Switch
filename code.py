import asyncio
import time
import os
import aesio

import adafruit_rfm9x
import board
import busio
from digitalio import DigitalInOut, Direction, Pull
from microcontroller import watchdog as w
from watchdog import WatchDogMode

import config

# basic encryption
import aesio
import os

# Padding functions
def pad_message(message, block_size=16):
    padding = block_size - (len(message) % block_size)
    return message + bytes([padding] * padding)

# Encrypt with IV
def encrypt_message(message, key):
    iv = os.urandom(16)
    padded_message = pad_message(message)
    aes = aesio.AES(key, aesio.MODE_CBC, iv)
    encrypted_message = bytearray(len(padded_message))
    aes.encrypt_into(padded_message, encrypted_message)

    return iv + encrypted_message

# Unpadding function
def unpad_message(message):
    padding = message[-1]
    return message[:-padding]

# Decrypt function
def decrypt_message(payload, key):
    iv = payload[:16]
    # Ensure IV length is correct
    if len(iv) != 16:
        raise ValueError(f"Invalid IV length: {len(iv)} (expected 16 bytes)")
    encrypted_message = payload[16:]
    aes = aesio.AES(key, aesio.MODE_CBC, iv)
    decrypted_message = bytearray(len(encrypted_message))
    aes.decrypt_into(encrypted_message, decrypted_message)

    return unpad_message(decrypted_message)


def purple(data):
    stamp = time.time()
    return "\x1b[38;5;104m[" + str(stamp) + "] " + data + "\x1b[0m"


def yellow(data):
    return "\x1b[38;5;220m" + data + "\x1b[0m"


def red(data):
    return "\x1b[1;5;31m -- " + data + "\x1b[0m"


# our version
VERSION = "RF.Guru_7P_Switch_LoRa 0.1"

print(red(config.name + " -=- " + VERSION))

# configure watchdog
w.timeout = 5
w.mode = WatchDogMode.RESET
w.feed()

async def initStuff(loop):
    global inputs, ports

    pp1 = DigitalInOut(board.GP23)
    pp1.direction = Direction.OUTPUT

    pp2 = DigitalInOut(board.GP22)
    pp2.direction = Direction.OUTPUT

    pp3 = DigitalInOut(board.GP14)
    pp3.direction = Direction.OUTPUT

    pp4 = DigitalInOut(board.GP13)
    pp4.direction = Direction.OUTPUT

    pp5 = DigitalInOut(board.GP1)
    pp5.direction = Direction.OUTPUT

    pp6 = DigitalInOut(board.GP3)
    pp6.direction = Direction.OUTPUT

    pp7 = DigitalInOut(board.GP2)
    pp7.direction = Direction.OUTPUT

    ports = {
        "1": pp1,
        "2": pp2,
        "3": pp3,
        "4": pp4,
        "5": pp5,
        "6": pp6,
        "7": pp7,
    }

    bt1 = DigitalInOut(board.GP0)
    bt1.direction = Direction.INPUT
    bt1.pull = Pull.UP

    bt2 = DigitalInOut(board.GP29)
    bt2.direction = Direction.INPUT
    bt2.pull = Pull.UP

    bt3 = DigitalInOut(board.GP28)
    bt3.direction = Direction.INPUT
    bt3.pull = Pull.UP

    bt4 = DigitalInOut(board.GP27)
    bt4.direction = Direction.INPUT
    bt4.pull = Pull.UP

    bt5 = DigitalInOut(board.GP26)
    bt5.direction = Direction.INPUT
    bt5.pull = Pull.UP

    bt6 = DigitalInOut(board.GP5)
    bt6.direction = Direction.INPUT
    bt6.pull = Pull.UP

    bt7 = DigitalInOut(board.GP6)
    bt7.direction = Direction.INPUT
    bt7.pull = Pull.UP

    inputs = {
        "1": bt1,
        "2": bt2,
        "3": bt3,
        "4": bt4,
        "5": bt5,
        "6": bt6,
        "7": bt7,
    }

    
    for port, data in config.ports.items():
        loop.create_task(initPort(port,data))
   
async def initPort(port,data):
    global config, ports
    await asyncio.sleep(data["delay"])
    ports[str(int(port))].value = data["state"]

async def loraListener():
    global inputs, ports, config, w
    await asyncio.sleep(1)
    w.feed()
    # Lora Stuff
    RADIO_FREQ_MHZ = 868.000
    CS = DigitalInOut(board.GP21)
    RESET = DigitalInOut(board.GP20)
    spi = busio.SPI(board.GP10, MOSI=board.GP11, MISO=board.GP8)
    rfm9x = adafruit_rfm9x.RFM9x(
        spi, CS, RESET, RADIO_FREQ_MHZ, baudrate=1000000, agc=False, crc=True
    )
    rfm9x.tx_power = 5

    while True:
        msg = yellow("Waiting for LoRa packet ...")
        print(f"{msg}\r", end="")
        packet = await rfm9x.areceive(w, with_header=True, timeout=10)

        if packet is not None:
            # print(packet)
            if packet[:3] == (b"<\xaa\x01"):
                try:
                    decrypted_message = decrypt_message(bytes(packet[3:]), config.key)
                    rawdata = decrypted_message.decode("utf-8")
                    name, setport, intstate = rawdata.split("/", 3)
                except:
                    name = "unknown"
                    setport = "0"
                    intstate = "0"
                    
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
            if packet is not None:
                print(yellow("Received an unknown packet: " + str(packet)))
    
async def buttonListener():
    global inputs, ports, w
    await asyncio.sleep(1)
    w.feed()
    while True:
        for key, ip in inputs.items():
            if ip.value is False:
                if ports[str(int(key))].value == False:
                    ports[str(int(key))].value = True
                elif ports[str(int(key))].value == True:
                    ports[str(int(key))].value = False
                await asyncio.sleep(0.5)
        await asyncio.sleep(0)


async def main():
    loop = asyncio.get_event_loop()
    init = asyncio.create_task(initStuff(loop))
    lora = asyncio.create_task(loraListener())
    buttons = asyncio.create_task(buttonListener())
    await asyncio.gather(lora, buttons, init)

asyncio.run(main())
