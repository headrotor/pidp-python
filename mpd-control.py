#!/usr/bin/python3
import os, sys
from subprocess import call, check_output
import time

# uses mpd2 for python 3 compat
# for python 3: sudo pip3 install python-mpd
# command ref http://pythonhosted.org/python-mpd2/topics/commands.html
from mpd import MPDClient

# #print(client.mpd_version)          # print the MPD version
# print ("status")
# print(client.status())          # print the MPD version
# #print ("stats")
# #print(client.stats())          # print the MPD version
# print(client.currentsong())          # print the MPD version
# #print(client.listall('smb://pidp'))          # print the MPD version
# print(client.notcommands())          # print the MPD version
# print ("-----------------------------commands")
# print(client.notcommands())          # print the MPD version
# #client.stop() # print result of the command "find any house"

# #time.sleep(0.5)
# #client.play() # print result of the command "find any house"
# client.close()                     # send the close command
# client.disconnect()      

"""
My fork of https://github.com/machina-speculatrix/pidp-python -- see below the fold.

picontrol.py: use PiDP control panel switches to
execute mpd2 (music streaming daemon) and display status (mostly mpd music
streaming info) on the LEDs

More information 
http://rotormind.com/blog/2016/PiDP8-streaming-radio-controller/

WARNING: STILL UNDER CONSTRUCTION <digger.gif>

Thank you Steve for doing the heavy interface lifting so we can do this!

NB: PYTHON 3 ONLY.
Requires the PiDP_CP_NT.py library.
Requires python mpd2 -- see above. 

NB: NEEDS TO BE RUN AS ROOT !

Use this as you will. If you blog about what you do with it, a link would be
the honourable thing to do.

For use with Oscar Vermeulen's PiDP kit. Every home should have one. Go here:
	http://obsolescence.wix.com/obsolescence#!pidp-8/cbie

PYTHON 3 ONLY. Requires the PiDP_CP_NT.py library.

NB: NEEDS TO BE RUN AS ROOT !


"""

import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO


def init_mpd(host='localhost'):
    client = MPDClient()               # create client object
    client.timeout = 10                # network timeout in secs (floats allow
    client.idletimeout = None          # timeout for idle is handled seperately
    client.connect(host, 6600)  # connect to localhost:6600
    return client


def get_mpd_status(client):
    """ use mpd2 to get mpd status. Right now just returns volume 
    as a 0-100 int and playlist"""
    result = client.status();
    vol = result['volume']
    sta = result['state']
    return vol, sta

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
            #print("got key " + k) 
            #print("execute action " + str(adict[k]))
            call(adict[k])


CP = PiDP_CP.PiDP_ControlPanel(ledDelay=100, debug=True)

# Okay, so you're set up now. Insert your code here.
# Everything below is for demo purposes only.

print(CP)


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

loop_count = 0
# for blinkenlights
bl_count = 0
loop = True
try:
    # light the mq lights to match the positions of the switches directly beneath.
    # We do this in the loop, too.
    CP.setLedDataBank('mq', CP.switchSetValue('swreg'))

    # make a list of the vertical LEDS to show pos in playlist
    stat_LEDS = ['and','tad','isz','dca',
                 'jms','jmp','iot','opr',
                 'fetch','exec','defer','wrdct',
                 'curad','break']
    
    client = init_mpd()
    
    while loop:

        CP.lightAllLeds(loops=5)

        if loop_count % 5 == 0:
            #CP.setLedDataBank('ma', bl_count)
            # blinkenlights
            #if CP.switchIsOn('swreg0') is True:
            if CP.switchIsOn('swreg0'):
                CP.setLedDataBank('ma', (loop_count << 5) + loop_count)
            else:
                CP.setLedDataBank('ma', 0)
            if not CP.switchIsOn('swreg1'):
                CP.setLedDataBank('mb', ((0x1F&~loop_count) << 5 ) + 0x1F&(~loop_count))
            else:
                CP.setLedDataBank('mb', 0)
            bl_count += 1
            result = client.status()
            vol = int(result['volume'])
            # make bargraph from volume

            for i in range(12):
                if i < int((1.2*vol)/10.0):
                    CP.ledState[0][i] = PiDP_CP.LED_ON
                else:
                    CP.ledState[0][i] = PiDP_CP.LED_OFF
            for i in range(len(stat_LEDS)):
                CP.setLedState(stat_LEDS[i],PiDP_CP.LED_OFF)

            song = int(result['song'])

            if  song < len(stat_LEDS):
                CP.setLedState(stat_LEDS[song - 1],PiDP_CP.LED_ON)                              
             # blink ion as 
        if loop_count > 15:
            CP.setLedState('ion', PiDP_CP.LED_ON)
        else:
            CP.setLedState('ion', PiDP_CP.LED_OFF)
        if loop_count > 30:
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
