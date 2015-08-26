#!/bin/bash

# AlarmPi installation script
# Download all the necessary libraries to run AlarmPi

# AlarmPi needs access to device-level stuff which requires root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

git clone https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code.git
git clone https://github.com/guyc/py-gaugette.git
git clone https://github.com/seanbechhofer/raspberrypi.git seanbechhofer
git clone https://github.com/baudm/mplayer.py.git
git clone https://github.com/PDKK/RpiLcdBackpack.git
git clone https://github.com/jso/py-wink.git

svn co http://projects.mattdyson.org/projects/LCDControl
git clone https://github.com/jwr456/alarmpi.git

touch "RpiLcdBackpack/__init__.py"

cd alarmpi

mkdir sounds
wget -q -nH --cut-dirs=2 --no-parent --reject "index.html*" -r "http://home.mattdyson.org/downloads/alarmpi-portal-sounds/" -P sounds

ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack/Adafruit_7Segment.py
ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_I2C/Adafruit_I2C.py
ln -s ../Adafruit-Raspberry-Pi-Python-Code/Adafruit_LEDBackpack/Adafruit_LEDBackpack.py
ln -s ../py-gaugette/gaugette/
ln -s ../LCDControl/LCDControl/
ln -s ../mplayer.py/mplayer/
ln -s ../RpiLcdBackpack/
ln -s ../seanbechhofer/python/TSL2561.py
ln -s ../py-wink/wink/

CREDFILE="CalendarCredentials.py"
touch $CREDFILE
echo -n "Enter Google Developer Client ID: "
read clientid
echo
echo -n "Enter Google Developer Client secret: "
read clientsecret
echo
echo -n "Enter Google Developer key: "
read developerkey
echo
echo -n "Enter Google Calendar address: "
read calendar

echo "CLIENT_ID='$clientid'" >> $CREDFILE
echo "CLIENT_SECRET='$clientsecret'" >> $CREDFILE
echo "DEVELOPER_KEY='$developerkey'" >> $CREDFILE
echo "CALENDAR='$calendar'" >> $CREDFILE

echo "goto https://pyspotify.mopidy.com/en/latest/installation/ to setup Spotify support"
echo "The Wink API is currently in beta and not yet publicly available. However, you may request a set of tokens by emailing questions@quirky.com and asking for early access to the Wink API."
