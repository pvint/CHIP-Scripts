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
	speed = 0

if args.dutycycle is not None:
	dutycycle = args.dutycycle

	# Start of pules is 0, convert % duty cycle to 12 bit value
	end = int(40.95 * dutycycle )

	# Force 0 to off and 100 to full on to avoid rounding errors
	if dutycycle == 0:
		end = 0

	if dutycycle == 100:
		end = 4095

else:
	#  --end or -e overrides duty cycle
	if args.end is not None:
		end = args.end
	else:
		print("Either --dutycycle (-d) or --end (-e) must be specified.")
		exit()

## If -c -1 is set it's ALLCALL  - just force all LEDs to level instantly
if channel == -1:
	pwm.set_all_pwm(0, end)
	exit()

# Get current value - if it's the same exit
currentOn, currentOff = pwm.get_pwm(channel)
#print ("Was: ", currentOff, " New:", end)

if currentOff == end:
	exit()

## Loop from current value to new value with delay
if end > currentOff:
	step = 1 * speed
else:
	step = -1 * speed

#print(currentOff, ":", end, ":", step)

for level in range(currentOff, end + step, step):
	if level > 4095:
		level = 4095

	pwm.set_pwm(channel, 0, level)
	#print(currentOff, ":", end, ":", step, ":", level)

# Force end correction to fix step issues
pwm.set_pwm(channel, 0, end)
exit()

# Configure min and max servo pulse lengths
servo_min = 150  # Min pulse length out of 4096
servo_max = 600  # Max pulse length out of 4096

# Helper function to make setting a servo pulse width simpler.
def set_servo_pulse(channel, pulse):
	pulse_length = 1000000	# 1,000,000 us per second
	pulse_length //= 60	   # 60 Hz
	print('{0}us per period'.format(pulse_length))
	pulse_length //= 4096	 # 12 bits of resolution
	print('{0}us per bit'.format(pulse_length))
	pulse *= 1000
	pulse //= pulse_length
	pwm.set_pwm(channel, 0, pulse)

pwm.set_pwm_freq(freq)


## Testing getting current value
pwm.get_pwm(channel)
#print('Val: {0}'.format(mode1 = pwm._device.readU8()))

print('Set duty cycle to 75% then 50%  Ctrl-C to quit...')
while True:
	# Move servo on channel O between extremes.
	pwm.set_pwm(channel, 1, 3000)
	oon, ooff = pwm.get_pwm(channel)
	#print (oon, ooff)
	print('Val: {0}	{1}'.format(oon,ooff))


	time.sleep(1)
	pwm.set_pwm(channel, 9, 2222)
	oon, ooff = pwm.get_pwm(channel)
	print('Val: {0}	{1}'.format(oon, ooff))

	time.sleep(1)
