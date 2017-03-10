#!/usr/bin/env python
from struct import unpack
from time import sleep
import sys
import traceback
import socket
import struct

class TSPacket(object):
    def __init__(self, raw_data=None):
        self.raw_data = raw_data
        self.sync = None
        self.pid = None
        self.error = None
        self.start = None
        self.priority = None
        self.scramble = None
        self.adapt = None
        self.count = None
        self.payload = None

        if raw_data:
            self.parse(raw_data)

    def parse(self, raw_data):
        self.raw_data = raw_data

        sync, pid, count, payload = unpack('>BHB184s', raw_data)
        
        self.sync = sync

        self.error = (pid & 32768) >> 15
        self.start = (pid & 16384) >> 14
        self.priority = (pid & 8192) >> 13
        self.pid = pid & 8191

        self.scramble = (count & 192) >> 6
        self.adapt = (count & 48) >> 4
        self.count = count & 15

        self.payload = payload

    def __str__(self):
        return 'sync: %#x  error: %i  start: %i  priority: %i  pid: %#x  scramble: %i  adapt: %i  count: %#x  len(payload): %i' % (self.sync, self.error, self.start, self.priority, self.pid, self.scramble, self.adapt, self.count, len(self.payload))

class PESPacket(object):
    STREAM_TYPES = {
        '\xbc':     'program_stream_map',
        '\xbd':     'private_stream_1',
        '\xbe':     'padding_stream',
        '\xbf':     'private_stream_2',
        '\xf0':     'ECM_stream',
        '\xf1':     'EMM_stream',
        '\xf2':     'DSM-CC',
        '\xf3':     'ISO/IEG_13552_stream',
        '\xf4':     'PMT',
        '\xf5':     'PMT',
        '\xf6':     'PMT',
        '\xf7':     'PMT',
        '\xf8':     'PMT',
        '\xf9':     'ancillary_stream',
        '\xff':     'program_stream_directory',
        '\xe0':     'Video',
        '\xc0':     'Audio',
    }

    def __init__(self, tspacket=None):
        self.tspacket = tspacket

        self.prefix = None
        self.id = None
        self.length = None

        self.streamid = None
        self.streamtype = None

        if tspacket:
            
            self.parse(tspacket)
            

    def parse(self, tspacket):
        
        if not tspacket.start:
            self.payload = tspacket.payload
            return
        
        #if tspacket.adapt:            
            #data = unpack('>%ic' % len(tspacket.payload),tspacket.payload)

        data = unpack('>%ic' % len(tspacket.payload),tspacket.payload)
        if data[3] in self.STREAM_TYPES:
          self.streamtype = self.STREAM_TYPES[data[3]]
        else:
          self.streamtype = unpack('>%ic' % len(tspacket.payload),tspacket.payload)[3]

    def is_header(self):
        if self.prefix and self.id and self.length:
            return True
        else:
            return False