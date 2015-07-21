#!/usr/bin/python

import logging
import sys
import socket
import threading
import time

import AlarmThread
import Settings
import MediaPlayer
from Weather import WeatherFetcher
from Web import WebApplication

log = logging.getLogger('root')
log.setLevel(logging.DEBUG)

stream = logging.StreamHandler(sys.stdout)
stream.setLevel(logging.DEBUG)

formatter = logging.Formatter('[%(asctime)s] %(levelname)8s %(module)15s: %(message)s')
stream.setFormatter(formatter)

log.addHandler(stream)

arg_names = ['mode']
args = dict(zip(arg_names, sys.argv))

class AlarmPi:
    def __init__(self):
        self.stopping = False
        self.connectivity_test_server = "www.google.com"

    def test_internet_connectivity(self):
        try:
            # see if we can resolve the host name -- tells us if there is
            # a DNS listening
            host = socket.gethostbyname(self.connectivity_test_server)
            # connect to the host -- tells us if the host is actually
            # reachable
            s = socket.create_connection((host, 80), 2)
            return True
        except:
            pass
            return False

    def internet_connectivity_true(self):
        placeholder = True


    def stop(self):
        self.stopping = True

    def execute(self):
        log.info("Starting up AlarmPi")

        settings = self.initSettings()
        media = self.initMedia(settings)
        weather = self.initWeather(settings)
        wink = self.initWink(settings)
        alarm = self.initAlarm(settings, media, weather, wink)
        web = self.initWeb(settings, alarm)
        if args["mode"] != "dev":
                log.info("Entering Prod Mode")
                clock = self.initClock(settings)
                self.initInput(settings, alarm)
                lcd = self.initLCD(settings, weather, media, alarm)
                bright = self.initBrightness(settings, clock, lcd)
        else:
            log.info("Entering Dev Mode")



        # # If there's a manual alarm time set in the database, then load it
        # manual = settings.getInt('manual_alarm')
        # log.debug("manual_alarm: {0}".format(manual))
        # if manual == 0 or manual is None:
        alarm.autoSetAlarm()
        # else:
        #     alarmTime = datetime.datetime.fromtimestamp(manual, pytz.timezone(settings.get('timezone')))
        #     log.info("Loaded previously set manual alarm time of %s", alarmTime)
        #     alarm.manualSetAlarm(alarmTime)

        log.debug("Starting alarm control")
        alarm.start()




        # Main loop where we just spin until we receive a shutdown request
        log.debug("Loop until KeyboardInterrupt or SystemExit")
        try:
            while (self.stopping is False):
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            log.warn("Interrupted, shutting down")

        log.warn("Shutting down")
        #media.playVoice('Shutting down. Goodbye')
        #time.sleep(2)

        log.info("Stopping all services")
        web.stop()
        alarm.stop()
        clock.stop()
        if settings.getInt('use_lcd') == 1:
            lcd.stop()
        bright.stop()
        media.spotify.stop()


        log.info("Shutdown complete, now exiting")

        time.sleep(2)  # To give threads time to shut down

    def initWink(self, settings):
        use_wink = settings.getInt('use_wink')
        if use_wink == 1:
            import Wink
            log.debug("Initializing Wink")
            wink = Wink.Wink()
        else:
            log.debug("Not using Wink")
            wink = None
        return wink

    def initWeather(self, settings):
        log.debug("Loading weather")
        weather = WeatherFetcher(settings)
        return weather

    def initInput(self, settings, alarm):
        from InputWorker import InputWorker
        log.debug("Initializing inputs")
        inputWorker = InputWorker(alarm, settings)
        inputWorker.start()
        return inputWorker

    def initLCD(self, settings, weather, media, alarm):
        if settings.getInt('use_lcd') == 1:
            import LcdThread
            log.debug("Loading LCD")
            lcd = LcdThread.LcdThread(alarm, settings, weather, media, self.stop)
            lcd.setDaemon(True)
            lcd.start()
        else:
            log.debug("Not using LCD")
            lcd = None
        return lcd

    def initMedia(self, settings):
        log.debug("Loading media")
        media = MediaPlayer.MediaPlayer(settings)
        # media.playVoice('Starting up')
        return media

    def initBrightness(self, settings, clock, lcd):
        if settings.getInt('use_luminosity_sensor') == 1:
            log.debug("Loading brightness control")
            import BrightnessThread
            bright = BrightnessThread.BrightnessThread(settings)
            bright.setDaemon(True)
            bright.registerControlObject(clock.segment.disp)
            if settings.getInt('use_lcd') == 1:
                log.debug("Loading brightness control for LCD")
                bright.registerControlObject(lcd)
            bright.start()
        else:
            log.debug("Not Luminosity Sensor")
            bright = None
        return bright

    def initWeb(self, settings, alarm):
        log.debug("Starting web application")
        web = WebApplication(alarm, settings)
        web.setDaemon(True)
        web.start()
        return web

    def initAlarm(self, settings, media, weather, wink):
        log.debug("Loading alarm thread")
        alarm = AlarmThread.AlarmThread(settings, media, weather, wink)
        alarm.setDaemon(True)
        return alarm

    def initClock(self, settings):
        log.debug("Loading clock")
        import ClockThread
        clock = ClockThread.ClockThread(settings)
        clock.setDaemon(True)

        log.debug("Starting clock")
        clock.start()
        return clock

    def initSettings(self):
        log.debug("Loading settings")
        settings = Settings.Settings()
        settings.setup()
        return settings


alarm_clock = AlarmPi()
alarm_clock.execute()
