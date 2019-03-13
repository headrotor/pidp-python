#!/usr/bin/python3
import os, sys
from subprocess import call, check_output
import time

# uses mpd2 for python 3 compat
# for python 3: sudo pip3 install python-mpd
# command ref http://pythonhosted.org/python-mpd2/topics/commands.html
from mpd import MPDClient, CommandError

"""
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
    # deprecated by use
    result = client.status();
    vol = result['volume']
    sta = result['state']
    return vol, sta


def process_toggles(cp, toggle_dict):
    adict = {"sing_inst":['/bin/bash','/home/pi/top_curtains.sh'],
             "sing_step":['/bin/bash','/home/pi/top_curtains.sh']}

    for key in toggle_dict:
        if toggle_dict[key] != cp.switchSetting(key):
            print("switch " + key + " toggled")
            toggle_dict[key] = cp.switchSetting(key)    
            call(adict[key])
            
def process_switches(cp, adict=None):
    """ process switches with dict of action. Remember last switch state"""
    # action dictionary
    if adict is None:
        adict = {"stop":['mpc', 'toggle'],
                 "load_add":['mpc', 'next'],
                 "dep":['mpc', 'prev'],
                 "exam":['mpc','volume','+5'],
                 "cont":['mpc','volume','-5'],
        }
    for k in adict:
        if cp.switchIsOn(k):
            #print("got key " + k) 
            #print("execute action " + str(adict[k]))
            call(adict[k])






def blinkenlights(CP):

    # blinkenlights on swreg3 swreg4
    if not CP.switchIsOn('swreg3'):
        CP.setLedDataBank('ma', (loop_count << 5) + loop_count)
    else:
        CP.setLedDataBank('ma', 0)
    if not CP.switchIsOn('swreg4'):
        CP.setLedDataBank('mb', ((0x1F&~loop_count) << 5 ) + 0x1F&(~loop_count))
    else:
        CP.setLedDataBank('mb', 0)

def vol_bargraph(CP, client):
    # make a list of the vertical LEDS to show pos in playlist
    stat_LEDS = ['and','tad','isz','dca',
                 'jms','jmp','iot','opr',
                 'fetch','exec','defer','wrdct',
                 'curad','break']
    
    result = client.status()
    song, vol = -1, -1
    try:
        song = int(result['song'])
        vol = int(result['volume'])

    except KeyError:
        # happens when no playlist loaded
        #print('mpd key error')
        # light status LED for position in playlist
        for led in stat_LEDS:
            CP.setLedState(led,PiDP_CP.LED_ON)



    for i in range(len(stat_LEDS)):
        CP.setLedState(stat_LEDS[i],PiDP_CP.LED_OFF)

    if song < 0:
        return

    # make volume bargraph
    for i in range(12):
        if i < int((1.2*vol)/10.0):
            CP.ledState[0][i] = PiDP_CP.LED_ON
        else:
            CP.ledState[0][i] = PiDP_CP.LED_OFF
    # light status LED for position in playlist
    if  song < len(stat_LEDS):
        CP.setLedState(stat_LEDS[song],PiDP_CP.LED_ON)                                

def handle_start(CP,client):
    #if CP.scanAllSwitches():
    #    CP.printSwitchState('Changed')
    if CP.switchIsOn('start'):
                
        # spcial treatment for start switch. Clear
        # playlist, load new playlist based on toggles

        #print(CP.switchSetValue('swreg'))
        swreg = int(CP.switchSetValue('swreg'))
        # ones complement not trivial
        mask =  (1 << swreg.bit_length()) - 1
        swreg = swreg^mask
        print(repr(swreg))
        client.clearerror()
        client.clear()
        playlistname = "{:1d}_playlist".format(swreg & 0x07)
        print("new playlist " + playlistname)
        try:
            client.load(playlistname)
        except CommandError:
            print("no such playlist :(")
        else:
            client.play()
        return False
    else:
        return True


def init_cp(CP):
    # dict of switch names we want to check for toggling (changed) since last call
    toggles = {'sing_step':False,'sing_inst':False}
    # init toggles dict
    for key in toggles:
        if CP.switchIsOn(key):
            toggles[key] = CP.switchSetting(key)
    return toggles

if __name__ == "__main__":

    CP = PiDP_CP.PiDP_ControlPanel(ledDelay=100, debug=True)

    toggles = init_cp(CP)
    client = init_mpd()

    loop_count = 0
    # main loop
    try:
        while True: 

            CP.lightAllLeds(loops=5)
            if loop_count % 5 == 0:
                blinkenlights(CP)
                try:
                    vol_bargraph(CP, client)
                except socket.timeout:
                    print("socket timeout")
                    pass
                
            # blink ion as status light
            if loop_count > 15:
                CP.setLedState('ion', PiDP_CP.LED_ON)
            else:
                CP.setLedState('ion', PiDP_CP.LED_OFF)

            if loop_count > 30:
                loop_count = 0

            loop_count += 1    
            CP.lightAllLeds(loops=5)

            if CP.scanAllSwitches():
                if handle_start(CP,client):
                    process_switches(CP)
                process_toggles(CP, toggles)

    except KeyboardInterrupt:
        # I'm bored and I've hit Ctrl-C
        print('\nStopped via keyboard interrupt.')
    except Exception as e:
        # Uh-oh
        print('Unanticipated and frankly rather worrying exception:\n', e)
        raise e
    finally:
        GPIO.cleanup()
