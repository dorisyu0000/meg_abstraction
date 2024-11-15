import serial
import logging
import time

DEFAULT_MESSAGES = [f'TRIGGER{i}' for i in range(8)]

class Triggers(object):
    mapping = ['mh\x01', 'mh\x02', 'mh\x04', 'mh\x08', 'mh\x10', 'mh 0', 'mh@0', 'mh\x20', 'mh\x40']

    """docstring for StimTrackerTriggers"""
    def __init__(self, port='/dev/cu.usbserial-A900a2R9', messages=DEFAULT_MESSAGES, baudrate=115200):
        super().__init__()
        self.port = port
        self.ser = serial.Serial(baudrate=baudrate)

        # 'Port (only serial port needs port name pre-define)'
        if port is None or port == 'dummy':
            logging.info('Using dummy triggers')
            self.port = 'dummy'
            return
        try:
            self.ser.port = port  # set the port
            self.ser.open()
            logging.info('Triggers connected to port %s', port)
        except:
            logging.exception('Failed to open port: %s', port)
            raise

    def send(self, code, duration = 0.01):
        '''
        Send trigger to StimTracker

        Parameters
        ----------
        code: an integer 0-8 writes to channel 160-168

        duration: how long the marker pulse stays
            unit in second

        Return
        ---------
        None
        '''
        logging.info('send trigger %s', code)
        if self.port == 'dummy':
            return

        data = self.mapping[code]
        try:
            #send the marker twice because of we don't know why. hmmm....
            self.ser.write(bytes(data, encoding='utf-8'))
            self.ser.write(bytes(data, encoding='utf-8'))

            #pulse duration
            time.sleep(duration)

            #setting the pulse back to zero
            zero_marker = 'mh\x00'
            self.ser.write(bytes(zero_marker, encoding='utf-8'))
            self.ser.write(bytes(zero_marker, encoding='utf-8'))

        except:
            logging.warning(f'Failed to send trigger: {msg}')
            if this.self.ser.port != '':
                logging.warning('The port might be closed.')



#sending marker
#sendTrigger(f'ch161',duration=0.01)

