CATEGORY_LEAD_TIMES = {
    "Circuit Boards": 14,
    "Sensors": 7,
    "Controllers": 10,
    "Actuators": 12,
    "Power Supplies": 9,
}

DEFAULT_LEAD_TIME_DAYS = 10


def lead_time_for(category: str | None) -> int:
    if not category:
        return DEFAULT_LEAD_TIME_DAYS
    return CATEGORY_LEAD_TIMES.get(category, DEFAULT_LEAD_TIME_DAYS)
