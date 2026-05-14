from aiogram.fsm.state import State, StatesGroup


class StarsOrder(StatesGroup):
    recipient = State()
    custom_amount = State()


class PremiumOrder(StatesGroup):
    recipient = State()


class TonOrder(StatesGroup):
    custom_amount = State()


class GiftOrder(StatesGroup):
    recipient = State()


class SellStarsOrder(StatesGroup):
    amount = State()
