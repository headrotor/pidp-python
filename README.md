# pidp-python
Python code for Oscar Vermeulen's PiDP PDP-8 replica.
By Steve Mansfield-Devine
http://www.lomcovak.com/speculatrix/

NB: All code in this repo is written by a hobbyist and is barely fit to be viewed, let alone used. YMMV. YHBW. SOOA.

The files are:

PiDP_CP_NT.py
Contains a Python 3 control panel class for lighting the LEDs and reading the state of the switches on the PiDP. All the necessary documentation (or, put another way, all the documentation you're going to get) is in the file.
The 'NT' bit means 'non-threaded' because I did have an idea that I might do a version that uses some threaded processes. Maybe. We'll see.

pidpnt-demo.py
This is a Python 3 demo program to show how the control panel class can be used.

bincalc.py
Another demo program. This uses the PiDP to carry out binary calculations. Enter two numbers using the switches and then AND, OR, XOR, ADD, SUB, NAND or NOR them. Results are shown on the PiDP's LEDs and on screen. Amaze your friends!

If you find this code doesn't work with Python 2.x it's because you're using Python 2.x. I mean, come on...
