__author__ = 'joel'

#!/usr/bin/python

from Weather import WeatherFetcher
import logging
import datetime
import pytz
import sys
import Settings

def suffix(d):
   return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

weatherFetcher = WeatherFetcher()
log = logging.getLogger('root')

log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

log.debug("Loading settings")
settings = Settings.Settings()
settings.setup()

log.debug("Playing weather information")

now = datetime.datetime.now(pytz.timezone('US/Eastern'))

weather = ""
try:
    weather = weatherFetcher.getWeather().speech()
except Exception:
    log.exception("Failed to get weather information")

day = now.strftime("%d").lstrip("0")
day += suffix(now.day)

hour = now.strftime("%I").lstrip("0")

salutation = "morning" if now.strftime("%p")=="AM" else "afternoon" if int(hour) < 18 else "evening"

# Today is Monday 31st of October, the time is 9 56 AM
speech = "Good %s Joel. Today is %s %s %s, the time is %s %s %s. " % (salutation, now.strftime("%A"), day, now.strftime("%B"), hour, now.strftime("%M"), now.strftime("%p"))
speech += weather

log.debug("weather information: %s" % speech)