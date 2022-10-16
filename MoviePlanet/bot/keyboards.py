from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


markup_cancel = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton('Отмена'))
markup_yes = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Выслать сейчас 🚀'),
                                                           KeyboardButton('Отмена'))

markup_admin = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('Сделать пост фильма 🤳'),
                                                             KeyboardButton('Отложенные посты 🕜'),
                                                             KeyboardButton('Рекламный пост 💰'))

markup_cancel_search = ReplyKeyboardMarkup(resize_keyboard=True,
                                           one_time_keyboard=True).add(KeyboardButton('Прекратить поиск фильма 🙅‍♂'))
