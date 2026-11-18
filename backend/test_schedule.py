
from datetime import datetime, timedelta

from backend.booking import (
    get_available_slots,
    TIMEZONE
)


# Выбираем следующий рабочий день
target_date = datetime.now(TIMEZONE).date() + timedelta(days=1)

while target_date.weekday() == 6:
    target_date += timedelta(days=1)


# Проверяем свободное время для мойки небольшого автомобиля
slots = get_available_slots(
    service_code="wash",
    car_size="small",
    target_date=target_date
)

print(f"Свободное время на {target_date}:")

if slots:
    for slot in slots:
        print(f"{slot['start']} — {slot['end']}")
else:
    print("Свободного времени нет.")
