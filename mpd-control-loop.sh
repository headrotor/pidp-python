#!/bin/bash
killall mpd-control.py
# loop forever -- can't catch exception when it crashes due to timeout
while true; do
      sudo /home/pi/gith/pidp-python/mpd-control.py > /var/log/mpd-err.log;
done
