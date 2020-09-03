import os
import urllib.parse

import requests
import arrow

BOT_TOKEN = os.environ['ERROR_BOT_TOKEN']  # https://t.me/yt_music_errors_log_bot
MY_CHAT_ID = os.environ['MY_CHAT_ID']


def send_error(text: str):
    now = arrow.now()
    msg = urllib.parse.quote('[' + str(now) + '] ' + text)
    link = 'https://api.telegram.org/bot' + BOT_TOKEN + '/sendMessage?chat_id=' + MY_CHAT_ID + \
           '&text=' + msg
    r = requests.get(link)
    if r.status_code != 200:
        raise Exception(r)

