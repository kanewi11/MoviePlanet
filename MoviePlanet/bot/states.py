from aiogram.dispatcher.filters.state import StatesGroup, State


class ForwardState(StatesGroup):
    cancel_or_message = State()


class PostState(StatesGroup):
    DATA = State()
    DATE_TIME = State()


class EditPostState(StatesGroup):
    ID = State()
    DATE_TIME = State()
