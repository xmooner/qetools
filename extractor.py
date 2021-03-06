#!/usr/bin/env python

import argparse
import sys
from pprint import pprint
import csv
import datetime

from pylab import *

class IterState :
	BODY = "BODY"
	GENERAL_ROUTINES = "GENERAL_ROUTINES"
	PARALLEL_ROUTINES = "PARALLEL_ROUTINES"
	HUBBARD_U = "HUBBARD_U"
	END = "END"

def fromTimeToMsec(timeStr):
	timeStr = timeStr.replace(' ','')
	hours , minutes , mseconds = 0.0 ,0.0, 0.0
	toRet = 0;
	if 'h' in timeStr: 
		hours = float(timeStr.split('h')[0])
		timeStr = timeStr.split('h')[1]
		toRet += hours * 60 * 60 * 1000
	if 'm' in timeStr:
		minutes = float(timeStr.split('m')[0])
		timeStr = timeStr.split('m')[1]
		toRet += minutes * 60 * 1000
	if 's' in timeStr:
		mseconds = int(float(timeStr.split('s')[0]) * 1000)
		toRet += mseconds
	print toRet
	return toRet
	
	



class BenchLine :
	"""
		class representing a single bench line
	"""
	name = ""
	CPUTime = ""
	WALLTime = ""
	Calls = 0
	Parent = ""
	Section = None
	
	def __init__(self, line, parent=None, section=None) :
		assert type(line) is str
		splitted = line.split(' ')
		if section == IterState.END :
			if 'h' in line :
				line = line.replace('h ','h')
			elif 'm' in line :
				line = line.replace('m ','m')
			splitted = line.split(' ')
			self.name = splitted[0]
			self.CPUTime = fromTimeToMsec(splitted[2])
			self.WALLTime = fromTimeToMsec(splitted[4])
			self.Section = section
		else :
			self.name = splitted[0]
			self.CPUTime = fromTimeToMsec(splitted[2])
			self.WALLTime = fromTimeToMsec(splitted[4])
			self.Calls = int (splitted[6])
			self.Parent = parent
			self.Section = section
	
	def toRow(self):
		return [self.name,self.CPUTime,self.WALLTime,self.Calls,self.Parent,self.Section]

		
	
	@staticmethod
	def headers():
		return ["name","cpuTime","wallTime","Calls","Parent","Section"]
			

		
	


parser = argparse.ArgumentParser(description="Parse espresso output file and generate a csv")
parser.add_argument("outfile", help="espresso output file")
parser.add_argument("--csvout-name", help="output csv file name")
args = parser.parse_args()

ofile = args.outfile + ".csv"

if args.csvout_name :
	ofile = args.csvout_name

init_runFinded=False;
benchLines = []

version = ''
start=''
stop=''

#start parsing
#extract generic informations and extract benchmarks lines
with open(args.outfile, 'r') as inputFile:
	for line in inputFile:
		if "init_run" in line and not init_runFinded :
			init_runFinded=True
		if init_runFinded :
			benchLines.append(line)
		if 'PWSCF' in line :
			init_runFinded = False
		if 'Program PWSCF' in line :
			#save version and start
			line = ' '.join(line.split())
			version = line.split(' ')[2]
			start = ' '.join(line.split(' ')[-3:])
		if 'This run was terminated on' in line :
			#save version and start
			line = ' '.join(line.split())
			stop = ' '.join(line.split(' ')[-2:])

			

if len(benchLines) == 0 :
	print "ERROR: invalid input file"
	sys.exit(1)

#clean up the lines
benchLines = [ x.replace('\n','')  for x in benchLines  ]			
benchLines = [ x.replace(')',' ')  for x in benchLines  ]			
benchLines = [ x.replace('(',' ')  for x in benchLines  ]
benchLines = [ x for x in benchLines if len(x.replace(' ','')) != 0 ]
benchLines = [ ' '.join(x.split()) for x in benchLines ] #remove multiple spaces

#iterate
iterState = IterState.BODY
lastParent = ''
finalLines = []
for line in benchLines :
	#set the state of the iteration
	if 'Called by' in line :
		lastParent = line.split(' ')[2][:-1]
		continue
	if 'General routines' in line :
		iterState = IterState.GENERAL_ROUTINES
		continue
	if 'Parallel routines' in line :
		iterState = IterState.PARALLEL_ROUTINES
		continue
	if 'Hubbard U routines' in line :
		iterState = IterState.HUBBARD_U
		continue
	if 'PWSCF' in line :
		iterState = IterState.END
	
	thisParent = None if iterState != IterState.BODY else lastParent
	print "line is: ", line
	benchLine = BenchLine(line,section=iterState,parent=thisParent)
	finalLines.append(benchLine)
	
	if iterState == IterState.END :
		break
	
#map(pprint,map(vars,finalLines))
		
print "version: ",version
print "start: ",start
print "stop: ",stop

#save on ofile
with open(ofile,'w') as toWrite :
	#write the header
	toWrite.write('#version %s\n' % version)
	toWrite.write('#start %s\n' % start)
	toWrite.write('#stop %s\n' % stop)
	toWrite.write('#')
	f_csv = csv.writer(toWrite)
	f_csv.writerow(BenchLine.headers())
	for line in finalLines :
		f_csv.writerow(line.toRow())
	

