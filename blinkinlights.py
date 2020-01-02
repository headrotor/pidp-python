#!/usr/bin/python3
import os, sys
import socket
from subprocess import call, check_output
import time


# uses mpd2 for python 3 compat
# for python 3: sudo pip3 install python-mpd
# command ref http://pythonhosted.org/python-mpd2/topics/commands.html


#from mpd import MPDClient, CommandError


# local imports, symlinked from 
from mpd_logic import MPDLogic
from dmx_logic import DMXLEDS


"""
PYTHON 3 ONLY. Requires the PiDP_CP_NT.py library.

NB: NEEDS TO BE RUN AS ROOT !


"""

import PiDP_CP_NT as PiDP_CP
import RPi.GPIO as GPIO


# def get_mpd_status(client):
#     """ use mpd2 to get mpd status. Right now just returns volume 
#     as a 0-100 int and playlist"""
#     # deprecated by use
#     result = client.status();
#     vol = result['volume']
#     sta = result['state']
#     return vol, sta


def process_toggles(cp, toggle_dict, dmx):
#    adict = {"sing_inst":['/bin/bash','/home/pi/top_curtains.sh'],
#             "sing_step":['/bin/bash','/home/pi/top_curtains.sh']}

    for key in toggle_dict:
        if toggle_dict[key] != cp.switchSetting(key):
            print("switch " + key + " toggled")
            print("state " + str(toggle_dict[key]))
            toggle_dict[key] = cp.switchSetting(key)    
            #call(adict[key])
            if key == "sing_inst":
                if toggle_dict[key] == 1:
                    dmx.clients[0].set_switch(True)
                else:
                    dmx.clients[0].set_switch(False)
            elif key == "sing_step":
                if toggle_dict[key] == 1:
                    dmx.clients[2].set_switch(True)
                else:
                    dmx.clients[2].set_switch(False)
                    
def process_switches(cp, mpd):
    """ process switches with dict of action. Remember last switch state"""
    # action dictionary

    adict = {"stop":['mpc', 'toggle'],
             "load_add":['mpc', 'next'],
             "dep":['mpc', 'prev'],
             "exam":['mpc','volume','+5'],
             "cont":['mpc','volume','-5'],
    }
    for k in adict:
        if cp.switchIsOn(k):
            print("got key " + k) 
            #print("execute action " + str(adict[k]))
            #call(adict[k])
            if k == "stop":
                mpl.toggle_play()                
            elif k == 'load_add':
                mpd.client.next()
            elif k == 'dep':
                mpd.client.previous()
            elif k == 'exam':
                mpd.volume_incr(+5)
            elif k == 'cont':
                mpd.volume_incr(-5)
            

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


        
def vol_bargraph(CP, mpl):
    # make a list of the vertical LEDS to show pos in playlist
    stat_LEDS = ['and','tad','isz','dca',
                 'jms','jmp','iot','opr',
                 'fetch','exec','defer','wrdct',
                 'curad','break']
    
    #result = client.status()

    result = mpl.get_status()
    
    if result is None:
        return
    if "error" in result:
        print("Error, skipping")
        return

    vol = mpl.volume
    # make volume bargraph
    for i in range(12):
        if i < int((1.2*vol)/10.0):
            CP.ledState[0][i] = PiDP_CP.LED_ON
        else:
            CP.ledState[0][i] = PiDP_CP.LED_OFF
    # light status LED for position in playlist

    for i in range(len(stat_LEDS)):
        CP.setLedState(stat_LEDS[i],PiDP_CP.LED_OFF)

    song = mpl.song
    if  song < len(stat_LEDS):
        CP.setLedState(stat_LEDS[song],PiDP_CP.LED_ON)                                

def handle_start(CP,mpl):
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
        #print(repr(swreg))

        mpl.client.clearerror()
        mpl.client.clear()
        playlistname = "{:1d}_playlist".format(swreg & 0x07)
        print("new playlist " + playlistname)
        mpl.client.load(playlistname)
        mpl.client.play()
        # try:
        #     mpl.client.load(playlistname)
        # except CommandError:
        #     print("no such playlist :(")
        # else:
        #     mpl.client.play()
        return False
    else:
        return True


def init_cp(CP):
    # dict of switch names we want to check for toggling (changed) since last call
    toggles = {'data_field0':False, 'inst_field0':False,
               'data_field2':False, 'swreg11':False,
               'swreg10':False, 'swreg9':False,
               'sing_step':False,'sing_inst':False}
    # init toggles dict
    for key in toggles:
        #if CP.switchIsOn(key):
        toggles[key] = CP.switchSetting(key)

    return toggles

if __name__ == "__main__":

    CP = PiDP_CP.PiDP_ControlPanel(ledDelay=100, debug=True)

    toggles = init_cp(CP)

    mpl = MPDLogic()


    dmx = DMXLEDS()
    
    loop_count = 0
    # main loop
    try:
        while True: 

            CP.lightAllLeds(loops=5)
            if loop_count % 5 == 0:
                blinkenlights(CP)
                vol_bargraph(CP, mpl)
                
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
                if handle_start(CP,mpl):
                    process_switches(CP,mpl)
            process_toggles(CP, toggles, dmx)

    except KeyboardInterrupt:
        # I'm bored and I've hit Ctrl-C
        print('\nStopped via keyboard interrupt.')
    except Exception as e:
        # Uh-oh
        print('Unanticipated and frankly rather worrying exception:\n', e)
        raise e
    finally:
        GPIO.cleanup()
