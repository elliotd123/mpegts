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

def main():
    
    pid = 0
    if (len(sys.argv) < 2):
      print('Usage: ' + sys.argv[0] + ' <multicast>:<port>')
      sys.exit(0)
    if (len(sys.argv) >= 3):
      pid=int(sys.argv[2])
    ip_address = sys.argv[1].split(':')[0]
    port = sys.argv[1].split(':')[1]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip_address,int(port)))
    
    mreq = struct.pack("4sl", socket.inet_aton(ip_address), socket.INADDR_ANY)
    
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    psize = 188 
    chunksize = 7
    counter = 0
    while True:
      data = b''
      for i in range(0,7):
        l_data = sock.recv(10240)
      	data += l_data
      if not data:
      	break
      
      # Chop off anything before the sync bit
      sync_offset = data.find('\x47')
      if sync_offset == -1:
          print 'No sync bit in packet.'
          continue
      if sync_offset != 0:
          print 'Resync'
          data = data[sync_offset:]
      
      for i in range(chunksize):
          packet = data[:psize]
          data = data[psize:]
      
          packet = TSPacket(packet)
          #if (packet.start):
          if (pid == 0 or packet.pid == pid):
            print('')
            print(packet)
            try:
              pes = PESPacket(packet)
              print(pes.streamtype)
            except:
              #print(traceback.format_exc())
              print('Oops')
          counter += 1
          if (counter % 100 == 0):
            prefix = 'Frames checked: '
            for i in range(0,len(str(counter)) + len(prefix)):
              sys.stdout.write('\b \b')
              sys.stdout.flush()
            sys.stdout.write(prefix + str(counter))
            sys.stdout.flush()

if __name__ == '__main__': main()
