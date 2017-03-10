#!/usr/bin/env python
import sys
import traceback
import socket
import struct
import datetime
from pat import PMTTable
from pat import PATTable
from mpeg_packet import TSPacket
from mpeg_packet import PESPacket


def start_collection(multicast, pid=-1, scte=False):
    ip_address = multicast.split(':')[0]
    port = multicast.split(':')[1]
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((ip_address,int(port)))
    
    mreq = struct.pack("4sl", socket.inet_aton(ip_address), socket.INADDR_ANY)
    
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    
    psize = 188 
    chunksize = 7
    counter = 0
    PATchecked = False
    PMTchecked = False
    while True:
      data = b''
      for i in range(0,chunksize):
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
          if (PATchecked == False and packet.pid == 0):
            pat = PATTable(packet.raw_data)
            print('\nPAT found: Program ' + str(pat.program))
            print('\tPID found: ' + str(pat.pid))
            PATchecked = True

          if (pid == -1 or packet.pid == pid):
            print('')
            sys.stdout.write(str(datetime.datetime.now()) + ' - ')
            print(packet)
            try:
              pes = PESPacket(packet)
              #print(pes.streamtype)
            except:
              print('Oops')
          counter += 1

          #Print out counter info
          if (counter % 100 == 0 and False):
            prefix = 'Mbits checked: '
            mb = counter * psize * chunksize * 8 / (1024 * 1024)
            for i in range(0,len(str(mb)) + len(prefix)):
              sys.stdout.write('\b \b')
              sys.stdout.flush()
            sys.stdout.write(prefix + str(mb))
            sys.stdout.flush()

if __name__ == '__main__':
  if (len(sys.argv) < 2):
    print('Usage: ' + sys.argv[0] + ' <multicast>:<port> [pid]')
    sys.exit(0)
  pid = -1
  if (len(sys.argv) >= 3):
    pid = int(sys.argv[2])
  start_collection(sys.argv[1], pid)
