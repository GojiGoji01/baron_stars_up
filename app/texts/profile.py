def build_profile_text(stats: dict) -> str:
    return (
        "Р’Р°С€ РїСЂРѕС„РёР»СЊ\n\n"
        f"Р’Р°С€ ID: {stats['user_id']}\n"
        f"Р РµС„РµСЂР°Р»СЊРЅС‹Р№ Р±Р°Р»Р°РЅСЃ: {stats['referral_balance']} в‚Ѕ\n"
        f"Р’СЃРµРіРѕ РєСѓРїР»РµРЅРѕ Р·РІС‘Р·Рґ: {stats['stars_bought']} ({stats['stars_bought_rub']} в‚Ѕ)\n"
        f"Р’СЃРµРіРѕ РєСѓРїР»РµРЅРѕ РїСЂРµРјРёСѓРјРѕРІ (РјРµСЃ): {stats['premium_months_bought']} ({stats['premium_bought_rub']} в‚Ѕ)\n"
        f"РћР±С‰РёР№ РґРµРїРѕР·РёС‚: {stats['total_deposit']} в‚Ѕ\n"
        f"РќР°РєРѕРїР»РµРЅРѕ Р·РІРµР·Рґ: {stats['saved_stars']} ({stats['saved_stars_rub']} в‚Ѕ)"
    )


PROFILE_WITHDRAW_STARS_ALERT = "Р’С‹РІРѕРґ Р·РІРµР·Рґ Р±СѓРґРµС‚ РґРѕР±Р°РІР»РµРЅ РїРѕР·Р¶Рµ."
