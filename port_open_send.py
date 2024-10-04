import serial

def sendTrigger(channel, duration = 0.01,zero_marker='mh\x00'):
    import time
    '''
    Send trigger to StimTracker

    Parameters
    ----------
    channel: any of 7 MISC channels: 160 - 166
        The trigger content
        
    duration: how long the marker pulse stays
        unit in second

    Return
    ---------
    None
    '''

    print(channel)
    mapping_bin_ascii = {'ch160':'mh\x01','ch161':'mh\x02','ch162':'mh\x04','ch163':'mh\x08',
                         'ch164':'mh\x10','ch165':'mh 0','ch166':'mh@0'}

    data = mapping_bin_ascii[channel]

    try:
        #send the marker twice because of we don't know why. hmmm....
        ser.write(bytes(data, encoding='utf-8'))
        ser.write(bytes(data, encoding='utf-8'))

        #pulse duration
        time.sleep(duration)

        #setting the pulse back to zero
        ser.write(bytes(zero_marker, encoding='utf-8'))
        ser.write(bytes(zero_marker, encoding='utf-8'))

    except:
        if ser.port != '':
            print('The port might be closed.')

port_dll = None

ser = serial.Serial(baudrate=115200)

# 'Port (only serial port needs port name pre-define)'
try:
    ser.port = '/dev/cu.usbserial-A900a2R9'  # set the port
    ser.open()
except:
    print('Could not open serial port')

#sending marker
#sendTrigger(f'ch161',duration=0.01)


