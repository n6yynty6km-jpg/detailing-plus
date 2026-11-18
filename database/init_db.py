from database.database import Base, engine, SessionLocal
from database.models import Service, Client, Appointment


# Создаём таблицы
Base.metadata.create_all(bind=engine)

print("Таблицы успешно созданы!")

# Добавляем демонстрационные услуги
session = SessionLocal()

try:
    services = [
        Service(
            code="wash",
            name="Мойка кузова",
            description="Мойка автомобиля",
            price_small=1000,
            price_medium=1300,
            price_large=1600,
            duration_minutes=60,
        ),
        Service(
            code="cleaning",
            name="Химчистка салона",
            description="Глубокая химчистка салона автомобиля",
            price_small=5000,
            price_medium=6500,
            price_large=8000,
            duration_minutes=240,
        ),
        Service(
            code="polishing",
            name="Полировка кузова",
            description="Полировка лакокрасочного покрытия",
            price_small=8000,
            price_medium=11000,
            price_large=14000,
            duration_minutes=300,
        ),
        Service(
            code="coating",
            name="Защитные покрытия",
            description="Нанесение защитного покрытия",
            price_small=7000,
            price_medium=9000,
            price_large=12000,
            duration_minutes=240,
        ),
    ]

    for service in services:
        existing = session.query(Service).filter_by(
            code=service.code
        ).first()

        if existing is None:
            session.add(service)

    session.commit()
    print("Демонстрационные услуги добавлены!")

except Exception:
    session.rollback()
    raise

finally:
    session.close()
