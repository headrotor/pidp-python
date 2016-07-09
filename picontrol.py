#!/usr/bin/env python3
import os, sys
from subprocess import call, check_output
import subprocess

'''


My fork of https://github.com/machina-speculatrix/pidp-python -- see below the fold.

My contribution: pipanel.py -- use PiDP control panel switches to
execute arbitrary commands and display status (mostly mpd music
streaming info) on the LEDs

WARNING: STILL UNDER CONSTRUCTION <digger.gif>

Thank you Steve for doing the heavy interface lifting so we can do this!

NB: PYTHON 3 ONLY. Requires the PiDP_CP_NT.py library.

NB: NEEDS TO BE RUN AS ROOT !

Use this as you will. If you blog about what you do with it, a link would be
the honourable thing to do.

For use with Oscar Vermeulen's PiDP kit. Every home should have one. Go here:
	http://obsolescence.wix.com/obsolescence#!pidp-8/cbie

PYTHON 3 ONLY. Requires the PiDP_CP_NT.py library.

NB: NEEDS TO BE RUN AS ROOT !


'''
import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO


def get_mpd_status():
    """ use mpc to get mpd status. Right now just returns volume 
    as a 0-100 int"""
    result = check_output(['mpc', 'status'])
    result = result.decode('utf-8')
    lines = result.split('\n')
    if len(lines) >= 3:
        #print(lines[2])
        parsed = lines[2].split()
        if len(parsed) > 0:
            return(int(parsed[1].strip('%')))
    return -1

def process_switches(cp, adict=None):
    """ process switches with dict of action. Remember last switch state"""
    # action dictionary
    if adict is None:
        adict = {"stop":['mpc', 'pause'],
                 "start":['mpc', 'play'],
                 "load_add":['mpc', 'next'],
                 "dep":['mpc', 'prev'],
                 "exam":['mpc','volume','+5'],
                 "cont":['mpc','volume','-5'],
                 "stop":['mpc','stop'],
                 "data_field2":['mpc','play','1'],
                 "data_field1":['mpc','play','2'],
                 "data_field0":['mpc','play','3'],
                 "inst_field2":['mpc','play','4'],
                 "inst_field1":['mpc','play','5'],
                 "inst_field0":['mpc','play','6'],

        }
    for k in adict:
        if cp.switchIsOn(k):
            print("got key " + k) 
            print("execute action " + str(adict[k]))
            call(adict[k])


CP = PiDP_CP.PiDP_ControlPanel(ledDelay=100, debug=True)

# Okay, so you're set up now. Insert your code here.
# Everything below is for demo purposes only.

print(CP)



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

# set accumulator row to show binary representation of number
CP.setLedDataBank('ac', 2730)

print('Ready...')
# ------------------------------------------------------------------------------
# ***  MAIN LOOP  ***
# ------------------------------------------------------------------------------
# Note that we call the lightAllLeds() method twice in the loop. The more often
# you call it in a loop, the brighter and less flickery the LEDs will be.
# For each  task that you add to the loop, I suggest adding another call to
# lightAllLeds().
# Note also, though, that we're really not doing much in this loop. It remains
# to be seen how effectively the LEDs work should you actually do anything
# serious here. I would suggest spawning any major tasks as separate threads or
# sub-processes if possible.

loop_count = 0
loop = True
try:
    # light the mq lights to match the positions of the switches directly beneath.
    # We do this in the loop, too.
    CP.setLedDataBank('mq', CP.switchSetValue('swreg'))
        
    while loop:

        CP.lightAllLeds(loops=5)
        # make bargraph from volume
        if loop_count % 5 == 0:
            vol = get_mpd_status()
            for i in range(0, 10):
                if i < int((1.39*vol)/10.0):
                    CP.ledState[0][i] = PiDP_CP.LED_ON
                else:
                    CP.ledState[0][i] = PiDP_CP.LED_OFF
        if loop_count > 10:
            CP.setLedState('ion', PiDP_CP.LED_ON)
        else:
            CP.setLedState('ion', PiDP_CP.LED_OFF)
        if loop_count > 20:
            loop_count = 0
        loop_count += 1    
        CP.lightAllLeds(loops=5)							        
        # make volume bargraph
        #CP.setLedDataBank('mq', CP.switchSetValue('swreg'))
        if CP.scanAllSwitches():
            CP.printSwitchState('Changed')
            process_switches(CP)
            #CP.setLedDataBank('mq', CP.switchSetValue('swreg'))
            print('df: {0}    if: {1}    sw: {2}'.format(CP.switchSetValue('data_field'),
                                                         CP.switchSetValue('inst\_field'),
                                                         CP.switchSetValue('swreg')))
                                    

            #if CP.switchIsOn('stop'):
            #    loop = False

        CP.lightAllLeds(loops=5)						       # light up the LEDs
        # Now trigger LEDs according to the dict we created above
        #for switchname in switchedLeds:
        #    if CP.switchSetting(switchname):
        #        CP.setLedState(switchedLeds[switchname], PiDP_CP.LED_ON)
        #    else:
        #        CP.setLedState(switchedLeds[switchname], PiDP_CP.LED_OFF)

except KeyboardInterrupt:
    # I'm bored and I've hit Ctrl-C
    print('\nStopped via keyboard interrupt.')
except Exception as e:
    # Uh-oh
    print('Unanticipated and frankly rather worrying exception:\n', e)
    raise e
GPIO.cleanup()
