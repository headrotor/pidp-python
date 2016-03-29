'''
PiDP control panel - NON-THREADED VERSION

THIS WORKS GREAT EXCEPT FOR BEING EXCEPTIONALLY CRASHY.
PRPBABLY SOMETHING TO DO WITH TURNING ALL THOSE GPIOs FROM INPUT TO OUTPUT
AND BACK AGAIN ALL THE TIME.

by Steve Mansfield-Devine
http://www.lomcovak.com/speculatrix/

Use this as you will. If you blog about what you do with it, a link would be
the honourable thing to do.

For use with Oscar Vermeulen's PiDP kit. Every home should have one. Go here:
	http://obsolescence.wix.com/obsolescence#!pidp-8/cbie

PYTHON 3 ONLY.

NB: NEEDS TO BE RUN AS ROOT !

VERY IMPORTANT: This is a work-in-progress by a non-programmer dilettante.
Use at your own risk. Seriously. If, as a result of using this code,
your dog leaves home, your significant other becomes more snarky than
usual and your house blows up, don't come crying to me. Subject to sudden
updates, changes and inconsistencies.
Very little error-checking so far. That'll come... one day...
So be careful what you pass to methods.

Usage:
	import PiDP_CP_NT as PiDP_CP
	CP = PiDP_CP.PiCP_ControlPanel(<params>)

Use the 'as' in the import because there may be other versions of this coming which
you *may* (no guarantees) be able to sort-of mostly use as a kind of drop-in
replacement. Well, we can all dream.

All parameters are optional and keyworded. Always init with keyword args because of
the future drop-in replacement thing which, because it won't be all that clever, may
have a different order of args. You have been warned.
Args are (with defaults):
	boardCfg='std'		use 'serial' for PiDP's configured with serial option (NOT TESTED)
	ledDelay=None		Experimental. Time to pause (seconds/100,000) when LEDs are lit.
						This is an attempt to make then brighter as the expense of
						slight flicker and possibly slower switch response.
	verbose=False		Use True to print messages to std output
	debug=False			Use True to print debugging messages to std output
(More may appear at any moment.)

A note on 'banks'. In the PiDP, Oscar uses the term 'rows' on the PCB. But these rows are
numbered from 1. As it's better from a programming point of view to number from 0,
and to avoid confusion, I've used the term 'bank'. So bank 0 == row 1.

LEDs --------------------------------------------------------------------------------

IMPORTANT PROPERTIES:
ledBanks[][]		A list of 8 lists containing the names of the LEDs.
ledCfg{}			A dictionary. Each entry consists of:
 						key: string with the name of the LED
						val: list - [bank,column,columnPin]
					Used as a lookup table. Maybe another dict would have been better,
					but hey ho...
ledState[][]		A list of 8 lists (one per LED bank) with values being LED_ON or
					LED_OFF. Used to determine which LEDs light up. Can be set via
					setLedState(). Maps to ledBanks. This is probably the only LED
					property you'd use from your own program.

MAIN METHODS:
lightAllLeds([<loops>])	Briefly flashes the LEDs according to the state settings in the
					ledState property. If you want the LEDs lit, you'll need to call
					lightAllLeds() as frequently as you can from within a loop. The
					optional arg allows you to loop through the scan several times, if
					you want, say, to give priority to LED scanning as opposed to
					switch scanning in your main loop.
lightLeds(<bank>, [<pause>])	Briefly flash the LEDs in a specific bank (0-7). This is
					what's called by lightAllLeds(). If you just want to use one or two
					banks of LEDs, use this in your loop instead. The optional pause arg
					overrides the global ledDelay setting in the constructor. It causes
					this routine to pause when the LEDs are lit. But it is blocking and
					means only one LED bank is lit.
setLedState(<name>)	Set the state (on/off) of a specific LED, referred to by name.
					Doesn't actually light it up, just changes its setting in
					ledState.

SWITCHES ----------------------------------------------------------------------------

IMPORTANT PROPERTIES:
switchBanks[][]		A list of 3 lists containing the names of the switches.
switchCfg{}			A dictionary. Each entry consists of:
 						key: string with the name of the switch
						val: list - [bank,column,columnPin]
					Used as a lookup table.
switchState[][]		A list of 3 lists (one per switch bank) with the values of the
					switches as they were the last time switchScan was run.

MAIN METHODS:
scanAllSwitches()	A wrapper to scanSwitches which reads all the switches. Returns
					True if any of the switches has changed since the last scan.
scanSwitches(<bank>)	Read the positions of the switches in a specific bank (0-2)
					and store the results in switchState. If you only want to use one
					bank of switches, use this in your program's loop, as it'll be
					quicker. Doesn't have to be used in a loop - you can use this or
					scanAllSwitches() ad hoc just to refresh switchState when needed.
					Returns True if a switch in this bank has changed since the last
					scan.
switchPosition(<name>)	Returns the state of the named switch according to switchState.
switchSetting(<name>)	Reads the current physical position of a named switch.
					Doesn't update switchState. I don't know why. It might do someday.

TO DO:
	* Method to pass in a list of LED names to set them on/off
	* Method to pass in a list of switch names and have returned a list showing switch state
'''

