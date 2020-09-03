import pickle
from os import path

from selenium import webdriver

COOKIES_FILE = '../cookies/play_music.pkl'


def browser_driver():
    def save_cookies():
        print('saving cookies...')
        pickle.dump(driver.get_cookies(), open(COOKIES_FILE, 'wb'))
        print('saved cookies')

    def shuffle():
        print('locate shuffle btn')
        shuffle_btn = driver.find_element_by_xpath('//yt-formatted-string[text()[contains(.,"Перемешать")]]')
        print('press shuffle btn')
        shuffle_btn.click()

    driver = webdriver.Chrome()
    driver.get('https://music.youtube.com/')
    # driver.implicitly_wait(3)

    if path.exists(COOKIES_FILE):
        print('loading cookies')
        cookies = pickle.load(open(COOKIES_FILE, 'rb'))
        for cookie in cookies:
            driver.add_cookie(cookie)
        driver.refresh()
        print('cookies loaded')

    # input('press any button. will save cookies')
    # save_cookies()

    # print('going to dinastya playlist')
    # driver.get('https://music.youtube.com/playlist?list=PL14knTXmhmngmWY9yLKcq7CTVWAx1xGM_')
    # shuffle()
    return driver
