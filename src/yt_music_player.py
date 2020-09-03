import datetime
import logging
import re
import subprocess
import sys
import threading

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver

from jsonreader import config
from telegram_error_bot_sender import send_error

logger = logging.getLogger('YT player')


def text_to_seconds(time_string):
    time = None
    if time_string.count(':') == 1:
        time = datetime.datetime.strptime(time_string, "%M:%S")
    if time_string.count(':') == 2:
        time = datetime.datetime.strptime(time_string, "%H:%M:%S")

    if time is None:
        send_error('Tried to parse time, but got ' + time_string)

    a_timedelta = time - datetime.datetime(1900, 1, 1)
    return a_timedelta.total_seconds()


def seconds_to_time(seconds):
    return str(datetime.timedelta(seconds=seconds))


class Player:

    def __str__(self) -> str:
        return 'Player \n' + self.generate_message()

    def __init__(self, player_driver: WebDriver):
        super().__init__()
        self.player_driver = player_driver
        self.current_track = 'None'
        self.current_song_info = 'None'
        self.current_play_seconds = 0
        self.max_play_seconds = 0
        self.player_visible = False
        self.player_stopped = True
        self.sound_level = '0'
        self.update_current_sound_level()

    def _find_element(self, x_path, alert=True):
        try:
            logger.info('Searching for ' + x_path)
            return self.player_driver.find_element_by_xpath(x_path)
        except NoSuchElementException:
            if alert:
                _type, value, traceback = sys.exc_info()
                send_error("Can't parse element, exception:\n" + str(value))

    def parse(self):
        self._parse_seconds()
        self._parse_author()
        self._parse_song_info()
        self.player_visible = self.is_visible()
        self.player_stopped = self._is_stopped()

    def _parse_seconds(self):
        # should get smth like '00:00 / 01:00'
        label = self._find_element(config('time_info_label'))
        time_parts = re.split(r'/', label.text)
        if len(time_parts) != 2:
            return
        current_time = time_parts[0].strip()
        max_time = time_parts[1].strip()
        self.current_play_seconds = text_to_seconds(current_time)
        self.max_play_seconds = text_to_seconds(max_time)

    def _parse_author(self):
        track_title = self._find_element(config('track_title_label'))
        self.current_track = str(track_title.text)

    def _parse_song_info(self):
        track_info = self._find_element(config('track_info_label'))
        info_text = track_info.get_attribute('title')
        self.current_song_info = info_text

    def find_elem(self, elem_name):
        return self.player_driver.find_element_by_xpath(config(elem_name))

    def current_play_time(self):
        return seconds_to_time(self.current_play_seconds)

    def max_play_time(self):
        return seconds_to_time(self.max_play_seconds)

    def generate_message(self):
        status = '⏹️' if self.player_stopped else '▶️'
        return self.current_track + "\n" + \
               self.current_song_info + "\n" + \
               self.current_play_time() + " / " + self.max_play_time() + "\n" + \
               "Current status: " + status + " 🔊 " + self.sound_level

    def _press_btn_new_thread(self, btn_name, alert=True):
        th = threading.Thread(target=self._press_btn, args=(btn_name, alert), daemon=True)
        th.start()

    def _press_btn(self, btn_name, alert=True):
        logger.info('Pressing ' + btn_name)
        element = self._find_element(config(btn_name), alert)
        if element is not None:
            element.click()

    def press_play_pause(self):
        self._press_btn_new_thread('play_pause_button')

    def press_next(self):
        self._press_btn_new_thread('next_button')

    def press_prev(self):
        self._press_btn_new_thread('prev_button')

    def press_play(self):
        self._press_btn_new_thread('play_pause_as_play', alert=False)

    def press_pause(self):
        self._press_btn_new_thread('play_pause_as_pause', alert=False)

    def _is_stopped(self):
        try:
            logger.info('Checking if player is paused')
            self.player_stopped = self.player_driver.find_element_by_xpath(config('play_pause_as_play')).is_displayed()
            logger.info(str(self.player_stopped))
            return self.player_stopped
        except NoSuchElementException:
            return False

    def is_visible(self):
        try:
            logger.info('Checking if player is visible')
            self.player_visible = self.player_driver.find_element_by_xpath(config('track_title_label')).is_displayed()
            logger.info(str(self.player_visible))
            return self.player_visible
        except NoSuchElementException:
            return False

    def update_current_sound_level(self):
        cmd = "pactl list sinks | grep '^[[:space:]]Громкость:' | head -n $(( $SINK + 1 )) | tail -n 1 | " \
              "sed -e 's,.* \([0-9][0-9]*\)%.*,\\1,'"
        self.sound_level = subprocess.check_output(cmd, shell=True, encoding='utf-8').strip()
        logger.info('Current sound level is ' + self.sound_level)

    def higher_sound(self):
        logger.info('Increased sound level')
        subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '+5%'], check=True, text=True)
        self.update_current_sound_level()

    def lower_sound(self):
        logger.info('Decreased sound level')
        subprocess.run(['pactl', 'set-sink-volume', '@DEFAULT_SINK@', '-5%'], check=True, text=True)
        self.update_current_sound_level()
