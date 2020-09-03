import os
import asyncio
import logging

import arrow
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.exceptions import MessageNotModified

from chrome_yt_browser import browser_driver
from jsonreader import config
from telegram_error_bot_sender import send_error
from yt_music_player import Player

API_TOKEN = os.environ['API_TOKEN']
MY_CHAT_ID = os.environ['MY_CHAT_ID']
DELAY = 1

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Telegram bot')

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
counter = 0
markup = types.InlineKeyboardMarkup()
markup.row(types.InlineKeyboardButton('⏮️', callback_data='btnPrev'),
           types.InlineKeyboardButton('⏯️', callback_data='btnPlayPause'),
           types.InlineKeyboardButton('⏭️', callback_data='btnNext'))
markup.row(types.InlineKeyboardButton('⏹️', callback_data='btnPause'),
           types.InlineKeyboardButton('▶️', callback_data='btnPlay'))
markup.row(types.InlineKeyboardButton('🔉', callback_data='btnLowerSound'),
           types.InlineKeyboardButton('🔊', callback_data='btnHigherSound'))

player_driver = browser_driver()
yt_player = Player(player_driver)
player_message_id = 0


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await bot.set_my_commands([types.BotCommand('player', 'Show the player')])
    await message.reply("Hi!\nI'm a private bot.")


@dp.message_handler(commands=['player'])
async def show_player(message: types.Message):
    if message.chat.id == int(MY_CHAT_ID):
        global yt_player, player_message_id
        sent_message = await bot.send_message(chat_id=int(MY_CHAT_ID), text=yt_player.generate_message(),
                                              reply_markup=markup)

        print('new player message id: ' + str(sent_message.message_id))
        player_message_id = sent_message.message_id


@dp.callback_query_handler(text='btnPlay')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Force play')
    yt_player.press_play()


@dp.callback_query_handler(text='btnPause')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Force pause')
    yt_player.press_pause()


@dp.callback_query_handler(text='btnPlayPause')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Play/Pause')
    yt_player.press_play_pause()


@dp.callback_query_handler(text='btnNext')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Next song')
    yt_player.press_next()


@dp.callback_query_handler(text='btnPrev')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Previous song')
    yt_player.press_prev()


@dp.callback_query_handler(text='btnLowerSound')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Lower sound')
    yt_player.lower_sound()


@dp.callback_query_handler(text='btnHigherSound')
async def inline_kb_answer_callback_handler(query: types.CallbackQuery):
    await query.answer(f'Higher sound')
    yt_player.higher_sound()


async def update_player():
    if yt_player is not None and yt_player.is_visible():
        now = arrow.now()
        hours = int(now.format('HH'))
        forbidden_to_play = hours >= int(config("hours_after")) or hours <= int(config("hours_until"))
        if forbidden_to_play and not yt_player.player_stopped:
            logger.info("It's forbidden to play now. Pressing pause")
            yt_player.press_pause()

        play_after = int(config("play_after"))
        should_play = play_after <= hours <= play_after + 1
        if should_play and yt_player.player_stopped:
            logger.info("It's time to play. Pressing play and next")
            yt_player.press_play()
            yt_player.press_next()
            morning_sound_level = config("morning_sound_level")
            while int(yt_player.sound_level) > int(morning_sound_level):
                logger.info("Current sound is " + yt_player.sound_level + ". Lowering to " + morning_sound_level)
                yt_player.lower_sound()

        if player_message_id != 0:
            if yt_player.max_play_seconds == 0 and not forbidden_to_play:
                yt_player.press_next()
                msg = ' player was stuck, pressed next'
                logger.info(msg)
                send_error(msg)
            yt_player.parse()
            msg = yt_player.generate_message()
            try:
                logger.info('updating player info')
                await bot.edit_message_text(text=msg, chat_id=MY_CHAT_ID,
                                            message_id=player_message_id, reply_markup=markup)
            except MessageNotModified:
                pass


def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(DELAY, repeat, coro, loop)


if __name__ == '__main__':
    loop = dp.loop
    loop.call_later(DELAY, repeat, update_player, loop)
    executor.start_polling(dp, skip_updates=True)
