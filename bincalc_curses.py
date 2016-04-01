#!/usr/bin/env python3
'''
bincalc.py

A somewhat clumsy and pointless binary calculator program that exists purely as a
way of playing with Oscar Vermeulen's PiDP PDP-8 replica.
If anyone ever points to the PiDP and asks "What's the point of that?" or "What use is
it?", just tell them it's a binary calculator and they'll probably be amazed into
silence (if they don't write you off as a hopeless geek).

Demonstration of the non-threaded version of the PiDP Control Panel class.

Version 1.01

by Steve Mansfield-Devine
http://www.lomcovak.com/speculatrix/

Use this as you will. If you blog about what you do with it, a link would be
the honourable thing to do.

For use with Oscar Vermeulen's PiDP kit. Every home should have one. Go here:
	http://obsolescence.wix.com/obsolescence#!pidp-8/cbie

PYTHON 3 ONLY. Requires the PiDP_CP_NT.py library.

NB: NEEDS TO BE RUN AS ROOT !


WHAT THIS DOES
This binary calculator allows you to enter two binary numbers and perform various
logical operations on them.

HOW IT WORKS
Make sure all the switches are up.
Use the 12 'swreg' switches - the ones directly under the Multiplier Quotient (MQ) lights
- to enter a binary number. The MQ lights will show what you're entering.

Select the Load/Add switch to load this number into memory. It is then displayed/stored
in the Memory Address (MA) line.

Now enter another binary number with the same switches. Switch down the Dep switch to
enter/store this number.

Set the Data Field (DF) switches - the three left-most switches - to select what
operator you want. You use the three switches to enter an octal value in the range 0-7.
	1	and
	2	or
	3	xor
	4	add			'link' LED lights if there's a carry (a 'C' shows on the screen)
	5	nand
	6	sub(tract)	'sc5' LED lights if result is negative (a '-' shows on the screen)
	7   nor

You can do this at any time. You can do it after you've obtained a result to do
another operation.

Then use the Exam switch to get the result.
The result of the operation is shown in the Accumulator (AC) row.
If you have a monitor (attached or via SSH) you'll also get stuff displayed on the
screen. It ain't pretty, but it works.

'''

import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO
import sys, curses

CP = PiDP_CP.PiDP_ControlPanel()

# ****************************************************************************
# ***   FUNCTIONS                                                          ***
# ****************************************************************************

def updateScreen(stdscr, calc):
	stdscr.clear()
	topStr = '{:^8}'.format(operators[calc['opcode']])
	topStr += opFormat.format(calc['input'])
	fillRpt = curses.COLS - len(topStr) - 1
	topStr = topStr + (' ' * fillRpt)
	stdscr.addstr(0,0, topStr, curses.A_REVERSE)
	if calc['opcode'] > 0:
		stdscr.addstr(5,46, '{:4}'.format(operators[calc['opcode']]))
	if calc['op1loaded']:
		stdscr.addstr(5,5, 'op1: ' + opFormat.format(calc['op1']))
		if calc['op2loaded']:
			stdscr.addstr(6,5, 'op2: ' + opFormat.format(calc['op2']))
			if calc['haveResult']:
				resultStr = '   = ' + opFormat.format(calc['result'])
				if calc['negFlag'] == PiDP_CP.LED_ON: resultStr += ' -'
				if calc['carryFlag'] == PiDP_CP.LED_ON: resultStr += ' C'
				stdscr.addstr(7,5, resultStr)

	stdscr.addstr(15,5, '1=AND 2=OR 3=XOR 4=ADD 5=NAND 6=SUB 7=NOR')
	stdscr.refresh()	#update screen

def printMsg(msg):
	stdscr.addstr(20,5, msg)

# ****************************************************************************
# ***   SETUP                                                              ***
# ****************************************************************************

operators = ['---', 'AND', 'OR', 'XOR', 'ADD', 'NAND', 'SUB', 'NOR']
opFormat = '{0:0>12b}  0o{0:0>4o}  0x{0:0>3X}  {0:>4}'

stdscr = curses.initscr()
#curses.LINES				# number  of lines in this screen
curses.curs_set(False)		# turn off the flashing cursor

