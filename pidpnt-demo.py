#!/usr/bin/env python3
'''
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


'''

import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO

CP = PiDP_CP.PiDP_ControlPanel(ledDelay=100, debug=True)

# Okay, so you're set up now. Insert your code here.
# Everything below is for demo purposes only.

print(CP)

# Use ion LED as a sort-of power light - ie, turn it on just to show we're alive
CP.setLedState('ion', PiDP_CP.LED_ON)

# Turn on alternate pc LEDs. It's pretty.
for i in range(1,12,2):
	CP.setLedState('pc' + str(i), PiDP_CP.LED_ON)

# The following dictionary is just an idea of what might be done. It links switches
# with LEDs by name, so that if the switch is on, so is the LED. The key is the
# switch name and the value the LED name.
switchedLeds = {
	'sing_step': 'pause',
	'start': 'run',
	'data_field0': 'df3',
	'data_field1': 'df2',
	'data_field2': 'df1',
	'inst_field0': 'if3',
	'inst_field1': 'if2',
	'inst_field2': 'if1'
}

# let's roll some lights across the Memory Buffer (dmb) row, which is bank 2.
# We'll use direct access to the ledState property to do this.
bank = 2
for i in range(0,14):
	#dmb = bank 2
	if i < 12:
		CP.ledState[bank][i] = PiDP_CP.LED_ON
	if i > 1:
		CP.ledState[bank][i-2] = PiDP_CP.LED_OFF
	CP.lightLeds(bank, pause=100000)


# set accumulator row to show binary representation of number
CP.setLedDataBank('ac', 2730)

print('Ready...')
# ------------------------------------------------------------------------------
# ***  MAIN LOOP  ***
# ------------------------------------------------------------------------------
# Note that we call the lightAllLeds() method twice in the loop. The more often
# you call it in a loop, the brighter and less flickery the LEDs will be. For each
# task that you add to the loop, I suggest adding another call to lightAllLeds().
# Note also, though, that we're really not doing much in this loop. It remains to
# be seen how effectively the LEDs work should you actually do anything serious
# here. I would suggest spawning any major tasks as separate threads or
# sub-processes if possible.
loop = True
try:
	# light the mq lights to match the positions of the switches directly beneath.
	# We do this in the loop, too.
	CP.setLedDataBank('mq', CP.switchSetValue('swreg'))

	while loop:
		CP.lightAllLeds(loops=5)							# light up the LEDs
		if CP.scanAllSwitches():
			CP.printSwitchState('Changed')
			CP.setLedDataBank('mq', CP.switchSetValue('swreg'))
			print('df: {0}    if: {1}    sw: {2}'.format(CP.switchSetValue('data_field'),
							CP.switchSetValue('inst_field'), CP.switchSetValue('swreg')))
			if CP.switchIsOn('stop'): loop = False
		CP.lightAllLeds(loops=5)							# light up the LEDs
		# Now trigger LEDs according to the dict we created above
		for switchname in switchedLeds:
			if CP.switchSetting(switchname):
				CP.setLedState(switchedLeds[switchname], PiDP_CP.LED_ON)
			else:
				CP.setLedState(switchedLeds[switchname], PiDP_CP.LED_OFF)

except KeyboardInterrupt:						# I'm bored and I've hit Ctrl-C
	print('\nStopped via keyboard interrupt.')
except Exception as e:							# Uh-oh
	print('Unanticipated and frankly rather worrying exception:\n', e)

GPIO.cleanup()
