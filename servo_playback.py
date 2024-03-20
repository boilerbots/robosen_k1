#!/usr/bin/env python3

import serial
import queue
import threading
import enum
import array
import pickle
import time

q = queue.SimpleQueue()
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
State = enum.Enum('State', ['IDLE', 'START1', 'START2', 'ADDRESS', 'LENGTH', 'DATA'])
key_press = ''

current_position = array.array('B', [ 0 ] * 48)

def keyboard():
    global key_press
    while True:
        key_press = input()

def worker():
    global key_press
    file_name = 'capture'
    capture_count = 0
    state = State.IDLE
    address = 0
    type_code = None
    data_len = 0
    #expected_data_len = [ 0, 0, 2, 3 ]
    data = array.array('B')

    while True:
        readbuf = ser.read(8)
        #print("received {} data while in state={}".format(len(data), state))
        for b in readbuf:
            if state == State.IDLE and b == 0xFF:
                state = State.START1
            elif state == State.START1 and b == 0xFF:
                state = State.START2
            elif state == State.START2:
                address = b
                state = State.ADDRESS
            elif state == State.ADDRESS:
                expected_data_len = b
                data_len = 0
                data = array.array('B')
                state = State.DATA
            elif state == State.DATA:
                data.append(b)
                data_len += 1
                if data_len >= expected_data_len:
                    state = State.IDLE
                    if data[0] == 0xA3:
                        print('servo {}  position={}'.format(address, data[1] * 256 + data[2]))
                        current_position[address * 2] = data[1]
                        current_position[address * 2 + 1] = data[2]
                    else:
                        print('Bad Status servo {}  position={}'.format(address, data[1] * 256 + data[2]))

                    #if address == 0xFE:
                    print('Captured addr={0:02x} len={1:02x} data={2}'.format(address, data_len, data))
                if key_press == 's':
                    print("Saved")
                    with open(file_name + str(capture_count) + '.pkl', 'wb') as f:
                        pickle.dump(data, f)
                    capture_count += 1
                    key_press = ''
                    


threading.Thread(target=worker).start()
threading.Thread(target=keyboard).start()
#with open('capture0.pkl', 'rb') as f:
#    p1 = pickle.load(f)
#    print('p1 size {}'.format(p1.itemsize))
#with open('capture1.pkl', 'rb') as f:
#    p2 = pickle.load(f)
#    print('p2 size {}'.format(p2.itemsize))

# addr, length, 254 = cmd?, msb, lsb
# addresses:
# 0xFE - Broadcast?
# 2, 0 -> Disable
# 2, 1 -> Enable
#
# for address 0-17 Commands:
# 3 -> readback position  -> 0xA3, msb, lsb
# 7 -> not sure
#
# Servo Map
#
# 0 left thigh
# 1 left calf
# 2 left ankle
# 3 right thigh
# 4 right calf
# 5 right ankle
# 6 left shoulder
# 7 right shoulder
# 8 left hip
# 9 left foot
# 10 right hip
# 11 right foot
# 12 left arm
# 13 left hand
# 14 right arm
# 15 right hand
# 16 head
# 
p1 = array.array('B', [254, 50, 254, 
1, 211, # ch0
1, 25, 
1, 109, 
1, 190, 
2, 144, 
1, 253, 
2, 243, # ch6 left arm
0, 194, # ch7 right shoulder
1, 181, 
1, 190, 
1, 181, 
1, 229, 
2, 192, 
2, 15, 
0, 212, 
1, 127, 
1, 211, # ch16 head
1, 205, 
1, 205, 
1, 205, 
1, 130, 
1, 130, 
1, 205, 
1, 205])  # , 168
#p2 = array.array('B', [254, 50, 254, 
#1, 211, # ch0
#1, 25, 
#1, 109, 
#1, 190, 
#2, 144, 
#1, 253, 
#2, 243, # ch6 left arm
#0, 194, 
#1, 181, 
#1, 190, 
#1, 181, 
#1, 229, 
#2, 192, 
#2, 15, 
#0, 212, 
#1, 127, 
#1, 231, # ch16
#1, 205, 
#1, 205, 
#1, 205, 
#1, 130, 
#1, 130, 
#1, 205, 
#1, 205])  # , 168
p2 = array.array('B', [254, 50, 254, 2, 108, 2, 72, 0, 212, 1, 37, 1, 94, 2, 153, 3, 17, 0, 164, 1, 196, 1, 208, 1, 166, 1, 211, 2, 195, 2, 150, 0, 212, 0, 248, 1, 205, 1, 205, 1, 205, 1, 205, 1, 130, 1, 130, 1, 205, 1, 205])  # , 166
#p3 = array.array('B', [254, 50, 254, 2, 210, 2, 249, 0, 140, 0, 191, 0, 176, 2, 222, 2, 213, 0, 224, 1, 196, 1, 205, 1, 166, 1, 214, 2, 222, 1, 211, 0, 182, 1, 187, 1, 211, 1, 205, 1, 205, 1, 205, 1, 130, 1, 130, 1, 205, 1, 205])  # , 166
initialize = array.array('B', [0xFA, 2, 7])  # , 3
enable = array.array('B', [0xFE, 3, 2, 1])  # , 4
disable = array.array('B', [0xFE, 3, 2, 0])
special = array.array('B', [0xFA, 0x03, 0x08, 0x00])
special2 = array.array('B', [0x16, 0x05, 0x09, 0x01, 0x01, 0xCD])

