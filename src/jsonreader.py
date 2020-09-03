import json


def config(key):
    with open("../config/yt_music_conf.json", "r", encoding='utf-8') as read_file:
        data = json.load(read_file)
        return data['xpath'][key]


print(config("time_info_label"))
