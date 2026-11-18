
from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

from database.database import SessionLocal
from database.models import Service, Appointment


# Часовой пояс Улан-Удэ
TIMEZONE = ZoneInfo("Asia/Irkutsk")

# Временное расписание
OPEN_TIME = time(9, 0)
CLOSE_TIME = time(20, 0)

# Интервал между вариантами времени записи
SLOT_INTERVAL = 30


def get_available_slots(service_code: str, car_size: str, target_date: date):
    """
    Возвращает свободное время для выбранной услуги
    и размера автомобиля на указанную дату.
    """

    if car_size not in ("small", "medium", "large"):
        raise ValueError("Неизвестный размер автомобиля")

    session = SessionLocal()

    try:
        # Находим выбранную услугу
        service = session.query(Service).filter_by(
            code=service_code,
            is_active=True
        ).first()

        if service is None:
            raise ValueError("Услуга не найдена или отключена")

        duration = service.duration_minutes

        # Воскресенье — выходной
        if target_date.weekday() == 6:
            return []

        # Начало и конец рабочего дня
        work_start = datetime.combine(
            target_date, OPEN_TIME, tzinfo=TIMEZONE
        )

        work_end = datetime.combine(
            target_date, CLOSE_TIME, tzinfo=TIMEZONE
        )

        now = datetime.now(TIMEZONE)

        available_slots = []
        current_time = work_start

        # Проверяем все интервалы с шагом 30 минут
        while current_time + timedelta(minutes=duration) <= work_end:

            end_time = current_time + timedelta(minutes=duration)

            # Прошедшее время не предлагаем
            if current_time > now:

                # Проверяем пересечение с существующими заявками
                conflicting_appointment = session.query(
                    Appointment
                ).filter(
                    Appointment.start_at < end_time,
                    Appointment.end_at > current_time,
                    Appointment.status != "cancelled"
                ).first()

                if conflicting_appointment is None:
                    available_slots.append({
                        "start": current_time.strftime("%H:%M"),
                        "end": end_time.strftime("%H:%M")
                    })

            current_time += timedelta(minutes=SLOT_INTERVAL)

        return available_slots

    finally:
        session.close()
