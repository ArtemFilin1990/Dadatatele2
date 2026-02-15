from aiogram.fsm.state import State, StatesGroup


class MainState(StatesGroup):
    waiting_inn = State()
