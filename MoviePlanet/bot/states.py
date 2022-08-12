from aiogram.dispatcher.filters.state import StatesGroup, State


class ForwardState(StatesGroup):
    CANCEL_OR_MASSAGE = State()


class PostState(StatesGroup):
    DATA = State()
    DATE_TIME = State()


class EditPostState(StatesGroup):
    ID = State()
    DATE_TIME = State()


class ChoiceFilmState(StatesGroup):
    FILM_CHOICE = State()
