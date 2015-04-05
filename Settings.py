import sqlite3
import subprocess
import CalendarCredentials
import logging
import json
import pytz
import sys
from codecs import BOM_UTF8

log = logging.getLogger('root')
# log.setLevel(logging.DEBUG)
#
# stream = logging.StreamHandler(sys.stdout)
# stream.setLevel(logging.DEBUG)
#
# formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
# stream.setFormatter(formatter)
#
# log.addHandler(stream)

# Database connection details
DB_NAME = 'settings.db'
JSON_NAME = 'settings.json'
TABLE_NAME = 'settings'


class Settings:

    # Path to executable to modify volume
    VOL_CMD = '../vol'

    def __init__(self):
        # self.conn = sqlite3.connect(self.DB_NAME, check_same_thread=False)
        # self.c = self.conn.cursor()
        self.settings = None


    def getStations(self):
        stations = ''
        # Radio stations we can play through mplayer
        STATIONS_DICT = {"BBC Radio 1": "http://www.radiofeeds.co.uk/bbcradio1.pls",
                    "BBC Radio 2": "http://www.radiofeeds.co.uk/bbcradio2.pls",
                    "Capital FM": "http://ms1.capitalinteractive.co.uk/fm_high",
                    "Kerrang Radio": "http://tx.whatson.com/icecast.php?i=kerrang.aac.m3u",
                    "Magic 105.4": "http://tx.whatson.com/icecast.php?i=magic1054.aac.m3u",
                    "Smooth Radio": "http://media-ice.musicradio.com/SmoothUK.m3u",
                    "XFM": "http://media-ice.musicradio.com/XFM.m3u",
                    "BBC Radio London": "http://www.radiofeeds.co.uk/bbclondon.pls"}
        STATIONS = [("http://www.radiofeeds.co.uk/bbcradio1.pls", "BBC Radio 1"),
                    ("http://www.radiofeeds.co.uk/bbcradio2.pls", "BBC Radio 2"),
                    ("http://ms1.capitalinteractive.co.uk/fm_high", "Capital FM"),
                    ("http://tx.whatson.com/icecast.php?i=kerrang.aac.m3u", "Kerrang Radio"),
                    ("http://tx.whatson.com/icecast.php?i=magic1054.aac.m3u", "Magic 105.4"),
                    ("http://media-ice.musicradio.com/SmoothUK.m3u", "Smooth Radio"),
                    ("http://media-ice.musicradio.com/XFM.m3u", "XFM"),
                    ("http://www.radiofeeds.co.uk/bbclondon.pls", "BBC Radio London")]
        for station in STATIONS_DICT.keys():
            stations += station
        return STATIONS


    def setupDb(self):
        # This method called once from alarmpi main class
        # Check to see if our table exists, if not then create and populate it
        r = self.c.execute('SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name=?;', (self.TABLE_NAME,))
        if self.c.fetchone()[0] == 0:
            self.firstRun()
        # Set the volume on this machine to what we think it should be
        self.setVolume(self.getInt('volume'))


    def setup(self):
        # This method called once from alarmpi main class
        # Check to see if our JSON file exists, if not then create and populate it
        try:
            with open(JSON_NAME, 'r') as f:
                try:
                    self.settings = json.load(f)
                    #log.debug("settings: %s" % json.dumps(self.settings))
                except ValueError as e:
                    log.error("ValueError: {0}".format(e.args))
                    self.firstRun()
        except IOError as io:
            log.error("IOError: {0}".format(io.args))
            self.firstRun()

        # Set the volume on this machine to what we think it should be
        self.setVolume(self.getInt('volume'))


    def firstRunDb(self):
        log.warn("Running first-time SQLite set-up")
        self.c.execute(
            'CREATE TABLE ' + self.TABLE_NAME + ' (name text, value text, desc text, form_type text, form_visibility text, form_validation text, form_validation_message text)')
        self.c.executemany('INSERT INTO ' + self.TABLE_NAME + ' VALUES (?,?,?,?,?,?,?)', self.DEFAULTS)
        self.conn.commit()


    def firstRun(self):
        log.warn("Running first-time JSON set-up")

        true_false = [("1", "true"),("0", "false")]

        defaults = {
            "snooze_length": {
                "formOrder": 1,
                "key": "snooze_length",
                "value": "9",
                "description": "Time (minutes) to Snooze",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "alarm_timeout": {
                "formOrder": 2,
                "key": "alarm_timeout",
                "value": "120",
                "description": "Time (minutes) to automatically cancel an alarm",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "holiday_mode": {
                "formOrder": 3,
                "key": "holiday_mode",
                "value": "0",
                "description": "Is Holiday Mode Enabled (no-alarm)",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": true_false
            },
            "default_wake": {
                "formOrder": 4,
                "key": "default_wake",
                "value": "1100",
                "description": "If the alarm is scheduled for later than this ignore and default to this",
                "formType": "textbox",
                "visibility": "advanced",
                "formRegexp": "[0-2][0-9][0-5][0-9]",
                "formRegexpMessage": "Must be a 24hr time (1645)",
                "formNullable": "null",
                "formDropdownValues": ""
            },
            "preempt_cancel": {
                "formOrder": 5,
                "key": "preempt_cancel",
                "value": "600",
                "description": "Time (seconds) before an alarm in which it can be cancelled",
                "formType": "textbox",
                "visibility": "advanced",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "wakeup_time": {
                "formOrder": 6,
                "key": "wakeup_time",
                "value": "0",
                "description": "Time (minutes) before event to sound alarm",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "timezone": {
                "formOrder": 7,
                "key": "timezone",
                "value": "US/Eastern",
                "description": "Alarm Timezone",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": pytz.common_timezones
            },
            "weather_on_alarm": {
                "formOrder": 20,
                "key": "weather_on_alarm",
                "value": "1",
                "description": "Speak weather on alarm cancel",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": true_false
            },
            "weather_location": {
                "formOrder": 21,
                "key": "weather_location",
                "value": "New York, NY",
                "description": "Location for which to fetch weather",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "location_home": {
                "formOrder": 22,
                "key": "location_home",
                "value": "201 E 19th st, New York, NY",
                "description": "Location used for travel time calculation",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "location_work": {
                "formOrder": 23,
                "key": "location_work",
                "value": "Stamford, CT",
                "description": "Location of event used for travel time calculation",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "station": {
                "formOrder": 30,
                "key": "station",
                "value": "http://www.radiofeeds.co.uk/bbcradio1.pls",
                "description": "Radio Station to Play",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": self.getStations()
            },
            "radio_delay": {
                "formOrder": 31,
                "key": "radio_delay",
                "value": "10",
                "description": "Radio Delay",
                "formType": "textbox",
                "visibility": "advanced",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "min_brightness": {
                "formOrder": 40,
                "key": "min_brightness",
                "value": "1",
                "description": "Minimum Brightness (0-15)",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": [str(i) for i in range(0, 16)]
            },
            "max_brightness": {
                "formOrder": 41,
                "key": "max_brightness",
                "value": "15",
                "description": "Maximum Brightness (0-15)",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": [str(i) for i in range(0, 16)]
            },
            "brightness_timeout": {
                "formOrder": 42,
                "key": "brightness_timeout",
                "value": "20",
                "description": "Time (seconds) after which to revert back to auto-brightness",
                "formType": "textbox",
                "visibility": "advanced",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "use_lcd": {
                "formOrder": 43,
                "key": "use_lcd",
                "value": "0",
                "description": "Use LCD or not",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": true_false
            },
            "sfx_enabled": {
                "formOrder": 44,
                "key": "sfx_enabled",
                "value": "1",
                "description": "Are sound affects enabled",
                "formType": "dropdown",
                "visibility": "advanced",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": true_false
            },
            "volume": {
                "formOrder": 45,
                "key": "volume",
                "value": "85",
                "description": "Volume",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit (1-100)",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "use_wink": {
                "formOrder": 46,
                "key": "use_wink",
                "value": "85",
                "description": "Use Wink",
                "formType": "dropdown",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": true_false
            },
            "wink_group_id": {
                "formOrder": 47,
                "key": "wink_group_id",
                "value": "2901700",
                "description": "Wink Group ID to manipulate",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "",
                "formDropdownValues": ""
            },
            "spotify_user": {
                "formOrder": 48,
                "key": "spotify_user",
                "value": "joel_roberts",
                "description": "Spotify Username",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "",
                "formDropdownValues": ""
            },
            "spotify_pass": {
                "formOrder": 49,
                "key": "spotify_user",
                "value": "p@ssw0rd",
                "description": "Spotify Password",
                "formType": "textbox",
                "visibility": "standard",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "",
                "formDropdownValues": ""
            },
            "calendar": {
                "formOrder": 999,
                "key": "calendar",
                "value": CalendarCredentials.CALENDAR,
                "description": "Calendar to gather events from",
                "formType": "textbox",
                "visibility": "invisible",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "manual_alarm": {
                "formOrder": 999,
                "key": "manual_alarm",
                "value": "",
                "description": "Manual alarm time",
                "formType": "textbox",
                "visibility": "invisible",
                "formRegexp": "[0-2][0-9][0-5][0-9]",
                "formRegexpMessage": "Must be a 24hr time (1645)",
                "formNullable": "null",
                "formDropdownValues": ""
            },
            "menu_timeout": {
                "formOrder": 999,
                "key": "menu_timeout",
                "value": "20",
                "description": "Time (seconds) after which an untouched menu should close",
                "formType": "textbox",
                "visibility": "invisible",
                "formRegexp": "\\d+",
                "formRegexpMessage": "Must be a digit",
                "formNullable": "notnull",
                "formDropdownValues": ""
            },
            "placeholder": {
                "formOrder": 999,
                "key": "placeholder",
                "value": "",
                "description": "here just to support dynamic form generation",
                "formType": "hidden",
                "visibility": "invisible",
                "formRegexp": "",
                "formRegexpMessage": "",
                "formNullable": "",
                "formDropdownValues": ""
            }
        }

        with open(JSON_NAME, 'w+') as self.jsonFile:
            json.dump(defaults, self.jsonFile, indent=4, separators=(',', ': '))

        self.settings = defaults


    def getDb(self, key):
        self.c.execute('SELECT * FROM ' + self.TABLE_NAME + ' WHERE name=?', (key,))
        r = self.c.fetchone()
        if r is None:
            raise Exception('Could not find setting %s' % (key))
        return r[1]


    def get(self, key):
        r = self.settings[key]["value"]
        if r is None:
            raise Exception('Could not find setting %s' % (key))
        return r


    def getInt(self, key):
        try:
            return int(self.get(key))
        except ValueError:
            log.warn("Could not fetch %s as integer, value was [%s], returning 0", key, self.get(key))
            return 0


    def setDb(self, key, val):
        self.get(key)  # So we know if it doesn't exist

        if key == "volume":
            self.setVolume(val)

        self.c.execute('UPDATE ' + self.TABLE_NAME + ' SET value=? where name=?', (val, key,))
        self.conn.commit()


    def set(self, key, val):
        self.get(key)  # So we know if it doesn't exist

        if key == "volume":
            self.setVolume(val)

        self.settings[key]["value"] = val
        log.info("setting {0} to {1}".format(key, val))
        with open(JSON_NAME, 'w') as f:
            json.dump(self.settings, f, indent=4, separators=(',', ': '))
            f.close()

    def setVolume(self, val):
        subprocess.Popen("%s %s" % (self.VOL_CMD, val), stdout=subprocess.PIPE, shell=True)
        log.info("Volume adjusted to %s", val)


        # def __del__(self):
        # self.conn.close()


if __name__ == '__main__':
    #print "Showing all current settings"
    mySettings = Settings()
    mySettings.setup()
    #print mySettings.get('location_home')
    mySettings.set('max_brightness', '10')
    #print json.dumps(mySettings.settings, indent=4, separators=(',', ': '))

    try:
        with open(JSON_NAME, 'r') as f:
            try:
                json_string =  json.load(f)
            except ValueError as e:
                log.error("ValueError: {0}".format(e.args))
    except IOError as io:
        log.error("IOError: {0}".format(io.args))

    print json.dumps(json_string, indent=4, separators=(',', ': '))

