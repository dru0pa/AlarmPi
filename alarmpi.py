#!/usr/bin/python

import logging
import sys
import pytz
import Wink
import dateutil.parser

log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

import time
import datetime
import threading
import ClockThread
import AlarmThread
import LcdThread
import BrightnessThread
import Settings
import MediaPlayer
from InputWorker import InputWorker
from Weather import WeatherFetcher
from Web import WebApplication


class AlarmPi:
    def __init__(self):
        self.stopping = False

    def stop(self):
        self.stopping = True

    def execute(self):
        log.info("Starting up AlarmPi")

        log.debug("Loading settings")
        settings = Settings.Settings()
        settings.setup()

        log.debug("Loading media")
        media = MediaPlayer.MediaPlayer(settings)
        # media.playVoice('Starting up')

        log.debug("Loading clock")
        clock = ClockThread.ClockThread(settings)
        clock.setDaemon(True)

        log.debug("Loading weather")
        weather = WeatherFetcher(settings)

        use_wink = settings.getInt('use_wink')
        if use_wink == 1:
            log.debug("Initializing Wink")
            wink = Wink.Wink()
        else:
            log.debug("Not using Wink")
            wink = None

        log.debug("Loading alarm thread")
        alarm = AlarmThread.AlarmThread(settings, media, weather, wink)
        alarm.setDaemon(True)

        log.debug("Initializing inputs")
        inputWorker = InputWorker(alarm, settings)
        inputWorker.start()

        use_lcd = settings.getInt('use_lcd')
        if use_lcd == 1:
            log.debug("Loading LCD")
            lcd = LcdThread.LcdThread(alarm, settings, weather, media, self.stop)
            lcd.setDaemon(True)
            lcd.start()
        else:
            log.debug("Not using LCD")

        log.debug("Loading brightness control")
        bright = BrightnessThread.BrightnessThread(settings)
        bright.setDaemon(True)
        bright.registerControlObject(clock.segment.disp)
        if use_lcd == 1:
            log.debug("Loading brightness control for LCD")
            bright.registerControlObject(lcd)
        bright.start()


        # If there's a manual alarm time set in the database, then load it
        manual = settings.getInt('manual_alarm')
        log.debug("manual_alarm: {0}".format(manual))
        if manual == 0 or manual is None:
            log.debug("Settings manual alarm")
            alarm.autoSetAlarm()
        else:
            alarmTime = datetime.datetime.fromtimestamp(manual, pytz.timezone(settings.get('timezone')))
            log.info("Loaded previously set manual alarm time of %s", alarmTime)
            alarm.manualSetAlarm(alarmTime)

        log.debug("Starting clock")
        clock.start()

        log.debug("Starting alarm control")
        alarm.start()

        log.debug("Starting web application")
        web = WebApplication(alarm, settings)
        web.setDaemon(True)
        web.start()

        # Main loop where we just spin until we receive a shutdown request
        log.debug("Loop until KeyboardInterrupt or SystemExit")
        try:
            while (self.stopping is False):
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            log.warn("Interrupted, shutting down")

        log.warn("Shutting down")
        #media.playVoice('Shutting down. Goodbye')
        time.sleep(2)

        log.info("Stopping all services")
        web.stop()
        alarm.stop()
        clock.stop()
        if use_lcd == 1:
            lcd.stop()
        bright.stop()
        media.spotify.stop()


        log.info("Shutdown complete, now exiting")

        time.sleep(2)  # To give threads time to shut down


alarm = AlarmPi()
alarm.execute()
