import time
from mplayer import Player
import subprocess
import logging
import Spotify

log = logging.getLogger('root')

PANIC_ALARM = './sounds/GuitarChords2.mp3'
FX_DIRECTORY = './sounds/'

class MediaPlayer:
    def __init__(self, settings):
        self.settings = settings
        self.player = False
        self.effect = False

        self.alarm_media = settings.get("alarm_media")

        if self.alarm_media == 'Spotify':
            log.debug("Loading Spotify")
            self.spotify = Spotify.Spotify()
            self.spotify.setDaemon(True)
            # log.debug("Spotify event loop")
            # self.spotify.event_loop = self.spotify.EventLoop(self.session)
            # self.spotify.event_loop.start()
            self.spotify.login(settings.get("spotify_user"), settings.get("spotify_pass"))

    def playerActive(self):
        # log.debug("playerActive: {0}".format(self.player != False))
        return self.player != False

    def soundAlarm(self):
        log.info("soundAlarm: Playing alarm")

        if self.alarm_media == 'Spotify':
            self.playSpotify()
        else:
            self.playStation()

            log.debug("Verifying Radio is playing")
            # Wait a few seconds and see if the mplayer instance is still running
            time.sleep(self.settings.getInt('radio_delay'))

            # Fetch the number of mplayer processes running
            processes = subprocess.Popen('ps aux | grep mplayer | egrep -v "grep" | wc -l',
                                         stdout=subprocess.PIPE,
                                         shell=True
                                         )
            num = int(processes.stdout.read())

            if num < 2 and self.player is not False:
                log.error("Radio fail: Could not find mplayer instance, playing panic alarm")
                self.stopPlayer()
                time.sleep(2)
                self.playMedia(PANIC_ALARM, 0)
            else:
                log.debug("Radio success")

    def playSpotify(self):
        log.debug("playSpotify: ")
        #self.spotify.play_playlist(self.settings.get("spotify_uri"))
        self.spotify.run()

    def playStation(self):
        log.debug("playStation: ")
        station = self.settings.get('station')

        log.info("Playing station %s", station)
        self.player = Player()
        self.player.loadlist(station)
        self.player.loop = 0

    def playMedia(self, file, loop=-1):
        log.info("playMedia: Playing file %s", file)
        self.player = Player()
        self.player.loadfile(file)
        self.player.loop = loop

    # Play some speech. None-blocking equivalent of playSpeech, which also pays attention to sfx_enabled setting
    def playVoice(self, text):
        log.debug("playVoice (non-blocking): {0}".format(text))
        if self.settings.get('sfx_enabled') == 0:
            # We've got sound effects disabled, so skip
            log.info("Sound effects disabled, not playing voice")
            return
        log.info("Playing voice: '%s'" % (text))
        play = subprocess.Popen('../speech/googletts "%s"' % (text), shell=True)

    # Play some speech. Warning: Blocks until we're done speaking
    def playSpeech(self, text):
        log.debug("playSpeech (blocking): {0}".format(text))
        if self.settings.get('sfx_enabled') == 0:
            log.info("Playing speech: '%s'" % (text))
            play = subprocess.Popen('../speech/googletts "%s"' % (text), shell=True)
            play.wait()

    def stopPlayer(self):
        log.debug("stopPlayer: ")
        if self.player:
            self.player.quit()
            self.player = False
            log.info("Player process terminated")
