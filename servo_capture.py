#!/usr/bin/env python3

import serial
import queue
import threading
import enum
import array
import pickle

q = queue.SimpleQueue()
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
State = enum.Enum('State', ['IDLE', 'START1', 'START2', 'ADDRESS', 'DATA'])
key_press = ''

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
        readbuf = q.get()
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
                type_code = b
                expected_data_len = type_code
                #if type_code not in expected_data_len:
                #    print('new type code: {}'.format(type_code))
                data_len = 0
                data = array.array('B')
                state = State.DATA
            elif state == State.DATA:
                data.append(b)
                data_len += 1
                if data_len >= expected_data_len:
                    state = State.IDLE
                    #if address == 0xFE:
                    if not (data[0] == 7 or data[0] == 167):
                        print('Captured addr={} len={} data={}'.format(address, expected_data_len, data))
                if key_press == 's':
                    print("Saved")
                    with open(file_name + str(capture_count) + '.pkl', 'wb') as f:
                        pickle.dump(data, f)
                    capture_count += 1
                    key_press = ''
                    

threading.Thread(target=worker).start()
threading.Thread(target=keyboard).start()
while True:
    q.put(ser.read(8))

