#!/bin/bash

USAGE="Usage: $SELF brightness (0-100)"
SELF=`basename "$0"`
PERIOD=200000	# Default period in ns
DUTYCYCLE=0	# Start with zero duty cycle

if [ -z "$1" ] 
then
        echo $USAGE
        exit 1
fi

## Check to see if the pwm device is enabled
if [ ! -d /sys/class/pwm/pwmchip0/pwm0 ]
then
	## Prepare the pwm0 device
	echo "0" > /sys/class/pwm/pwmchip0/export
	## Set the polarity
	echo "normal" > /sys/class/pwm/pwmchip0/pwm0/polarity
	echo "1" > /sys/class/pwm/pwmchip0/pwm0/enable
	echo "$DUTYCYCLE" > /sys/class/pwm/pwmchip0/pwm0/duty_cycle
fi

## Moved this here so changing the PERIOD variable can take effect
echo "$PERIOD" > /sys/class/pwm/pwmchip0/pwm0/period

BRIGHTNESS=$1

# Check to make sure the argument is a number
if [ "$BRIGHTNESS" -eq "$BRIGHTNESS" ] 2>/dev/null
then
        # Is a number
        :
else
        echo $USAGE
        exit 1
fi

if [ "$BRIGHTNESS" -lt 0 ]
then
        BRIGHTNESS=0
fi

if [ "$BRIGHTNESS" -gt 100 ]
then
        BRIGHTNESS=100
fi

DCFILE=/sys/class/pwm/pwmchip0/pwm0/duty_cycle
MAX=`cat /sys/class/pwm/pwmchip0/pwm0/period`

LEVEL=$(expr $MAX / 100 \* $BRIGHTNESS)
CURRENT=`cat $DCFILE`
STEP=$PERIOD/100
DELAY=0.008s

LOGFILE=/tmp/pwm.log
echo "$CURRENT  Set to $1 : $LEVEL" >> $LOGFILE
if (( "$LEVEL" > "$CURRENT" ))
then
        for ((x=$CURRENT ; x<$LEVEL; x+=$STEP))
        do
                echo $x > $DCFILE
                #echo $x >> $LOGFILE
                sleep $DELAY
        done
        echo $LEVEL > $DCFILE
else
        for ((x=$CURRENT ; x>$LEVEL ; x-=$STEP))
        do
                echo $x > $DCFILE
                #echo $x #>> $LOGFILE
                sleep $DELAY
        done
        echo $LEVEL > $DCFILE
fi
