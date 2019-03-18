#!/bin/bash
killall mpd-control-loop.sh
# wait for mpd to fire up and read library
sleep 30

# loop forever -- can't catch exception when it crashes due to timeout
#(while true; do /home/pi/gith/pidp-python/mpd-control.py > /var/log/mpd-err.log; done) &

/home/pi/mpd-control-loop.sh  &
#sudo /home/pi/gith/pidp-python/mpd-control.py > /dev/null 2> /var/log/mpd-err.log &

killall dash-poll-daemon.py
sudo /home/pi/gith/rpi-utils/localfoo/dash-poll-daemon.py > /var/log/dash-daemon.log 2>&1 &

