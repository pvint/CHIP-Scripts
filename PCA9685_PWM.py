## Control PCA9685 PWM outputs from NextThing CHIP

## TODO
# Options: set freq, set o/p to value, instantaneous or smooth, all on/off, speed delay

from __future__ import division
import time

# Import the PCA9685 module.
import Adafruit_PCA9685
import argparse
#pwm = Adafruit_PCA9685.PCA9685(address=0x42,busnum=1)
#pwm.set_pwm(0, 1, 3000)
#currentOn, currentOff = pwm.get_pwm(0)

#print ("Was: ", currentOff)

#exit()

## Get arguments
parser = argparse.ArgumentParser(description="Control PCA9685 PWM Outputs via I2C.")
parser.add_argument("-v", "--verbose", help="Enable verbose debugging output", action="store_true")
parser.add_argument("-f","--freq", help="Set PWM Frequency", type=int)
parser.add_argument("-d","--dutycycle", help="Set duty cycle in percent (0-100)", type=float)
parser.add_argument("-e","--end", help="Set end of pulse (0-4095)", type=int)
parser.add_argument("-s","--speed", help="Set speed (fading) delay (ms)", type=int)
parser.add_argument("-a","--address", help="I2C Address, ie: 0x42",required=True)
parser.add_argument("-c", "--channel", help="PWM Channel (0-15) or -1 for all", type=int,required=True)
parser.add_argument("-b", "--bus", help="I2C Bus Number (0-x)", type=int, required=True)
parser.add_argument("-r", "--reset", help="Reset the PCA9685", action="store_true")

args = parser.parse_args()

verbose = args.verbose

# Uncomment to enable debug output.
#import logging
#logging.basicConfig(level=logging.DEBUG)


def software_reset():
    """Sends a software reset (SWRST) command to all servo drivers on the bus."""
    # Setup I2C interface for device 0x00 to talk to all of them.
    import Adafruit_GPIO.I2C as I2C
    i2c = I2C
    a = {"busnum": args.bus}
    device = i2c.get_i2c_device(0x00, **a)
    device.writeRaw8(0x06)  # SWRST


## Rec 709 luminosity adjustment
## Reason: Our eyes do not perceive the brightness in a linear fashion
## and the difference between 1% and 2% appears greater than the difference between 90% and 100%
## TODO: Move this to the class

# Level is 0-1 
def linearToVisualLevel( level ):
	if level < 0.081:
		vLevel = level / 4.5
	else:
		vLevel = (( level + 0.099) / 1.099 ) ** ( 1 / 0.45 )  

	#print ("Level set: ", level, " Adjusted level: ", vLevel)

	return vLevel

## Init the device
a = {"address":int(args.address, 16), "busnum": args.bus, "reset": args.reset}
pwm = Adafruit_PCA9685.PCA9685( **a )
#pwm = Adafruit_PCA9685.PCA9685(address=0x42,busnum=1)

# Send reset if -r
#if args.reset:
#	print ("Resetting device")
#	software_reset()

## If frequency is default 200Hz we will assume that the device has been reset
freq = pwm.get_pwm_freq()
if freq <= 200:
	print("Resetting PCA9685.")
	a = {"address":int(args.address, 16), "busnum": args.bus, "reset": "True"}
	pwm = Adafruit_PCA9685.PCA9685( **a )

	freq = 1000
	pwm.set_pwm_freq(freq)
	

# Set frequency if -f is specified
if args.freq is not None:
	freq = args.freq
	pwm.set_pwm_freq(freq)
else:
	freq = pwm.get_pwm_freq()
	#print ("Freq: ", freq)
	

channel = args.channel

if args.speed is not None:
	speed = args.speed
else:
	speed = 1

## All levels will be from 0-1
if args.dutycycle is not None:
	dutycycle = args.dutycycle

	# Start of pulse is 0, convert % duty cycle to 12 bit value
	end = dutycycle / 100.0

	# Force 0 to off and 100 to full on to avoid rounding errors
	if dutycycle == 0:
		end = 0.0

	if dutycycle == 100:
		end = 1.0

else:
	#  --end or -e overrides duty cycle
	if args.end is not None:
		end = args.end / 4095.0
	else:
		print("Either --dutycycle (-d) or --end (-e) must be specified.")
		exit()

## If -c -1 is set it's ALLCALL  - just force all LEDs to level instantly
if channel == -1:
	pwm.set_all_pwm(0, int ( end * 4095 ) )
	exit()


adjustedEnd = pwm.get_visual_level( end ) 

# Get current value - if it's the same exit
currentOn, currentOff = pwm.get_pwm(channel)
#print ("Was: ", currentOff, " New:", adjustedEnd)
currentOn /= 4095.0
currentOff /= 4095.0
#print ("CurrentOff: ", currentOff)

if currentOff == adjustedEnd:
	exit()

## Loop from current value to new value with delay
if adjustedEnd > currentOff:
	step = 1 * speed
else:
	step = -1 * speed

#print(currentOff, " AdjEnd:", adjustedEnd, ":", step)

first = int( 4095 * currentOff )
last = int( 4095 * adjustedEnd )

for level in range(first, last + step, step):
	if level > 4095:
		level = 4095

	pwm.set_pwm(channel, 0, level)

# Force end correction to fix step issues
pwm.set_pwm(channel, 0, last)
#print ( "Set to: ", last / 4095)
exit()
