AVAILABLE_GIFTS = (
    {"gift_id": 69, "title": "🍭 Леденец", "price": 69},
    {"gift_id": 99, "title": "💐 Цветы", "price": 99},
    {"gift_id": 149, "title": "🧸 Мишка", "price": 149},
    {"gift_id": 199, "title": "🎂 Торт", "price": 199},
    {"gift_id": 249, "title": "💝 Сердце", "price": 249},
    {"gift_id": 349, "title": "🏆 Кубок", "price": 349},
)


async def get_available_gifts() -> tuple[dict, ...]:
    return AVAILABLE_GIFTS


async def get_gift_price(gift_id: int) -> int:
    gifts = await get_available_gifts()
    for gift in gifts:
        if gift["gift_id"] == gift_id:
            return int(gift["price"])

    return gift_id
