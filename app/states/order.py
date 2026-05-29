from aiogram.fsm.state import State, StatesGroup


class StarsOrder(StatesGroup):
    recipient = State()
    custom_amount = State()


class PremiumOrder(StatesGroup):
    recipient = State()
    recipient_tg_id = State()


class GiftOrder(StatesGroup):
    recipient = State()
    recipient_tg_id = State()


class SellStarsOrder(StatesGroup):
    amount = State()
