def build_callback(section: str, action: str, value: str | int | None = None) -> str:
    if value is None:
        return f"{section}:{action}"

    return f"{section}:{action}:{value}"


class MenuCallbacks:
    MAIN = build_callback("menu", "main")
    BUY = build_callback("menu", "buy")
    HELP = build_callback("menu", "help")
    SUPPORT = build_callback("menu", "support")
    INFO = build_callback("menu", "info")
    NEWS = build_callback("menu", "news")
    PARTNERS = build_callback("menu", "partners")


class BuyCallbacks:
    STARS = build_callback("buy", "stars")
    PREMIUM = build_callback("buy", "premium")
    GIFT = build_callback("buy", "gift")


class StarsCallbacks:
    SELF = build_callback("stars", "self")
    FRIEND = build_callback("stars", "friend")
    AMOUNT_PREFIX = build_callback("stars", "amount")
    AMOUNT_CUSTOM = build_callback("stars", "amount", "custom")
    AMOUNT_BACK = build_callback("stars", "amount", "back")

    @staticmethod
    def amount(value: int) -> str:
        return build_callback("stars", "amount", value)


class PremiumCallbacks:
    SELF = build_callback("premium", "self")
    FRIEND = build_callback("premium", "friend")
    DURATION_PREFIX = build_callback("premium", "duration")
    DURATION_BACK = build_callback("premium", "duration", "back")
    TARGET_BACK = build_callback("premium", "target", "back")

    @staticmethod
    def duration(months: int) -> str:
        return build_callback("premium", "duration", months)


class GiftCallbacks:
    SELF = build_callback("gift", "self")
    FRIEND = build_callback("gift", "friend")
    SELECT_PREFIX = build_callback("gift", "select")

    @staticmethod
    def select(gift_id: int | str) -> str:
        return build_callback("gift", "select", gift_id)


class SellCallbacks:
    STARS = build_callback("sell", "stars")
    AMOUNT_PREFIX = build_callback("sell", "amount")
    AMOUNT_CUSTOM = build_callback("sell", "amount", "custom")

    @staticmethod
    def amount(value: int) -> str:
        return build_callback("sell", "amount", value)


class PaymentCallbacks:
    SBP = build_callback("payment", "sbp")
    CRYPTO = build_callback("payment", "crypto")
    CHECK_PREFIX = build_callback("payment", "check")

    @staticmethod
    def check(order_id: int | str) -> str:
        return build_callback("payment", "check", order_id)


class InfoCallbacks:
    RULES = build_callback("info", "rules")
    PRIVACY = build_callback("info", "privacy")
    OFFER = build_callback("info", "offer")
    FRANCHISE = build_callback("info", "franchise")


class ReferralCallbacks:
    OPEN = build_callback("referral", "open")
    WITHDRAW = build_callback("referral", "withdraw")
    LIST = build_callback("referral", "list")
    PAGE_PREFIX = build_callback("referral", "page")

    @staticmethod
    def page(value: int) -> str:
        return build_callback("referral", "page", value)


class ProfileCallbacks:
    OPEN = build_callback("profile", "open")
    WITHDRAW_STARS = build_callback("profile", "withdraw", "stars")
