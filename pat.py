#!/usr/bin/env python
import struct

def ItoH(hex_data):
	return int(hex_data.encode('hex'),16)

class PATTable(object):
  def __init__(self, raw_data=None):
    self.raw_data = raw_data
    self.program = ItoH(raw_data[13]) << 8 | ItoH(raw_data[14])
    self.pid = (ItoH(raw_data[15]) << 8 | ItoH(raw_data[16])) - 0xe000

class PMTTable(object):
  def __init__(self, raw_data=None):
    self.raw_data = raw_data