import RPi.GPIO as GPIO
import time

LED_ON = GPIO.LOW				# Just to make stuff easier to read. My eyes are old.
LED_OFF = GPIO.HIGH
SWITCH_BANK_ON = GPIO.LOW
SWITCH_BANK_OFF = GPIO.HIGH
SWITCH_ON = 1
SWITCH_OFF = 0
SCAN_START = 1
SCAN_STOP = 0


class PiDP_ControlPanel:

	# ***********************************************************************************
	# ***  INITIALISER / CONSTRUCTOR call it what you will                            ***
	# ***********************************************************************************
	def __init__(self, boardCfg='std', ledDelay=None, verbose=False, debug=False):
		self._ledDelay = ledDelay
		self._verbose = verbose
		self._debug = debug
		if self._debug:
			self._verbose = True
			GPIO.setwarnings(True)
		else:
			GPIO.setwarnings(False)

		GPIO.setmode(GPIO.BOARD)		# In my world, pins use board numbering, not BCM

		self._colPins = [8, 10, 7, 29, 31, 26, 24, 21, 19, 23, 32, 33]
		if boardCfg.lower() == 'serial':		# Untested !
			self._colPins = [3, 5, 7, 29, 31, 26, 24, 21, 19, 23, 32, 33]

		# ---------------------------------------------------------------------
		# ***  LED CONFIGURATION  ***
		# ---------------------------------------------------------------------

		self._ledRowPins = [38, 40, 15, 16, 18, 22, 37, 13]
		self.ledBanks = [
			# Bank 0 (led1)
			['pci1', 'pci2', 'pci3', 'pci4', 'pci5', 'pci6', 'pci7', 'pci8', 'pci9', 'pci10', 'pci11', 'pci12'],
			# Bank 1 (led2)
			['dma1', 'dma2', 'dma3', 'dma4', 'dma5', 'dma6', 'dma7', 'dma8', 'dma9', 'dma10', 'dma11', 'dma12'],
			# Bank 2 (led3)
			['dmb1', 'dmb2', 'dmb3', 'dmb4', 'dmb5', 'dmb6', 'dmb7', 'dmb8', 'dmb9', 'dmb10', 'dmb11', 'dmb12'],
			# Bank 3 (led4)
			['dac1', 'dac2', 'dac3', 'dac4', 'dac5', 'dac6', 'dac7', 'dac8', 'dac9', 'dac10', 'dac11', 'dac12'],
			# Bank 4 (led5)
			['dmq1', 'dmq2', 'dmq3', 'dmq4', 'dmq5', 'dmq6', 'dmq7', 'dmq8', 'dmq9', 'dmq10', 'dmq11', 'dmq12'],
			# Bank 5 (led6)
			['and', 'tad', 'isz', 'dca', 'jms', 'jmp', 'iot', 'opr', 'fetch', 'exec', 'defer', 'wrdct'],
			# Bank 6 (led7)
			['curad', 'break', 'ion', 'pause', 'run', 'dsc1', 'dsc2', 'dsc3', 'dsc4', 'dsc5'],
			# Bank 7 (led8)
			['ddf1', 'ddf2', 'ddf3', 'dif1', 'dif2', 'dif3']
			]

		self.ledCfg = {}				# A dictionary with LED names as keys and
										# a list containing [bank,column,columnPin] as vals
		self.ledState = []				# A list of 8 lists containing the last set state of
										# the 8 banks of LEDs.
		for bankNum in range(0, 8):
			column = 0
			bankLeds = []
			for key in self.ledBanks[bankNum]:
				self.ledCfg[key] = [bankNum, column, self._colPins[column]]
				column += 1
				bankLeds.append(LED_OFF)
			self.ledState.append(bankLeds)

		# ---------------------------------------------------------------------
		# ***  SWITCH CONFIGURATION  ***
		# ---------------------------------------------------------------------
		# The switchRowPins are set to OUTPUT and set LOW to provide a power sink.
		# The column pins, are switched to INPUT with pullups so that they read high normally.
		# But when a switch is on, there's a connection to the switchRow pin which sinks the
		# current and causes the column pin to read low.

		self._switchRowPins = [36, 11, 12]
		self._switchBankPanelOrder = [1, 0, 2] 	# Needed because the bank/row order doesn't
												# match the order of switches on front panel
		self.switchBanks = [
			# Bank 0 (row 1)
			['swreg11', 'swreg10', 'swreg9', 'swreg8', 'swreg7', 'swreg6',
			'swreg5', 'swreg4', 'swreg3', 'swreg2', 'swreg1', 'swreg0'],

			# Bank 1 (row 2)
			['data_field2', 'data_field1', 'data_field0',
			'inst_field2', 'inst_field1', 'inst_field0'],

			# Bank 2 (row 3)
			['start', 'load_add', 'dep', 'exam', 'cont', 'stop', 'sing_step', 'sing_inst' ]
			]

		self.switchState = [						# a list of 3 lists containing the last
			[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],	# scanned state of the 3 banks of switches.
			[0, 0, 0, 0, 0, 0],						# Each bank/list gets updated with
			[0, 0, 0, 0, 0, 0, 0, 0],				# scanSwitches(bank)
			]

		self._previousSwitchState = [0, 0, 0]		# for detecting changes to switch states

		self.switchCfg = {}			# A dictionary with switch names as keys and
		for bank in range(0,3):		# a list containing [bank,column,columnPin] as vals
			column = 0
			for key in self.switchBanks[bank]:
				self.switchCfg[key] = [bank, column, self._colPins[column]]
				column += 1

		# Initial GPIO pin settings
		# set LED row pins to OUTPUT and LOW
		for ledRowPin in self._ledRowPins:
			GPIO.setup(ledRowPin, GPIO.OUT, initial=GPIO.LOW)

		# set switch row pins to OUTPUT and set HIGH
		for switchRowPin in self._switchRowPins:
			GPIO.setup(switchRowPin, GPIO.OUT, initial=GPIO.HIGH)

		# set column pins to INPUT
		for colPin in self._colPins:
			GPIO.setup(colPin, GPIO.IN)

		self._debugPrint('GPIO version:', GPIO.VERSION)

		self.scanAllSwitches()	# get switchState set up

		return


	# *************************************************************************
	# ***  LED METHODS                                                      ***
	# *************************************************************************

	def lightAllLeds(self, loops=1):
		''' Wrapper to self.lightLeds(). Loops through all 8 banks to light all LEDs. '''
		for _ in range(0,loops):
			for bank in range(0,8):
				self.lightLeds(bank)

	def lightLeds(self, bank, pause=None):
		''' Sets the LEDs on or off for all LEDs in a bank, according to the state info held
			in ledState[][].
			This needs to be called repeatedly in as fast a loop as you can manage to keep
			the LEDs lit.
			To turn an LED ON:
				- LED bank row pin must be OUTPUT and set HIGH
				- LED column pin must be OUTPUT and set LOW '''
		# Set coloumn pins to OUTPUT defaulting to HIGH (LED_OFF)
		for pin in self._colPins:
			GPIO.setup(pin, GPIO.OUT, initial=LED_OFF)

		# Take the row pin for this bank to OUTPUT and LOW (LEDs off)
		GPIO.output(self._ledRowPins[bank], GPIO.LOW)

		# Now set the column pins for those LEDS that should be on to LED_ON
		try:
			for ledNum in range(0, len(self.ledBanks[bank])):
				ledName = self.ledBanks[bank][ledNum]
				colpin = self.ledCfg[ledName][2]
				GPIO.output(colpin, self.ledState[bank][ledNum])
		except Exception as e:
			self._exit('Problem setting column pins for LEDs', e)

		# Take the row pin for this bank to HIGH to flash lights
		GPIO.output(self._ledRowPins[bank], GPIO.HIGH)

		# wait a moment
		if pause:
			time.sleep(pause/1000000.0)
		elif self._ledDelay:
			time.sleep(self._ledDelay/1000000.0)

		#take the LED row pin to LOW AGAIN
		GPIO.output(self._ledRowPins[bank], GPIO.LOW)


	def printLedInfo(self):
		''' Print the names of the LEDs on screen with their bank numbers. Well why not? '''
		print('LED names:')
		for bank in range(0, 8):
			for key in self.ledBanks[bank]:
				#print(pFormat.format(key, self.ledCfg[key][0], self.ledCfg[key][1], self.ledCfg[key][2]), end='')
				print('{0:5} {1}'.format(key, self.ledCfg[key][0]), end='')
			print('')

	def setLedState(self, ledName, onOff):
		''' Set the state of an individual, named LED on or off. This changes the state
			in ledState but doesn't change whether the LED is actually on or off - that'll
			happen the next time lightLeds()is called. '''
		bank = self.ledCfg[ledName][0]
		col = self.ledCfg[ledName][1]
		self.ledState[bank][col] = onOff

	# *************************************************************************
	# ***  SWITCH METHODS                                                   ***
	# *************************************************************************

	def printSwitchInfo(self):
		''' Just print out the switch names. Not very useful but I'm easily amused. '''
		print('Switch names:')
		for bank in self._switchBankPanelOrder:
			for key in self.switchBanks[bank]:
				print('{0:12}'.format(key), end='')
			print('')

	def printSwitchState(self, message=None):
		''' Pretty print the state of switches (according to switchState) on screen. '''
		if message: print(message)
		print('d2 d1 d0 i2 i1 i0 11 10 09 08 07 06 05 04 03 02 01 00 st ld dp ex cn sp ss si <')
		for bank in self._switchBankPanelOrder:
			for state in self.switchState[bank]:
				print(' {0} '.format(state), end='')
		print('<')

	def scanAllSwitches(self):
		''' Wrapper to scanSwitches(). Read all switch banks. '''
		changed = False
		for bank in range(0,3):
			bankchanged = self.scanSwitches(bank)
			if bankchanged: changed = True
		return changed

	def scanSwitches(self, bank):
		''' Reads all switches in a bank and updates the switchState[][] property and
			returns a Boolean indicating whether the settings for this bank have changed
			since switchState[][] was last updated.
			Values for switches are:	0 == off == up
										1 == on  == down '''
		state = []
		numericState = 0	# will be stored to see if future state of switch bank has changed
		changed = False
		self._setSwitchBank(bank, SWITCH_BANK_ON)
		# Now go through the switches for this bank reading the column pins
		for switchName in self.switchBanks[bank]:
			column = self.switchCfg[switchName][1]
			colpin = self.switchCfg[switchName][2]
			# read the pin
			switchValue = 1 - GPIO.input(colpin)
			state.append(switchValue)
			# build a numeric value for the state of the switches in the bank. We'll
			# be using this in checking for state changes.
			numericState += (switchValue) << column
		self._setSwitchBank(bank, SWITCH_BANK_OFF)
		# save the state of this bank
		self.switchState[bank] = state
		if numericState != self._previousSwitchState[bank]:
			self._debugPrint('Bank:{0} Previous: {1:<5} Now: {2:<5}'.format(bank, self._previousSwitchState[bank], numericState))
			changed = True
			self._previousSwitchState[bank] = numericState
		return changed

	def switchPosition(self, switchName):
		''' Get the state of a named switch in the switchState property. '''
		bank = self.switchCfg[switchName][0]
		column = self.switchCfg[switchName][1]
		return self.switchState[bank][column]

	def switchSetting(self, switchName):
		''' Read the current physical setting for a single named switch. NB: This does not
			update the switchState[][] property '''
		bank = self.switchCfg[switchName][0]
		colpin = self.switchCfg[switchName][2]
		self._setSwitchBank(bank, SWITCH_BANK_ON)
		switchValue = (1 - GPIO.input(colpin))
		self._setSwitchBank(bank, SWITCH_BANK_OFF)
		return switchValue

	def _setSwitchBank(self, bank, onOff):
		''' Set a switch bank pin:
			- SWITCH_BANK_ON (LOW) for sinking, to read switch(es)
			- SWITCH_BANK_OFF (HIGH) when finished reading '''
		if onOff == SWITCH_BANK_ON:
			try:	# Make all the column pins INPUTS and take HIGH with pull-ups
				for pin in self._colPins:
					GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
				# make all switch rows OUTPUTS defaulting to HIGH
				for pin in self._switchRowPins:
					GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
				# take the row pin for this bank LOW
				GPIO.output(self._switchRowPins[bank], GPIO.LOW)
			except Exception as e:
				self._exit('Uh-oh. Problem when turning switch bank on.\n', e)
		else:
			# set row pins to INPUTS
			for pin in self._switchRowPins:
				GPIO.output(pin, GPIO.IN)
			# make the column pins outputs again
			#for switchName in self.switchBanks[bank]:
			#	GPIO.setup(self.switchCfg[switchName][2], GPIO.OUT, initial=GPIO.LOW)


	# *************************************************************************
	# ***  INTERNAL ('PRIVATE', if you will) METHODS                        ***
	# *************************************************************************

	def _debugPrint(self, *printItems):
		''' A wrapper to self._print() to be used where you want to print stuff only if
			debug is set, not verbose. '''
		if self._debug:
			printItems = printItems
			if isinstance(printItems, tuple): printItems = list(printItems)
			self._print(printItems)

	def _exit(self, *msgs=None):		# to be used in exceptions that should be fatal.
		if msgs: self._print(msgs)
		GPIO.cleanup()
		exit()

	def _print(self, *printItems):
		''' Print stuff, but only if in verbose mode. '''
		if self._verbose or self._debug:
			# In case printItems is a tuple, turn it into a list. Some people say you
			# shouldn't use 'isinstance'. I don't listen to them.
			if isinstance(printItems, tuple): printItems = list(printItems)
			for item in printItems:
				# And again, in case one of the de-tupled items is also a tuple. That's
				# actually happened to me.
				if isinstance(item, tuple): item = list(item)
				if isinstance(item, list):
					for subitem in item:
						print(subitem, end=' ')
				else:
					print(item, end=' ')
			print('')
		return

	def __str__(self):
		''' Print info about this object.'''
		print('PiDP CONTROL PANEL')
		self.printLedInfo()
		print()
		self.printSwitchInfo()
		print()
		self.printSwitchState()
		print('debug:', self._debug, 'verbose:', self._verbose)
		return('')
