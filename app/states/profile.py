from aiogram.fsm.state import State, StatesGroup


class ProfileWalletState(StatesGroup):
    wallet_address = State()
