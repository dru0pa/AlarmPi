#!/usr/bin/python

import time
import datetime
import pytz
import calendar
import threading
import AlarmGatherer
import logging
from TravelCalculator import TravelCalculator

log = logging.getLogger('root')

def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

class AlarmThread(threading.Thread):
    def __init__(self, settings, media, weather, wink):
        threading.Thread.__init__(self)
        self.stopping = False
        self.nextAlarm = None
        self.alarmTimeout = None
        self.snoozing = False

        self.settings = settings
        self.alarm_media = settings.get("alarm_media")
        self.media = media

        log.debug("Loading AlarmGatherer")
        self.alarmGatherer = AlarmGatherer.AlarmGatherer(settings)

        self.weatherFetcher = weather
        self.use_wink = self.settings.getInt("use_wink")
        self.wink = wink
        self.fromEvent = False  # False if auto or manual, True if from an event

        log.debug("Loading Travel Calculator")
        self.travel = TravelCalculator(self.settings.get('location_home'))
        self.travelTime = 0  # The travel time we last fetched
        self.travelCalculated = False  # Have we re-calculated travel for this alarm cycle?

    def stop(self):
        log.info("Stopping alarm thread")
        if (self.media.playerActive()):
            self.stopAlarm()
        if self.alarm_media == 'Spotify':
            self.media.spotify.stop()
        self.stopping = True

    def isAlarmSounding(self):
        #sounding = (self.media.playerActive() and self.nextAlarm is not None and self.nextAlarm < datetime.datetime.now(
        #    pytz.timezone(self.settings.get('timezone'))))
        sounding = (self.media.playerActive() and self.nextAlarm is not None)
        # log.debug("isAlarmSounding: {0}".format(sounding))
        return sounding

    def isSnoozing(self):
        # log.debug("isSnoozing: {0}".format(self.snoozing))
        return self.snoozing

    def getNextAlarm(self):
        log.debug("getNextAlarm: {0}".format(self.nextAlarm))
        return self.nextAlarm

    def snooze(self):
        message = "Snoozing alarm for {0} minutes".format(self.settings.getInt('snooze_length'))
        log.info(message)
        log.debug("snooze: {0}".format(self.settings.getInt('snooze_length')))

        self.snoozing = True
        self.silenceAlarm(self.snoozing)
        #self.media.playSpeech(message)
        #self.silenceAlarm()
        if self.use_wink == 1:
            log.debug("turning off Wink")
            self.wink.activate(self.settings.get('wink_group_id'),bool(),0)

        alarmTime = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))
        alarmTime += datetime.timedelta(minutes=self.settings.getInt('snooze_length'))
        self.setAlarmTime(alarmTime)
        self.alarmTimeout = None
        self.fromEvent = False

    # Only to be called if we're stopping this alarm cycle - see silenceAlarm() for shutting off the player
    def stopAlarm(self):
        log.debug("stopAlarm")
        self.silenceAlarm()

        if self.use_wink == 1:
            log.debug("turning on Wink")
            self.wink.activate(self.settings.get('wink_group_id'),bool(1),0.25)

        self.clearAlarm()

        if self.settings.getInt('weather_on_alarm') == 1:
            log.debug("Playing weather information")

            now = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))

            weather = ""
            try:
                weather = self.weatherFetcher.getWeather().speech()
            except Exception:
                log.exception("Failed to get weather information")

            day = now.strftime("%d").lstrip("0")
            day += suffix(now.day)

            hour = now.strftime("%I").lstrip("0")

            salutation = "morning" if now.strftime("%p") == "AM" else "afternoon" if int(hour) < 18 else "evening"

            # Today is Monday 31st of October, the time is 9 56 AM
            speech = "Good {0} {1}. Today is {2} {3} {4}, the time is {5} {6} {7}. ".format(
            salutation, self.settings.get("name"), now.strftime("%A"), day, now.strftime("%B"), hour, now.strftime("%M"), now.strftime("%p"))
            speech += weather

            self.media.playVoice(speech)

        # Send a notification to HomeControl (OpenHAB) that we're now awake
        # try:
        #     log.debug("Sending wake notification to HomeControl")
        #     urllib2.urlopen("http://homecontrol:9090/CMD?isSleeping=OFF").read()
        # except Exception:
        #     log.exception("Failed to send wake state to HomeControl")


        # Automatically set up our next alarm.
        self.autoSetAlarm()

    def soundAlarm(self):
        log.debug("soundAlarm")
        if self.use_wink == 1:
            log.debug("turning on Wink")
            self.wink.activate(self.settings.get('wink_group_id'),bool(1),0.25)
        self.media.soundAlarm(self.snoozing)
        timeout = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))
        timeout += datetime.timedelta(minutes=self.settings.getInt('alarm_timeout'))
        self.alarmTimeout = timeout

    # Stop whatever is playing
    def silenceAlarm(self, snoozing=False):
        log.debug("silenceAlarm")
        if self.alarm_media == 'Spotify':
            if snoozing:
                self.media.spotify.pause()
            else:
                self.media.spotify.stop()
        else:
            self.media.stopPlayer()

    # Called by InputWorker on press of the cancel button
    def cancel(self):
        log.debug("cancel: Cancel button pressed")
        if self.isAlarmSounding():
            # Lets snooze for a while
            self.snooze()
            return

        if self.isSnoozing():
            # Stop the alarm!
            self.stopAlarm()
            return

        if self.alarmInSeconds() < self.settings.getInt('preempt_cancel'):
            # We're in the allowable window for pre-empting a cancel alarm, and we're not in the menu
            log.info("Preempt cancel triggered")
            self.stopAlarm()
            return

    def autoSetAlarm(self):
        log.debug("autoSetAlarm")
        if self.settings.getInt('holiday_mode') == 1:
            log.debug("Holiday mode enabled, won't auto-set alarm as requested")
            return

        log.debug("Automatically setting next alarm")
        log.debug("entering very large try: clause")
        try:

            event = self.alarmGatherer.getNextEventTime()  # The time of the next event on our calendar.
            default = self.alarmGatherer.getDefaultAlarmTime()

            diff = datetime.timedelta(
                minutes=self.settings.getInt('wakeup_time'))  # How long before event do we want alarm
            event -= diff

            # Adjust for travel time
            self.travelTime = self.fetchTravelTime()
            travelDelta = datetime.timedelta(minutes=self.travelTime)
            event -= travelDelta

            if event > default:  # Is the event time calculated greater than our default wake time
                log.debug("Calculated wake time of %s is after our default of %s, reverting to default", event, default)
                event = default
                self.fromEvent = False
            else:
                self.fromEvent = True

            self.setAlarmTime(event)
            self.settings.set('manual_alarm', '')  # We've just auto-set an alarm, so clear any manual ones

            # Read out the time we've just set
            hour = event.strftime("%I").lstrip("0")
            readTime = "%s %s %s" % (hour, event.strftime("%M"), event.strftime("%p"))
            self.media.playVoice('Automatic alarm has been set for %s' % (readTime))

        except Exception as e:
            log.exception("Could not automatically set alarm")
            self.media.playVoice('Error setting alarm')
            self.nextAlarm = None

    # Find out where our next event is, and then calculate travel time to there
    def fetchTravelTime(self, update=False):
        log.debug("fetchTravelTime: {0}".format(update))
        destination = self.alarmGatherer.getNextEventLocation(includeToday=update)
        if (destination is None):
            destination = self.settings.get('location_work')
        travelTime = self.travel.getTravelTime(destination)

        return travelTime

    def travelAdjustAlarm(self):
        log.info("travelAdjustAlarm: Adjusting alarm for current travel time")
        newTravelTime = self.fetchTravelTime(update=True)
        travelDiff = newTravelTime - self.travelTime
        log.debug("Old travel time: %s, new travel time: %s, diff: %s" % (self.travelTime, newTravelTime, travelDiff))

        adjustDelta = datetime.timedelta(minutes=travelDiff)
        newTime = self.nextAlarm - adjustDelta
        self.setAlarmTime(newTime)
        self.travelCalculated = True

    def manualSetAlarm(self, alarmTime):
        log.info("manualSetAlarm: Manually setting next alarm to %s", alarmTime)
        self.fromEvent = False
        self.settings.set('manual_alarm', calendar.timegm(alarmTime.utctimetuple()))
        self.setAlarmTime(alarmTime)
        self.media.playVoice('Manual alarm has been set')

    def setAlarmTime(self, alarmTime):
        log.debug("setAlarmTime: {0}".format(alarmTime))
        self.nextAlarm = alarmTime

    def clearAlarm(self):
        log.debug("clearAlarm")
        self.snoozing = False
        self.nextAlarm = None
        self.alarmTimeout = None
        self.settings.set('manual_alarm', '')  # If we've just stopped an alarm, we can't have a manual one set yet
        self.travelTime = 0
        self.travelCalculated = False
        self.fromEvent = False

    # Number of seconds until alarm is triggered
    def alarmInSeconds(self):
        now = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))
        if self.nextAlarm is None:
            return -1

        if self.isSnoozing() or self.isAlarmSounding():
            return 0

        diff = self.nextAlarm - now
        # log.debug("alarmInSeconds: {0}".format(diff.seconds))
        return diff.seconds

    # Return a line of text describing the alarm state
    def getMenuLine(self):
        now = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))
        message = ""

        if self.nextAlarm is not None:
            diff = self.nextAlarm - now
            if diff.days < 1:
                if self.snoozing:
                    message += "Snoozing"
                else:
                    message += "Alarm"

                if diff.seconds < (2 * 60 * 60):  # 2 hours
                    if self.snoozing:
                        message += " for "
                    else:
                        message += " in "
                    message += "%s min" % ((diff.seconds // 60) + 1)
                    if diff.seconds // 60 != 0:
                        message += "s"
                else:
                    if self.snoozing:
                        message += " until "
                    else:
                        message += " at "
                    message += self.nextAlarm.strftime("%H:%M")

        log.debug("getMenuLine: {0}".format(message))
        return message

    def run(self):
        log.debug("starting alarm thread loop")
        while (not self.stopping):
            now = datetime.datetime.now(pytz.timezone(self.settings.get('timezone')))

            # log.info("now: %s", now)
            #log.info("nextAlarm: %s", self.nextAlarm)

            if (self.nextAlarm is not None and self.fromEvent and self.alarmInSeconds() < 3600 and not self.travelCalculated):
                # We're inside 1hr of an event alarm being triggered, and we've not taken into account the current traffic situation
                self.travelAdjustAlarm()

            #if (self.nextAlarm is not None and self.nextAlarm < now and not self.media.playerActive()):
            if self.nextAlarm is not None:
                log.debug("self.nextAlarm is not None")
                if self.nextAlarm < now:
                    log.debug("self.nextAlarm < now")
                    if not self.media.playerActive():
                        log.debug("not self.media.playerActive()")
                        if not self.snoozing:
                            log.debug("not self.snoozing")
                            self.soundAlarm()

            if (self.alarmTimeout is not None and self.alarmTimeout < now):
                log.info("Alarm timeout reached, stopping alarm")
                self.stopAlarm()

            time.sleep(1)
        log.debug("ending alarm thread loop")
