
from datetime import datetime, date, time, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from database.database import SessionLocal
from database.models import Service, Client, Appointment
from backend.booking import TIMEZONE, OPEN_TIME, CLOSE_TIME, SLOT_INTERVAL


def create_appointment(
    client_name: str,
    client_phone: str,
    service_code: str,
    car_brand: str,
    car_model: str,
    car_size: str,
    appointment_date: date,
    start_time: time,
    comment: str = None
):
    """Создаёт заявку на обслуживание автомобиля."""

    # Проверяем обязательные данные
    if not all([
        client_name.strip(),
        client_phone.strip(),
        car_brand.strip(),
        car_model.strip()
    ]):
        raise ValueError("Заполните все обязательные поля")

    if car_size not in ("small", "medium", "large"):
        raise ValueError("Некорректный размер автомобиля")

    if appointment_date.weekday() == 6:
        raise ValueError("В воскресенье центр не работает")

    if start_time.minute % SLOT_INTERVAL != 0 or start_time.second != 0:
        raise ValueError("Время записи должно быть кратно 30 минутам")

    start_at = datetime.combine(
        appointment_date,
        start_time,
        tzinfo=TIMEZONE
    )

    if start_at <= datetime.now(TIMEZONE):
        raise ValueError("Нельзя записаться на прошедшее время")

    session = SessionLocal()

    try:
        # Находим услугу
        service = session.query(Service).filter_by(
            code=service_code,
            is_active=True
        ).first()

        if service is None:
            raise ValueError("Услуга не найдена или отключена")

        # Получаем стоимость и продолжительность
        price_field = f"price_{car_size}"
        price = getattr(service, price_field)

        duration = service.duration_minutes
        end_at = start_at + timedelta(minutes=duration)

        # Проверяем рабочее время
        work_start = datetime.combine(
            appointment_date,
            OPEN_TIME,
            tzinfo=TIMEZONE
        )

        work_end = datetime.combine(
            appointment_date,
            CLOSE_TIME,
            tzinfo=TIMEZONE
        )

        if start_at < work_start or end_at > work_end:
            raise ValueError("Выбранное время выходит за рабочие часы")

        # Проверяем пересечение с существующими заявками
        conflict = session.query(Appointment).filter(
            Appointment.start_at < end_at,
            Appointment.end_at > start_at,
            Appointment.status != "cancelled"
        ).first()

        if conflict:
            raise ValueError("Это время уже занято. Выберите другое.")

        # Ищем клиента по номеру телефона
        client = session.query(Client).filter_by(
            phone=client_phone.strip()
        ).first()

        if client is None:
            client = Client(
                name=client_name.strip(),
                phone=client_phone.strip()
            )
            session.add(client)
            session.flush()

        else:
            # Обновляем имя, если клиент уже есть
            client.name = client_name.strip()

        # Создаём заявку
        appointment = Appointment(
            client_id=client.id,
            service_id=service.id,
            car_brand=car_brand.strip(),
            car_model=car_model.strip(),
            car_size=car_size,
            start_at=start_at,
            end_at=end_at,
            estimated_price=price,
            status="new",
            comment=comment
        )

        session.add(appointment)
        session.commit()

        return {
            "success": True,
            "appointment_id": appointment.id,
            "client_name": client.name,
            "service": service.name,
            "car": f"{car_brand} {car_model}",
            "date": appointment_date.isoformat(),
            "start": start_time.strftime("%H:%M"),
            "end": end_at.strftime("%H:%M"),
            "price": str(price),
            "status": appointment.status
        }

    except IntegrityError as error:
        session.rollback()

        # PostgreSQL: нарушение ограничения пересечения записей
        original_error = getattr(error, "orig", None)
        error_code = getattr(original_error, "pgcode", None)

        if error_code == "23P01":
            raise ValueError(
                "Это время только что заняли. Выберите другое."
            ) from error

        raise

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
