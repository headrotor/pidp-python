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

CP = PiDP_CP.PiDP_ControlPanel()

# ****************************************************************************
# ***   FUNCTIONS                                                          ***
# ****************************************************************************


def printCurrentSettings():
	operandsStr = opFormat.format(operand1)
	operandsStr += '{:^6}'.format(operators[opcode])
	operandsStr += opFormat.format(operand2)
	if op1loaded and op2loaded and haveResult:
		resultStr = '= ' + opFormat.format(result)
		if negFlag == PiDP_CP.LED_ON: resultStr += ' -'
		if carryFlag == PiDP_CP.LED_ON: resultStr += ' C'
	else:
		resultStr = ''
	print(operandsStr, resultStr)


# ****************************************************************************
# ***   SETUP                                                              ***
# ****************************************************************************
operators = ['---', 'AND', 'OR', 'XOR', 'ADD', 'NAND', 'SUB', 'NOR']
operand1 = 0
operand2 = 0
opcode = 0
result = 0
carryFlag = True
negFlag = PiDP_CP.LED_OFF
haveResult = PiDP_CP.LED_OFF

opFormat = '{0:0>12b} {0:4o} 0x{0:3X} {0:<4}'

op1loaded = False
op2loaded = False

OP1_DEP_SW = 'load_add'		# switches used to set the numbers and execute
OP2_DEP_SW = 'dep'			# the calculation. Change these if your version of
EXEC_SW = 'exam'			# the PiDP has momentary switches. The inst_field
							# switches would be good alternatives
opLeds = {
	'data_field0': 'sc3',
	'data_field1': 'sc2',
	'data_field2': 'sc1',
}

print('bincalc ready...')

# *****************************************************************************
# *** MAIN LOOP                                                             ***
# *****************************************************************************
loop = True
# main function
while loop:
	CP.lightAllLeds(loops=5)							# light up the LEDs
	if CP.scanAllSwitches():
		# switches have changed
		if CP.switchIsOn('stop'):
			loop = False
		else:
			entered = CP.switchSetValue('swreg')
			opcode = CP.switchSetValue('data_field')
			CP.setLedDataBank('mq', entered)
			result = 0
			carryFlag = PiDP_CP.LED_OFF
			negFlag = PiDP_CP.LED_OFF
			haveResult = False
			if CP.switchIsOn(OP1_DEP_SW):
				if not op1loaded:
					operand1 = entered

					print('Setting op1:', opFormat.format(operand1))
					op1loaded = True
					printCurrentSettings()
				else:
					if CP.switchIsOn(OP2_DEP_SW):
						if not op2loaded:
							operand2 = entered
							print('Setting op2:', opFormat.format(operand2))
							op2loaded = True
							printCurrentSettings()
						else:
							if opcode > 0 and CP.switchIsOn(EXEC_SW):
								if opcode == 1:						# and
									result = operand1 & operand2
								if opcode == 2:						# or
									result = operand1 | operand2
								if opcode == 3:						# xor
									result = operand1 ^ operand2
								if opcode == 4:						# add
									result = operand1 + operand2
									if result > 4095:
										result = result % 4096
										carryFlag = PiDP_CP.LED_ON
								if opcode == 5:						#nand
									result = ~(operand1 & operand2) & 0xFFF	# mask highest bits of 32-bit int to avoid negative
								if opcode == 6:						# sub
									result = operand1 - operand2
									if result < 0:
										negFlag = PiDP_CP.LED_ON
								if opcode == 7:						#nor
									result = ~(operand1 | operand2) & 0xFFF	# mask highest bits to avoid negative
								haveResult = True
								printCurrentSettings()
							else:
								haveResult = False
								printCurrentSettings()
					else:
						op2loaded = False
						operand2 = 0
			else:
				op1loaded = False
				operand1 = 0
		CP.setLedDataBank('ma', operand1)
		CP.setLedDataBank('mb', operand2)
		CP.setLedDataBank('ac', result)
		CP.setLedState('link', carryFlag)
		CP.setLedState('sc5', negFlag)
		for switchname in opLeds:
			if CP.switchSetting(switchname):
				CP.setLedState(opLeds[switchname], PiDP_CP.LED_ON)
			else:
				CP.setLedState(opLeds[switchname], PiDP_CP.LED_OFF)


GPIO.cleanup()
