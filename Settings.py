import sqlite3
import subprocess
import CalendarCredentials
import logging
import json
import pytz

log = logging.getLogger('root')

# Radio stations we can play through mplayer
STATIONS = [
       {"name":"BBC Radio 1", "url":"http://www.radiofeeds.co.uk/bbcradio1.pls"},
       {"name":"BBC Radio 2", "url":"http://www.radiofeeds.co.uk/bbcradio2.pls"},
       {"name":"Capital FM", "url":"http://ms1.capitalinteractive.co.uk/fm_high"},
       {"name":"Kerrang Radio", "url":"http://tx.whatson.com/icecast.php?i=kerrang.aac.m3u"},
       {"name":"Magic 105.4", "url":"http://tx.whatson.com/icecast.php?i=magic1054.aac.m3u"},
       {"name":"Smooth Radio", "url":"http://media-ice.musicradio.com/SmoothUK.m3u"},
       {"name":"XFM", "url":"http://media-ice.musicradio.com/XFM.m3u"},
       {"name":"BBC Radio London", "url":"http://www.radiofeeds.co.uk/bbclondon.pls"},
    ]

class Settings:
   # Database connection details
   DB_NAME='settings.db'
   JSON_NAME='settings.json'
   TABLE_NAME='settings'

   # Path to executable to modify volume
   VOL_CMD='../vol'

   # Our default settings for when we create the table
   DEFAULTS_LIST= [
      ('volume','85','Volume','textbox','standard','',''), # Volume
      ('station','0','Radio Station to Play','textbox','advanced','\d+','Must be a digit'), # Radio station to play
      ('radio_delay','10','Radio Delay','textbox','advanced','',''), # Delay (secs) to wait for radio to start
      ('snooze_length','9','Time (minutes) to Snooze','textbox','standard','\d+','Must be a digit'), # Time (mins) to snooze for
      ('max_brightness','15','Maximum Brightness (0-15)','textbox','standard','\d+','Must be a digit'), # Maximum brightness
      ('min_brightness','0','Minimum Brightness (0-15)','textbox','standard','\d+','Must be a digit'), # Minimum brightness
      ('brightness_timeout','20','Time (seconds) after which to revert back to auto-brightness','textbox','advanced','\d+','Must be a digit'), # Time (secs) after which we should revert to auto-brightness
      ('menu_timeout','20','Time (seconds) after which an untouched menu should close','textbox','advanced','\d+','Must be a digit'), # Time (secs) after which an un-touched menu should close
      ('wakeup_time','0','Time (minutes) before event to sound alarm','textbox','advanced','\d+','Must be a digit'), # Time (mins) before event that alarm should be triggered (excluding travel time) (30 mins pre-shift + 45 mins wakeup)
      ('manual_alarm','','Manual alarm time','textbox','invisible','[0-2][0-9][0-5][0-9]','Must be a 24hr time'), # Manual alarm time (default not set)
      ('calendar',CalendarCredentials.CALENDAR,'Calendar to gather events from','textbox','invisible','',''), # Calendar to gather events from
      ('holiday_mode','0','Is Holiday Mode Enabled (no-alarm)','textbox','standard','\d+','Must be a digit'), # Is holiday mode (no auto-alarm setting) enabled?0
      ('sfx_enabled','1','Are sound affects enabled','textbox','advanced','\d+','Must be a digit'), # Are sound effects enabled?
      ('default_wake','','If the alarm is scheduled for later than this, ignore and default to this','textbox','advanced','[0-2][0-9][0-5][0-9]','Must be a 24hr time'), # If our alarm gets scheduled for later than this, ignore and default to this
      ('alarm_timeout','120','Time (minutes) to automatically cancel an alarm','textbox','standard','\d+','Must be a digit'), # If the alarm is still going off after this many minutes, stop it
      ('weather_location','New York, NY','Location for which to fetch weather','textbox','standard','',''), # The location to load weather for0
      ('weather_on_alarm','1','Speak weather on alarm cancel','textbox','standard','\d+','Must be a digit'), # Read out the weather on alarm cancel
      ('preempt_cancel','600','Time (seconds) before an alarm in which it can be cancelled','textbox','advanced','\d+','Must be a digit'), # Number of seconds before an alarm that we're allowed to cancel it
      ('location_home','201 E 19th st, New York, NY','Location used for travel time calculation','textbox','standard','',''), # Location for home
      ('location_work','Stamford, CT','Location of event used for travel time calculation','textbox','standard','',''), # Default location for work (if lookup from event fails)
      ('use_lcd','0','Use LCD or not','textbox','invisible','\d+','Must be a digit'), # Use LCD or not
      ('timezone','US/Eastern','PYTZ timezone','textbox','invisible','',''), # pytz timezone
   ]

   DEFAULTS = {
      "snooze_length":{
        "formOrder":1,
        "key":"snooze_length",
        "value":"9",
        "description":"Time (minutes) to Snooze",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "alarm_timeout":{
        "formOrder":2,
        "key":"alarm_timeout",
        "value":"120",
        "description":"Time (minutes) to automatically cancel an alarm",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "holiday_mode":{
        "formOrder":3,
        "key":"holiday_mode",
        "value":"false",
        "description":"Is Holiday Mode Enabled (no-alarm)",
        "formType":"radio",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":"true, false"
      },
      "default_wake":{
        "formOrder":4,
        "key":"default_wake",
        "value":"",
        "description":"If the alarm is scheduled for later than this ignore and default to this",
        "formType":"textbox",
        "visibility":"advanced",
        "formRegexp":"[0-2][0-9][0-5][0-9]",
        "formRegexpMessage":"Must be a 24hr time (1645)",
        "formNullable":"null",
        "formDropdownValues":""
      },
      "preempt_cancel":{
        "formOrder":5,
        "key":"preempt_cancel",
        "value":"600",
        "description":"Time (seconds) before an alarm in which it can be cancelled",
        "formType":"textbox",
        "visibility":"advanced",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "wakeup_time":{
        "formOrder":6,
        "key":"wakeup_time",
        "value":"0",
        "description":"Time (minutes) before event to sound alarm",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "timezone":{
        "formOrder":7,
        "key":"timezone",
        "value":"US/Eastern",
        "description":"Alarm Timezone",
        "formType":"dropdown",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":pytz.common_timezones
      },
      "weather_on_alarm":{
        "formOrder":20,
        "key":"weather_on_alarm",
        "value":"true",
        "description":"Speak weather on alarm cancel",
        "formType":"radio",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":"true, false"
      },
      "weather_location":{
        "formOrder":21,
        "key":"weather_location",
        "value":"New York, NY",
        "description":"Location for which to fetch weather",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "location_home":{
        "formOrder":22,
        "key":"location_home",
        "value":"201 E 19th st, New York, NY",
        "description":"Location used for travel time calculation",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "location_work":{
        "formOrder":23,
        "key":"location_work",
        "value":"Stamford, CT",
        "description":"Location of event used for travel time calculation",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "station":{
        "formOrder":30,
        "key":"station",
        "value":"BBC Radio 1",
        "description":"Radio Station to Play",
        "formType":"dropdown",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":STATIONS["name"].iteritems()
      },
      "radio_delay":{
        "formOrder":31,
        "key":"radio_delay",
        "value":"10",
        "description":"Radio Delay",
        "formType":"textbox",
        "visibility":"advanced",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "min_brightness":{
        "formOrder":40,
        "key":"min_brightness",
        "value":"0",
        "description":"Minimum Brightness (0-15)",
        "formType":"dropdown",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":xrange(0,15)
      },
      "max_brightness":{
        "formOrder":41,
        "key":"max_brightness",
        "value":"15",
        "description":"Maximum Brightness (0-15)",
        "formType":"dropdown",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":xrange(0,15)
      },
      "brightness_timeout":{
        "formOrder":42,
        "key":"brightness_timeout",
        "value":"20",
        "description":"Time (seconds) after which to revert back to auto-brightness",
        "formType":"textbox",
        "visibility":"advanced",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "use_lcd":{
        "formOrder":43,
        "key":"use_lcd",
        "value":"false",
        "description":"Use LCD or not",
        "formType":"radio",
        "visibility":"standard",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":"true, false"
      },
      "sfx_enabled":{
        "formOrder":44,
        "key":"sfx_enabled",
        "value":"true",
        "description":"Are sound affects enabled",
        "formType":"radio",
        "visibility":"advanced",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":"true, false"
      },
      "volume":{
        "formOrder":45,
        "key":"volume",
        "value":"85",
        "description":"Volume",
        "formType":"textbox",
        "visibility":"standard",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit (1-100)",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "calendar":{
        "formOrder":999,
        "key":"calendar",
        "value":"CalendarCredentials.CALENDAR",
        "description":"Calendar to gather events from",
        "formType":"textbox",
        "visibility":"invisible",
        "formRegexp":"",
        "formRegexpMessage":"",
        "formNullable":"notnull",
        "formDropdownValues":""
      },
      "manual_alarm":{
        "formOrder":999,
        "key":"manual_alarm",
        "value":"",
        "description":"Manual alarm time",
        "formType":"textbox",
        "visibility":"invisible",
        "formRegexp":"[0-2][0-9][0-5][0-9]",
        "formRegexpMessage":"Must be a 24hr time (1645)",
        "formNullable":"null",
        "formDropdownValues":""
      },
      "menu_timeout":{
        "formOrder":999,
        "key":"menu_timeout",
        "value":"20",
        "description":"Time (seconds) after which an untouched menu should close",
        "formType":"textbox",
        "visibility":"invisible",
        "formRegexp":"\\d+",
        "formRegexpMessage":"Must be a digit",
        "formNullable":"notnull",
        "formDropdownValues":""
      }
   }

   def __init__(self):
      #self.conn = sqlite3.connect(self.DB_NAME, check_same_thread=False)
      self.jsonFile = open(self.JSON_NAME,'w+')
      #self.c = self.conn.cursor()
      self.settings = []

   def setupDb(self):
      # This method called once from alarmpi main class
      # Check to see if our table exists, if not then create and populate it
      r = self.c.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?;',(self.TABLE_NAME,))
      if self.c.fetchone()[0]==0:
         self.firstRun()
      # Set the volume on this machine to what we think it should be
      self.setVolume(self.getInt('volume'))

   def setup(self):
      # This method called once from alarmpi main class
      # Check to see if our JSON file exists, if not then create and populate it
      with open(self.JSON_NAME) as data_file:
         self.settings = json.load(self.jsonFile)
      if self.settings is None:
         self.firstRun()
      # Set the volume on this machine to what we think it should be
      self.setVolume(self.getInt('volume'))


   def firstRunDb(self):
      log.warn("Running first-time SQLite set-up")
      self.c.execute('CREATE TABLE '+self.TABLE_NAME+' (name text, value text, desc text, form_type text, form_visibility text, form_validation text, form_validation_message text)')
      self.c.executemany('INSERT INTO '+self.TABLE_NAME+' VALUES (?,?,?,?,?,?,?)',self.DEFAULTS)
      self.conn.commit()

   def firstRun(self):
      log.warn("Running first-time JSON set-up")
      json.dump(self.DEFAULTS, self.jsonFile)

   def getDb(self,key):
      self.c.execute('SELECT * FROM '+self.TABLE_NAME+' WHERE name=?',(key,))
      r = self.c.fetchone()
      if r is None:
         raise Exception('Could not find setting %s' % (key))
      return r[1]

   def get(self,key):
      r = self.settings[key]["value"]
      if r is None:
         raise Exception('Could not find setting %s' % (key))
      return r

   def getInt(self,key):
      try:
         return int(self.get(key))
      except ValueError:
         log.warn("Could not fetch %s as integer, value was [%s], returning 0",key,self.get(key))
         return 0

   def setDb(self,key,val):
      self.get(key) # So we know if it doesn't exist

      if key=="volume":
         self.setVolume(val)

      self.c.execute('UPDATE '+self.TABLE_NAME+' SET value=? where name=?',(val,key,))
      self.conn.commit()

   def set(self,key,val):
      self.get(key) # So we know if it doesn't exist

      if key=="volume":
         self.setVolume(val)

      self.settings[key]["value"] = val
      json.dump(self.settings, self.jsonFile)

   def setVolume(self,val):
      subprocess.Popen("%s %s" % (self.VOL_CMD,val), stdout=subprocess.PIPE, shell=True)
      log.info("Volume adjusted to %s", val)

   def __del__(self):
      self.conn.close()

if __name__ == '__main__':
   print "Showing all current settings"
   settings = Settings()
   for s in settings.DEFAULTS:
      print "%s = %s" % (s[0], settings.get(s[0]))