startMsg = [
	'BINCALC READY...',
	'Enter the first number using the 12 switches',
	'beneath the Multiplier Quotient row. The controls are:',
	'-----------------------------------------------------------',
	'item                  activate with     displayed on',
	'-----------------------------------------------------------',
	'Number to enter       12 main switches  Multiplier Quotient',
	'Store first number    load_add          Memory Address',
	'Store second number   dep               Memory Bank',
	'Get result            exam              Accumulator',
	'Select operator       data_field 1-3    Step Counter 1-3'
]

startLine = 5
for line in startMsg:
	stdscr.addstr(startLine,5, line)
	startLine += 1

# *****************************************************************************
# *** MAIN LOOP                                                             ***
# *****************************************************************************


def main(stdscr):
	calc = {
		'op1': 0,
		'op2': 0,
		'opcode': 0,
		'result': 0,
		'carryFlag': PiDP_CP.LED_OFF,
		'negFlag': PiDP_CP.LED_OFF,
		'haveResult': False,
		'input': 0,
		'op1loaded': False,
		'op2loaded': False
	}
	OP1_DEP_SW = 'load_add'		# switches used to set the numbers and execute
	OP2_DEP_SW = 'dep'			# the calculation. Change these if your version of
	EXEC_SW = 'exam'			# the PiDP has momentary switches. The inst_field
								# switches would be good alternatives
	opLeds = {
		'data_field0': 'sc3',
		'data_field1': 'sc2',
		'data_field2': 'sc1',
	}
	loop = True
	while loop:
		CP.lightAllLeds(loops=5)							# light up the LEDs
		if CP.scanAllSwitches():
			# switches have changed
			if CP.switchIsOn('stop'):
				loop = False
			else:
				calc['input'] = CP.switchSetValue('swreg')
				calc['opcode'] = CP.switchSetValue('data_field')
				CP.setLedDataBank('mq', calc['input'])
				calc['result'] = 0
				calc['carryFlag'] = PiDP_CP.LED_OFF
				calc['negFlag'] = PiDP_CP.LED_OFF
				calc['haveResult'] = False
				if CP.switchIsOn(OP1_DEP_SW):
					if not calc['op1loaded']:
						calc['op1'] = calc['input']
						calc['op1loaded'] = True
					else:
						if CP.switchIsOn(OP2_DEP_SW):
							if not calc['op2loaded']:
								calc['op2'] = calc['input']
								calc['op2loaded'] = True
							else:
								if calc['opcode'] > 0 and CP.switchIsOn(EXEC_SW):
									if calc['opcode'] == 1:						# and
										calc['result'] = calc['op1'] & calc['op2']
									if calc['opcode'] == 2:						# or
										calc['result'] = calc['op1'] | calc['op2']
									if calc['opcode'] == 3:						# xor
										calc['result'] = calc['op1'] ^ calc['op2']
									if calc['opcode'] == 4:						# add
										calc['result'] = calc['op1'] + calc['op2']
										if calc['result'] > 4095:
											calc['result'] = calc['result'] % 4096
											calc['carryFlag'] = PiDP_CP.LED_ON
									if calc['opcode'] == 5:						# nand
										calc['result'] = ~(calc['op1'] & calc['op2']) & 0xFFF	# mask highest bits of 32-bit int to avoid negative
									if calc['opcode'] == 6:						# sub
										calc['result'] = calc['op1'] + ((~calc['op2']) + 1)
										if calc['result'] < 0:
											calc['negFlag'] = PiDP_CP.LED_ON
									if calc['opcode'] == 7:						# nor
										calc['result'] = ~(calc['op1'] | calc['op2']) & 0xFFF	# mask highest bits to avoid negative
									calc['haveResult'] = True
								else:
									calc['haveResult'] = False
						else:
							calc['op2loaded'] = False
							calc['op2'] = 0
				else:
					calc['op1loaded'] = False
					calc['op2loaded'] = False
					calc['op1'] = 0
					calc['op2'] = 0
			CP.setLedDataBank('ma', calc['op1'])
			CP.setLedDataBank('mb', calc['op2'])
			CP.setLedDataBank('ac', calc['result'])
			CP.setLedState('link', calc['carryFlag'])
			CP.setLedState('sc5', calc['negFlag'])
			for switchname in opLeds:
				if CP.switchSetting(switchname):
					CP.setLedState(opLeds[switchname], PiDP_CP.LED_ON)
				else:
					CP.setLedState(opLeds[switchname], PiDP_CP.LED_OFF)
			updateScreen(stdscr, calc)

curses.wrapper(main)
stdscr.clear()
GPIO.cleanup()
