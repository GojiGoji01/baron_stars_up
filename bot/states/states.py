from aiogram.fsm.state import State, StatesGroup

class MenuStates(StatesGroup):
    """Состояния главного меню"""
    main_menu = State()
    language_select = State()
    partners_hub = State()
    help_screen = State()
    news_screen = State()

class BuyStates(StatesGroup):
    """Покупка: Stars / Premium до шага оплаты (фаза 4)."""
    choose_type = State()
    stars_recipient = State()
    stars_amount = State()
    stars_custom_amount = State()
    premium_duration = State()
    premium_recipient = State()
    payment_method = State()

class PaymentStates(StatesGroup):
    """Состояния платежной системы"""
    choose_method = State()
    ton_payment = State()
    sbp_payment = State()
    crypto_payment = State()

class ReferralStates(StatesGroup):
    """Состояния реферальной системы"""
    referral_menu = State()
    referral_stats = State()
    referral_withdraw = State()
