#!/usr/bin/env python
import sys, time
from SerialPort_linux import *

# serial device to communicate with
DEVICE="/dev/ttyUSB0"
# baudrate used for communication with pkernel
KERNEL_BAUDRATE=115200

def recvByte():
	i = tty.read()
	return ord(i)

def sendByte(byte):
	tty.write(chr(byte))
	tty.flush()

def sendWord(word):
	sendByte(word & 0xFF)
	sendByte((word >> 8) & 0xFF)

def sendDWord(dword):
	sendByte(dword & 0xFF)
	sendByte((dword >> 8) & 0xFF)
	sendByte((dword >> 16) & 0xFF)
	sendByte((dword >> 24) & 0xFF)

def pkernCHIPERASE():
	sendByte(0x15)
	if (recvByte() != 0x45):
		raise Exception
	print "wait..."
	if (recvByte() != 0x23):
		raise Exception

def pkernERASE(address, size):
	sendByte(0x12)
	if (recvByte() != 0x11):
		raise Exception
	sendDWord(address)
	sendWord(size)
	if (recvByte() != 0x18):
		raise Exception
	#print "Erasing done."


def pkernWRITE(address, size, data):
	# send WRITE command
	sendByte(0x13)
	if (recvByte() != 0x37):
		raise Exception
	# tell desired address and size
	sendDWord(address)
	sendWord(size)

	# write binary stream of data
	for i in range(0, size):
		sendByte(data[i])

	if (recvByte() != 0x28):
		raise Exception
	#print "Flashing done."


class FlashSequence(object):
	def __init__(self, address, data):
		self.address = address
		self.data = data

# list of all our address/data pairs to flash
flashseqs = []


print "Initializing serial port..."
tty = SerialPort(DEVICE, None, KERNEL_BAUDRATE)

# check command line arguments
if len(sys.argv) != 2:
	print "Usage: " + sys.argv[0] + " [mhx-file]"
	sys.exit(1)

# read in data from mhx-file before starting
try:
	fp = open(sys.argv[1], "r")
except IOError:
	print sys.argv[0] + ": Error - couldn't open file " + sys.argv[1] + "!"
	sys.exit(1)

linecount = 0
for line in fp:
	linecount += 1
	# get rid of newline characters
	line = line.strip()

	# we're only interested in S2 (data sequence with 3 address bytes) records by now
	if line[0:2] == "S2":
		byte_count = int(line[2:4], 16)
		# just to get sure, check if byte count field is valid
		if (len(line)-4) != (byte_count*2):
			print sys.argv[0] + ": Warning - inavlid byte count field in " + \
				sys.argv[1] + ":" + str(linecount) + ", skipping line!"
			continue

		# address and checksum bytes are not needed
		byte_count -= 4
		address = int(line[4:10], 16)
		datastr = line[10:10+byte_count*2]

		# convert data hex-byte-string to real byte data list
		data = []
		for i in range(0, len(datastr)/2):
			data.append(int(datastr[2*i:2*i+2], 16))

		# add flash sequence to our list
		flashseqs.append(FlashSequence(address, data))

#print "The following flash sequences have been read in:"
#for seq in flashseqs:
#	print hex(seq.address) + ":", [hex(x) for x in seq.data]


# let the fun begin!
"""
for seq in flashseqs:
	print "Erasing", len(seq.data), "bytes at address", hex(seq.address)
	pkernERASE(seq.address, len(seq.data))
"""
print "ChipErase..."
pkernCHIPERASE()
print "Chip erasing done."


print "Flashing",
for seq in flashseqs:
	sys.stdout.write(".")
	sys.stdout.flush()
	# skip seqs only consisting of 0xffs
	seqset = list(set(seq.data))
	if len(seqset) == 1 and seqset[0] == 0xff:
		continue
	#print "Flashing", len(seq.data), "bytes at address", hex(seq.address)
	pkernWRITE(seq.address, len(seq.data), seq.data)
print

"""
sendByte(0x99) #exit and wait
print "Reset your board now to run code from Flash"
"""

sendByte(0x97) #exit and restart