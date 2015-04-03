#!/usr/bin/python

import time
import datetime
import pytz
import threading
import Settings
from Adafruit_7Segment import SevenSegment

class ClockThread(threading.Thread):

   def __init__(self, settings):
      threading.Thread.__init__(self)
      self.segment = SevenSegment(address=0x70)
      self.stopping=False
      #self.settings = Settings.Settings()
      self.settings = settings
      self.colon = 0

   def stop(self):
      self.segment.disp.clear()
      self.stopping=True

   def run(self):
      while(not self.stopping):
          now = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))
          #hour = now.hour
          hour = int(now.strftime("%I").lstrip("0"))

          minute = now.minute
          second = now.second

          # Set hours
          self.segment.writeDigit(0, int(hour / 10))     # Tens
          self.segment.writeDigit(1, hour % 10)          # Ones
          # Set minutes
          self.segment.writeDigit(3, int(minute / 10))   # Tens
          self.segment.writeDigit(4, minute % 10)        # Ones
          # Toggle colon
          self.segment.writeDigitRaw(2, self.colon)
          self.colon = self.colon ^ 0x2

          time.sleep(1)
