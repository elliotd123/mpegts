#!/usr/bin/env python
import subprocess
import sys
import simplejson as json

class stream:
  def __init__(self,streamData):
    self.streamData = streamData
    self.index = streamData['index']
    self.codec_name = streamData['codec_name']
    self.codec_type = streamData['codec_type']
    self.width = streamData.get('width',None)
    self.height = streamData.get('height',None)
    self.codec_tag = streamData['codec_tag']
    self.pix_fmt = streamData.get('pix_fmt',None)
    self.pid = streamData['id']

class program:
  def __init__(self,programData):
    self.programData = programData
    self.pmt_pid = self.programData['pmt_pid']
    self.program_id = self.programData['program_id']

    #Get stream data
    self.streamCount = len(self.programData['streams'])
    self.streams = []
    for i in range(0,self.streamCount):
      self.streams.append(stream(self.programData['streams'][i]))

class mpegData:
  def __init__(self,multicast):
    self.multicast = multicast
    cmd = 'ffprobe -show_format -show_programs -print_format json udp://@' + self.multicast
    res = subprocess.Popen(cmd,stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    self.result = res.stdout.read()
    self.error = res.stderr.read()
    #self.result = subprocess.check_output(['ffprobe','-show_format','-show_programs','-print_format','json','udp://@' + self.multicast])
    self.js = json.loads(self.result)
    self.programCount = len(self.js['programs'])
    self.programs = []
    for i in range(0,self.programCount):
      self.programs.append(program(self.js['programs'][i]))
    

if __name__ == '__main__':
  if (len(sys.argv) < 2):
    print('Usage: ' + sys.argv[0] + ' <multicast_address>:<port>')
    sys.exit(0)
  multicast = sys.argv[len(sys.argv)-1]

  scte=False
  if (len(sys.argv) > 2 and sys.argv[1] == '-scte'):
    scte=True
  print('Collecting data from stream...')
  d = mpegData(multicast)

  if not scte:
    print(d.result)
    sys.exit(0)

  if scte:
    scte_found = False
    print('Checking for scte data...')
    print(str(d.programCount) + ' program(s) found.')
    scte_pid = -1
    for i in range(0,d.programCount):
      print('Checking program ' + str(d.programs[i].program_id) + '...')
      for j in range(0,d.programs[i].streamCount):
        stream = d.programs[i].streams[j]
        if (stream.codec_name == 'scte_35'):
          print('\tSCTE data found! PID ' + str(int(stream.pid,16)) + ' (' + stream.pid + ')')
          scte_pid = int(stream.pid,16)
          scte_found = True
      if not scte_found:
        print('\tNo SCTE data found.')
    if scte_found:
      import mpeg2
      mpeg2.start_collection(multicast,pid=scte_pid,scte=True)