packets = [
array.array('B', [0xFA, 0x03, 0x08, 0x00]), # , 0x05
array.array('B', [0x16, 0x05, 0x09, 0x01, 0x01, 0xCD]), # , 0xF3
# start iterating through channels
array.array('B', [0x00, 0x02, 0x03]),  # expect response about 0.28ms 0, 4, A3, 1, F4, 9C
array.array('B', [0x01, 0x02, 0x03]),  # expect response about 0.28ms 1, 4, A3, 1, 50, F9
# send this after 5ms, multiple times
array.array('B', [0x11, 0x02, 0x03]),  # no response
# From 0x11 through 0x17 with no response
array.array('B', [0xFE, 50, 254, 1, 211, 1, 25, 1, 109, 1, 190, 2, 144, 1, 253, 2, 243, 0, 194, 1, 181, 1, 190, 1, 181, 1, 229, 2, 192, 2, 15, 0, 212, 1, 127, 1, 211, 1, 205, 1, 205, 1, 205, 1, 130, 1, 130, 1, 205, 1, 205]),  # p1
# after sending 0xFE for a while it sends
array.array('B', [0x00, 0x02, 0x07]),  # response 0, 3, A7, 0, AA
array.array('B', [0x01, 0x02, 0x07]),  # response 1, 3, A7, 0, AB
array.array('B', [0x02, 0x02, 0x07]),  # response 2, 3, A7, 0, AC
]
                  
def add_crc(data):
    checksum = 0
    for b in data:
        checksum += b
    checksum %= 256
    return checksum

def position(data):
    crc = add_crc(data)
    msg = array.array('B', [0xFF, 0xFF])
    #msg.append(len(data))
    msg += data
    msg.append(crc)
    ser.write(msg) 
    #print('msg: {}'.format(msg))
    #ser.write(data.tobytes()) 

position(initialize)
time.sleep(0.300)
#position(disable)
#time.sleep(0.002)
position(enable)
time.sleep(0.002)
position(special)
position(special2)
time.sleep(0.002)
if True:
    channel = 0
    while key_press != 'c':
        # responses seem to respond with 0xAx so 0x03 => 0xA3
        test = array.array('B', [channel, 0x02, 0x03])  # expect response about 0.28ms 0, 4, A3, 1, F4, 9C
        position(test)
        time.sleep(0.0020)
        #
        #test = array.array('B', [channel, 0x02, 0x07])  # Not sure
        #position(test)
        #time.sleep(0.005)
        channel += 1
        if channel > 16:
            channel = 0

#for p in packets:
#    position(p)
#    time.sleep(0.005)

while True:
    #position(current_position)
    #time.sleep(1.10)
    position(p1)
    time.sleep(1.10)
    #position(p2)
    #time.sleep(1.10)

