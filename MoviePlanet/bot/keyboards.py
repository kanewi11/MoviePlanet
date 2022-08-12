from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


kb_cancel = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Отмена'))
button_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('Отмена'))
kb_yes = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Выслать сейчас 🚀'), KeyboardButton('Отмена'))

kb_start = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Сделать пост фильма 🤳'),
                                                         KeyboardButton('Отложенные посты 🕜'),
                                                         KeyboardButton('Рекламный пост 💰'))

kb_cancel_search = ReplyKeyboardMarkup(resize_keyboard=True,
                                       one_time_keyboard=True).add(KeyboardButton('Прекратить поиск фильма 🙅‍♂'))
