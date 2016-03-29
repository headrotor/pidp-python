#!/usr/bin/env python3
'''	Demonstration of the non-threaded version of the PiDP Control Panel class. '''

import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO

DEBUG = True

CP = PiDP_CP.PiDP_ControlPanel(ledDelay=50, debug=DEBUG)

print(CP)

# For demo purpose only

# Use ion LED as a sort-of power light - ie, turn it on just to show we're alive
CP.setLedState('ion', PiDP_CP.LED_ON)

# Turn on alternate pci LEDs. It's pretty.
for i in range(1,12,2):
	CP.setLedState('pci' + str(i), PiDP_CP.LED_ON)

# The following dictionary is just an idea of what might be done. It links switches
# with LEDs by name, so that if the switch is on, so is the LED. The key is the
# switch name and the value the LED name.
switchedLeds = {
	'sing_step': 'pause',
	'start': 'run',
	'data_field0': 'ddf3',
	'data_field1': 'ddf2',
	'data_field2': 'ddf1',
	'inst_field0': 'dif3',
	'inst_field1': 'dif2',
	'inst_field2': 'dif1'
}

# let's roll some lights across the Memory Buffer (dmb) row, which is bank 2.
# We'll use direct access to the ledState property to do this.
bank = 2
for i in range(0,12):
	#dmb = bank 2

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
	while loop:
		CP.lightAllLeds(loops=5)							# light up the LEDs
		if CP.scanAllSwitches():
			CP.printSwitchState('Changed')
			if CP.switchPosition('stop') == PiDP_CP.SWITCH_ON:
				loop = False
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
	print('Unanticipated and frankly rather worrying exception:', e)
finally:
	print('Cleaning up...')
	GPIO.cleanup()

GPIO.cleanup()
